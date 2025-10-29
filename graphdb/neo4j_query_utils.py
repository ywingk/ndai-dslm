"""
Neo4j 그래프 쿼리 유틸리티
--------------------------
QA 생성 및 그래프 분석을 위한 Cypher 쿼리 함수들
"""
from typing import List, Dict, Any, Optional
from neo4j_connector import Neo4jConnector
import logging

logger = logging.getLogger(__name__)


class Neo4jQueryUtils:
    """Neo4j 쿼리 유틸리티 클래스"""
    
    def __init__(self, connector: Neo4jConnector):
        self.conn = connector
    
    # ==========================================
    # 기본 쿼리
    # ==========================================
    
    def get_concept_by_term(self, term: str) -> Optional[Dict]:
        """용어로 Concept 검색"""
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.term) CONTAINS toLower($term)
        RETURN c.conceptId as conceptId, c.term as term
        LIMIT 1
        """
        results = self.conn.execute_query(query, {"term": term})
        return results[0] if results else None
    
    def get_concept_by_id(self, concept_id: str) -> Optional[Dict]:
        """ID로 Concept 조회"""
        query = """
        MATCH (c:Concept {conceptId: $conceptId})
        RETURN c.conceptId as conceptId, c.term as term
        """
        results = self.conn.execute_query(query, {"conceptId": concept_id})
        return results[0] if results else None
    
    def get_direct_relationships(self, concept_id: str, direction: str = "outgoing", rel_type: str = None) -> List[Dict]:
        """특정 Concept의 직접 관계 조회
        
        Args:
            concept_id: Concept ID
            direction: "outgoing", "incoming", "both"
            rel_type: 특정 관계 타입으로 필터링 (예: "IS_A", "FINDING_SITE")
        """
        rel_pattern = f"[r:{rel_type}]" if rel_type else "[r]"
        
        if direction == "outgoing":
            query = f"""
            MATCH (source:Concept {{conceptId: $conceptId}})-{rel_pattern}->(target:Concept)
            RETURN source.term as source_term,
                   type(r) as relation_type,
                   r.typeTerm as relation,
                   target.term as target_term,
                   target.conceptId as target_id
            """
        elif direction == "incoming":
            query = f"""
            MATCH (source:Concept)-{rel_pattern}->(target:Concept {{conceptId: $conceptId}})
            RETURN source.term as source_term,
                   type(r) as relation_type,
                   r.typeTerm as relation,
                   target.term as target_term,
                   source.conceptId as source_id
            """
        else:  # both
            query = f"""
            MATCH (c1:Concept)-{rel_pattern}-(c2:Concept)
            WHERE c1.conceptId = $conceptId
            RETURN c1.term as concept1_term,
                   type(r) as relation_type,
                   r.typeTerm as relation,
                   c2.term as concept2_term,
                   c2.conceptId as concept2_id
            """
        
        return self.conn.execute_query(query, {"conceptId": concept_id})
    
    # ==========================================
    # Multi-hop 쿼리
    # ==========================================
    
    def find_path(self, start_id: str, end_id: str, max_hops: int = 3) -> List[Dict]:
        """두 Concept 간 경로 찾기"""
        query = """
        MATCH path = shortestPath(
            (start:Concept {conceptId: $startId})-[*1..%d]-(end:Concept {conceptId: $endId})
        )
        RETURN [node in nodes(path) | node.term] as path_terms,
               [rel in relationships(path) | rel.typeTerm] as relations,
               length(path) as hops
        LIMIT 5
        """ % max_hops
        
        return self.conn.execute_query(query, {
            "startId": start_id,
            "endId": end_id
        })
    
    def find_multihop_concepts(self, start_id: str, hops: int = 2) -> List[Dict]:
        """N-hop 거리의 모든 Concept 찾기"""
        query = """
        MATCH path = (start:Concept {conceptId: $startId})-[*%d..%d]->(end:Concept)
        WHERE start <> end
        RETURN DISTINCT end.conceptId as conceptId,
                        end.term as term,
                        length(path) as distance
        LIMIT 100
        """ % (hops, hops)
        
        return self.conn.execute_query(query, {"startId": start_id})
    
    def find_common_ancestors(self, concept_id1: str, concept_id2: str) -> List[Dict]:
        """두 Concept의 공통 상위 개념 찾기"""
        query = """
        MATCH (c1:Concept {conceptId: $id1})-[:RELATED_TO*1..3]->(ancestor:Concept),
              (c2:Concept {conceptId: $id2})-[:RELATED_TO*1..3]->(ancestor)
        WHERE c1 <> c2
        RETURN ancestor.conceptId as conceptId,
               ancestor.term as term
        LIMIT 10
        """
        
        return self.conn.execute_query(query, {
            "id1": concept_id1,
            "id2": concept_id2
        })
    
    # ==========================================
    # 그래프 분석
    # ==========================================
    
    def get_most_connected_concepts(self, limit: int = 10) -> List[Dict]:
        """가장 연결이 많은 Concept들"""
        query = """
        MATCH (c:Concept)-[r:RELATED_TO]-()
        WITH c, count(r) as degree
        ORDER BY degree DESC
        LIMIT $limit
        RETURN c.conceptId as conceptId,
               c.term as term,
               degree
        """
        
        return self.conn.execute_query(query, {"limit": limit})
    
    def get_relationship_distribution(self) -> List[Dict]:
        """관계 타입별 분포"""
        query = """
        MATCH ()-[r]->()
        WITH type(r) as relationshipType, 
             head(collect(r.typeTerm)) as typeTerm,
             count(r) as count
        ORDER BY count DESC
        RETURN relationshipType, typeTerm, count
        """
        
        return self.conn.execute_query(query)
    
    def get_relationship_types(self) -> List[str]:
        """데이터베이스에 존재하는 모든 관계 타입 조회"""
        query = """
        CALL db.relationshipTypes() YIELD relationshipType
        RETURN relationshipType
        ORDER BY relationshipType
        """
        
        results = self.conn.execute_query(query)
        return [r["relationshipType"] for r in results]
    
    def find_leaf_concepts(self, limit: int = 20) -> List[Dict]:
        """말단 Concept들 (자식이 없는 노드)"""
        query = """
        MATCH (c:Concept)
        WHERE NOT (c)<-[:RELATED_TO]-()
        RETURN c.conceptId as conceptId,
               c.term as term
        LIMIT $limit
        """
        
        return self.conn.execute_query(query, {"limit": limit})
    
    # ==========================================
    # QA 생성용 쿼리
    # ==========================================
    
    def get_qa_single_hop_data(self, concept_id: str, rel_type: str = None) -> List[Dict]:
        """단순 1-hop QA 생성용 데이터
        
        Args:
            concept_id: 시작 Concept ID
            rel_type: 특정 관계 타입으로 필터링 (선택)
        """
        rel_pattern = f"[r:{rel_type}]" if rel_type else "[r]"
        
        query = f"""
        MATCH (source:Concept {{conceptId: $conceptId}})-{rel_pattern}->(target:Concept)
        RETURN source.term as source_term,
               type(r) as relation_type,
               r.typeId as relation_id,
               r.typeTerm as relation_term,
               target.term as target_term,
               target.conceptId as target_id
        """
        
        return self.conn.execute_query(query, {"conceptId": concept_id})
    
    def get_qa_multihop_paths(self, start_id: str, min_hops: int = 2, max_hops: int = 3, limit: int = 50) -> List[Dict]:
        """Multi-hop QA 생성용 경로 데이터"""
        query = """
        MATCH path = (start:Concept {conceptId: $startId})-[*%d..%d]->(end:Concept)
        WHERE start <> end
        WITH path, [node in nodes(path) | node.term] as terms,
                   [rel in relationships(path) | rel.typeTerm] as relations
        RETURN terms, relations, length(path) as hops
        ORDER BY hops
        LIMIT $limit
        """ % (min_hops, max_hops)
        
        return self.conn.execute_query(query, {
            "startId": start_id,
            "limit": limit
        })
    
    def get_comparison_concepts(self, concept_id: str, limit: int = 10) -> List[Dict]:
        """비교 QA 생성용: 비슷한 레벨의 Concept들"""
        query = """
        MATCH (c:Concept {conceptId: $conceptId})-[:RELATED_TO]->(parent:Concept)
        MATCH (sibling:Concept)-[:RELATED_TO]->(parent)
        WHERE c <> sibling
        RETURN DISTINCT sibling.conceptId as conceptId,
                        sibling.term as term
        LIMIT $limit
        """
        
        return self.conn.execute_query(query, {
            "conceptId": concept_id,
            "limit": limit
        })


# 편의 함수들
def search_concept(conn: Neo4jConnector, term: str) -> Optional[Dict]:
    """용어로 Concept 검색 (간편 함수)"""
    utils = Neo4jQueryUtils(conn)
    return utils.get_concept_by_term(term)


def get_neighbors(conn: Neo4jConnector, concept_id: str) -> List[Dict]:
    """이웃 노드 조회 (간편 함수)"""
    utils = Neo4jQueryUtils(conn)
    return utils.get_direct_relationships(concept_id, direction="both")


if __name__ == "__main__":
    from neo4j_connector import get_connector
    from neo4j_config import Neo4jConfig
    
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        utils = Neo4jQueryUtils(conn)
        
        # 예제: "dental caries" 검색
        concept = utils.get_concept_by_term("dental caries")
        if concept:
            print(f"\n🔍 검색 결과: {concept['term']}")
            print(f"   ID: {concept['conceptId']}")
            
            # 직접 관계 조회
            rels = utils.get_direct_relationships(concept['conceptId'])
            print(f"\n📊 직접 관계 ({len(rels)}개):")
            for rel in rels[:5]:
                print(f"  - {rel['relation']}: {rel['target_term']}")

