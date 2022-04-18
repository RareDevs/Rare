from dataclasses import dataclass

@dataclass
class UIUpdate:
    """
    Status update object sent from the manager to the CLI/GUI to update status indicators
    """

    def __init__(self, progress, runtime, estimated_time_left, processed_chunks, chunk_tasks,
                 total_downloaded, total_written, cache_usage, active_tasks, download_speed,
                 download_decompressed_speed, write_speed, read_speed, memory_usage, current_filename=''):
        self.progress = progress
        self.runtime = runtime
        self.estimated_time_left = estimated_time_left
        self.processed_chunks = processed_chunks
        self.chunk_tasks = chunk_tasks
        self.total_downloaded = total_downloaded
        self.total_written = total_written
        self.cache_usage = cache_usage
        self.active_tasks = active_tasks
        self.download_speed = download_speed
        self.download_decompressed_speed = download_decompressed_speed
        self.write_speed = write_speed
        self.read_speed = read_speed
        self.memory_usage = memory_usage
        self.current_filename = current_filename
