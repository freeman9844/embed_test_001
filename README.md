[🌐 English Version](README_EN.md)

# 🌌 Scene Intelligence - Multimodal Video Semantic Search

> **구글 Vertex AI 및 Gemini Embedding**을 기반으로 한 하이브리드 비디오 시맨틱(의미형) 검색 엔진 대시보드입니다.  
> 대용량 비디오를 10초 단위로 분절하고, 텍스츄얼/비주얼 멀티모달 프레임을 교차 분석하여 사용자 질의에 가장 적합한 **특정 구간(Scene)을 즉각 탐색**합니다.

---

## 🚀 주요 탑재 기능 (Core Features)

### 1. 🎞️ 초정밀 10초 단위 분절 (Video Split)
- **FFmpeg 기반 Re-encoding 분절**: 영상 프레임의 Keyframe 한계를 격파하여 **오차 없는 10s 단위의 독립 비디오 파절 분절**을 생성합니다.

### 2. 🧠 다중 임베딩 가동 체인 (Diverse Embedding Fusion)
- **비주얼/멀티모달 임베딩 (`gemini-embedding-2-preview`)**: Vertex AI의 차세대 임베딩 모델을 이용해 영상의 **시각적 구도, 사물, 동적 피사체의 변화**를 다차원 벡터 스페이스에 직접 투영합니다.
- **텍스츄얼 설명문 생성 (`gemini-3.1-flash-lite-preview`)**: 각 클립의 시각 정보를 불필요한 미사여구 없이 **300자 내외**의 사실적인 의미 단위 묘사문으로 자동 생성하여 의미적 보정을 덧댑니다.
- **텍스트 덴스 임베딩 (`gemini-embedding-001`)**: 생성된 구조 묘사문은 구글의 전용 덴스 임베딩 엔진을 타고 **3072차원** 초정밀 밀집 벡터로 퓨전됩니다.

### 3. ⚖️ 하이브리드 RRF 및 Full-Text Search 통합 (Hybrid Fusion)
- **AlloyDB pgvector 벡터 검색**: 비주얼 및 텍스트 벡터는 AlloyDB의 `<=>` 코사인 거리 연산자를 통해 고속 근사 연산됩니다.
- **PostgreSQL Full-Text Search (FTS)**: `to_tsvector` 및 `plainto_tsquery` 와 `ts_rank_cd` 점수를 활용한 형태소 기반 키워드 매치 가중치를 상호 대조합니다.
- **3차원 상호 순위 병합(RRF)**: 비주얼 임베딩 랭킹, 텍스트 설명 임베딩 랭킹, 그리고 Keyword FTS 랭킹 총 3가지 독립 지표를 역순위 가중 합산(Reciprocal Rank Fusion)하여 최적 장면을 도출합니다.

### 4. ⚡ 고속 클라우드 저장 및 가속 (GCS & Threaded)
- **GCS 자동 백업 백그라운드 워커**: 분할된 미디어 세그먼트들은 분할 즉시 **Google Cloud Storage**(`gs://jwlee-gcs-video-002`) 버킷에 고속 분배 적재되어 서버 디스크 가용량을 지지합니다.
- **분배 병렬 가동 기법 (`ThreadPoolExecutor`)**: 대량 동시 요청 레이턴시 상쇄를 위해 지연 지표 가동 체이닝 가속화 지원 노드 장착.

### 5. 🧹 실시간 Vector DB 초기화 (Clear Database)
- 대시보드 화면상 **`버튼 클릭 한 번`** 으로 AlloyDB 데이터 클리어링 및 서빙 메모리 누수를 무력화하는 자동 초기화 테스팅 가변 공급망 공급.

---

## 🛠️ 기술 스택 (Tech Stack)

| 영역 | 기술 명세 |
| :--- | :--- |
| **Backend** | `FastAPI` (Async Streaming), `Jinja2` |
| **Vector DB** | **`AlloyDB for PostgreSQL`** (`pgvector` 확장 포함, `asyncpg` 풀 이용) |
| **Cloud Storage** | **`Google Cloud Storage`** (분할 세그먼트 미디어 다이렉트 스트리밍 서빙) |
| **Embedding / LLM** | `gemini-embedding-2-preview`, `gemini-embedding-001`, `gemini-3.1-flash-lite-preview` |
| **Media Processing**| `FFmpeg` (Accurate Frame Re-encoding Splits) |
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
> "비디오 임베딩만 하니 텍스트 키워드가 안 맞고, 텍스트 캡셔닝만 하니 비주얼 구도가 어긋날 때" – 두 세계를 **AlloyDB의 고밀도 벡터 연산**과 **Reciprocal Rank Fusion(RRF)** 가중치 점합 노드로 교차 결합하는 최적 아키텍처 예제입니다.
