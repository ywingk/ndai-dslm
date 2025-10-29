"""
SNOMED CT Subgraph → QA Dataset Generator (JSONL)
-------------------------------------------------
입력: SNOMED CT Relationship / Description 파일 (CSV 또는 RF2 텍스트)
출력: QA dataset (train.jsonl)

⚙ 필요 패키지:
    pip install pandas tqdm
"""
import pandas as pd
import json
from tqdm import tqdm

# -----------------------------
# 1️⃣ RF2 파일 경로 설정
# -----------------------------
import os

FULL_PATH = "/mls/_downloads/SNOMED/data/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/Full/Terminology/"
#SNAP_PATH = "/home/kyi/mls/_downloads/SNOMED/data/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/Snapshot/Terminology"
CONCEPT_FILE = os.path.join(FULL_PATH, "sct2_Concept_Full_INT_20251001.txt")
DESCRIPTION_FILE = os.path.join(FULL_PATH, "sct2_Description_Full-en_INT_20251001.txt") 
RELATIONSHIP_FILE = os.path.join(FULL_PATH, "sct2_Relationship_Full_INT_20251001.txt") 


# ==========================
# 1. 설정값
# ==========================
TARGET_CONCEPT_ID = "80967001"  # Dental caries
OUTPUT_FILE = "dental_caries_qa.jsonl"

# 관계 typeId → 의미 매핑 (SNOMED 관계코드 일부)
REL_MAP = {
    "116680003": "isa",
    "363698007": "finding site",
    "246075003": "causative agent",
    "116676008": "associated morphology",
    "370135005": "clinical course",
    "47429007":  "associated finding",
    "363589002": "associated procedure",
    "255234002": "occurs in",
    "370131001": "pathophysiology",
    "246454002": "associated with",
    "260870009": "method",
    "255234002": "occurs in"
}

# 관계 유형별 QA 템플릿
QA_TEMPLATES = {
    "isa": [
        ("{term}는 어떤 종류의 개념인가요?", "{term}는 {object}의 하위 개념입니다."),
    ],
    "finding site": [
        ("{term}는 인체의 어떤 부위에 발생하나요?", "{term}는 주로 {object} 부위에서 발생합니다.")
    ],
    "causative agent": [
        ("{term}의 원인은 무엇인가요?", "{term}의 주요 원인은 {object}입니다.")
    ],
    "associated morphology": [
        ("{term}에서 나타나는 형태학적 변화는 무엇인가요?", "{term}의 형태학적 변화는 {object}입니다.")
    ],
    "clinical course": [
        ("{term}의 임상 경과는 어떤가요?", "{term}는 {object}한 경과를 보입니다.")
    ],
    "associated finding": [
        ("{term}의 일반적인 증상이나 징후는 무엇인가요?", "{term}의 주요 징후는 {object}입니다.")
    ],
    "associated procedure": [
        ("{term}와 관련된 진단 또는 치료 절차는 무엇인가요?", "{term}의 평가에는 {object}가 사용됩니다.")
    ],
    "pathophysiology": [
        ("{term}의 병태생리는 무엇인가요?", "{term}는 {object} 과정으로 인해 발생합니다.")
    ],
    "associated with": [
        ("{term}과 관련된 질환은 무엇인가요?", "{term}은(는) {object}와 관련이 있습니다.")
    ],
    "occurs in": [
        ("{term}는 어떤 연령대에서 흔한가요?", "{term}는 주로 {object}에서 발생합니다.")
    ]
}


# ==========================
# 2. SNOMED 데이터 로드
# ==========================
def load_snomed_data():
    """
    실제 SNOMED RF2 관계, 설명 파일을 읽는 함수
    여기서는 예시용 CSV 구조로 가정
    """
    relationships = pd.read_csv(RELATIONSHIP_FILE, sep="\t", dtype=str)
    descriptions = pd.read_csv(DESCRIPTION_FILE, sep="\t", dtype=str)
    return relationships, descriptions


# ==========================
# 3. Subgraph 추출
# ==========================
def extract_subgraph(rel_df, target_id, depth=1):
    """특정 concept ID 중심의 1~2-hop 관계 추출"""
    sub = rel_df[rel_df["sourceId"] == target_id].copy()
    if depth > 1:
        # 2-hop 확장
        next_ids = sub["destinationId"].unique().tolist()
        sub2 = rel_df[rel_df["sourceId"].isin(next_ids)]
        sub = pd.concat([sub, sub2])
    return sub


# ==========================
# 4. Concept ID → 명칭 변환
# ==========================
def id_to_term(desc_df, concept_id):
    """SNOMED Description에서 preferred term 반환"""
    term_row = desc_df[(desc_df["conceptId"] == concept_id) &
                       (desc_df["typeId"] == "900000000000003001")]  # FSN
    if not term_row.empty:
        return term_row.iloc[0]["term"]
    else:
        return f"Concept_{concept_id}"


# ==========================
# 5. QA 생성
# ==========================
def generate_qa_from_subgraph(subgraph_df, desc_df):
    qa_list = []
    for _, row in tqdm(subgraph_df.iterrows(), total=len(subgraph_df)):
        src = row["sourceId"]
        rel = REL_MAP.get(row["typeId"], None)
        dst = row["destinationId"]

        if not rel or rel not in QA_TEMPLATES:
            continue

        term = id_to_term(desc_df, src)
        obj = id_to_term(desc_df, dst)

        templates = QA_TEMPLATES[rel]
        for q_temp, a_temp in templates:
            q = q_temp.format(term=term, object=obj)
            a = a_temp.format(term=term, object=obj)
            qa_list.append({
                "instruction": q,
                "input": "",
                "output": a,
                "relation": rel,
                "source": src,
                "target": dst
            })
    return qa_list


# ==========================
# 6. JSONL 저장
# ==========================
def save_jsonl(qa_list, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for item in qa_list:
            json.dump(item, f, ensure_ascii=False)
            f.write("\n")
    print(f"✅ Saved {len(qa_list)} QA pairs → {filename}")


# ==========================
# 7. 실행
# ==========================
if __name__ == "__main__":
    rels, desc = load_snomed_data()
    sub = extract_subgraph(rels, TARGET_CONCEPT_ID, depth=1)
    qa = generate_qa_from_subgraph(sub, desc)
    save_jsonl(qa, OUTPUT_FILE)

