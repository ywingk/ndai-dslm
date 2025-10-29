import json
import random
import networkx as nx
from typing import List, Dict

# ---------------------------------------
# 1. 다단계 QA 템플릿 정의
# ---------------------------------------
MULTIHOP_TEMPLATES = [
    ("{start}와 {end} 사이에는 어떤 개념적 관계가 있나요?", 
     "{start}는 {path}를 거쳐 {end}와 연결됩니다."),
    ("{start}와 관련된 더 상위 개념은 무엇인가요?", 
     "{start}는 {path} 관계를 통해 {end}의 하위 개념으로 분류됩니다."),
    ("{start}와 {end}는 어떤 임상적 경로로 연관되어 있나요?", 
     "{start}에서 {path}를 따라가면 {end}에 도달합니다."),
]

# ---------------------------------------
# 2. Multi-hop 경로 탐색
# ---------------------------------------
def find_multihop_paths(G: nx.DiGraph, start: str, max_hops: int = 3) -> List[List[str]]:
    paths = []
    for target in G.nodes:
        if start == target:
            continue
        try:
            for path in nx.all_simple_paths(G, start, target, cutoff=max_hops):
                if len(path) > 2:  # multi-hop only
                    paths.append(path)
        except nx.NetworkXNoPath:
            continue
    return paths

# ---------------------------------------
# 3. 자연어 QA 생성
# ---------------------------------------
def generate_multihop_qa(G: nx.DiGraph, start_concept: str, max_hops: int = 3, num_samples: int = 20) -> List[Dict]:
    paths = find_multihop_paths(G, start_concept, max_hops)
    qa_pairs = []

    for i, path in enumerate(random.sample(paths, min(num_samples, len(paths)))):
        end = path[-1]
        path_text = " → ".join(path[1:-1])  # 중간 개념만 표시
        q_template, a_template = random.choice(MULTIHOP_TEMPLATES)
        
        question = q_template.format(start=start_concept, end=end)
        answer = a_template.format(start=start_concept, end=end, path=path_text)
        
        qa_pairs.append({
            "id": f"multi_{i}",
            "type": f"{len(path)-1}-hop",
            "question": question,
            "answer": answer,
            "path": path
        })
    return qa_pairs

# ---------------------------------------
# 4. JSONL 파일로 저장
# ---------------------------------------
def save_as_jsonl(qa_data: List[Dict], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for qa in qa_data:
            f.write(json.dumps(qa, ensure_ascii=False) + "\n")
    print(f"✅ {len(qa_data)}개의 multi-hop QA가 '{output_path}'에 저장되었습니다.")

# ---------------------------------------
# 5. 예시 실행
# ---------------------------------------
if __name__ == "__main__":
    G = nx.DiGraph()

    # 1-hop 관계 (기본)
    G.add_edge("Dental caries", "Bacteria", label="caused_by")
    G.add_edge("Dental caries", "Fluoride treatment", label="treated_by")
    G.add_edge("Dental caries", "Tooth pain", label="has_symptom")

    # 2-hop 관계 확장
    G.add_edge("Bacteria", "Microorganism", label="isa")
    G.add_edge("Microorganism", "Living organism", label="isa")
    G.add_edge("Fluoride treatment", "Preventive dental procedure", label="isa")
    G.add_edge("Preventive dental procedure", "Dental procedure", label="isa")

    qa_data = generate_multihop_qa(G, "Dental caries", max_hops=3, num_samples=10)
    save_as_jsonl(qa_data, "dental_caries_multihop_qa.jsonl")

