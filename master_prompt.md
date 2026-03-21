# 🌌 Master Prompt: Multimodal Video Semantic Search Engine (FastAPI + AlloyDB + Vertex AI)

이 프롬프트는 비디오 데이터를 10초 단위로 파절 압축하고, Vertex AI 멀티모달 프레임 분석과 AlloyDB `pgvector` + `pg_bigm` 하이브리드 RRF 엔진을 통해 초정밀 의미형 검색(Scene Search)을 수행하는 백엔드/인프라 가동 앱을 구성하는 마스터 프롬프트입니다.

---

## 🛠️ [System Prompt Instruction]

"개발자로서 당신은 **영상 데이터를 10초 단위로 하이퍼 분할 분석하고, 다차원 임베딩 결합과 RRF(Reciprocal Rank Fusion) SQL 아키텍처를 이용하여 인프라 지연 없는 고속 하이브리드 비디오 세그먼트 검색 대시보드**를 만듭니다. 하단에 기술된 파이프라인과 스택 규격을 준수하여 전체 백엔드 코드를 도출하세요."

---

## 🏗️ 1. 핵심 아키텍처 및 아키타입 (Core Architecture)

### 📼 A. 비디오 전처리 및 수급 파이프라인 (Data Ingestion)
1. **FFmpeg 분절 최적화**: 
   - 업로드된 대용량 비디오를 10s 단위 파편 클립(`segment_001.mp4` 등)으로 자동 하이퍼 슬라이싱 분해합니다.
   - 인코딩 오버헤드 완화를 위해 가로 720p 픽셀 보정(`scale=720:-2`) 및 프레임 레이트 압축(`5 FPS`)을 강제 탑재하여 Vertex AI 주입량을 경량 가속화합니다.
   - subprocess 가동 시 Async I/O 파이프 교착(`OSError 5`)을 막기 위해 캡처 버퍼를 회피(`stdout=DEVNULL`, `stderr=DEVNULL`)하도록 구현합니다.

2. **GCS-Driven Streaming**:
   - 메모리 상주 버퍼(`base64`) 인코딩 전송을 원천 배제합니다. 
   - 10s 파편화 즉시 **Google Cloud Storage (GCS)** 내부 지정 버킷에 `.mp4` 클립을 다이렉트 푸시 전송한 뒤 `gs://` URI 주소를 Vertex AI 바인딩 및 서빙 원천으로 삼습니다.

---

### 🧠 B. 임베딩 퓨전 체인 파이프라인 (Multi-Embedding Fusion)
1. **멀티모달 시각 구조 (`gemini-embedding-2-preview`)**:
   - 영상 고유의 구도, 액션, 공간감을 추출하여 고정 다차원 벡터 스페이스에 투영합니다.
2. **텍스트 설명문 보강 (`gemini-3.1-flash-lite-preview`)**:
   - 영상 클립에 대해 사실적이고 압축적인 200자 내외의 **비주얼 콤팩트 묘사문**을 동적 자동 생성하여 의미적 필터링의 보완재로 삼습니다.
3. **텍스트 덴스 임베딩 부과 (`gemini-embedding-001`)**:
   - 캡셔닝 묘사문을 바탕으로 한 번 더 초정밀 밀집 벡터(3072차원 등) 연산을 수행 체인에 결합합니다.

---

### ⚖️ C. 서버사이드 하이브리드 검색엔진 (AlloyDB Single SQL CTE RRF)
1. **AlloyDB `pg_bigm` & `pgvector` 결합**:
   - 형태소 다중 단절 한계를 상쇄하기 위해 `pg_bigm`의 `bigm_similarity` 기반 바이그램 부분 일치 검색(`description LIKE ANY(...)`)을 탑재합니다.
2. **상호 순위 병합 (RRF, Reciprocal Rank Fusion)**:
   - 클라이언트 사이드 루프 지연을 소거하기 위해 비주얼 검색, 텍스트 검색, 키워드 검색을 **단일 SQL 쿼리 내부 CTE(`WITH`절)** 로 가둡니다.
   - 순위 스무딩 상수 $k=60$ 및 최대 부스팅 배율 `x1.25` (텍스트 가중 우수)을 이용해 0.001초 만에 통합 교차 RRF 정렬 순번을 병합 반환 처리합니다.

---

## 🛠️ 2. 기술 스택 구현 가이드 (Implementation Guidelines)

- **Backend**: Python `FastAPI` (동적 백그라운드 태스크 러너 동시 구사)
- **Database**: AlloyDB (PostgreSQL) - `pgvector` + `pg_bigm` 확장 활성 하에 초기 1회 테이블 DDL 및 index setup 인자 자동 가이드 포함
- **Async Execution**: `asyncpg` 데이터베이스 풀 동학 핸들 활용 Node.
- **Configuration**: Pydantic `Settings` (변숫값 누출 및 검증 누락 우회를 위한 `extra="ignore"` 스위치 공급).

---

## 💻 3. 가동 스크립트 도출 명세 (File deliverables)

이 마스터 프롬프트를 주입할 때 AI는 아래 파일들을 일사분란하게 토해내야 합니다:

1.  **`app/main.py`**: FFmpeg 분절 알고리즘, GCS 푸시백그라운드 스레드 가상화, Verse AI REST 연결 루틴 및 RRF 서버 사이드 구사 시나리오가 단일 병합된 올라운더 라우터 코드
2.  **`create_alloydb_table.py` / `setup_bigm.py`**: 초기 1회 `CREATE EXTENSION` 및 인덱스 색인 가속 세팅 보완 스크립트 Node.
3.  **`app/templates/index.html`**: 진단 패널 지표 상 가중 배수 가변 비율 배포 및 Segment sequence 마크업 처리가 매끄럽게 얹힌 하이테크 대시보드 구조 프론트 뷰

---
💡 **사용법**: 이 문서를 복사하여 원하시는 생성형 AI 창이나 Assistant 서빙 창에 붙여넣으시고, "이 구조대로 뼈대를 짜서 FastAPI 코드를 작성해 줘"라고 명령하시면 즉각적으로 대동소이한 고효율 하이브리드 RRF 벡터 체인 앱을 획득하실 수 있습니다
