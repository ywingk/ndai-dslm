"""
Neo4j 연동 예제
---------------
기본 사용법과 주요 쿼리 예제
"""
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig
from neo4j_query_utils import Neo4jQueryUtils


def example_basic_queries():
    """기본 쿼리 예제"""
    print("=" * 60)
    print("📌 예제 1: 기본 쿼리")
    print("=" * 60)
    
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        utils = Neo4jQueryUtils(conn)
        
        # 데이터베이스 통계
        stats = conn.get_stats()
        print(f"\n📊 데이터베이스 통계:")
        print(f"  - 총 노드: {stats['nodes']:,}개")
        print(f"  - 총 관계: {stats['relationships']:,}개")
        
        # Concept 검색
        print(f"\n🔍 'dental caries' 검색:")
        concept = utils.get_concept_by_term("dental caries")
        if concept:
            print(f"  ✓ 찾음: {concept['term']}")
            print(f"    ID: {concept['conceptId']}")
        else:
            print("  ✗ 검색 결과 없음")


def example_relationship_queries():
    """관계 쿼리 예제"""
    print("\n" + "=" * 60)
    print("📌 예제 2: 관계 쿼리")
    print("=" * 60)
    
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        utils = Neo4jQueryUtils(conn)
        
        # Dental caries의 직접 관계
        concept = utils.get_concept_by_term("dental caries")
        if concept:
            print(f"\n🔗 '{concept['term']}'의 직접 관계:")
            rels = utils.get_direct_relationships(concept['conceptId'], direction="outgoing")
            
            for i, rel in enumerate(rels[:10], 1):
                print(f"  {i}. {rel['relation']}: {rel['target_term']}")
            
            if len(rels) > 10:
                print(f"  ... 외 {len(rels) - 10}개 더")


def example_multihop_queries():
    """Multi-hop 쿼리 예제"""
    print("\n" + "=" * 60)
    print("📌 예제 3: Multi-hop 경로")
    print("=" * 60)
    
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        utils = Neo4jQueryUtils(conn)
        
        concept = utils.get_concept_by_term("dental caries")
        if concept:
            print(f"\n🛤️  '{concept['term']}'에서 2-hop 거리의 개념들:")
            multihop = utils.find_multihop_concepts(concept['conceptId'], hops=2)
            
            for i, item in enumerate(multihop[:10], 1):
                print(f"  {i}. {item['term']} (거리: {item['distance']})")
            
            if len(multihop) > 10:
                print(f"  ... 외 {len(multihop) - 10}개 더")


def example_graph_analysis():
    """그래프 분석 예제"""
    print("\n" + "=" * 60)
    print("📌 예제 4: 그래프 분석")
    print("=" * 60)
    
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        utils = Neo4jQueryUtils(conn)
        
        # 가장 연결이 많은 개념들
        print(f"\n🌟 가장 연결이 많은 개념 (Top 10):")
        top_concepts = utils.get_most_connected_concepts(limit=10)
        
        for i, c in enumerate(top_concepts, 1):
            print(f"  {i}. {c['term']}: {c['degree']}개 연결")
        
        # 관계 타입 분포
        print(f"\n📈 관계 타입 분포:")
        rel_dist = utils.get_relationship_distribution()
        
        for i, item in enumerate(rel_dist[:5], 1):
            print(f"  {i}. {item['relationType']}: {item['count']}개")


def example_qa_data_extraction():
    """QA 생성용 데이터 추출 예제"""
    print("\n" + "=" * 60)
    print("📌 예제 5: QA 데이터 추출")
    print("=" * 60)
    
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        utils = Neo4jQueryUtils(conn)
        
        concept = utils.get_concept_by_term("dental caries")
        if concept:
            # 1-hop QA 데이터
            print(f"\n📝 1-hop QA 데이터 (단순 사실):")
            qa_data = utils.get_qa_single_hop_data(concept['conceptId'])
            
            for i, data in enumerate(qa_data[:3], 1):
                print(f"\n  예시 {i}:")
                print(f"    Q: {data['source_term']}의 {data['relation_term']}은 무엇인가요?")
                print(f"    A: {data['source_term']}의 {data['relation_term']}은 {data['target_term']}입니다.")
            
            # Multi-hop QA 데이터
            print(f"\n📝 Multi-hop QA 데이터 (복잡한 추론):")
            paths = utils.get_qa_multihop_paths(concept['conceptId'], min_hops=2, max_hops=2, limit=3)
            
            for i, path in enumerate(paths, 1):
                print(f"\n  경로 {i} ({path['hops']}-hop):")
                print(f"    개념들: {' → '.join(path['terms'])}")
                print(f"    관계들: {' → '.join(path['relations'])}")


def example_custom_cypher():
    """사용자 정의 Cypher 쿼리 예제"""
    print("\n" + "=" * 60)
    print("📌 예제 6: 사용자 정의 Cypher 쿼리")
    print("=" * 60)
    
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        # 사용자 정의 쿼리: "tooth"가 포함된 모든 개념
        custom_query = """
        MATCH (c:Concept)
        WHERE toLower(c.term) CONTAINS 'tooth'
        RETURN c.conceptId as id, c.term as term
        LIMIT 10
        """
        
        print(f"\n🔧 사용자 정의 쿼리: 'tooth'가 포함된 개념들")
        results = conn.execute_query(custom_query)
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['term']} ({result['id']})")


def main():
    """모든 예제 실행"""
    print("\n🚀 Neo4j 그래프 데이터베이스 예제\n")
    
    try:
        example_basic_queries()
        example_relationship_queries()
        example_multihop_queries()
        example_graph_analysis()
        example_qa_data_extraction()
        example_custom_cypher()
        
        print("\n" + "=" * 60)
        print("✅ 모든 예제 실행 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        print("\n💡 확인사항:")
        print("  1. Neo4j가 실행 중인가요?")
        print("  2. neo4j_config.py에서 비밀번호를 설정했나요?")
        print("  3. SNOMED CT 데이터를 임포트했나요?")
        print("     → python snomed_to_neo4j.py --clear")


if __name__ == "__main__":
    main()

