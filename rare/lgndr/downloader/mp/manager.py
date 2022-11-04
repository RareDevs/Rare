import logging
import os
import queue
import time
from multiprocessing import Queue as MPQueue
from multiprocessing.shared_memory import SharedMemory
from sys import exit
from threading import Condition, Thread

from legendary.downloader.mp.manager import DLManager as DLManagerReal
from legendary.downloader.mp.workers import DLWorker, FileWorker
from legendary.models.downloading import ChunkTask, SharedMemorySegment, TerminateWorkerTask

from rare.lgndr.glue.monkeys import DLManagerSignals
from rare.lgndr.models.downloading import UIUpdate


# fmt: off
class DLManager(DLManagerReal):
    # Rare: prototype to avoid undefined variable in type checkers
    signals_queue: MPQueue

    # @staticmethod
    def run_real(self):
        self.shared_memory = SharedMemory(create=True, size=self.max_shared_memory)
        self.log.debug(f'Created shared memory of size: {self.shared_memory.size / 1024 / 1024:.02f} MiB')

        # create the shared memory segments and add them to their respective pools
        for i in range(int(self.shared_memory.size / self.analysis.biggest_chunk)):
            _sms = SharedMemorySegment(offset=i * self.analysis.biggest_chunk,
                                       end=i * self.analysis.biggest_chunk + self.analysis.biggest_chunk)
            self.sms.append(_sms)

        self.log.debug(f'Created {len(self.sms)} shared memory segments.')

        # Create queues
        self.dl_worker_queue = MPQueue(-1)
        self.writer_queue = MPQueue(-1)
        self.dl_result_q = MPQueue(-1)
        self.writer_result_q = MPQueue(-1)

        self.log.info(f'Starting download workers...')
        for i in range(self.max_workers):
            w = DLWorker(f'DLWorker {i + 1}', self.dl_worker_queue, self.dl_result_q,
                         self.shared_memory.name, logging_queue=self.logging_queue,
                         dl_timeout=self.dl_timeout)
            self.children.append(w)
            w.start()

        self.log.info('Starting file writing worker...')
        writer_p = FileWorker(self.writer_queue, self.writer_result_q, self.dl_dir,
                              self.shared_memory.name, self.cache_dir, self.logging_queue)
        self.children.append(writer_p)
        writer_p.start()

        num_chunk_tasks = sum(isinstance(t, ChunkTask) for t in self.tasks)
        num_dl_tasks = len(self.chunks_to_dl)
        num_tasks = len(self.tasks)
        num_shared_memory_segments = len(self.sms)
        self.log.debug(f'Chunks to download: {num_dl_tasks}, File tasks: {num_tasks}, Chunk tasks: {num_chunk_tasks}')

        # active downloader tasks
        self.active_tasks = 0
        processed_chunks = 0
        processed_tasks = 0
        total_dl = 0
        total_write = 0

        # synchronization conditions
        shm_cond = Condition()
        task_cond = Condition()
        self.conditions = [shm_cond, task_cond]

        # start threads
        s_time = time.time()
        self.threads.append(Thread(target=self.download_job_manager, args=(task_cond, shm_cond)))
        self.threads.append(Thread(target=self.dl_results_handler, args=(task_cond,)))
        self.threads.append(Thread(target=self.fw_results_handler, args=(shm_cond,)))

        for t in self.threads:
            t.start()

        last_update = time.time()

        # Rare: kill requested
        kill_request = False

        while processed_tasks < num_tasks:
            delta = time.time() - last_update
            if not delta:
                time.sleep(self.update_interval)
                continue

            # update all the things
            processed_chunks += self.num_processed_since_last
            processed_tasks += self.num_tasks_processed_since_last

            total_dl += self.bytes_downloaded_since_last
            total_write += self.bytes_written_since_last

            dl_speed = self.bytes_downloaded_since_last / delta
            dl_unc_speed = self.bytes_decompressed_since_last / delta
            w_speed = self.bytes_written_since_last / delta
            r_speed = self.bytes_read_since_last / delta
            # c_speed = self.num_processed_since_last / delta

            # set temporary counters to 0
            self.bytes_read_since_last = self.bytes_written_since_last = 0
            self.bytes_downloaded_since_last = self.num_processed_since_last = 0
            self.bytes_decompressed_since_last = self.num_tasks_processed_since_last = 0
            last_update = time.time()

            perc = (processed_chunks / num_chunk_tasks) * 100
            runtime = time.time() - s_time
            total_avail = len(self.sms)
            total_used = (num_shared_memory_segments - total_avail) * (self.analysis.biggest_chunk / 1024 / 1024)

            if runtime and processed_chunks:
                average_speed = processed_chunks / runtime
                estimate = (num_chunk_tasks - processed_chunks) / average_speed
                hours, estimate = int(estimate // 3600), estimate % 3600
                minutes, seconds = int(estimate // 60), int(estimate % 60)

                rt_hours, runtime = int(runtime // 3600), runtime % 3600
                rt_minutes, rt_seconds = int(runtime // 60), int(runtime % 60)
            else:
                estimate = 0
                hours = minutes = seconds = 0
                rt_hours = rt_minutes = rt_seconds = 0

            # Rare: Disable up to INFO logging level for the segment below
            log_level = self.log.level
            self.log.setLevel(logging.ERROR)
            self.log.info(f'= Progress: {perc:.02f}% ({processed_chunks}/{num_chunk_tasks}), '
                          f'Running for {rt_hours:02d}:{rt_minutes:02d}:{rt_seconds:02d}, '
                          f'ETA: {hours:02d}:{minutes:02d}:{seconds:02d}')
            self.log.info(f' - Downloaded: {total_dl / 1024 / 1024:.02f} MiB, '
                          f'Written: {total_write / 1024 / 1024:.02f} MiB')
            self.log.info(f' - Cache usage: {total_used:.02f} MiB, active tasks: {self.active_tasks}')
            self.log.info(f' + Download\t- {dl_speed / 1024 / 1024:.02f} MiB/s (raw) '
                          f'/ {dl_unc_speed / 1024 / 1024:.02f} MiB/s (decompressed)')
            self.log.info(f' + Disk\t- {w_speed / 1024 / 1024:.02f} MiB/s (write) / '
                          f'{r_speed / 1024 / 1024:.02f} MiB/s (read)')
            # Rare: Restore previous logging level
            self.log.setLevel(log_level)

            # send status update to back to instantiator (if queue exists)
            if self.status_queue:
                try:
                    self.status_queue.put(UIUpdate(
                        progress=perc, download_speed=dl_unc_speed, write_speed=w_speed, read_speed=r_speed,
                        runtime=round(runtime),
                        estimated_time_left=round(estimate),
                        processed_chunks=processed_chunks,
                        chunk_tasks=num_chunk_tasks,
                        total_downloaded=total_dl,
                        total_written=total_write,
                        cache_usage=total_used,
                        active_tasks=self.active_tasks,
                        download_compressed_speed=dl_speed,
                        memory_usage=total_used * 1024 * 1024
                    ), timeout=1.0)
                except Exception as e:
                    self.log.warning(f'Failed to send status update to queue: {e!r}')

            # Rare: queue of control signals
            try:
                signals: DLManagerSignals = self.signals_queue.get(timeout=0.5)
                self.log.warning('Immediate stop requested!')
                if signals.kill is True:
                    # lk: graceful but not what legendary does
                    self.running = False
                    # send conditions to unlock threads if they aren't already
                    for cond in self.conditions:
                        with cond:
                            cond.notify()
                    kill_request = True
                    break
                    # # lk: alternative way, but doesn't clean shm
                    # for i in range(self.max_workers):
                    #     self.dl_worker_queue.put_nowait(TerminateWorkerTask())
                    #
                    # self.log.info('Waiting for installation to finish...')
                    # self.writer_queue.put_nowait(TerminateWorkerTask())
                    # raise KeyboardInterrupt
            except queue.Empty:
                pass

            time.sleep(self.update_interval)

        for i in range(self.max_workers):
            self.dl_worker_queue.put_nowait(TerminateWorkerTask())

        self.log.info('Waiting for installation to finish...')
        self.writer_queue.put_nowait(TerminateWorkerTask())

        writer_p.join(timeout=10.0)
        if writer_p.exitcode is None:
            self.log.warning(f'Terminating writer process, no exit code!')
            writer_p.terminate()

        # forcibly kill DL workers that are not actually dead yet
        for child in self.children:
            if child.exitcode is None:
                child.terminate()

        # make sure all the threads are dead.
        for t in self.threads:
            t.join(timeout=5.0)
            if t.is_alive():
                self.log.warning(f'Thread did not terminate! {repr(t)}')

        # clean up resume file
        if self.resume_file and not kill_request:
            try:
                os.remove(self.resume_file)
            except OSError as e:
                self.log.warning(f'Failed to remove resume file: {e!r}')

        # close up shared memory
        self.shared_memory.close()
        self.shared_memory.unlink()
        self.shared_memory = None

        self.log.info('All done! Download manager quitting...')
        # finally, exit the process.
        exit(0)

# fmt: on
