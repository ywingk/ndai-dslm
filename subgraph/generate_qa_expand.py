import json
import random
import networkx as nx
from typing import List, Dict

# -------------------------------
# 1. 질문 템플릿 정의
# -------------------------------
QA_TEMPLATES = [
    ("{source}는 어떤 개념인가요?", "{source}는 {target}과 관련된 개념으로, {relation} 관계를 가집니다."),
    ("{source}와 {target} 사이의 관계는 무엇인가요?", "{source}와 {target}은 SNOMED에서 '{relation}' 관계로 연결됩니다."),
    ("{source}의 원인은 무엇인가요?", "{target}은 {source}의 원인으로 알려져 있습니다."),
    ("{source}는 어떻게 치료하나요?", "{target}은 {source}의 치료 방법으로 사용됩니다."),
    ("{source}와 관련된 질병은 무엇인가요?", "{target}이 {source}와 관련된 질병으로 보고됩니다."),
    ("{source}의 증상에는 어떤 것이 있나요?", "{target}은 {source}의 주요 증상 중 하나입니다."),
    ("{source}의 병리학적 원인은?", "{target}은 {source}의 병리학적 원인으로 분류됩니다."),
    ("{source}와 {target}은 어떤 임상적 연관성이 있나요?", "{source}와 {target}은 임상적으로 '{relation}' 관계를 갖습니다."),
    ("{source}와 유사한 개념은?", "{target}은 {source}와 유사한 개념으로 간주됩니다."),
    ("{source}의 진단은 어떻게 내리나요?", "{target}을 사용하여 {source}를 진단할 수 있습니다.")
]

# 확장형 (추론형) 질문 템플릿
EXPANSION_TEMPLATES = [
    ("왜 {source}가 {target}과 관련이 있나요?", "이는 '{relation}' 관계로 정의되어 있기 때문입니다. {source}는 {target}과 병리적, 해부학적 또는 임상적 연관성을 가집니다."),
    ("{source}가 발생할 때 {target}이 중요한 이유는?", "{target}은 {source}의 진행이나 진단에 중요한 역할을 하기 때문입니다."),
    ("{source}와 {target}의 관계가 임상적으로 의미 있는 이유는?", "이 관계는 {source}의 치료나 예후 평가에 영향을 미치기 때문입니다."),
]

# -------------------------------
# 2. QA 생성 함수
# -------------------------------
def generate_qa_from_subgraph(G: nx.Graph, num_samples: int = 50) -> List[Dict]:
    qa_pairs = []
    edges = list(G.edges(data=True))

    if not edges:
        print("⚠️ 그래프에 edge가 없습니다.")
        return []

    for i, (source, target, data) in enumerate(random.sample(edges, min(len(edges), num_samples))):
        rel = data.get("label", "related_to")

        # 일반형 QA
        q_template, a_template = random.choice(QA_TEMPLATES)
        question = q_template.format(source=source, target=target, relation=rel)
        answer = a_template.format(source=source, target=target, relation=rel)

        qa_pairs.append({
            "id": f"qa_{i}",
            "type": "basic",
            "question": question,
            "answer": answer
        })

        # 확장형 QA 추가
        if random.random() < 0.4:  # 40% 확률로 확장형 생성
            q_template, a_template = random.choice(EXPANSION_TEMPLATES)
            question = q_template.format(source=source, target=target, relation=rel)
            answer = a_template.format(source=source, target=target, relation=rel)
            qa_pairs.append({
                "id": f"qa_{i}_exp",
                "type": "expanded",
                "question": question,
                "answer": answer
            })

    return qa_pairs

# -------------------------------
# 3. JSONL 파일로 저장
# -------------------------------
def save_as_jsonl(qa_data: List[Dict], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for qa in qa_data:
            f.write(json.dumps(qa, ensure_ascii=False) + "\n")
    print(f"✅ {len(qa_data)}개 QA가 '{output_path}'에 저장되었습니다.")

# -------------------------------
# 4. 예시 실행
# -------------------------------
if __name__ == "__main__":
    # 예시 그래프 구성 (실제는 SNOMED subgraph 사용)
    G = nx.DiGraph()
    G.add_edge("Dental caries", "Tooth decay", label="isa")
    G.add_edge("Dental caries", "Bacteria", label="caused_by")
    G.add_edge("Dental caries", "Fluoride treatment", label="treated_by")
    G.add_edge("Dental caries", "Tooth pain", label="has_symptom")
    G.add_edge("Dental caries", "Plaque", label="associated_with")

    qa_data = generate_qa_from_subgraph(G, num_samples=20)
    save_as_jsonl(qa_data, "dental_caries_qa.jsonl")

