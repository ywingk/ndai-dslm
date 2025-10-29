# Domain-Specific SLM (Small Language Model) Project

도메인별 전문가 LLM을 만들기 위한 지식 그래프 기반 프로젝트입니다.

## 🎯 프로젝트 목표

각 도메인의 지식을 Graph DB로 구축하고, 이를 활용하여 도메인 특화 SLM을 학습시키는 것이 주요 목표입니다.

## 📋 개발 계획 - 2025/10/29, Kyi

- 지식 Graph DB를 구축하는 일에서 시작하자
- SLM이 지식 Graph DB를 잘 활용하도록 만드는 것이 주요 임무

## 🏗️ 아키텍처

```
Domain Knowledge Sources
    ↓
Knowledge Graph (Neo4j)
    ↓
QA Dataset Generation
    ↓
Domain-Expert LLM Training
```

## 📁 프로젝트 구조

```
ndai-dslm/
├── graphdb/                          # Graph Database 모듈
│   ├── dental/                       # 치과 도메인
│   │   ├── snomed_to_neo4j.py       # SNOMED CT → Neo4j
│   │   ├── generate_qa_dataset.py   # QA 생성
│   │   └── README.md
│   │
│   ├── hacking/                      # 사이버보안 도메인
│   │   ├── stix_to_neo4j.py         # STIX → Neo4j
│   │   ├── uco_mapping.py           # UCO 온톨로지 매핑
│   │   ├── generate_qa_dataset.py   # QA 생성
│   │   ├── download_mitre_attack.py # MITRE ATT&CK 다운로드
│   │   └── README.md
│   │
│   └── ARCHITECTURE_COMPARISON.md    # 아키텍처 비교 문서
│
├── subgraph/                         # 서브그래프 분석
└── README.md                         # 이 파일
```

## 🚀 시작하기

### 1. Dental Domain (치과)

```bash
cd graphdb/dental

# Neo4j 실행
docker-compose up -d

# SNOMED CT 데이터 임포트
python snomed_to_neo4j.py --keywords "dental caries" --clear

# QA 데이터셋 생성
python generate_qa_dataset.py --output qa_dataset/dental_qa.json

# 사용 예시
python example_usage.py
```

자세한 내용: [graphdb/dental/README.md](graphdb/dental/README.md)

### 2. Hacking Domain (사이버보안)

```bash
cd graphdb/hacking

# 자동 설정 (권장)
./setup.sh

# 또는 수동 설정
docker-compose up -d
python download_mitre_attack.py --domain enterprise
python stix_to_neo4j.py --input data/enterprise-attack.json --clear
python generate_qa_dataset.py --output qa_dataset/hacking_qa.json

# 사용 예시
python example_usage.py
```

자세한 내용: [graphdb/hacking/README.md](graphdb/hacking/README.md)

## 📊 도메인별 특징

### Dental Domain
- **데이터 소스**: SNOMED CT (의료 표준 온톨로지)
- **그래프 크기**: ~10K-50K 노드
- **노드 타입**: Concept (의료 개념)
- **관계 타입**: IS_A, FINDING_SITE, ASSOCIATED_WITH 등
- **QA 샘플**: ~1000개 (Easy/Medium/Hard)

### Hacking Domain
- **데이터 소스**: STIX 2.x (MITRE ATT&CK), MISP
- **그래프 크기**: ~5K-20K 노드
- **노드 타입**: AttackPattern, Malware, ThreatActor, Vulnerability 등
- **관계 타입**: USES, MITIGATES, TARGETS, EXPLOITS 등
- **QA 샘플**: ~1000개 (Easy/Medium/Hard)

## 🔧 기술 스택

- **Graph Database**: Neo4j 5.14+
- **온톨로지**: 
  - Dental: SNOMED CT
  - Hacking: UCO (Unified Cyber Ontology)
- **데이터 형식**:
  - Dental: TSV (RF2)
  - Hacking: JSON (STIX 2.x)
- **Python**: 3.8+
- **주요 라이브러리**: neo4j, pandas, stix2, pymisp

## 📖 아키텍처 비교

도메인별 아키텍처 상세 비교: [graphdb/ARCHITECTURE_COMPARISON.md](graphdb/ARCHITECTURE_COMPARISON.md)

## 🎓 QA 데이터셋

각 도메인은 3단계 난이도의 QA 데이터셋을 생성합니다:

### Easy (30%)
- 1-hop 쿼리
- 직접적인 관계
- 예: "이 개념의 정의는 무엇인가?"

### Medium (40%)
- 2-3 hop 쿼리
- 중간 수준 추론
- 예: "이 공격 그룹이 사용하는 악성코드의 특징은?"

### Hard (30%)
- 4+ hop 쿼리
- 복잡한 추론 및 종합
- 예: "이 캠페인의 공격 체인을 CVE와 연결하여 설명하라"

## 🔍 Neo4j 접속 정보

### Dental Domain
- HTTP (Browser): http://localhost:7474
- Bolt: bolt://localhost:7687
- 인증: neo4j / dental_slm_2025

### Hacking Domain
- HTTP (Browser): http://localhost:7475
- Bolt: bolt://localhost:7688
- 인증: neo4j / hacking_slm_2025

## 📈 향후 계획

### 단기 (1-2개월)
- [x] Dental Domain 구현 완료
- [x] Hacking Domain 구현 완료
- [ ] MISP 데이터 통합 (Hacking)
- [ ] QA 데이터셋 품질 개선

### 중기 (3-6개월)
- [ ] 새로운 도메인 추가 (Legal, Financial 등)
- [ ] GraphRAG 구현 (검색 증강 생성)
- [ ] Multi-hop 추론 개선
- [ ] 도메인 간 크로스 지식 연결

### 장기 (6-12개월)
- [ ] Domain-Expert LLM 학습
- [ ] 실시간 지식 업데이트 파이프라인
- [ ] Multi-Domain Knowledge Graph 통합
- [ ] 프로덕션 배포

## 🤝 기여

새로운 도메인을 추가하고 싶으시다면:

1. `graphdb/{new_domain}` 디렉토리 생성
2. 공통 패턴 따라 구현:
   - `{source}_to_neo4j.py`: 데이터 임포트
   - `neo4j_query_utils.py`: 쿼리 유틸리티
   - `generate_qa_dataset.py`: QA 생성
3. README 및 아키텍처 문서 업데이트

## 📚 참고 자료

### Graph Databases
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)

### Ontologies
- [SNOMED CT](https://www.snomed.org/)
- [UCO (Unified Cyber Ontology)](https://unifiedcyberontology.org/)
- [STIX 2.x](https://oasis-open.github.io/cti-documentation/)

### Threat Intelligence
- [MITRE ATT&CK](https://attack.mitre.org/)
- [MISP Project](https://www.misp-project.org/)

## 📝 라이선스

MIT License (프로젝트 코드)

**주의**: 각 데이터 소스는 별도의 라이선스를 가질 수 있습니다:
- SNOMED CT: IHTSDO 라이선스 필요
- MITRE ATT&CK: Apache 2.0 (자유 사용 가능)

## 👥 연락처

프로젝트 관련 문의: Kyi (2025/10/29)
