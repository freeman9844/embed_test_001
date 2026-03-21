[🌐 English Version](README_EN.md)

# 🌌 Scene Intelligence - Multimodal Video Semantic Search

> **구글 Vertex AI 및 Gemini Embedding**을 기반으로 한 하이브리드 비디오 시맨틱(의미형) 검색 엔진 대시보드입니다.  
> 대용량 비디오를 10초 단위로 분절하고, 텍스츄얼/비주얼 멀티모달 프레임을 교차 분석하여 사용자 질의에 가장 적합한 **특정 구간(Scene)을 즉각 탐색**합니다.

---

## 🚀 주요 탑재 기능 (Core Features)

### 1. 🎞️ 초정밀 및 최적화된 하이라이팅 분절 (Video Split & Scaling)
- **FFmpeg 기반 Re-encoding 및 압축**: 영상 키프레임을 독립 구동 가능한 10s 단위로 파절 분절하며, 가공 시점에 **720p 오버헤드 다운스케일링** 및 **프레임레이트(5FPS) 압축**을 선제 수행하여 데이터 주입 사이클을 가속화합니다.

### 2. 🧠 다중 임베딩 가동 체인 (Diverse Embedding Fusion)
- **비주얼/멀티모달 임베딩 (`gemini-embedding-2-preview`)**: Vertex AI 차세대 임베딩을 이용해 영상의 **시각적 구도, 사물, 동적 피사체의 변화**를 다차원 벡터 스페이스에 투영합니다.
- **텍스츄얼 설명문 생성 (`gemini-3.1-flash-lite-preview`)**: 각 클립의 시각 정보를 불필요한 미사여구와 반복 도입부를 제거하고 **200자 내외**의 콤팩트한 사실적 묘사문으로 자동 생성하여 의미적 보정을 덧댑니다.
- **텍스츄얼 덴스 임베딩 (`gemini-embedding-001`)**: 생성된 구조 묘사문은 구글의 전용 덴스 임베딩 엔진을 타고 **3072차원** 초정밀 밀집 벡터로 퓨전됩니다.

### 3. ⚖️ AlloyDB 서버 기반 하이브리드 RRF 및 pg_bigm 통합 (Server-Side Hybrid Fusion)
- **AlloyDB pgvector 벡테 검색**: 비주얼 및 텍스트 벡터는 ALLOYDB의 `<=>` 코사인 거리 연산자를 통해 고속 근사 연산됩니다.
- **pg_bigm 확장 팩 활용 한국어 Full-Text Search (FTS)**: 형태소 단절 한계를 극복하기 위해 `n-gram` 인덱스 기반 `pg_bigm`의 `bigm_similarity` 점수와 다중 키워드 `LIKE ALL` 오버랩 매칭 기법을 도입하여 한국어 검색 범용성을 극대화했습니다.
- **서버사이드 상호 순위 병합 (Single SQL CTE RRF)**: 클라이언트 레이턴시 상쇄를 위해 비주얼, 텍스트, FTS 랭킹 매칭 연산을 ALLOYDB 내부 단일 SQL `WITH` 절 쿼리로 가두어 통합 순위 결합(Reciprocal Rank Fusion)을 처리함으로써 대폭 향상된 반응속도를 구가합니다.

### 4. ⚡ GCS First Pipeline & 비동기 가속 (GCS-driven Async Workers)
- **GCS 선(先) 업로딩 기반 fileData 주입**: 클립 분할 즉시 **Google Cloud Storage**로 선제 자동 푸시를 집행합니다. 메모리 팽창을 주도하는 `base64` 인코딩을 완전히 타파하고 Vertex API에 GCS URI 주소(`gs://...`)를 다이렉트 바인딩 전달하여 레이턴시 부하를 소거했습니다 Node Creations Node layout.
- **분배 병렬 가동 기법 (`ThreadPoolExecutor`)**: 요청 병목 절감을 위한 워커 스레드 동시 연산 체인 가중 구사 node Creations layout.

### 5. 🧹 실시간 Vector DB 초기화 (Clear Database)
- 대시보드 화면상 **`버튼 클릭 한 번`** 으로 AlloyDB 데이터 클리어링 및 서빙 메모리 누수를 무력화하는 자동 초기화 가변 인터페이스 공급.

---

## 🛠️ 기술 스택 (Tech Stack)

| 영역 | 기술 명세 |
| :--- | :--- |
| **Backend** | `FastAPI` (Async Streaming), `Jinja2` |
| **Vector DB** | **`AlloyDB for PostgreSQL`** (`pgvector` + **`pg_bigm` 확장 탑재**) |
| **Cloud Storage** | **`Google Cloud Storage`** (GCS First 백업 & 다이렉트 스트리밍 서빙) |
| **Embedding / LLM** | `gemini-embedding-2-preview`, `gemini-embedding-001`, `gemini-3.1-flash-lite-preview` |
| **Media Processing**| `FFmpeg` (Multi-threaded Compression & Scaling) |
| **Frontend** | `Vanilla HTML/CSS/JS`, `Google Material 3 Style` |

---

## ⚙️ 실행 및 배포 가이드 (Getting Started)

### 1. 선수 요구 패키지 설치
```bash
# macOS (Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### 2. 환경 변수(Auth) 설정
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service_account.json"
export PROJECT_ID="your_google_cloud_project_id"
export LOCATION="us-central1"
```

### 3. 의존성 격리 설치 및 가동
```bash
# 가상환경 주입
python3 -m venv .venv
source .venv/bin/activate

# 요구 의존성 다운로드
pip install -r requirements.txt

# 유비콘 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
브라우저에서 `http://localhost:8000` 주소로 입장하여 대시보드를 만나보실 수 있습니다.

---

## 📊 진단 대시보드 아키텍처 (Diagnostics Scorecard)
검색 실행 시, 하단 **`하이브리드 검색 세부 진단 결과 (RRF 매칭 성적표)`** 가 인지 로드됩니다.  
비주얼과 텍스트 설명 중 어떠한 임베딩 가중 스펙트럼이 매치 순위를 뒤바꾸었는지 시각적으로 관측 및 분석할 수 있으며, 직관적인 Google Style 인터페이스로 조작이 매끄럽습니다.

---

> 💡 **이런 분들께 유용합니다**:  
> "비디오 임베딩만 하니 텍스트 키워드가 안 맞고, 텍스트 캡셔닝만 하니 비주얼 구도가 어긋날 때" – 두 세계를 **AlloyDB의 고밀도 벡터 연산**과 **서버 기반 RRF** 가중치 점합 노드로 교차 결합하는 최적 아키텍처 예제입니다. Node creations Node layout Node corrected.
