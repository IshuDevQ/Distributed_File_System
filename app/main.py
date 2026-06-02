from fastapi import FastAPI

from app.database import Base, engine
from app.routers import files, nodes, repair
from app.services.storage import ensure_storage_nodes_exist

Base.metadata.create_all(bind=engine)

ensure_storage_nodes_exist()

app = FastAPI(
    title="Distributed File Storage System",
    description="A Python-based distributed file storage system with chunking, replication, metadata service, and repair.",
    version="1.0.0"
)

app.include_router(files.router)
app.include_router(nodes.router)
app.include_router(repair.router)


@app.get("/")
def root():
    return {
        "message": "Distributed File Storage System is running"
    }