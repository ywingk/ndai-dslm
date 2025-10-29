"""
Neo4j에서 난이도별 QA 데이터셋 생성
------------------------------------
SNOMED CT 그래프에서 1-hop, 2-hop, 3-hop 관계를 이용한
난이도별 QA 데이터셋 자동 생성

난이도 분류:
- Level 1 (쉬움): 단순 1-hop 사실 검색
- Level 2 (중간): 2-hop 다단계 추론
- Level 3 (어려움): 3+ hop 복잡한 추론, 복합 관계
"""
import json
import random
from typing import List, Dict, Optional
from tqdm import tqdm
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig
from neo4j_query_utils import Neo4jQueryUtils
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==========================================
# QA 템플릿 정의 (관계 타입별)
# ==========================================

QA_TEMPLATES = {
    # IS_A 관계
    "IS_A": [
        ("{{term}}은(는) 어떤 종류의 개념인가요?", 
         "{{term}}은(는) {{target}}의 하위 개념입니다."),
        ("{{term}}의 상위 개념은 무엇인가요?", 
         "{{term}}의 상위 개념은 {{target}}입니다."),
        ("{{term}}은(는) 무엇으로 분류되나요?", 
         "{{term}}은(는) {{target}}으로 분류됩니다."),
    ],
    
    # FINDING_SITE 관계
    "FINDING_SITE": [
        ("{{term}}은(는) 신체의 어느 부위에서 발생하나요?", 
         "{{term}}은(는) {{target}} 부위에서 발생합니다."),
        ("{{term}}의 발생 부위는 어디인가요?", 
         "{{term}}의 발생 부위는 {{target}}입니다."),
        ("{{term}}은(는) 어디에 위치하나요?", 
         "{{term}}은(는) {{target}}에 위치합니다."),
    ],
    
    # CAUSATIVE_AGENT 관계
    "CAUSATIVE_AGENT": [
        ("{{term}}의 원인은 무엇인가요?", 
         "{{term}}의 주요 원인은 {{target}}입니다."),
        ("{{term}}을(를) 일으키는 원인 물질은 무엇인가요?", 
         "{{term}}을(를) 일으키는 원인 물질은 {{target}}입니다."),
        ("무엇이 {{term}}을(를) 유발하나요?", 
         "{{target}}이(가) {{term}}을(를) 유발합니다."),
    ],
    
    # PATHOLOGICAL_PROCESS 관계
    "PATHOLOGICAL_PROCESS": [
        ("{{term}}의 병태생리학적 과정은 무엇인가요?", 
         "{{term}}의 병태생리학적 과정은 {{target}}입니다."),
        ("{{term}}에서 일어나는 병리학적 과정은 무엇인가요?", 
         "{{term}}에서는 {{target}} 과정이 일어납니다."),
    ],
    
    # ASSOCIATED_MORPHOLOGY 관계
    "ASSOCIATED_MORPHOLOGY": [
        ("{{term}}에서 나타나는 형태학적 변화는 무엇인가요?", 
         "{{term}}에서는 {{target}}의 형태학적 변화가 나타납니다."),
        ("{{term}}의 특징적인 형태는 무엇인가요?", 
         "{{term}}의 특징적인 형태는 {{target}}입니다."),
    ],
    
    # CLINICAL_COURSE 관계
    "CLINICAL_COURSE": [
        ("{{term}}의 임상 경과는 어떤가요?", 
         "{{term}}은(는) {{target}}한 임상 경과를 보입니다."),
        ("{{term}}의 진행 양상은 어떤가요?", 
         "{{term}}은(는) {{target}}한 양상으로 진행됩니다."),
    ],
    
    # DUE_TO 관계
    "DUE_TO": [
        ("{{term}}은(는) 무엇 때문에 발생하나요?", 
         "{{term}}은(는) {{target}} 때문에 발생합니다."),
        ("{{term}}의 원인은 무엇인가요?", 
         "{{term}}은(는) {{target}}로 인해 발생합니다."),
    ],
}


class QADatasetGenerator:
    """난이도별 QA 데이터셋 생성기"""
    
    def __init__(self, config: Neo4jConfig):
        self.config = config
        self.conn = None
        self.utils = None
        
    def connect(self):
        """Neo4j 연결"""
        self.conn = get_connector(self.config)
        self.conn.connect()
        self.utils = Neo4jQueryUtils(self.conn)
        logger.info("✅ Neo4j 연결 완료")
    
    def close(self):
        """연결 종료"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ==========================================
    # Level 1: 단순 1-hop QA 생성
    # ==========================================
    
    def generate_level1_qa(self, max_samples: int = 1000) -> List[Dict]:
        """Level 1: 단순 1-hop 사실 검색 QA
        
        예: "치아 우식증의 원인은?" -> "치아 우식증의 원인은 박테리아입니다."
        """
        logger.info("🔹 Level 1 QA 생성 중 (1-hop)...")
        qa_list = []
        
        # 모든 Concept 조회
        all_concepts = self.conn.execute_query("""
            MATCH (c:Concept)
            RETURN c.conceptId as conceptId, c.term as term
            LIMIT 100
        """)
        
        for concept in tqdm(all_concepts, desc="Level 1 QA"):
            concept_id = concept['conceptId']
            concept_term = concept['term']
            
            # 각 관계 타입별로 QA 생성
            for rel_type in ["IS_A", "FINDING_SITE", "CAUSATIVE_AGENT", 
                            "PATHOLOGICAL_PROCESS", "ASSOCIATED_MORPHOLOGY"]:
                
                # 해당 관계 타입의 데이터 조회
                rels = self.utils.get_direct_relationships(
                    concept_id, 
                    direction="outgoing", 
                    rel_type=rel_type
                )
                
                if not rels or rel_type not in QA_TEMPLATES:
                    continue
                
                # 템플릿 선택 및 QA 생성
                for rel in rels[:2]:  # 각 관계당 최대 2개
                    template = random.choice(QA_TEMPLATES[rel_type])
                    q_template, a_template = template
                    
                    question = q_template.replace("{{term}}", concept_term)\
                                        .replace("{{target}}", rel['target_term'])
                    answer = a_template.replace("{{term}}", concept_term)\
                                      .replace("{{target}}", rel['target_term'])
                    
                    qa_list.append({
                        "id": f"L1_{len(qa_list)}",
                        "level": 1,
                        "difficulty": "easy",
                        "question": question,
                        "answer": answer,
                        "source_concept": concept_term,
                        "relation_type": rel_type,
                        "target_concept": rel['target_term'],
                        "metadata": {
                            "hops": 1,
                            "relation": rel_type
                        }
                    })
                    
                    if len(qa_list) >= max_samples:
                        break
            
            if len(qa_list) >= max_samples:
                break
        
        logger.info(f"  ✓ Level 1 QA {len(qa_list)}개 생성 완료")
        return qa_list
    
    # ==========================================
    # Level 2: 2-hop QA 생성
    # ==========================================
    
    def generate_level2_qa(self, max_samples: int = 500) -> List[Dict]:
        """Level 2: 2-hop 다단계 추론 QA
        
        예: "치아 우식증의 상위 개념의 발생 부위는?" 
            -> "치아 우식증은 질병이고, 질병은 구강에서 발생합니다."
        """
        logger.info("🔹 Level 2 QA 생성 중 (2-hop)...")
        qa_list = []
        
        # 2-hop 경로 조회
        query = """
        MATCH path = (start:Concept)-[r1]->(middle:Concept)-[r2]->(end:Concept)
        WHERE start.term CONTAINS 'caries' OR start.term CONTAINS 'dental'
        RETURN start.term as start_term,
               type(r1) as rel1_type,
               r1.typeTerm as rel1_term,
               middle.term as middle_term,
               type(r2) as rel2_type,
               r2.typeTerm as rel2_term,
               end.term as end_term
        LIMIT 200
        """
        
        paths = self.conn.execute_query(query)
        
        for path in tqdm(paths, desc="Level 2 QA"):
            # 2-hop 추론 QA 생성
            question = f"{path['start_term']}의 {path['rel1_term']}인 {path['middle_term']}의 {path['rel2_term']}은 무엇인가요?"
            answer = f"{path['start_term']}의 {path['rel1_term']}은 {path['middle_term']}이고, " \
                    f"이것의 {path['rel2_term']}은 {path['end_term']}입니다."
            
            qa_list.append({
                "id": f"L2_{len(qa_list)}",
                "level": 2,
                "difficulty": "medium",
                "question": question,
                "answer": answer,
                "source_concept": path['start_term'],
                "intermediate_concept": path['middle_term'],
                "target_concept": path['end_term'],
                "metadata": {
                    "hops": 2,
                    "relations": [path['rel1_type'], path['rel2_type']],
                    "path": f"{path['start_term']} -> {path['middle_term']} -> {path['end_term']}"
                }
            })
            
            if len(qa_list) >= max_samples:
                break
        
        logger.info(f"  ✓ Level 2 QA {len(qa_list)}개 생성 완료")
        return qa_list
    
    # ==========================================
    # Level 3: 3+ hop 복잡한 QA 생성
    # ==========================================
    
    def generate_level3_qa(self, max_samples: int = 200) -> List[Dict]:
        """Level 3: 3+ hop 복잡한 추론 QA
        
        예: "치아 우식증의 원인의 상위 분류의 특성은?"
            -> 다단계 추론 필요
        """
        logger.info("🔹 Level 3 QA 생성 중 (3+ hop)...")
        qa_list = []
        
        # 3-hop 경로 조회
        query = """
        MATCH path = (start:Concept)-[*3..3]->(end:Concept)
        WHERE start.term CONTAINS 'caries'
        WITH start, end, 
             [node in nodes(path) | node.term] as node_terms,
             [rel in relationships(path) | type(rel)] as rel_types
        RETURN start.term as start_term,
               end.term as end_term,
               node_terms,
               rel_types
        LIMIT 100
        """
        
        paths = self.conn.execute_query(query)
        
        for path in tqdm(paths, desc="Level 3 QA"):
            # 복잡한 추론 QA 생성
            question = f"{path['start_term']}에서 3단계 관계를 통해 연결된 개념은 무엇인가요?"
            answer = f"{path['start_term']}은(는) {' -> '.join(path['node_terms'][1:-1])}을(를) " \
                    f"거쳐 {path['end_term']}과(와) 연결됩니다."
            
            qa_list.append({
                "id": f"L3_{len(qa_list)}",
                "level": 3,
                "difficulty": "hard",
                "question": question,
                "answer": answer,
                "source_concept": path['start_term'],
                "target_concept": path['end_term'],
                "metadata": {
                    "hops": 3,
                    "relations": path['rel_types'],
                    "path": " -> ".join(path['node_terms'])
                }
            })
            
            if len(qa_list) >= max_samples:
                break
        
        logger.info(f"  ✓ Level 3 QA {len(qa_list)}개 생성 완료")
        return qa_list
    
    # ==========================================
    # 복합 관계 QA 생성
    # ==========================================
    
    def generate_complex_qa(self, max_samples: int = 200) -> List[Dict]:
        """복합 관계 QA: 여러 관계를 동시에 고려
        
        예: "원인이 박테리아이고 치아에서 발생하는 질병은?"
        """
        logger.info("🔹 복합 관계 QA 생성 중...")
        qa_list = []
        
        # 원인과 부위를 모두 가진 개념
        query = """
        MATCH (concept:Concept)-[:CAUSATIVE_AGENT]->(agent:Concept)
        MATCH (concept)-[:FINDING_SITE]->(site:Concept)
        WHERE concept.term CONTAINS 'caries' OR concept.term CONTAINS 'dental'
        RETURN concept.term as concept_term,
               agent.term as agent_term,
               site.term as site_term
        LIMIT 100
        """
        
        results = self.conn.execute_query(query)
        
        for result in tqdm(results, desc="Complex QA"):
            # 복합 질문 생성
            question = f"원인이 {result['agent_term']}이고 {result['site_term']}에서 발생하는 질병은 무엇인가요?"
            answer = f"{result['concept_term']}은(는) {result['agent_term']}이(가) 원인이며 " \
                    f"{result['site_term']}에서 발생하는 질병입니다."
            
            qa_list.append({
                "id": f"LC_{len(qa_list)}",
                "level": 3,
                "difficulty": "hard",
                "type": "complex",
                "question": question,
                "answer": answer,
                "concept": result['concept_term'],
                "metadata": {
                    "causative_agent": result['agent_term'],
                    "finding_site": result['site_term'],
                    "query_type": "multi_constraint"
                }
            })
            
            if len(qa_list) >= max_samples:
                break
        
        logger.info(f"  ✓ 복합 QA {len(qa_list)}개 생성 완료")
        return qa_list
    
    # ==========================================
    # 전체 데이터셋 생성
    # ==========================================
    
    def generate_all_qa(self, 
                        level1_samples: int = 1000,
                        level2_samples: int = 500,
                        level3_samples: int = 200,
                        complex_samples: int = 200) -> Dict[str, List[Dict]]:
        """모든 난이도의 QA 생성"""
        logger.info("🚀 전체 QA 데이터셋 생성 시작...")
        
        dataset = {
            "level1": self.generate_level1_qa(level1_samples),
            "level2": self.generate_level2_qa(level2_samples),
            "level3": self.generate_level3_qa(level3_samples),
            "complex": self.generate_complex_qa(complex_samples)
        }
        
        # 통계 출력
        total = sum(len(v) for v in dataset.values())
        logger.info("\n📊 생성된 QA 통계:")
        logger.info(f"  - Level 1 (쉬움): {len(dataset['level1'])}개")
        logger.info(f"  - Level 2 (중간): {len(dataset['level2'])}개")
        logger.info(f"  - Level 3 (어려움): {len(dataset['level3'])}개")
        logger.info(f"  - Complex (복합): {len(dataset['complex'])}개")
        logger.info(f"  - 총합: {total}개")
        
        return dataset
    
    # ==========================================
    # 저장
    # ==========================================
    
    def save_to_jsonl(self, dataset: Dict[str, List[Dict]], output_dir: str = "."):
        """JSONL 형식으로 저장"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 난이도별 파일 저장
        for level, qa_list in dataset.items():
            output_file = os.path.join(output_dir, f"qa_{level}.jsonl")
            with open(output_file, 'w', encoding='utf-8') as f:
                for qa in qa_list:
                    f.write(json.dumps(qa, ensure_ascii=False) + '\n')
            logger.info(f"  ✓ {output_file} 저장 완료 ({len(qa_list)}개)")
        
        # 전체 데이터셋 저장
        all_qa = []
        for qa_list in dataset.values():
            all_qa.extend(qa_list)
        
        output_file = os.path.join(output_dir, "qa_all.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for qa in all_qa:
                f.write(json.dumps(qa, ensure_ascii=False) + '\n')
        logger.info(f"  ✓ {output_file} 저장 완료 (총 {len(all_qa)}개)")
        
        # 통계 파일 저장
        stats = {
            "total": len(all_qa),
            "by_level": {k: len(v) for k, v in dataset.items()},
            "by_difficulty": {
                "easy": len(dataset['level1']),
                "medium": len(dataset['level2']),
                "hard": len(dataset['level3']) + len(dataset['complex'])
            }
        }
        
        stats_file = os.path.join(output_dir, "qa_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        logger.info(f"  ✓ {stats_file} 저장 완료")


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Neo4j에서 난이도별 QA 데이터셋 생성")
    parser.add_argument("--output-dir", default="./qa_dataset", help="출력 디렉토리")
    parser.add_argument("--level1", type=int, default=1000, help="Level 1 샘플 수")
    parser.add_argument("--level2", type=int, default=500, help="Level 2 샘플 수")
    parser.add_argument("--level3", type=int, default=200, help="Level 3 샘플 수")
    parser.add_argument("--complex", type=int, default=200, help="복합 QA 샘플 수")
    
    args = parser.parse_args()
    
    # Neo4j 연결 설정
    config = Neo4jConfig.default()
    
    # QA 생성
    with QADatasetGenerator(config) as generator:
        dataset = generator.generate_all_qa(
            level1_samples=args.level1,
            level2_samples=args.level2,
            level3_samples=args.level3,
            complex_samples=args.complex
        )
        
        # 저장
        generator.save_to_jsonl(dataset, args.output_dir)
    
    logger.info("\n✅ QA 데이터셋 생성 완료!")
    logger.info(f"📁 저장 위치: {args.output_dir}/")


if __name__ == "__main__":
    main()

