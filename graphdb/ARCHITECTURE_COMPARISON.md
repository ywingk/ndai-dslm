# 도메인별 Graph DB 아키텍처 비교

## 개요

여러 도메인에 특화된 전문가 LLM을 만들기 위해, 각 도메인의 지식을 Neo4j Graph DB로 구축하고 QA 데이터셋을 생성하는 통합 프레임워크입니다.

## 도메인별 아키텍처

### 1. Dental Domain (치과)

```
SNOMED CT (의료 온톨로지)
         ↓
    RF2 파일 파싱
         ↓
  키워드 필터링 (dental, tooth, etc.)
         ↓
    Neo4j Graph DB
         ↓
    QA Dataset 생성
```

**주요 특징:**
- **데이터 소스**: SNOMED CT (Systematized Nomenclature of Medicine - Clinical Terms)
- **온톨로지**: 의료 표준 온톨로지
- **노드 타입**: `Concept` (의료 개념)
- **관계 타입**: `IS_A`, `FINDING_SITE`, `ASSOCIATED_WITH` 등
- **필터링 방식**: 키워드 기반 (dental, caries, tooth 등)
- **QA 난이도**: 
  - Easy: 개념 정의, 직접 관계
  - Medium: 2-3 hop 추론
  - Hard: 복잡한 진단/치료 경로

**파일 구조:**
```
graphdb/dental/
├── snomed_to_neo4j.py        # SNOMED → Neo4j 변환
├── neo4j_config.py            # 연결 설정
├── neo4j_connector.py         # DB 커넥터
├── neo4j_query_utils.py       # 쿼리 유틸
├── generate_qa_dataset.py     # QA 생성
└── docker-compose.yml         # Neo4j 설정 (포트 7474/7687)
```

### 2. Hacking Domain (사이버 보안)

```
STIX 2.x / MISP Data
         ↓
   UCO 매핑 (Unified Cyber Ontology)
         ↓
    Neo4j Graph DB
         ↓
    QA Dataset 생성
```

**주요 특징:**
- **데이터 소스**: STIX 2.x (MITRE ATT&CK), MISP
- **온톨로지**: UCO (Unified Cyber Ontology)
- **노드 타입**: 
  - `AttackPattern` (공격 기법)
  - `Malware` (악성코드)
  - `ThreatActor` (위협 주체)
  - `Vulnerability` (취약점)
  - `Tool` (도구)
  - `CourseOfAction` (대응 방안)
- **관계 타입**: `USES`, `MITIGATES`, `TARGETS`, `EXPLOITS` 등
- **필터링 방식**: STIX 타입 기반, 키워드 기반
- **QA 난이도**:
  - Easy: 공격 기법 정의, 악성코드 타입
  - Medium: 공격 체인, TTP 분석
  - Hard: 복잡한 위협 인텔리전스, 방어 전략

**파일 구조:**
```
graphdb/hacking/
├── stix_to_neo4j.py           # STIX → Neo4j 변환
├── misp_to_neo4j.py           # MISP → Neo4j 변환 (TODO)
├── uco_mapping.py             # STIX/MISP → UCO 매핑
├── neo4j_config.py            # 연결 설정
├── neo4j_connector.py         # DB 커넥터
├── neo4j_query_utils.py       # 쿼리 유틸 (hacking 특화)
├── generate_qa_dataset.py     # QA 생성
├── download_mitre_attack.py   # MITRE ATT&CK 다운로드
└── docker-compose.yml         # Neo4j 설정 (포트 7475/7688)
```

## 공통 패턴

### 1. 데이터 파이프라인

모든 도메인은 다음과 같은 공통 파이프라인을 따릅니다:

```
Raw Data → Domain-Specific Parser → Ontology Mapping → Neo4j → QA Generation
```

### 2. 파일 구조

```python
domain/
├── {source}_to_neo4j.py      # 데이터 임포트
├── neo4j_config.py            # 공통 설정
├── neo4j_connector.py         # 공통 커넥터
├── neo4j_query_utils.py       # 도메인 특화 쿼리
├── generate_qa_dataset.py     # QA 생성
├── requirements.txt           # 의존성
└── docker-compose.yml         # Neo4j 설정
```

### 3. Neo4j 연결 관리

```python
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig

config = Neo4jConfig.default()
with get_connector(config) as conn:
    # 작업 수행
    pass
```

### 4. QA 생성 템플릿

모든 도메인은 3단계 난이도로 QA를 생성합니다:

- **Easy**: 1-hop (직접 관계)
- **Medium**: 2-3 hop (중간 추론)
- **Hard**: 4+ hop (복잡한 추론)

## 도메인별 비교표

| 항목 | Dental | Hacking |
|------|--------|---------|
| **데이터 소스** | SNOMED CT | STIX 2.x, MISP |
| **데이터 형식** | TSV (RF2) | JSON (STIX Bundle) |
| **온톨로지** | SNOMED CT | UCO |
| **주요 노드** | Concept | AttackPattern, Malware, ThreatActor |
| **관계 수** | ~10-20 타입 | ~20-30 타입 |
| **필터링** | 키워드 | 타입 + 키워드 |
| **Neo4j 포트** | 7474/7687 | 7475/7688 |
| **평균 그래프 크기** | ~10K-50K 노드 | ~5K-20K 노드 |
| **QA 샘플 수** | ~1000 | ~1000 |

## 확장 가능성

### 새로운 도메인 추가 시

1. **데이터 소스 선정**
   - 표준 온톨로지/데이터베이스 확인
   - API 또는 파일 형식 확인

2. **디렉토리 구조 생성**
   ```bash
   mkdir graphdb/{new_domain}
   cd graphdb/{new_domain}
   ```

3. **공통 파일 복사 및 수정**
   ```bash
   cp ../dental/neo4j_config.py .
   cp ../dental/neo4j_connector.py .
   # 포트 번호 변경
   ```

4. **도메인 특화 구현**
   - `{source}_to_neo4j.py`: 데이터 파싱 및 임포트
   - `neo4j_query_utils.py`: 도메인 특화 쿼리
   - `generate_qa_dataset.py`: QA 템플릿

5. **Docker Compose 설정**
   - 포트 충돌 방지 (각 도메인 별도 포트)

### 추천 도메인

1. **Legal Domain (법률)**
   - 데이터 소스: Legal Ontology, Case Law DB
   - 온톨로지: LKIF (Legal Knowledge Interchange Format)

2. **Financial Domain (금융)**
   - 데이터 소스: FIBO (Financial Industry Business Ontology)
   - 온톨로지: FIBO

3. **Manufacturing Domain (제조)**
   - 데이터 소스: ISA-95, Industrial Ontology
   - 온톨로지: IOF (Industrial Ontology Foundry)

4. **Biology Domain (생물학)**
   - 데이터 소스: Gene Ontology, UniProt
   - 온톨로지: GO (Gene Ontology)

## 통합 프레임워크 설계

### Multi-Domain Knowledge Graph

장기적으로는 여러 도메인을 통합할 수 있습니다:

```
┌─────────────────────────────────────┐
│     Multi-Domain Knowledge Graph    │
├─────────────────────────────────────┤
│  Dental  │  Hacking  │  Legal  │ ...│
├──────────┼───────────┼─────────┼────┤
│ SNOMED   │   STIX    │  LKIF   │    │
│   Neo4j  │   Neo4j   │  Neo4j  │    │
└─────────────────────────────────────┘
           ↓
    Unified Query Interface
           ↓
      Domain-Expert LLMs
```

### 통합 쿼리 인터페이스

```python
class DomainKnowledgeGraph:
    def __init__(self):
        self.domains = {
            'dental': DentalConnector(),
            'hacking': HackingConnector(),
            'legal': LegalConnector(),
        }
    
    def query(self, domain: str, query: str):
        return self.domains[domain].query(query)
```

## 참고 자료

### Dental Domain
- [SNOMED CT](https://www.snomed.org/)
- [SNOMED CT Browser](https://browser.ihtsdotools.org/)

### Hacking Domain
- [STIX 2.x](https://oasis-open.github.io/cti-documentation/)
- [MITRE ATT&CK](https://attack.mitre.org/)
- [UCO Ontology](https://unifiedcyberontology.org/)
- [MISP Project](https://www.misp-project.org/)

### Graph Databases
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)

## 라이선스 및 주의사항

- **SNOMED CT**: IHTSDO 라이선스 필요
- **MITRE ATT&CK**: Apache 2.0 (자유 사용 가능)
- **STIX 2.x**: OASIS 표준 (자유 사용 가능)

