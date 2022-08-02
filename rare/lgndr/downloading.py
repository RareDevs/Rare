from dataclasses import dataclass
from typing import Optional


@dataclass
class UIUpdate:
    """
        Status update object sent from the manager to the CLI/GUI to update status indicators
        Inheritance doesn't work due to optional arguments in UIUpdate proper
    """
    progress: float
    download_speed: float
    write_speed: float
    read_speed: float
    memory_usage: float
    runtime: float
    estimated_time_left: float
    processed_chunks: int
    chunk_tasks: int
    total_downloaded: float
    total_written: float
    cache_usage: float
    active_tasks: int
    download_compressed_speed: float
    current_filename: Optional[str] = None
