[🇰🇷 한국어 버전](README.md)

# 🌌 Scene Intelligence - Multimodal Video Semantic Search

> **Dashboard for Hybrid Video Semantic Search Engine** based on **Google Vertex AI and Gemini Embedding**.  
> Splits large videos into 10-second intervals and cross-analyzes textual/visual multimodal frames to instantly retrieve the most relevant **Scenes (Intervals)** for user queries.

---

## 🚀 Core Features

### 1. 🎞️ Ultra-precise 10s Interval Split (Video Split)
- **FFmpeg-based Re-encoding Split**: Bypasses traditional keyframe limitations to generate **error-free, independent 10s video clips** with perfect continuity.

### 2. 🧠 Diverse Embedding Fusion Chain
- **Visual/Multimodal Embedding (`gemini-embedding-2-preview`)**: Projects the video's **visual composition, objects, and dynamic motions** directly into a multi-dimensional vector space via Vertex AI's next-gen embedding model.
- **Textual Description Generation (`gemini-3.1-flash-lite-preview`)**: Automatically generates descriptive text in **300-character descriptive units** using facts-only framing to augment framing accuracy.
- **Dense Text Embedding (`gemini-embedding-001`)**: The generated descriptions are processed into extreme-precision **3072-dimensional** dense vectors using Google's dedicated text embedding engine.

### 3. ⚖️ Hybrid RFF & AlloyDB Full-Text Search Fusion
- **AlloyDB pgvector Vector Search**: Visual and text vectors are processed using AlloyDB's `<=>` cosine distance operators for fast kNN approximation.
- **PostgreSQL Full-Text Search (FTS)**: Cross-references morph-based keyword weights via `to_tsvector` and `plainto_tsquery` together with `ts_rank_cd` scoring systems.
- **3-Way Reciprocal Rank Fusion (RRF)**: Weighs and merges Visual dense vectors, Text dense vectors, and Keyword FTS ranks fairly using Reciprocal Rank Fusion (RRF) standards to determine absolute winning clip scenes.

### 4. ⚡ Fully Async Architecture & High-Performance Pipeline
- **Background Cloud Storage Worker**: Segmented `.mp4` files are immediately dispatched into the **Google Cloud Storage** bucket to maintain zero footprint loads inside server disk mounts.
- **httpx Async Layer**: Swapped `requests` with `httpx.AsyncClient` to eliminate synchronous I/O blocking overhead natively Nodes.
- **asyncio.gather & Semaphore**: Replaced `ThreadPoolExecutor` with **`asyncio.Semaphore(5)`** + **`asyncio.gather`** for nearly zero worker context switching overhead Node.
- **OAuth Token Caching**: Isolated redundant `credentials.refresh()` inside a memory-buffered **`TokenCacheManager`** isolating authentication latency Node.
- **Stream Chunking Upload**: Re-engineered `/api/upload` to write iterative **`1MB chunks`** ensuring extreme RAM safety for large video file buffering Node.

### 5. 🗄️ Dashboard Sidebar & AlloyDB Detailed Viewer
- **Standard Sidebar Navigation**: Spaces out `🔍 영상 검색` (Search) and `🗄️ 적재 데이터` (Database) views into-dedicated seamless Tab views Node Productions.
- **Segment Detailed Grid Viewer (`/api/db_contents`)**: Unwraps video names, individual timestamps, & Gemini descriptions into a transparent spreadsheet loading array Node Productions.
- **Client-Side Live Filter & Pagination**: Employs live reactive memory search and `Prev/Next` split pagination bottom controls keeping dashboards fluid for heavy bulk buffers index 4 Nodes.

### 6. 🧹 Real-time Vector DB Clear (Clear Database)
- Supplies an admin-facing maintenance trigger with **`one-click layout buttons`** that completely drops AlloyDB rows and zeroes serve-state caches instantly for prototype-heavy recursions.

---

## 🛠️ Tech Stack

| Domain | Technical Specification |
| :--- | :--- |
| **Backend** | `FastAPI` (Async Streaming), `Jinja2` |
| **Vector DB** | **`AlloyDB for PostgreSQL`** (Using `pgvector` and asynchronous `asyncpg` connect chains) |
| **Cloud Storage** | **`Google Cloud Storage`** (Delivering direct media split streaming buffers to browsers) |
| **Embedding / LLM** | `gemini-embedding-2-preview`, `gemini-embedding-001`, `gemini-3.1-flash-lite-preview` |
| **Media Processing**| `FFmpeg` (Accurate Frame Re-encoding Splits) |
| **Frontend** | `Vanilla HTML/CSS/JS`, `Google Material 3 Light Style` |

---

## ⚙️ Getting Started

### 1. Prerequisite Installations
Your host machine must contain `FFmpeg` packages configured upfront.
```bash
# macOS (Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### 2. Environment Variables configuration
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service_account.json"
export PROJECT_ID="your_google_cloud_project_id"
export LOCATION="us-central1"
```

### 3. Isolated installation and Start Commands
```bash
# Initialize Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# Install Requirements
pip install -r requirements.txt

# Run Uvicorn Server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Visit `http://localhost:8000` via your browser to view the hybrid dashboard immediately.

---

## 📊 Diagnostics Scorecard
Search lookup populates tables for **`Hybrid Search Diagnostics (RRF Results)`** below reels.  
Enables visual traceability covering which embedding weights (visual vs captions) turned lookup rankings upside down with straightforward design fluidity.

---

> 💡 **Highly Recommended for**:  
> Developer scopes struggling because "Visual embeddings miss exact noun lookup accuracy, yet text captioning misses visual design layouts" – bridging both worlds natively under **AlloyDB dense vector operations and RRF thresholds**.
