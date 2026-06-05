import random
from typing import List

from app.config import (
    STORAGE_NODES,
    REPLICATION_FACTOR,
    REPLICATION_STRATEGY,
    CANARY_PERCENTAGE,
)
from app.services.storage import store_chunk


def should_use_canary_strategy() -> bool:
    if CANARY_PERCENTAGE <= 0:
        return False

    return random.randint(1, 100) <= CANARY_PERCENTAGE


def choose_replica_nodes_round_robin(chunk_index: int) -> List[str]:
    node_names = list(STORAGE_NODES.keys())
    total_nodes = len(node_names)

    selected_nodes = []

    for i in range(REPLICATION_FACTOR):
        node_index = (chunk_index + i) % total_nodes
        selected_nodes.append(node_names[node_index])

    return selected_nodes


def choose_replica_nodes_reverse_round_robin(chunk_index: int) -> List[str]:
    node_names = list(reversed(STORAGE_NODES.keys()))
    total_nodes = len(node_names)

    selected_nodes = []

    for i in range(REPLICATION_FACTOR):
        node_index = (chunk_index + i) % total_nodes
        selected_nodes.append(node_names[node_index])

    return selected_nodes


def choose_replica_nodes(chunk_index: int) -> List[str]:
    strategy = REPLICATION_STRATEGY

    if should_use_canary_strategy():
        strategy = "reverse_round_robin"

    if strategy == "reverse_round_robin":
        return choose_replica_nodes_reverse_round_robin(chunk_index)

    return choose_replica_nodes_round_robin(chunk_index)


def replicate_chunk(
    file_id: int,
    chunk_index: int,
    chunk_data: bytes
) -> list[tuple[str, str]]:
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