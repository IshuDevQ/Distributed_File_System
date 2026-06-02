from typing import Generator

from app.config import CHUNK_SIZE


def chunk_bytes(data: bytes) -> Generator[tuple[int, bytes], None, None]:
    """
    Splits bytes into chunks.

    Yields:
        tuple: (chunk_index, chunk_data)
    """

    chunk_index = 0

    for start in range(0, len(data), CHUNK_SIZE):
        end = start + CHUNK_SIZE
        yield chunk_index, data[start:end]
        chunk_index += 1