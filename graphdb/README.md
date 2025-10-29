# Neo4j Graph Database 연동

SNOMED CT 치과 서브그래프를 Neo4j에 저장하고 쿼리하는 모듈입니다.

## 📋 사전 준비

### 1. Neo4j 설치 및 실행 
```bash
cd /home/kyi/dcai-dental-slm/graphdb

# Docker Compose로 Neo4j 실행
docker-compose up -d
docker-compose up 
docker-compose down 

# 또는 직접 Docker 실행
docker run -d \
  --name neo4j-dental \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/dental_password_2024 \
  neo4j:latest

# 또는 로컬 설치: https://neo4j.com/download/
```

### 2. Python 패키지 설치
```bash
pip install -r requirements.txt

# 또는 직접 설치 
pip install neo4j pandas tqdm
```

## 🚀 사용법

### 1단계: 데이터베이스 설정

**방법 A: 환경 변수 사용**
```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
```

**방법 B: 설정 파일 수정**
```python
# neo4j_config.py에서 직접 수정
password="your_password"
```

### 2단계: SNOMED CT 데이터 임포트

```bash
# 기본 사용 (dental caries 관련 데이터)
python snomed_to_neo4j.py --clear

# 다른 키워드로 필터링
python snomed_to_neo4j.py --keywords tooth dental periodont --clear

# 임플란트 관련 데이터
python snomed_to_neo4j.py --keywords implant --clear

# 연결 정보 직접 지정
python snomed_to_neo4j.py \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password your_password \
  --keywords "dental caries" \
  --clear
```

### 3단계: 그래프 쿼리 및 분석

```python
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig
from neo4j_query_utils import Neo4jQueryUtils

# 연결
config = Neo4jConfig.default()
with get_connector(config) as conn:
    utils = Neo4jQueryUtils(conn)
    
    # 1. Concept 검색
    concept = utils.get_concept_by_term("dental caries")
    print(f"찾은 개념: {concept['term']}")
    
    # 2. 직접 관계 조회
    rels = utils.get_direct_relationships(concept['conceptId'])
    for rel in rels:
        print(f"{rel['relation']}: {rel['target_term']}")
    
    # 3. Multi-hop 경로 찾기
    paths = utils.get_qa_multihop_paths(concept['conceptId'], min_hops=2, max_hops=3)
    for path in paths[:5]:
        print(f"{path['terms']} (hops: {path['hops']})")
    
    # 4. 가장 연결이 많은 Concept
    top_concepts = utils.get_most_connected_concepts(limit=10)
    for c in top_concepts:
        print(f"{c['term']}: {c['degree']} 연결")
```

## 📊 주요 기능

### 1. 기본 쿼리
- `get_concept_by_term()`: 용어로 검색
- `get_concept_by_id()`: ID로 조회
- `get_direct_relationships()`: 직접 관계 조회

### 2. Multi-hop 분석
- `find_path()`: 두 개념 간 최단 경로
- `find_multihop_concepts()`: N-hop 거리의 개념들
- `find_common_ancestors()`: 공통 상위 개념

### 3. 그래프 분석
- `get_most_connected_concepts()`: 중심 개념 찾기
- `get_relationship_distribution()`: 관계 타입 분포
- `find_leaf_concepts()`: 말단 개념들

### 4. QA 생성용
- `get_qa_single_hop_data()`: 단순 QA 데이터
- `get_qa_multihop_paths()`: 복잡한 추론 경로
- `get_comparison_concepts()`: 비교 QA용 개념들

## 🔍 Neo4j Browser에서 직접 쿼리

Neo4j Browser (http://localhost:7474) 에서 Cypher 쿼리 실행:

```cypher
// 전체 그래프 통계
MATCH (n:Concept) RETURN count(n) as concepts
MATCH ()-[r]->() RETURN count(r) as relationships

// "dental caries" 검색
MATCH (c:Concept)
WHERE toLower(c.term) CONTAINS "dental caries"
RETURN c LIMIT 10

// 직접 관계 시각화
MATCH (c:Concept {conceptId: "80967001"})-[r:RELATED_TO]->(target)
RETURN c, r, target

// 2-hop 경로
MATCH path = (start:Concept)-[*2..2]->(end:Concept)
WHERE start.conceptId = "80967001"
RETURN path LIMIT 25

// 가장 연결이 많은 개념
MATCH (c:Concept)-[r]-()
WITH c, count(r) as degree
ORDER BY degree DESC
LIMIT 10
RETURN c.term, degree
```

## 📁 파일 구조

```
graphdb/
├── neo4j_config.py          # 연결 설정
├── neo4j_connector.py       # 기본 연결 및 작업
├── snomed_to_neo4j.py       # 데이터 임포트
├── neo4j_query_utils.py     # 쿼리 유틸리티
└── README.md                # 이 파일
```

## 🔧 문제 해결

### 연결 실패
```
❌ Neo4j 연결 실패: ServiceUnavailable
```
- Neo4j가 실행 중인지 확인: `docker ps` 또는 Neo4j Desktop 확인
- 포트가 올바른지 확인: 기본값 7687
- 비밀번호가 정확한지 확인

### 임포트 느림
- 배치 크기 조정: `snomed_to_neo4j.py`의 `batch_size` 변경
- 인덱스가 생성되었는지 확인
- Docker 메모리 제한 증가

### 메모리 부족
```bash
# Docker 메모리 증가
docker run -d \
  --memory=4g \
  --name neo4j-dental \
  ...
```

## 📖 다음 단계

1. **QA 생성과 연동**: `generate_qa_from_neo4j.py` (다음 단계에서 구현)
2. **난이도 분류**: 경로 길이 기반 자동 난이도 지정
3. **GraphRAG**: 검색 증강 생성 파이프라인

