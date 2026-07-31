## Storage Configuration

The GIS MCP Server stores files used for reading, writing, and downloading geospatial data. Two storage backends are supported:

1. **Local filesystem** — default; files under `~/.gis_mcp/data/` (or a custom path)
2. **Google Cloud Storage (GCP)** — use when you want files in a GCS bucket

---

## Local filesystem storage

This is the default. Configure it with `--storage-path` or `GIS_MCP_STORAGE_PATH`.

### Custom storage folder

1. **Command-line argument:**

   ```bash
   gis-mcp --storage-path /path/to/your/storage
   ```

2. **Environment variable:**

   ```bash
   export GIS_MCP_STORAGE_PATH=/path/to/your/storage
   gis-mcp
   ```

On Windows PowerShell:

```powershell
$env:GIS_MCP_STORAGE_PATH="C:\path\to\your\storage"
gis-mcp
```

### Default storage location

If no path is set, the server uses:

- **Default:** `~/.gis_mcp/data/`
  - Linux/Mac: `/home/username/.gis_mcp/data/`
  - Windows: `C:\Users\username\.gis_mcp\data\`

The directory is created automatically if it does not exist.

### How local storage works

- **File writes:** Tools such as `write_file_gpd`, `write_raster`, or `save_results` resolve relative paths against the storage directory. Absolute paths are used as-is.
- **Data downloads:** Downloaded data is saved under subdirectories of the storage folder:
  - `movement_data/` — street networks
  - `land_products/` — land cover
  - `satellite_imagery/` — satellite imagery
  - `ecology_data/` — species occurrences
  - `climate_data/` — climate datasets
  - `administrative_boundaries/` — administrative boundaries
  - `outputs/` — general outputs

### MCP client example (local)

**Claude Desktop / Cursor:**

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "/home/YourUsername/.venv/bin/gis-mcp",
      "args": ["--storage-path", "/custom/path/to/storage"]
    }
  }
}
```

Windows:

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "C:\\\\Users\\\\YourUsername\\\\.venv\\\\Scripts\\\\gis-mcp",
      "args": ["--storage-path", "C:\\\\custom\\\\path\\\\to\\\\storage"]
    }
  }
}
```

### Persist the local path in your shell

```bash
export GIS_MCP_STORAGE_PATH=/custom/path/to/storage
```

PowerShell:

```powershell
$env:GIS_MCP_STORAGE_PATH="C:\custom\path\to\storage"
```

---

## Google Cloud Storage (GCP)

Use this backend when you want the server to read and write files in a **Google Cloud Storage** bucket instead of (or in addition to caching on) a local disk path.

### Why use a GCS bucket?

Local storage is fine for a single machine or a Docker volume on one host. A GCS bucket helps when geospatial files need to live in shared, durable cloud storage:

- **Shared access** — several agents, servers, or teammates can use the same layers and outputs without copying files between machines
- **Durable object storage** — rasters, shapefiles, and downloads survive container restarts and host replacement (no reliance on ephemeral container disks)
- **Fits cloud deployments** — natural choice when GIS MCP runs on GCE, GKE, Cloud Run, or other GCP workloads next to your data lake / pipeline buckets
- **Scalable data volume** — large imagery and climate downloads are not limited by a single VM disk; you pay for objects you store
- **Clear separation** — keep tool working files under a bucket prefix (e.g. `gis-data/`) while apps and pipelines read/write the same objects

**Typical use cases:** multi-user or multi-agent GIS workflows; HTTP-mode servers in the cloud that upload/download via `/storage/*`; keeping satellite, climate, or movement downloads in a project bucket; handing analysis outputs to downstream GCP jobs (BigQuery loaders, Dataflow, another service).

### Install

```bash
pip install gis-mcp[gcp]
```

(`gis-mcp[all]` also includes the GCP client.)

### Configuration

```json
{
  "provider": "gcp",
  "bucket": "my-gis-bucket",
  "prefix": "gis-data/",
  "credentials": "/path/to/service-account.json"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `provider` | yes | `"gcp"` |
| `bucket` | yes | GCS bucket name |
| `prefix` | no | Object prefix (e.g. `gis-data/`) |
| `credentials` | no | Path to a service-account JSON key |
| `project` | no | GCP project ID (often inferred from credentials) |
| `local_cache` | no | Local cache for GIS tools (default: `~/.gis_mcp/gcp_cache/<bucket>/`) |

**CLI:**

```bash
gis-mcp --storage-config '{"provider":"gcp","bucket":"my-gis-bucket","prefix":"gis-data/"}'
```

Or a JSON file:

```bash
gis-mcp --storage-config /path/to/storage.json
```

**Single env var:**

```bash
export GIS_MCP_STORAGE_CONFIG='{"provider":"gcp","bucket":"my-gis-bucket","prefix":"gis-data/"}'
gis-mcp
```

**Separate env vars:**

```bash
export GIS_MCP_STORAGE_PROVIDER=gcp
export GIS_MCP_GCS_BUCKET=my-gis-bucket
export GIS_MCP_GCS_PREFIX=gis-data/
export GIS_MCP_GCS_CREDENTIALS=/path/to/service-account.json   # if using a key file
gis-mcp
```

### Credentials

Resolved in this order:

1. `credentials` in `storage_config` (or `GIS_MCP_GCS_CREDENTIALS`)
2. `GOOGLE_APPLICATION_CREDENTIALS`
3. [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)

The path must be readable by the **process that runs `gis-mcp`**:

- **Linux host (no Docker):** path on the host
- **Docker:** path **inside the container**, with the host key mounted there

#### Linux — run on the host

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/home/ubuntu/secrets/gis-mcp-sa.json
export GIS_MCP_STORAGE_PROVIDER=gcp
export GIS_MCP_GCS_BUCKET=my-gis-bucket
export GIS_MCP_GCS_PREFIX=gis-data/
gis-mcp
```

Or:

```bash
gis-mcp --storage-config '{
  "provider": "gcp",
  "bucket": "my-gis-bucket",
  "prefix": "gis-data/",
  "credentials": "/home/ubuntu/secrets/gis-mcp-sa.json"
}'
```

#### Linux — run in Docker

Env vars use the **container** path; mount the host key into that path:

```bash
# Host:      /home/ubuntu/secrets/gis-mcp-sa.json
# Container: /secrets/gis-mcp-sa.json
docker run -p 9010:9010 \
  -e GIS_MCP_STORAGE_PROVIDER=gcp \
  -e GIS_MCP_GCS_BUCKET=my-gis-bucket \
  -e GIS_MCP_GCS_PREFIX=gis-data/ \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/gis-mcp-sa.json \
  -v /home/ubuntu/secrets/gis-mcp-sa.json:/secrets/gis-mcp-sa.json:ro \
  gis-mcp
```

### Bucket access (IAM)

The server **reads, writes, and lists** objects in the bucket:

| Operation | Used for |
|-----------|----------|
| Write / upload | `POST /storage/upload` |
| Read / download | `GET /storage/download` |
| List | `GET /storage/list` |

Recommended role on the bucket: **`roles/storage.objectUser`** (Storage Object User).

Minimum custom permissions:

- `storage.objects.create`
- `storage.objects.get`
- `storage.objects.list`

```bash
gcloud storage buckets add-iam-policy-binding gs://my-gis-bucket \
  --member="serviceAccount:gis-mcp@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectUser"
```

Do not use read-only roles such as `roles/storage.objectViewer` if you need uploads.

### How GCP storage works

- Storage HTTP endpoints read and write objects in the configured bucket (under the prefix, if set).
- GIS tools that need real filesystem paths use a local cache; files written through the storage API are mirrored into that cache.
- Local path settings (`--storage-path` / `GIS_MCP_STORAGE_PATH`) continue to use the local filesystem backend.

### MCP client example (GCP on Linux host)

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "/home/YourUsername/.venv/bin/gis-mcp",
      "args": [
        "--storage-config",
        "{\"provider\":\"gcp\",\"bucket\":\"my-gis-bucket\",\"prefix\":\"gis-data/\"}"
      ],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/home/YourUsername/secrets/gis-mcp-sa.json"
      }
    }
  }
}
```

---

## Docker

In Docker (`Dockerfile` or `Dockerfile.local`), container filesystem data is ephemeral unless you mount a volume. Use a volume for **local** storage, or configure **GCP** when you want a GCS bucket.

### Local storage with volumes

#### Host directory mount

```bash
# Linux/Mac
docker run -p 9010:9010 \
  -v /home/user/gis-data:/app/.gis_mcp/data \
  gis-mcp

# Windows
docker run -p 9010:9010 \
  -v C:\gis-data:/app/.gis_mcp/data \
  gis-mcp
```

#### Named volume

```bash
docker volume create gis-mcp-storage

docker run -p 9010:9010 \
  -v gis-mcp-storage:/app/.gis_mcp/data \
  gis-mcp
```

#### Custom path inside the container

```bash
docker run -p 9010:9010 \
  -v /host/path/to/storage:/container/storage \
  -e GIS_MCP_STORAGE_PATH=/container/storage \
  gis-mcp
```

Default path in the image is `/app/.gis_mcp/data/` unless you set `GIS_MCP_STORAGE_PATH`.

### GCP storage in Docker

Images built with `gis-mcp[all]` include the GCP client. Point credentials at a path **inside the container** and mount the host key:

```bash
docker run -p 9010:9010 \
  -e GIS_MCP_STORAGE_PROVIDER=gcp \
  -e GIS_MCP_GCS_BUCKET=my-gis-bucket \
  -e GIS_MCP_GCS_PREFIX=gis-data/ \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/gis-mcp-sa.json \
  -v /home/ubuntu/secrets/gis-mcp-sa.json:/secrets/gis-mcp-sa.json:ro \
  gis-mcp
```

Docker Compose (Linux, GCP):

```yaml
services:
  gis-mcp:
    image: gis-mcp:latest
    ports:
      - "9010:9010"
    environment:
      - GIS_MCP_TRANSPORT=http
      - GIS_MCP_HOST=0.0.0.0
      - GIS_MCP_PORT=9010
      - GIS_MCP_STORAGE_PROVIDER=gcp
      - GIS_MCP_GCS_BUCKET=my-gis-bucket
      - GIS_MCP_GCS_PREFIX=gis-data/
      - GOOGLE_APPLICATION_CREDENTIALS=/secrets/gis-mcp-sa.json
    volumes:
      - /home/ubuntu/secrets/gis-mcp-sa.json:/secrets/gis-mcp-sa.json:ro
```

On GCE/GKE you can often omit the key file and use the attached service account (ADC).

### Docker Compose (local volume)

```yaml
version: "3.8"

services:
  gis-mcp:
    image: gis-mcp:latest
    ports:
      - "9010:9010"
    volumes:
      - gis-mcp-data:/app/.gis_mcp/data
    environment:
      - GIS_MCP_TRANSPORT=http
      - GIS_MCP_HOST=0.0.0.0
      - GIS_MCP_PORT=9010

volumes:
  gis-mcp-data:
```

### Managing volumes

```bash
docker volume ls
docker volume inspect gis-mcp-storage

# Backup
docker run --rm \
  -v gis-mcp-storage:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/gis-mcp-backup.tar.gz -C /data .

# Restore
docker run --rm \
  -v gis-mcp-storage:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/gis-mcp-backup.tar.gz -C /data

docker volume rm gis-mcp-storage
```

### Docker tips

- Prefer named volumes in production; host mounts are convenient for development
- Ensure the container user can write to mounted host directories
- Back up volumes regularly for important data
