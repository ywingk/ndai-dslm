# Neo4j Graph Database - Hacking/Cybersecurity Domain

STIX/MISP 데이터를 UCO(Unified Cyber Ontology) 온톨로지 형태로 Neo4j에 저장하고 쿼리하는 모듈입니다.

## 🎯 아키텍처 개요

```
STIX 2.x / MISP Data
        ↓
UCO Ontology Mapping
        ↓
Neo4j Graph DB
        ↓
QA Dataset Generation
```

### UCO (Unified Cyber Ontology) 주요 개념

UCO는 사이버 보안 정보를 표현하기 위한 표준 온톨로지입니다:

- **Observable**: 관찰 가능한 객체 (IP, 파일, 프로세스 등)
- **Action**: 수행된 작업 (네트워크 통신, 파일 생성 등)
- **Relationship**: 객체 간 관계
- **Facet**: 속성 및 메타데이터
- **Bundle**: 관련 객체의 그룹

### STIX 2.x 주요 객체

- **Attack Pattern**: 공격 기법 (MITRE ATT&CK 매핑)
- **Campaign**: 조직적인 공격 캠페인
- **Course of Action**: 대응 조치
- **Identity**: 공격자/조직
- **Indicator**: IoC (Indicator of Compromise)
- **Intrusion Set**: 공격 그룹
- **Malware**: 악성코드
- **Threat Actor**: 위협 주체
- **Tool**: 공격 도구
- **Vulnerability**: 취약점 (CVE 등)

### MISP 주요 객체

- **Event**: 보안 이벤트 (인시던트, 위협 정보 등)
- **Attribute**: 관찰 가능한 속성 (IP, 도메인, 파일 해시 등)
- **Object**: 구조화된 객체 (파일, 네트워크 연결 등)
- **Galaxy**: 위협 분류 체계 (MITRE ATT&CK, Malware 등)
- **Tag**: 분류 및 라벨링

## 📋 사전 준비

### 1. Neo4j 설치 및 실행

```bash
cd /user/ndai-dslm/graphdb/hacking

# Docker Compose로 Neo4j 실행
docker-compose up -d

# 또는 직접 Docker 실행
docker run -d \
  --name neo4j-hacking \
  -p 7475:7474 -p 7688:7687 \
  -e NEO4J_AUTH=neo4j/hacking_slm_2025 \
  neo4j:latest
```

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt

# 또는 직접 설치
pip install neo4j pandas tqdm stix2 pymisp
```

### 3. 데이터 소스 준비

**STIX 데이터**:
```bash
# MITRE ATT&CK STIX 데이터
wget https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json

# CIRCL MISP STIX 피드 (예시)
# https://www.circl.lu/doc/misp/feed-osint/
```

**MISP 데이터**:
```python
# MISP API를 통한 데이터 수집 (별도 설정 필요)
from pymisp import PyMISP
misp = PyMISP('https://your-misp-instance', 'your-api-key')
```

## 🚀 사용법

### 1단계: STIX 데이터를 Neo4j로 임포트

```bash
# MITRE ATT&CK 데이터 임포트
python stix_to_neo4j.py \
  --input ./data/enterprise-attack.json \
  --clear

# 특정 공격 기법만 필터링
python stix_to_neo4j.py \
  --input ./data/enterprise-attack.json \
  --filter-type attack-pattern \
  --keywords "ransomware" "phishing" \
  --clear

# 연결 정보 직접 지정
python stix_to_neo4j.py \
  --input data/stix_bundle.json \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password domain_slm_2025 \
  --clear
```

### 2단계: MISP 데이터를 Neo4j로 임포트

```bash
# MISP 샘플 데이터 생성 및 임포트
python generate_misp_sample.py --output misp_sample.json --count 5
python misp_to_neo4j.py --input misp_sample.json --clear

# MISP API에서 직접 다운로드
python download_misp_data.py \
  --url https://your-misp-instance.com \
  --key your-api-key \
  --output misp_events.json

# MISP JSON 파일에서 임포트
python misp_to_neo4j.py --input misp_events.json --clear

# 특정 이벤트만 임포트
python misp_to_neo4j.py \
  --input misp_events.json \
  --event-id 12345 \
  --clear

# 특정 태그가 포함된 이벤트만 임포트
python misp_to_neo4j.py \
  --input misp_events.json \
  --tags malware ransomware \
  --clear

# 위협 수준별 필터링
python misp_to_neo4j.py \
  --input misp_events.json \
  --threat-level 4 \
  --analysis-level 2 \
  --clear
```

### 3단계: 그래프 쿼리 및 분석

```python
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig
from neo4j_query_utils import Neo4jQueryUtils

# 연결
config = Neo4jConfig(
    uri="bolt://localhost:7688",
    user="neo4j",
    password="hacking_slm_2025"
)

with get_connector(config) as conn:
    utils = Neo4jQueryUtils(conn)
    
    # 1. 공격 패턴 검색
    attack = utils.get_attack_pattern_by_name("Phishing")
    print(f"공격 기법: {attack['name']}")
    
    # 2. 관련 악성코드 조회
    malware = utils.get_related_malware(attack['id'])
    for m in malware:
        print(f"  - {m['name']}: {m['description']}")
    
    # 3. 공격 체인 분석 (Multi-hop)
    chains = utils.get_attack_chains(attack['id'], max_hops=3)
    for chain in chains[:5]:
        print(f"공격 경로: {' → '.join(chain['steps'])}")
    
    # 4. CVE와 연결된 공격 기법
    vulns = utils.get_vulnerabilities_for_attack(attack['id'])
    for v in vulns:
        print(f"취약점: {v['cve_id']} - {v['description']}")
```

## 📊 주요 기능

### 1. STIX 객체 쿼리
- `get_attack_pattern_by_name()`: 공격 기법 검색
- `get_malware_by_name()`: 악성코드 검색
- `get_threat_actor_by_name()`: 위협 주체 검색
- `get_vulnerability_by_cve()`: CVE로 취약점 조회

### 2. 관계 분석
- `get_related_malware()`: 관련 악성코드
- `get_related_tools()`: 사용된 도구
- `get_attack_chains()`: 공격 체인/킬체인
- `get_mitigations()`: 대응 방안

### 3. Multi-hop 분석
- `find_attack_path()`: 공격 경로 탐색
- `find_common_ttps()`: 공통 TTP (Tactics, Techniques, Procedures)
- `get_campaign_analysis()`: 캠페인 분석

### 4. QA 생성용
- `get_qa_attack_chains()`: 공격 체인 QA
- `get_qa_malware_analysis()`: 악성코드 분석 QA
- `get_qa_threat_intelligence()`: 위협 인텔리전스 QA

## 🔍 Neo4j Browser에서 직접 쿼리

Neo4j Browser (http://localhost:7475) 에서 Cypher 쿼리 실행:

```cypher
// 전체 그래프 통계
MATCH (n) RETURN labels(n) as type, count(n) as count
MATCH ()-[r]->() RETURN type(r) as relation, count(r) as count

// "Phishing" 공격 기법 검색
MATCH (a:AttackPattern)
WHERE toLower(a.name) CONTAINS "phishing"
RETURN a LIMIT 10

// 공격 체인 시각화
MATCH path = (a:AttackPattern)-[:USES|TARGETS|EXPLOITS*1..3]->(target)
WHERE a.name =~ "(?i).*phishing.*"
RETURN path LIMIT 25

// 가장 많이 사용되는 악성코드
MATCH (m:Malware)-[r:USES]-(a:AttackPattern)
WITH m, count(r) as usage_count
ORDER BY usage_count DESC
LIMIT 10
RETURN m.name, usage_count

// MITRE ATT&CK Tactics 별 공격 기법 수
MATCH (a:AttackPattern)
WHERE a.kill_chain_phases IS NOT NULL
UNWIND a.kill_chain_phases as phase
RETURN phase.phase_name as tactic, count(a) as technique_count
ORDER BY technique_count DESC
```

## 📁 파일 구조

```
graphdb/hacking/
├── neo4j_config.py              # Neo4j 연결 설정
├── neo4j_connector.py           # 기본 연결 및 작업
├── stix_to_neo4j.py             # STIX → Neo4j 임포트
├── misp_to_neo4j.py             # MISP → Neo4j 임포트
├── uco_mapping.py               # STIX/MISP → UCO 매핑
├── neo4j_query_utils.py         # 쿼리 유틸리티
├── generate_qa_dataset.py       # QA 데이터셋 생성
├── docker-compose.yml           # Neo4j Docker 설정
├── requirements.txt             # 의존성
└── README.md                    # 이 파일

data/
├── enterprise-attack.json       # MITRE ATT&CK 데이터
├── stix_bundles/                # STIX 데이터 번들
└── misp_exports/                # MISP 내보내기 파일
```

## 🔧 UCO 온톨로지 매핑

### STIX → UCO 매핑 예시

| STIX Object | UCO Class | 설명 |
|------------|-----------|------|
| Indicator | Observable | IoC (IP, Hash, URL 등) |
| Malware | Observable (File/Process) | 악성코드 |
| Attack Pattern | Action | 공격 기법 |
| Threat Actor | Identity | 위협 주체 |
| Vulnerability | Observable (Vulnerability) | 취약점 |
| Relationship | Relationship | 객체 간 관계 |

### Neo4j 노드 레이블

```
:Observable          # 관찰 가능한 객체
  :IPAddress
  :DomainName
  :FileHash
  :URL
  :EmailAddress

:Action              # 액션/공격
  :AttackPattern
  :Malware
  :Tool

:Identity            # 주체
  :ThreatActor
  :IntrusionSet

:Vulnerability       # 취약점
  :CVE

:Mitigation          # 대응 방안
  :CourseOfAction
```

## 🎓 QA 데이터셋 생성

```bash
# QA 데이터셋 생성
python generate_qa_dataset.py \
  --output qa_dataset/hacking_qa.json \
  --num-samples 1000 \
  --difficulty all

# 난이도별 샘플 수
# - Easy: 단일 hop (예: "이 악성코드는 어떤 공격 기법을 사용하는가?")
# - Medium: 2-3 hop (예: "이 공격 그룹이 사용하는 악성코드의 공통 특징은?")
# - Hard: 4+ hop (예: "이 캠페인과 관련된 공격 체인을 CVE와 연결하여 설명하라")
```

## 📖 다음 단계

1. **MITRE ATT&CK 통합**: ATT&CK Matrix 완전 매핑
2. **실시간 위협 인텔리전스**: OSINT 피드 자동 수집
3. **GraphRAG**: 위협 인텔리전스 검색 증강 생성
4. **자동 TTP 추출**: 보안 리포트에서 TTP 자동 추출

## 🔗 참고 자료

- [STIX 2.x Specification](https://oasis-open.github.io/cti-documentation/)
- [UCO Ontology](https://unifiedcyberontology.org/)
- [MITRE ATT&CK](https://attack.mitre.org/)
- [MISP Project](https://www.misp-project.org/)
- [Neo4j Graph Database](https://neo4j.com/)

## 📝 참고사항
앞으로는 docker 설정을 변경할 때:
- docker-compose.yml 수정
- neo4j_config.py 동일하게 수정
- 컨테이너 재시작: docker-compose down -v && docker-compose up -d
- 인증 잠금이 발생하면 -v 옵션으로 볼륨까지 삭제해야 합니다! 💡
