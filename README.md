# Space DB

Space is a high-performance, document-relational hybrid database management system implemented in Rust. It is engineered for low-latency data access and transactional durability, combining the structure of relational engines with the flexibility of document-oriented stores.

## Core Features

| Feature | Description |
|:--- |:--- |
| **Hybrid Engine** | Supports structured relational columns and flexible BSON document blobs. |
| **ACID Compliant** | Fully atomic, consistent, isolated, and durable via ARIES-style WAL. |
| **Slotted Storage** | 8KB binary pages with slotted-page architecture for variable-length records. |
| **Advanced Caching** | LRU-K Buffer Pool Manager to optimize memory usage and disk I/O. |
| **Custom Protocol** | High-speed TCP binary framing protocol on Port 4500. |
| **Async Core** | Powered by the Tokio runtime for high-concurrency connection handling. |

## System Requirements

* **Language:** Rust 1.75+
* **Operating System:** Linux, macOS, Windows
* **Architecture:** x86_64 or ARM64
* **Default Port:** 4500

## Quick Start

### 1. Build the Binary
```bash
cargo build --release
```

### 2. Initialize the Environment
Space requires a specific directory structure for data persistence. Ensure the following directories exist relative to the binary:
```bash
mkdir -p data/storage data/wal
```

### 3. Run the Server
```bash
./target/release/space
```
The server will start listening for TCP connections on `127.0.0.1:4500`.

## Project Structure

```text
space/
├── src/
│   ├── main.rs          # Entry point and server orchestration
│   ├── server/          # TCP transport and BSON command handler
│   ├── storage/         # Slotted pages, Pager, and Buffer Pool
│   ├── catalog/         # Metadata and schema management
│   └── common/          # Shared types and binary utilities
├── data/                # Persistent database files
│   ├── storage/         # .tbl files (Binary Pages)
│   └── wal/             # .wal files (Write-Ahead Logs)
└── ARCHITECTURE.md      # Detailed technical specifications
```

## Communication Protocol

Space uses a custom length-prefixed binary protocol. Every request must start with a 10-byte header.

### Binary Header Format
1. **Message Length (4 bytes):** Total frame size (Header + Payload + Checksum).
2. **Request ID (4 bytes):** Client-generated ID for request multiplexing.
3. **OpCode (2 bytes):** `0x00` for Ping, `0x01` for Command.

### Command Format (BSON)
Operations are sent as BSON documents. For example, a `find` operation:
```json
{
  "command": "find",
  "collection": "users",
  "filter": { "username": "sarthak" }
}
```

## Command Reference

| Command | Arguments | Description |
|:--- |:--- |:--- |
| `insert` | `collection`, `data` | Persists a new document to the specified collection. |
| `find` | `collection`, `filter` | Retrieves documents matching the BSON filter. |
| `update` | `collection`, `filter`, `update` | Modifies existing documents matching the filter. |
| `delete` | `collection`, `filter` | Removes documents matching the filter. |
| `ping` | N/A | Validates server connectivity and latency. |

## Internal Architecture

Space is built on a layered architecture to ensure isolation between the transport and storage concerns:

1. **Transport Layer:** Handles TCP state and asynchronous packet ingestion.
2. **Command Layer:** Decodes BSON payloads and validates schema constraints.
3. **Storage Layer:** Manages the Buffer Pool, Page fetching, and Slotted Record layout.
4. **Persistence Layer:** Direct I/O with the filesystem, utilizing Write-Ahead Logging for safety.

For a deep dive into the internal binary formats and recovery protocols, refer to [ARCHITECTURE.md](./ARCHITECTURE.md).

## Development Standards

* **Zero-Panic:** The system propagates results through the `thiserror` crate; `unwrap()` is strictly prohibited in the execution path.
* **Memory Safety:** Rust's borrow checker ensures memory safety; `unsafe` blocks are restricted to binary-to-struct casting in the storage engine.
* **Concurrency:** Fine-grained locking is managed via `parking_lot::RwLock` to provide high parallel read throughput.