from fastapi import APIRouter

from app.config import STORAGE_NODES
from app.schemas import NodeHealthResponse

router = APIRouter(prefix="/nodes", tags=["Nodes"])


@router.get("/health", response_model=list[NodeHealthResponse])
def check_nodes_health():
    health_status = []

    for node_name, node_path in STORAGE_NODES.items():
        if node_path.exists() and node_path.is_dir():
            status = "alive"
        else:
            status = "dead"

        health_status.append(
            NodeHealthResponse(
                node_name=node_name,
                path=str(node_path),
                status=status
            )
        )

    return health_status