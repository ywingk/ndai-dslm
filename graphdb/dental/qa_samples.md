# QA 데이터셋 샘플

## Level 1 (쉬움) - 단순 1-hop 사실 검색

### 예시 1: IS_A

**Q:** Secondary non-active dental caries extending into outer third of dentin (disorder)은(는) 무엇으로 분류되나요?

**A:** Secondary non-active dental caries extending into outer third of dentin (disorder)은(는) Secondary non-active dental caries extending into dentin (disorder)으로 분류됩니다.

- 난이도: easy
- 관계: IS_A

---

### 예시 2: FINDING_SITE

**Q:** Secondary non-active dental caries extending into outer third of dentin (disorder)은(는) 어디에 위치하나요?

**A:** Secondary non-active dental caries extending into outer third of dentin (disorder)은(는) Outer third of dentin (body structure)에 위치합니다.

- 난이도: easy
- 관계: FINDING_SITE

---

### 예시 3: CAUSATIVE_AGENT

**Q:** 무엇이 Secondary non-active dental caries extending into outer third of dentin (disorder)을(를) 유발하나요?

**A:** Domain Bacteria (organism)이(가) Secondary non-active dental caries extending into outer third of dentin (disorder)을(를) 유발합니다.

- 난이도: easy
- 관계: CAUSATIVE_AGENT

---

### 예시 4: PATHOLOGICAL_PROCESS

**Q:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 병태생리학적 과정은 무엇인가요?

**A:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 병태생리학적 과정은 Infectious process (qualifier value)입니다.

- 난이도: easy
- 관계: PATHOLOGICAL_PROCESS

---

### 예시 5: ASSOCIATED_MORPHOLOGY

**Q:** Secondary non-active dental caries extending into outer third of dentin (disorder)에서 나타나는 형태학적 변화는 무엇인가요?

**A:** Secondary non-active dental caries extending into outer third of dentin (disorder)에서는 Secondary non-active caries (morphologic abnormality)의 형태학적 변화가 나타납니다.

- 난이도: easy
- 관계: ASSOCIATED_MORPHOLOGY

---

## Level 2 (중간) - 2-hop 다단계 추론

### 예시 1

**Q:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 Is a인 Secondary non-active dental caries extending into dentin (disorder)의 Pathological process은 무엇인가요?

**A:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 Is a은 Secondary non-active dental caries extending into dentin (disorder)이고, 이것의 Pathological process은 Infectious process (qualifier value)입니다.

- 난이도: medium
- 경로: Secondary non-active dental caries extending into outer third of dentin (disorder) -> Secondary non-active dental caries extending into dentin (disorder) -> Infectious process (qualifier value)

---

### 예시 2

**Q:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 Is a인 Secondary non-active dental caries extending into dentin (disorder)의 Causative agent은 무엇인가요?

**A:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 Is a은 Secondary non-active dental caries extending into dentin (disorder)이고, 이것의 Causative agent은 Domain Bacteria (organism)입니다.

- 난이도: medium
- 경로: Secondary non-active dental caries extending into outer third of dentin (disorder) -> Secondary non-active dental caries extending into dentin (disorder) -> Domain Bacteria (organism)

---

### 예시 3

**Q:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 Is a인 Secondary non-active dental caries extending into dentin (disorder)의 Associated morphology은 무엇인가요?

**A:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 Is a은 Secondary non-active dental caries extending into dentin (disorder)이고, 이것의 Associated morphology은 Secondary non-active caries (morphologic abnormality)입니다.

- 난이도: medium
- 경로: Secondary non-active dental caries extending into outer third of dentin (disorder) -> Secondary non-active dental caries extending into dentin (disorder) -> Secondary non-active caries (morphologic abnormality)

---

### 예시 4

**Q:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 Is a인 Secondary non-active dental caries extending into dentin (disorder)의 Finding site은 무엇인가요?

**A:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 Is a은 Secondary non-active dental caries extending into dentin (disorder)이고, 이것의 Finding site은 Dentin structure (body structure)입니다.

- 난이도: medium
- 경로: Secondary non-active dental caries extending into outer third of dentin (disorder) -> Secondary non-active dental caries extending into dentin (disorder) -> Dentin structure (body structure)

---

### 예시 5

**Q:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 Is a인 Secondary non-active dental caries extending into dentin (disorder)의 Is a은 무엇인가요?

**A:** Secondary non-active dental caries extending into outer third of dentin (disorder)의 Is a은 Secondary non-active dental caries extending into dentin (disorder)이고, 이것의 Is a은 Arrested dental caries (disorder)입니다.

- 난이도: medium
- 경로: Secondary non-active dental caries extending into outer third of dentin (disorder) -> Secondary non-active dental caries extending into dentin (disorder) -> Arrested dental caries (disorder)

---

## Level 3 (어려움) - 3+ hop 복잡한 추론

### 예시 1

**Q:** Active cavitated caries of tooth root (disorder)에서 3단계 관계를 통해 연결된 개념은 무엇인가요?

**A:** Active cavitated caries of tooth root (disorder)은(는) Active dental caries (disorder) -> Dental caries (disorder)을(를) 거쳐 Infectious disease (disorder)과(와) 연결됩니다.

- 난이도: hard
- Hop 수: 3
- 경로: Active cavitated caries of tooth root (disorder) -> Active dental caries (disorder) -> Dental caries (disorder) -> Infectious disease (disorder)

---

### 예시 2

**Q:** Active cavitated caries of tooth root (disorder)에서 3단계 관계를 통해 연결된 개념은 무엇인가요?

**A:** Active cavitated caries of tooth root (disorder)은(는) Active dental caries (disorder) -> Dental caries (disorder)을(를) 거쳐 Infectious process (qualifier value)과(와) 연결됩니다.

- 난이도: hard
- Hop 수: 3
- 경로: Active cavitated caries of tooth root (disorder) -> Active dental caries (disorder) -> Dental caries (disorder) -> Infectious process (qualifier value)

---

### 예시 3

**Q:** Active cavitated caries of tooth root (disorder)에서 3단계 관계를 통해 연결된 개념은 무엇인가요?

**A:** Active cavitated caries of tooth root (disorder)은(는) Active dental caries (disorder) -> Dental caries (disorder)을(를) 거쳐 Bacterium (organism)과(와) 연결됩니다.

- 난이도: hard
- Hop 수: 3
- 경로: Active cavitated caries of tooth root (disorder) -> Active dental caries (disorder) -> Dental caries (disorder) -> Bacterium (organism)

---

### 예시 4

**Q:** Active cavitated caries of tooth root (disorder)에서 3단계 관계를 통해 연결된 개념은 무엇인가요?

**A:** Active cavitated caries of tooth root (disorder)은(는) Active dental caries (disorder) -> Dental caries (disorder)을(를) 거쳐 Domain Bacteria (organism)과(와) 연결됩니다.

- 난이도: hard
- Hop 수: 3
- 경로: Active cavitated caries of tooth root (disorder) -> Active dental caries (disorder) -> Dental caries (disorder) -> Domain Bacteria (organism)

---

### 예시 5

**Q:** Active cavitated caries of tooth root (disorder)에서 3단계 관계를 통해 연결된 개념은 무엇인가요?

**A:** Active cavitated caries of tooth root (disorder)은(는) Active dental caries (disorder) -> Dental caries (disorder)을(를) 거쳐 Caries (morphologic abnormality)과(와) 연결됩니다.

- 난이도: hard
- Hop 수: 3
- 경로: Active cavitated caries of tooth root (disorder) -> Active dental caries (disorder) -> Dental caries (disorder) -> Caries (morphologic abnormality)

---

## 복합 QA - 여러 제약 조건

### 예시 1

**Q:** 원인이 Bacterium (organism)이고 Structure of hard tissue of tooth (body structure)에서 발생하는 질병은 무엇인가요?

**A:** Dental caries associated with enamel hypomineralization (disorder)은(는) Bacterium (organism)이(가) 원인이며 Structure of hard tissue of tooth (body structure)에서 발생하는 질병입니다.

- 난이도: hard
- 원인: Bacterium (organism)
- 부위: Structure of hard tissue of tooth (body structure)

---

### 예시 2

**Q:** 원인이 Bacterium (organism)이고 Jaw region structure (body structure)에서 발생하는 질병은 무엇인가요?

**A:** Dental caries associated with enamel hypomineralization (disorder)은(는) Bacterium (organism)이(가) 원인이며 Jaw region structure (body structure)에서 발생하는 질병입니다.

- 난이도: hard
- 원인: Bacterium (organism)
- 부위: Jaw region structure (body structure)

---

### 예시 3

**Q:** 원인이 Bacterium (organism)이고 Enamel structure (body structure)에서 발생하는 질병은 무엇인가요?

**A:** Dental caries associated with enamel hypomineralization (disorder)은(는) Bacterium (organism)이(가) 원인이며 Enamel structure (body structure)에서 발생하는 질병입니다.

- 난이도: hard
- 원인: Bacterium (organism)
- 부위: Enamel structure (body structure)

---

### 예시 4

**Q:** 원인이 Bacterium (organism)이고 Enamel structure (body structure)에서 발생하는 질병은 무엇인가요?

**A:** Dental caries associated with enamel hypocalcification (disorder)은(는) Bacterium (organism)이(가) 원인이며 Enamel structure (body structure)에서 발생하는 질병입니다.

- 난이도: hard
- 원인: Bacterium (organism)
- 부위: Enamel structure (body structure)

---

### 예시 5

**Q:** 원인이 Bacterium (organism)이고 Jaw region structure (body structure)에서 발생하는 질병은 무엇인가요?

**A:** Dental caries associated with enamel hypocalcification (disorder)은(는) Bacterium (organism)이(가) 원인이며 Jaw region structure (body structure)에서 발생하는 질병입니다.

- 난이도: hard
- 원인: Bacterium (organism)
- 부위: Jaw region structure (body structure)

---

