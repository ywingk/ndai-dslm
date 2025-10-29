# 난이도별 QA 데이터셋

SNOMED CT 치과 서브그래프에서 자동 생성된 난이도별 QA 데이터셋입니다.

## 📊 데이터셋 통계

- **총 QA 쌍**: 621개
- **난이도별 분포**:
  - 쉬움 (Level 1): 221개 (35.6%)
  - 중간 (Level 2): 200개 (32.2%)
  - 어려움 (Level 3+): 200개 (32.2%)

## 📁 파일 구조

```
qa_dataset/
├── qa_all.jsonl        # 전체 QA 데이터셋 (621개)
├── qa_level1.jsonl     # Level 1: 단순 1-hop (221개)
├── qa_level2.jsonl     # Level 2: 2-hop 추론 (200개)
├── qa_level3.jsonl     # Level 3: 3+ hop 추론 (100개)
├── qa_complex.jsonl    # 복합 제약 조건 QA (100개)
└── qa_stats.json       # 통계 정보
```

## 🎯 난이도별 설명

### Level 1 (쉬움) - 단순 1-hop 사실 검색

직접 연결된 관계를 묻는 단순한 질문입니다.

**관계 타입 분포**:
- IS_A: 65개 (29.4%)
- FINDING_SITE: 51개 (23.1%)
- CAUSATIVE_AGENT: 36개 (16.3%)
- PATHOLOGICAL_PROCESS: 36개 (16.3%)
- ASSOCIATED_MORPHOLOGY: 33개 (14.9%)

**예시**:
```json
{
  "question": "치아 우식증의 원인은 무엇인가요?",
  "answer": "치아 우식증의 주요 원인은 박테리아입니다.",
  "level": 1,
  "difficulty": "easy",
  "relation_type": "CAUSATIVE_AGENT"
}
```

**평균 길이**:
- 질문: 75.2자
- 답변: 109.7자

### Level 2 (중간) - 2-hop 다단계 추론

중간 개념을 거쳐 연결된 관계를 이해해야 하는 질문입니다.

**주요 관계 조합**:
- IS_A → IS_A: 36개
- IS_A → FINDING_SITE: 32개
- DUE_TO → IS_A: 32개
- IS_A → PATHOLOGICAL_PROCESS: 21개
- IS_A → CAUSATIVE_AGENT: 21개

**예시**:
```json
{
  "question": "치아 우식증의 상위 개념의 발생 부위는?",
  "answer": "치아 우식증의 상위 개념은 치아 질환이고, 이것의 발생 부위는 구강입니다.",
  "level": 2,
  "difficulty": "medium",
  "metadata": {
    "relations": ["IS_A", "FINDING_SITE"],
    "path": "치아 우식증 -> 치아 질환 -> 구강"
  }
}
```

**평균 길이**:
- 질문: 135.3자
- 답변: 172.5자

### Level 3 (어려움) - 3+ hop 복잡한 추론

여러 단계의 관계를 통해 연결된 개념들을 이해해야 하는 질문입니다.

**Hop 수 분포**:
- 3-hop: 100개

**예시**:
```json
{
  "question": "치아 우식증에서 3단계 관계를 통해 연결된 개념은?",
  "answer": "치아 우식증은 치아 질환 -> 구강 질환을 거쳐 감염성 질환과 연결됩니다.",
  "level": 3,
  "difficulty": "hard",
  "metadata": {
    "hops": 3,
    "relations": ["IS_A", "IS_A", "PATHOLOGICAL_PROCESS"]
  }
}
```

**평균 길이**:
- 질문: 71.7자
- 답변: 162.3자

### 복합 QA - 여러 제약 조건

여러 관계를 동시에 고려해야 하는 복잡한 질문입니다.

**특징**:
- 원인(CAUSATIVE_AGENT)과 부위(FINDING_SITE)를 동시에 제약
- 역방향 추론 필요

**예시**:
```json
{
  "question": "원인이 박테리아이고 치아에서 발생하는 질병은?",
  "answer": "치아 우식증은 박테리아가 원인이며 치아에서 발생하는 질병입니다.",
  "level": 3,
  "difficulty": "hard",
  "type": "complex",
  "metadata": {
    "causative_agent": "Bacterium (organism)",
    "finding_site": "Structure of hard tissue of tooth",
    "query_type": "multi_constraint"
  }
}
```

**평균 길이**:
- 질문: 84.8자
- 답변: 138.0자

## 💡 사용 방법

### Python으로 로드

```python
import json

# JSONL 파일 로드
def load_qa_dataset(file_path):
    qa_list = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            qa_list.append(json.loads(line))
    return qa_list

# Level 1 데이터 로드
level1_qa = load_qa_dataset('qa_dataset/qa_level1.jsonl')

# 예시 출력
for qa in level1_qa[:3]:
    print(f"Q: {qa['question']}")
    print(f"A: {qa['answer']}")
    print(f"Level: {qa['level']}, Difficulty: {qa['difficulty']}")
    print()
```

### Curriculum Learning에 활용

난이도 순서대로 학습:

```python
# 1. Level 1로 기본 개념 학습
train_on_dataset('qa_level1.jsonl', epochs=3)

# 2. Level 2로 추론 능력 향상
train_on_dataset('qa_level2.jsonl', epochs=2)

# 3. Level 3로 복잡한 추론 학습
train_on_dataset('qa_level3.jsonl', epochs=2)

# 4. Complex QA로 종합 능력 향상
train_on_dataset('qa_complex.jsonl', epochs=1)
```

## 📈 품질 관리

### 자동 생성 기준
- ✅ SNOMED CT의 공식 관계 활용
- ✅ 사전 정의된 QA 템플릿 사용
- ✅ 관계 타입별 다양한 질문 형식
- ✅ 메타데이터로 추적 가능

### 제한사항
- 용어가 길고 전문적 (SNOMED CT 용어 그대로 사용)
- 자연스러운 한국어 표현 개선 필요
- 일부 QA는 사람의 검수 권장

## 🔄 데이터셋 재생성

```bash
# 기본 생성 (총 621개)
python generate_qa_dataset.py --output-dir ./qa_dataset

# 샘플 수 조정
python generate_qa_dataset.py \
  --level1 1000 \
  --level2 500 \
  --level3 200 \
  --complex 200 \
  --output-dir ./qa_dataset

# 분석 및 샘플 출력
python analyze_qa_dataset.py --export-samples
```

## 📚 다음 단계

1. **데이터 정제**: 용어 단순화, 자연스러운 표현 개선
2. **데이터 증강**: 
   - 패러프레이징으로 질문 다양화
   - 부정 예제 추가 (잘못된 답변)
3. **Curriculum Learning**: 난이도 순서대로 학습
4. **DPO/RLHF**: 선호도 기반 추가 학습
5. **평가 데이터셋**: 별도의 Test Set 생성

## 📖 참고

- 생성 스크립트: `generate_qa_dataset.py`
- 분석 스크립트: `analyze_qa_dataset.py`
- Neo4j 쿼리: `neo4j_query_utils.py`

