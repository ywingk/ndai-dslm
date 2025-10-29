# 🚀 Quick Start Guide

도메인별 Graph DB를 빠르게 시작하는 가이드입니다.

## 📋 전체 설치 (한 번만)

```bash
# 1. 프로젝트 클론 (이미 되어있다면 스킵)
cd /user/ndai-dslm

# 2. Docker 설치 확인
docker --version
docker-compose --version
```

## 🦷 Dental Domain 시작하기 (5분)

```bash
cd graphdb/dental

# 1. 패키지 설치
pip install -r requirements.txt

# 2. Neo4j 시작
docker-compose up -d

# 3. 데이터 임포트 (SNOMED CT 데이터 필요)
python snomed_to_neo4j.py --keywords "dental caries" --clear

# 4. 브라우저에서 확인
# http://localhost:7474
# ID: neo4j, PW: dental_slm_2025

# 5. 예시 실행
python example_usage.py

# 6. QA 생성
python generate_qa_dataset.py
```

## 🔒 Hacking Domain 시작하기 (자동, 5분)

```bash
cd graphdb/hacking

# 자동 설정 스크립트 실행
./setup.sh

# 브라우저에서 확인
# http://localhost:7475
# ID: neo4j, PW: hacking_slm_2025

# 예시 실행
python example_usage.py
```

## 🔒 Hacking Domain 시작하기 (수동)

```bash
cd graphdb/hacking

# 1. 패키지 설치
pip install -r requirements.txt

# 2. Neo4j 시작
docker-compose up -d

# 3. MITRE ATT&CK 다운로드
python download_mitre_attack.py --domain enterprise

# 4. 데이터 임포트
python stix_to_neo4j.py \
  --input data/enterprise-attack.json \
  --clear

# 5. 예시 실행
python example_usage.py

# 6. QA 생성
python generate_qa_dataset.py
```

## 📊 Neo4j Browser 사용법

### Dental Domain (http://localhost:7474)

```cypher
// 1. 전체 통계
MATCH (n:Concept) RETURN count(n) as total_concepts

// 2. "dental caries" 검색
MATCH (c:Concept)
WHERE toLower(c.term) CONTAINS "dental caries"
RETURN c LIMIT 10

// 3. 관계 시각화
MATCH (c:Concept {conceptId: "80967001"})-[r]->(target)
RETURN c, r, target LIMIT 25
```

### Hacking Domain (http://localhost:7475)

```cypher
// 1. 전체 통계
MATCH (n) RETURN labels(n) as type, count(n) as count

// 2. "Phishing" 공격 기법 검색
MATCH (a:AttackPattern)
WHERE toLower(a.name) CONTAINS "phishing"
RETURN a LIMIT 10

// 3. 공격 체인 시각화
MATCH path = (a:AttackPattern)-[:USES*1..3]->(target)
WHERE a.name =~ "(?i).*phishing.*"
RETURN path LIMIT 25

// 4. 가장 위험한 악성코드
MATCH (m:Malware)-[r]-(other)
WITH m, count(r) as connections
ORDER BY connections DESC
LIMIT 10
RETURN m.name, connections
```

## 🐛 문제 해결

### Neo4j 연결 실패

```bash
# 1. Neo4j가 실행 중인지 확인
docker ps | grep neo4j

# 2. 로그 확인
docker logs neo4j-dental  # 또는 neo4j-hacking

# 3. 재시작
docker-compose down
docker-compose up -d

# 4. 포트 확인
netstat -tuln | grep 7474  # dental
netstat -tuln | grep 7475  # hacking
```

### 데이터 임포트 실패

```bash
# 1. 데이터 파일 경로 확인
# Dental: /user/data/SNOMED/...
# Hacking: data/enterprise-attack.json

# 2. Python 패키지 재설치
pip install -r requirements.txt --upgrade

# 3. Neo4j 초기화
docker-compose down -v  # 주의: 모든 데이터 삭제
docker-compose up -d
```

### 메모리 부족

```bash
# Docker 메모리 증가 (docker-compose.yml 수정)
environment:
  - NEO4J_dbms_memory_heap_max__size=8G
  - NEO4J_dbms_memory_pagecache_size=4G
```

## 📈 다음 단계

### 1. QA 데이터셋 활용

```python
import json

# QA 데이터 로드
with open('qa_dataset/hacking_qa.json', 'r') as f:
    qa_data = json.load(f)

# 난이도별 필터링
easy_qa = [q for q in qa_data['qa_samples'] if q['difficulty'] == 'easy']
medium_qa = [q for q in qa_data['qa_samples'] if q['difficulty'] == 'medium']
hard_qa = [q for q in qa_data['qa_samples'] if q['difficulty'] == 'hard']

print(f"Easy: {len(easy_qa)}, Medium: {len(medium_qa)}, Hard: {len(hard_qa)}")
```

### 2. 커스텀 쿼리 작성

```python
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig

config = Neo4jConfig.default()
with get_connector(config) as conn:
    # 커스텀 Cypher 쿼리
    result = conn.execute_read("""
        MATCH (n)-[r]->(m)
        WHERE n.name CONTAINS $keyword
        RETURN n.name, type(r), m.name
        LIMIT 10
    """, {"keyword": "ransomware"})
    
    for record in result:
        print(record)
```

### 3. GraphRAG 구현 (예정)

```python
# TODO: 검색 증강 생성 파이프라인
from graph_rag import GraphRAG

rag = GraphRAG(domain="hacking")
answer = rag.query("How does APT28 conduct phishing attacks?")
print(answer)
```

## 🎯 성능 벤치마크

### 예상 실행 시간

| 작업 | Dental | Hacking |
|------|--------|---------|
| Neo4j 시작 | 30초 | 30초 |
| 데이터 임포트 | 2-5분 | 1-3분 |
| QA 생성 | 1-2분 | 1-2분 |
| 총 설정 시간 | ~5-10분 | ~3-7분 |

### 그래프 크기

| 도메인 | 노드 수 | 관계 수 |
|--------|---------|---------|
| Dental (dental caries) | ~5K-10K | ~10K-30K |
| Dental (전체) | ~50K-100K | ~200K-500K |
| Hacking (ATT&CK Enterprise) | ~5K-10K | ~15K-40K |

## 💡 팁

### 1. 여러 키워드로 필터링 (Dental)

```bash
python snomed_to_neo4j.py \
  --keywords tooth dental periodont implant \
  --clear
```

### 2. 특정 공격 타입만 임포트 (Hacking)

```bash
python stix_to_neo4j.py \
  --input data/enterprise-attack.json \
  --filter-type attack-pattern \
  --keywords ransomware phishing \
  --clear
```

### 3. 데이터 업데이트

```bash
# 기존 데이터 유지하고 추가 임포트 (--clear 없이)
python stix_to_neo4j.py --input new_data.json
```

### 4. 백그라운드 실행

```bash
# Neo4j를 백그라운드로 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

## 🔗 유용한 링크

- **Neo4j Browser**: 
  - Dental: http://localhost:7474
  - Hacking: http://localhost:7475
- **Neo4j 공식 문서**: https://neo4j.com/docs/
- **Cypher 치트시트**: https://neo4j.com/docs/cypher-cheat-sheet/
- **MITRE ATT&CK Navigator**: https://mitre-attack.github.io/attack-navigator/

## 📞 도움이 필요하신가요?

1. README 문서 확인: `/user/ndai-dslm/README.md`
2. 아키텍처 비교: `/user/ndai-dslm/graphdb/ARCHITECTURE_COMPARISON.md`
3. 도메인별 README:
   - Dental: `/user/ndai-dslm/graphdb/dental/README.md`
   - Hacking: `/user/ndai-dslm/graphdb/hacking/README.md`

