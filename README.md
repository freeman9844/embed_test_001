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
- **텍스츄얼 설명문 생성 (`gemini-3.1-flash-lite-preview`)**: 각 클립의 시각 정보를 한국어 전용 프롬프트로 간결하게 자동 생성(`1~2줄 묘사`)하여 의미적 보정을 덧댑니다.
- **텍스트 덴스 임베딩 (`gemini-embedding-001`)**: 생성된 구조 묘사문은 구글의 전용 덴스 임베딩 엔진을 타고 **3072차원** 초정밀 밀집 벡터로 퓨전됩니다.

### 3. ⚖️ 하이브리드 RRF 및 BM25 키워드 검색 통합 (Hybrid Fusion)
- **자연어 BM25 FTS 점수 취합**: 단순 글자 매칭 보정 대신, LanceDB 내부의 형태소 기반 BM25 Keyword Full-Text Search(FTS)를 정식 교차 가교합니다.
- **3차원 상호 순위 병합(RRF)**: 비주얼 임베딩 랭킹, 텍스트 설명 임베딩 랭킹, 그리고 BM25 키워드 랭킹 총 3가지 독립 지표를 역순위 가중 합산하는 RRF 방식으로 최종 장면을 도출합니다.

### 4. ⚡ 고속 병렬 처리 (Threaded Acceleration)
- 클립 분절 이후 REST 지연(Latency) 상쇄를 위해 **`ThreadPoolExecutor` 배포 기법**을 장착했습니다. 순차 처리 대비 **최대 70% 이상 가속**되어 로드 지연이 없습니다.

### 5. 🧹 실시간 Vector DB 초기화 (Clear Database)
- 대시보드 화면상 **`버튼 클릭 한 번`** 으로 로컬 LanceDB 색인을 파괴 및 자동 초기화하는 관리자(테스팅) 편의 기능을 공급합니다. 대기 타임라인을 끊고 연속 테스트를 돌릴 때 유용합니다.

---

## 🛠️ 기술 스택 (Tech Stack)

| 영역 | 기술 명세 |
| :--- | :--- |
| **Backend** | `FastAPI` (Async Streaming), `Jinja2` |
| **Vector DB** | `LanceDB` (On-Disk 로컬 영속화 백업) |
| **Embedding / LLM** | `gemini-embedding-2-preview` (멀티모달), `gemini-embedding-001` (텍스트), `gemini-3.1-flash-lite-preview` (생성형) |
| **Media Processing**| `FFmpeg` (Accurate Frame Re-encoding Splits) |
| **Frontend** | `Vanilla HTML/CSS/JS`, `Google Material 3 Light Style`, `FontAwesome` |

---

## ⚙️ 실행 및 배포 가이드 (Getting Started)

### 1. 선수 요구 패키지 설치
로컬 시스템에 `FFmpeg` 가 설치되어 있어야 원활한 분절 오차 연산 가이드가 가능합니다.
```bash
# macOS (Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### 2. 환경 변수(Auth) 설정
구글 클라우드 통합 노드에 필요한 핵심 Config를 주사합니다.
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service_account.json"
export PROJECT_ID="your_google_cloud_project_id"
export LOCATION="us-central1" # 지원되는 리전에 맞춤 설정
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

## 🔬 임베딩 다양화 예제 가이드 (Embedding Diversity Guide)

본 프로젝트는 단순 검색 구현을 넘어, **상황에 맞는 구글 임베딩 모델의 분할 활용(Diversity)** 처세를 학습할 수 있는 레퍼런스 가이드입니다.

1.  **`gemini-embedding-2-preview` (Multimodal Integration)**
    *   **목적**: 비디오와 같은 연속적 비주얼 데이터의 밀집 공간 사영.
    *   **특징**: 텍스트와 이미지를 하이브리드 인지하여 3072차원의 딥 스페이스를 생성합니다.

2.  **`gemini-3.1-flash-lite-preview` (Visual2Text Conversion)**
    *   **목적**: 비가독성 영상 데이터를 인간이 검증 가능한 텍스트 오버레이 문서로 추출.
    *   **특징**: 하이브리드 임베딩이 커버하지 못하는 '유니크 명사' 검색 보조용 캡셔닝 엔진으로 사용됩니다.

3.  **`gemini-embedding-001` (Dense Text Density)**
    *   **목적**: 캡셔닝된 한국어 결과값의 3072차원 초고해상도 밀집 보정.
    *   **특징**: 비주얼 임베딩 대비 연산이 빠르고 정확도가 확고하여 가중 퓨전(RRF)의 핵심을 담당합니다.

> 💡 **이런 분들께 유용합니다**:  
> "비디오 임베딩만 하니 텍스트 키워드가 안 맞고, 텍스트 캡셔닝만 하니 비주얼 구도가 어긋날 때" – 두 세계를 **Reciprocal Rank Fusion(RRF)** 과 **가중 보정**으로 접합하는 최적 아키텍처 예제입니다.
