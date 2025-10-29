"""
다양한 SNOMED CT 관계 타입 활용 예제
------------------------------------
IS_A, FINDING_SITE, CAUSATIVE_AGENT 등 다양한 관계 타입별 쿼리
"""
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig
from neo4j_query_utils import Neo4jQueryUtils


def example_relationship_types():
    """데이터베이스의 모든 관계 타입 확인"""
    print("=" * 60)
    print("📌 예제 1: 관계 타입 목록")
    print("=" * 60)
    
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        utils = Neo4jQueryUtils(conn)
        
        # 모든 관계 타입 조회
        rel_types = utils.get_relationship_types()
        print(f"\n🔗 데이터베이스의 관계 타입 ({len(rel_types)}개):")
        for i, rel_type in enumerate(rel_types, 1):
            print(f"  {i}. {rel_type}")
        
        # 관계 타입별 분포
        print(f"\n📊 관계 타입별 개수:")
        distribution = utils.get_relationship_distribution()
        for item in distribution:
            print(f"  {item['relationshipType']:30s} ({item['typeTerm']:40s}): {item['count']}개")


def example_filter_by_relationship():
    """특정 관계 타입으로 필터링"""
    print("\n" + "=" * 60)
    print("📌 예제 2: 특정 관계 타입으로 필터링")
    print("=" * 60)
    
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        utils = Neo4jQueryUtils(conn)
        
        # Dental caries 검색
        concept = utils.get_concept_by_term("dental caries")
        if not concept:
            print("❌ dental caries를 찾을 수 없습니다.")
            return
        
        print(f"\n🔍 개념: {concept['term']}")
        
        # IS_A 관계만 조회
        print(f"\n1️⃣ IS_A 관계 (상위 개념):")
        is_a_rels = utils.get_direct_relationships(
            concept['conceptId'], 
            direction="outgoing",
            rel_type="IS_A"
        )
        for i, rel in enumerate(is_a_rels[:5], 1):
            print(f"  {i}. {rel['target_term']}")
        
        # FINDING_SITE 관계만 조회
        print(f"\n2️⃣ FINDING_SITE 관계 (발생 부위):")
        finding_site_rels = utils.get_direct_relationships(
            concept['conceptId'],
            direction="outgoing",
            rel_type="FINDING_SITE"
        )
        for i, rel in enumerate(finding_site_rels, 1):
            print(f"  {i}. {rel['target_term']}")
        
        # CAUSATIVE_AGENT 관계만 조회
        print(f"\n3️⃣ CAUSATIVE_AGENT 관계 (원인 물질):")
        causative_rels = utils.get_direct_relationships(
            concept['conceptId'],
            direction="outgoing",
            rel_type="CAUSATIVE_AGENT"
        )
        for i, rel in enumerate(causative_rels, 1):
            print(f"  {i}. {rel['target_term']}")


def example_relationship_specific_qa():
    """관계 타입별 QA 생성 예제"""
    print("\n" + "=" * 60)
    print("📌 예제 3: 관계 타입별 QA 생성")
    print("=" * 60)
    
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        utils = Neo4jQueryUtils(conn)
        
        concept = utils.get_concept_by_term("dental caries")
        if not concept:
            return
        
        # IS_A 관계 기반 QA
        print(f"\n💡 IS_A 관계 기반 QA:")
        is_a_data = utils.get_qa_single_hop_data(concept['conceptId'], rel_type="IS_A")
        for i, data in enumerate(is_a_data[:3], 1):
            print(f"\n  예시 {i}:")
            print(f"    Q: {data['source_term']}은(는) 어떤 종류의 질환인가요?")
            print(f"    A: {data['source_term']}은(는) {data['target_term']}의 하위 개념입니다.")
        
        # FINDING_SITE 관계 기반 QA
        print(f"\n💡 FINDING_SITE 관계 기반 QA:")
        site_data = utils.get_qa_single_hop_data(concept['conceptId'], rel_type="FINDING_SITE")
        for i, data in enumerate(site_data[:2], 1):
            print(f"\n  예시 {i}:")
            print(f"    Q: {data['source_term']}은(는) 어디에서 발생하나요?")
            print(f"    A: {data['source_term']}은(는) {data['target_term']} 부위에서 발생합니다.")


def example_custom_cypher_by_type():
    """관계 타입별 사용자 정의 쿼리"""
    print("\n" + "=" * 60)
    print("📌 예제 4: 관계 타입별 Cypher 쿼리")
    print("=" * 60)
    
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        # IS_A 관계로만 연결된 개념 계층 탐색
        query1 = """
        MATCH path = (start:Concept)-[:IS_A*1..3]->(ancestor:Concept)
        WHERE start.term CONTAINS "dental caries"
        WITH start, ancestor, length(path) as depth
        ORDER BY depth
        RETURN start.term as start_term, 
               ancestor.term as ancestor_term, 
               depth
        LIMIT 10
        """
        
        print(f"\n🔍 IS_A 관계 계층 구조 (1-3 hop):")
        results = conn.execute_query(query1)
        for r in results:
            indent = "  " * r['depth']
            print(f"{indent}└─ {r['ancestor_term']} (depth: {r['depth']})")
        
        # CAUSATIVE_AGENT와 FINDING_SITE를 동시에 가진 개념
        query2 = """
        MATCH (concept:Concept)-[:CAUSATIVE_AGENT]->(agent:Concept)
        MATCH (concept)-[:FINDING_SITE]->(site:Concept)
        WHERE concept.term CONTAINS "caries"
        RETURN concept.term as concept, 
               agent.term as causative_agent, 
               site.term as finding_site
        LIMIT 5
        """
        
        print(f"\n🔍 원인 물질과 발생 부위를 모두 가진 개념:")
        results = conn.execute_query(query2)
        for r in results:
            print(f"\n  개념: {r['concept']}")
            print(f"    원인: {r['causative_agent']}")
            print(f"    부위: {r['finding_site']}")


def main():
    """모든 예제 실행"""
    print("\n🚀 SNOMED CT 다양한 관계 타입 활용 예제\n")
    
    try:
        example_relationship_types()
        example_filter_by_relationship()
        example_relationship_specific_qa()
        example_custom_cypher_by_type()
        
        print("\n" + "=" * 60)
        print("✅ 모든 예제 실행 완료!")
        print("=" * 60)
        
        print("\n💡 Neo4j Browser에서 시각화:")
        print("  http://localhost:7474")
        print("\n  추천 쿼리:")
        print("  1. MATCH (c:Concept)-[:IS_A]->(parent) RETURN c, parent LIMIT 25")
        print("  2. MATCH (c:Concept)-[:FINDING_SITE]->(site) RETURN c, site LIMIT 25")
        print("  3. MATCH (c:Concept)-[:CAUSATIVE_AGENT]->(agent) RETURN c, agent LIMIT 25")
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        print("\n💡 먼저 데이터를 새로 임포트하세요:")
        print("  python snomed_to_neo4j.py --keywords 'dental caries' --clear")


if __name__ == "__main__":
    main()

