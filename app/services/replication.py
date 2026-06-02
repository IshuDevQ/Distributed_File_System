from typing import List

from app.config import STORAGE_NODES, REPLICATION_FACTOR
from app.services.storage import store_chunk


def choose_replica_nodes(chunk_index: int) -> List[str]:
    """
    Selects nodes for a chunk.

    We use round-robin placement so chunks are distributed evenly.
    """

    node_names = list(STORAGE_NODES.keys())
    total_nodes = len(node_names)

    selected_nodes = []

    for i in range(REPLICATION_FACTOR):
        node_index = (chunk_index + i) % total_nodes
        selected_nodes.append(node_names[node_index])

    return selected_nodes


def replicate_chunk(
    file_id: int,
    chunk_index: int,
    chunk_data: bytes
) -> list[tuple[str, str]]:
    """
    Stores the chunk on multiple nodes.

    Returns:
        list of (node_name, path)
    """

    replicas = []

    selected_nodes = choose_replica_nodes(chunk_index)

    for node_name in selected_nodes:
        path = store_chunk(
            node_name=node_name,
            file_id=file_id,
            chunk_index=chunk_index,
            chunk_data=chunk_data
        )

        replicas.append((node_name, path))

    return replicas