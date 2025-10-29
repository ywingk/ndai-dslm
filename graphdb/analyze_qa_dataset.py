"""
QA 데이터셋 분석 및 시각화
-------------------------
생성된 QA 데이터셋의 통계와 예시를 확인
"""
import json
import os
from collections import Counter
from typing import List, Dict


def load_jsonl(file_path: str) -> List[Dict]:
    """JSONL 파일 로드"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data


def analyze_qa_dataset(dataset_dir: str = "./qa_dataset"):
    """QA 데이터셋 분석"""
    print("=" * 80)
    print("📊 QA 데이터셋 분석")
    print("=" * 80)
    
    # 통계 로드
    stats_file = os.path.join(dataset_dir, "qa_stats.json")
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    
    print(f"\n📈 전체 통계:")
    print(f"  - 총 QA 쌍: {stats['total']}개")
    print(f"\n난이도별 분포:")
    print(f"  - 쉬움 (Level 1): {stats['by_difficulty']['easy']}개 ({stats['by_difficulty']['easy']/stats['total']*100:.1f}%)")
    print(f"  - 중간 (Level 2): {stats['by_difficulty']['medium']}개 ({stats['by_difficulty']['medium']/stats['total']*100:.1f}%)")
    print(f"  - 어려움 (Level 3+): {stats['by_difficulty']['hard']}개 ({stats['by_difficulty']['hard']/stats['total']*100:.1f}%)")
    
    # Level 1 분석
    print("\n" + "=" * 80)
    print("📌 Level 1 (쉬움) - 단순 1-hop 사실 검색")
    print("=" * 80)
    
    level1_data = load_jsonl(os.path.join(dataset_dir, "qa_level1.jsonl"))
    
    # 관계 타입 분포
    relation_types = Counter([qa['relation_type'] for qa in level1_data])
    print(f"\n관계 타입 분포:")
    for rel_type, count in relation_types.most_common():
        print(f"  - {rel_type}: {count}개 ({count/len(level1_data)*100:.1f}%)")
    
    # 예시
    print(f"\n예시 (3개):")
    for i, qa in enumerate(level1_data[:3], 1):
        print(f"\n  [{i}] {qa['relation_type']}")
        print(f"      Q: {qa['question']}")
        print(f"      A: {qa['answer']}")
    
    # Level 2 분석
    print("\n" + "=" * 80)
    print("📌 Level 2 (중간) - 2-hop 다단계 추론")
    print("=" * 80)
    
    level2_data = load_jsonl(os.path.join(dataset_dir, "qa_level2.jsonl"))
    
    # 관계 조합 분석
    relation_combos = Counter([
        " -> ".join(qa['metadata']['relations']) 
        for qa in level2_data
    ])
    print(f"\n관계 조합 Top 5:")
    for combo, count in relation_combos.most_common(5):
        print(f"  - {combo}: {count}개")
    
    # 예시
    print(f"\n예시 (2개):")
    for i, qa in enumerate(level2_data[:2], 1):
        print(f"\n  [{i}] 경로: {' -> '.join(qa['metadata']['relations'])}")
        print(f"      Q: {qa['question']}")
        print(f"      A: {qa['answer']}")
    
    # Level 3 분석
    print("\n" + "=" * 80)
    print("📌 Level 3 (어려움) - 3+ hop 복잡한 추론")
    print("=" * 80)
    
    level3_data = load_jsonl(os.path.join(dataset_dir, "qa_level3.jsonl"))
    
    # hop 수 분포
    hop_counts = Counter([qa['metadata']['hops'] for qa in level3_data])
    print(f"\nHop 수 분포:")
    for hops, count in sorted(hop_counts.items()):
        print(f"  - {hops}-hop: {count}개")
    
    # 예시
    print(f"\n예시 (2개):")
    for i, qa in enumerate(level3_data[:2], 1):
        print(f"\n  [{i}] {qa['metadata']['hops']}-hop")
        print(f"      경로: {qa['metadata']['path']}")
        print(f"      Q: {qa['question'][:100]}...")
        print(f"      A: {qa['answer'][:100]}...")
    
    # Complex QA 분석
    print("\n" + "=" * 80)
    print("📌 복합 QA - 여러 제약 조건")
    print("=" * 80)
    
    complex_data = load_jsonl(os.path.join(dataset_dir, "qa_complex.jsonl"))
    
    print(f"\n총 {len(complex_data)}개의 복합 QA")
    
    # 예시
    print(f"\n예시 (2개):")
    for i, qa in enumerate(complex_data[:2], 1):
        print(f"\n  [{i}] 복합 제약")
        print(f"      원인: {qa['metadata']['causative_agent']}")
        print(f"      부위: {qa['metadata']['finding_site']}")
        print(f"      Q: {qa['question']}")
        print(f"      A: {qa['answer']}")
    
    # 난이도별 질문 길이 분석
    print("\n" + "=" * 80)
    print("📊 질문/답변 길이 분석")
    print("=" * 80)
    
    all_data = {
        "Level 1": level1_data,
        "Level 2": level2_data,
        "Level 3": level3_data,
        "Complex": complex_data
    }
    
    for level_name, data in all_data.items():
        avg_q_len = sum(len(qa['question']) for qa in data) / len(data)
        avg_a_len = sum(len(qa['answer']) for qa in data) / len(data)
        print(f"\n{level_name}:")
        print(f"  - 평균 질문 길이: {avg_q_len:.1f}자")
        print(f"  - 평균 답변 길이: {avg_a_len:.1f}자")
    
    print("\n" + "=" * 80)
    print("✅ 분석 완료!")
    print("=" * 80)


def export_samples(dataset_dir: str = "./qa_dataset", 
                   output_file: str = "./qa_samples.md"):
    """샘플 QA를 Markdown으로 출력"""
    print(f"\n📝 샘플 QA를 {output_file}로 출력 중...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# QA 데이터셋 샘플\n\n")
        
        # Level 1
        f.write("## Level 1 (쉬움) - 단순 1-hop 사실 검색\n\n")
        level1_data = load_jsonl(os.path.join(dataset_dir, "qa_level1.jsonl"))
        for i, qa in enumerate(level1_data[:5], 1):
            f.write(f"### 예시 {i}: {qa['relation_type']}\n\n")
            f.write(f"**Q:** {qa['question']}\n\n")
            f.write(f"**A:** {qa['answer']}\n\n")
            f.write(f"- 난이도: {qa['difficulty']}\n")
            f.write(f"- 관계: {qa['relation_type']}\n\n")
            f.write("---\n\n")
        
        # Level 2
        f.write("## Level 2 (중간) - 2-hop 다단계 추론\n\n")
        level2_data = load_jsonl(os.path.join(dataset_dir, "qa_level2.jsonl"))
        for i, qa in enumerate(level2_data[:5], 1):
            f.write(f"### 예시 {i}\n\n")
            f.write(f"**Q:** {qa['question']}\n\n")
            f.write(f"**A:** {qa['answer']}\n\n")
            f.write(f"- 난이도: {qa['difficulty']}\n")
            f.write(f"- 경로: {qa['metadata']['path']}\n\n")
            f.write("---\n\n")
        
        # Level 3
        f.write("## Level 3 (어려움) - 3+ hop 복잡한 추론\n\n")
        level3_data = load_jsonl(os.path.join(dataset_dir, "qa_level3.jsonl"))
        for i, qa in enumerate(level3_data[:5], 1):
            f.write(f"### 예시 {i}\n\n")
            f.write(f"**Q:** {qa['question']}\n\n")
            f.write(f"**A:** {qa['answer']}\n\n")
            f.write(f"- 난이도: {qa['difficulty']}\n")
            f.write(f"- Hop 수: {qa['metadata']['hops']}\n")
            f.write(f"- 경로: {qa['metadata']['path']}\n\n")
            f.write("---\n\n")
        
        # Complex
        f.write("## 복합 QA - 여러 제약 조건\n\n")
        complex_data = load_jsonl(os.path.join(dataset_dir, "qa_complex.jsonl"))
        for i, qa in enumerate(complex_data[:5], 1):
            f.write(f"### 예시 {i}\n\n")
            f.write(f"**Q:** {qa['question']}\n\n")
            f.write(f"**A:** {qa['answer']}\n\n")
            f.write(f"- 난이도: {qa['difficulty']}\n")
            f.write(f"- 원인: {qa['metadata']['causative_agent']}\n")
            f.write(f"- 부위: {qa['metadata']['finding_site']}\n\n")
            f.write("---\n\n")
    
    print(f"✅ {output_file} 생성 완료")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="QA 데이터셋 분석")
    parser.add_argument("--dataset-dir", default="./qa_dataset", help="데이터셋 디렉토리")
    parser.add_argument("--export-samples", action="store_true", help="샘플을 Markdown으로 출력")
    
    args = parser.parse_args()
    
    # 분석 실행
    analyze_qa_dataset(args.dataset_dir)
    
    # 샘플 출력
    if args.export_samples:
        export_samples(args.dataset_dir, "./qa_samples.md")


if __name__ == "__main__":
    main()

