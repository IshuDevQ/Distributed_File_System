## Overview

The Distributed File Storage System stores uploaded files by splitting them into smaller fixed-size chunks. Each chunk is replicated across multiple storage nodes. Metadata about files, chunks, hashes, and replica locations is stored in a database.

When a user downloads a file, the system reconstructs the original file by reading the chunks in order from available replicas. Each chunk is verified using SHA-256 hashing before being used. If a node fails, the system can still serve files using replicas from other nodes. The repair service can recreate missing replicas after the failed node is restored or another healthy node is available.

---

## Features

- File upload and download through REST APIs
- Fixed-size file chunking
- Chunk-level replication across multiple storage nodes
- Metadata service using SQLite and SQLAlchemy
- SHA-256 based file and chunk integrity verification
- Storage-node health check API
- Automatic re-replication for under-replicated chunks
- Structured application logging
- Docker and Docker Compose support
- Swagger UI for API testing
- Local filesystem-based distributed storage simulation

---

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Docker
- Docker Compose
- Local filesystem storage
- SHA-256 hashing

---

## System Architecture

```text
Client / Browser / curl
        |
        v
FastAPI Application
        |
        |---- Metadata Service
        |          |
        |          v
        |      SQLite Database
        |
        |---- Storage Node 1
        |---- Storage Node 2
        |---- Storage Node 3
```

The FastAPI application acts as both the API gateway and metadata service. The storage nodes are represented as separate local directories. This makes the project simple to run locally while still demonstrating distributed storage concepts.

---

## How the System Works

### 1. File Upload

When a file is uploaded:

1. The API receives the file.
2. The full file is read as bytes.
3. A SHA-256 hash is calculated for the complete file.
4. The file is split into fixed-size chunks.
5. A SHA-256 hash is calculated for each chunk.
6. Each chunk is replicated across multiple storage nodes.
7. File, chunk, and replica metadata are saved in the database.

Example:

```text
sample.pdf
   |
   v
chunk_0, chunk_1, chunk_2, chunk_3
   |
   v
replicated across node1, node2, node3
```

---

### 2. File Download

When a file is downloaded:

1. The system fetches the file metadata from the database.
2. It finds all chunks belonging to that file.
3. Chunks are sorted by chunk index.
4. For each chunk, the system searches for a valid replica.
5. The chunk hash is verified using SHA-256.
6. Verified chunks are merged in the correct order.
7. The reconstructed file hash is compared with the original file hash.
8. The final file is returned to the user.

This ensures that corrupted or missing replicas are not used during reconstruction.

---

### 3. Replication Strategy

The project uses a configurable replication factor.

For example, with 3 storage nodes and replication factor 2:

```text
chunk_0 -> node1, node2
chunk_1 -> node2, node3
chunk_2 -> node3, node1
chunk_3 -> node1, node2
```

This round-robin strategy distributes chunks across nodes instead of storing every chunk on the same two nodes.

---

### 4. Node Health Checks

The system checks whether each storage-node directory exists and is accessible.

Example health response:

```text
node1 -> alive
node2 -> dead
node3 -> alive
```

A node failure can be simulated by deleting one of the storage-node directories.

---

### 5. Automatic Repair

If a chunk has fewer valid replicas than the configured replication factor, the repair service attempts to restore the missing replica by copying data from an existing valid replica to another alive node.

This demonstrates basic fault recovery in a distributed storage system.

---

## Project Structure

```text
distributed-file-storage/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   │
│   ├── services/
│   │   ├── chunker.py
│   │   ├── storage.py
│   │   ├── replication.py
│   │   ├── metadata.py
│   │   └── repair.py
│   │
│   ├── routers/
│   │   ├── files.py
│   │   ├── nodes.py
│   │   └── repair.py
│   │
│   └── utils/
│       ├── hashing.py
│       └── logger.py
│
├── storage_nodes/
│   ├── node1/
│   ├── node2/
│   └── node3/
│
├── downloads/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Check whether the service is running |
| `POST` | `/files/upload` | Upload a file |
| `GET` | `/files` | List all uploaded files |
| `GET` | `/files/{file_id}` | Get metadata for a specific file |
| `GET` | `/files/{file_id}/download` | Download and reconstruct a file |
| `GET` | `/nodes/health` | Check storage-node health |
| `POST` | `/repair/run` | Repair under-replicated chunks |

Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

or when using Docker:

```text
http://localhost:8000/docs
```

---

## Running Locally

### 1. Clone the Repository

```bash
git clone https://github.com/IshuDevQ/Distributed_File_System.git
cd Distributed_File_System
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

For Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the FastAPI Application

```bash
uvicorn app.main:app --reload
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Running with Docker

Make sure Docker Desktop is running before using Docker Compose.

### 1. Build and Run

```bash
docker compose up --build
```

Open:

```text
http://localhost:8000/docs
```

### 2. Run in Detached Mode

```bash
docker compose up --build -d
```

### 3. View Logs

```bash
docker compose logs -f
```

### 4. Stop the Container

```bash
docker compose down
```

---

## Example Usage

### Upload a File

Using Swagger UI:

```text
POST /files/upload
```

Using curl:

```bash
curl -X POST "http://127.0.0.1:8000/files/upload" \
  -F "uploaded_file=@sample.txt"
```

---

### List Uploaded Files

```bash
curl http://127.0.0.1:8000/files
```

---

### Get File Metadata

```bash
curl http://127.0.0.1:8000/files/1
```

---

### Download a File

```bash
curl -OJ http://127.0.0.1:8000/files/1/download
```

---

### Check Node Health

```bash
curl http://127.0.0.1:8000/nodes/health
```

---

## Failure Simulation and Repair

### 1. Upload a File

Upload any file using Swagger UI or curl.

### 2. Simulate Storage Node Failure

Delete one storage-node directory:

```bash
rm -rf storage_nodes/node2
```

### 3. Check Node Health

```bash
curl http://127.0.0.1:8000/nodes/health
```

Expected result:

```text
node1 -> alive
node2 -> dead
node3 -> alive
```

### 4. Restore the Failed Node

```bash
mkdir -p storage_nodes/node2
```

### 5. Run Repair

```bash
curl -X POST http://127.0.0.1:8000/repair/run
```

The system will try to copy missing chunks from valid replicas to restore the desired replication factor.

---

## Configuration

Important values are configured in:

```text
app/config.py
```

Example configuration:

```python
CHUNK_SIZE = 1024 * 1024
REPLICATION_FACTOR = 2
```

- `CHUNK_SIZE` controls the size of each file chunk.
- `REPLICATION_FACTOR` controls how many copies of each chunk are stored.
- `STORAGE_NODES` defines the available storage-node directories.

---

## Database Design

The system uses three main tables.

### Files Table

Stores file-level metadata:

- File name
- Content type
- File size
- Full file hash
- Total number of chunks
- Upload timestamp

### Chunks Table

Stores chunk-level metadata:

- File ID
- Chunk index
- Chunk hash
- Chunk size

### Chunk Replicas Table

Stores replica-level metadata:

- Chunk ID
- Storage node name
- Chunk path

---

## Integrity Verification

The system uses SHA-256 hashing for integrity checks.

During upload:

- The complete file hash is calculated.
- Each chunk hash is calculated.
- Metadata is stored in the database.

During download:

- Each chunk replica is verified before use.
- Corrupted replicas are skipped.
- The reconstructed file is verified against the original file hash.

This prevents corrupted or incomplete data from being returned to the user.

---

## Resume Description

**Distributed File Storage System with Replication and Metadata Service**

- Built a distributed file storage backend using FastAPI, SQLite, and Docker Compose with support for file upload, download, chunking, and metadata tracking.
- Implemented chunk-level replication across multiple storage nodes using a configurable replication factor and round-robin placement strategy.
- Designed a metadata service to track file hashes, chunk hashes, replica locations, and storage-node mappings.
- Added file integrity verification using SHA-256 hashes during upload, storage, and download reconstruction.
- Implemented node health checks and automatic re-replication to restore missing replicas after simulated node failures.
- Containerized the application using Docker Compose with persistent storage volumes for node data and metadata.

---

## Future Improvements

- Replace SQLite with PostgreSQL
- Run each storage node as an independent FastAPI service
- Add background scheduled health checks
- Add user authentication and file ownership
- Add file deletion API
- Add async streaming upload for large files
- Add unit and integration tests
- Add Prometheus and Grafana monitoring
- Add CLI client for uploads and downloads
- Deploy using AWS EC2, Docker Compose, or Kubernetes

---

## Author

**Ishu Dev**

GitHub: [IshuDevQ](https://github.com/IshuDevQ)