"""
Neo4j 데이터베이스 연결 및 기본 작업
-------------------------------------
SNOMED CT 데이터를 Neo4j에 저장하고 쿼리하는 기능 제공
"""
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging
from neo4j_config import Neo4jConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jConnector:
    """Neo4j 데이터베이스 연결 및 작업 클래스"""
    
    def __init__(self, config: Neo4jConfig):
        self.config = config
        self.driver = None
        
    def connect(self):
        """Neo4j 데이터베이스 연결"""
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password)
            )
            # 연결 테스트
            with self.driver.session(database=self.config.database) as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            logger.info(f"✅ Neo4j 연결 성공: {self.config.uri}")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j 연결 실패: {e}")
            return False
    
    def close(self):
        """연결 종료"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j 연결 종료")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """Cypher 쿼리 실행"""
        if not self.driver:
            raise RuntimeError("Neo4j 연결이 없습니다. connect()를 먼저 호출하세요.")
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def execute_write(self, query: str, parameters: Dict[str, Any] = None) -> Any:
        """쓰기 트랜잭션 실행"""
        if not self.driver:
            raise RuntimeError("Neo4j 연결이 없습니다. connect()를 먼저 호출하세요.")
        
        with self.driver.session(database=self.config.database) as session:
            result = session.execute_write(
                lambda tx: tx.run(query, parameters or {}).data()
            )
            return result
    
    def clear_database(self):
        """데이터베이스 초기화 (주의: 모든 데이터 삭제)"""
        logger.warning("⚠️  데이터베이스를 초기화합니다...")
        query = "MATCH (n) DETACH DELETE n"
        self.execute_write(query)
        logger.info("✅ 데이터베이스 초기화 완료")
    
    def create_indexes(self):
        """SNOMED CT용 인덱스 생성"""
        indexes = [
            "CREATE INDEX concept_id IF NOT EXISTS FOR (c:Concept) ON (c.conceptId)",
            "CREATE INDEX concept_term IF NOT EXISTS FOR (c:Concept) ON (c.term)",
            "CREATE CONSTRAINT concept_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.conceptId IS UNIQUE"
        ]
        
        for idx_query in indexes:
            try:
                self.execute_write(idx_query)
                logger.info(f"✅ 인덱스 생성: {idx_query[:50]}...")
            except Exception as e:
                logger.warning(f"인덱스 생성 건너뜀: {e}")
    
    def get_node_count(self) -> int:
        """노드 개수 조회"""
        result = self.execute_query("MATCH (n) RETURN count(n) as count")
        return result[0]["count"] if result else 0
    
    def get_relationship_count(self) -> int:
        """관계 개수 조회"""
        result = self.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
        return result[0]["count"] if result else 0
    
    def get_stats(self) -> Dict[str, Any]:
        """데이터베이스 통계 조회"""
        stats = {
            "nodes": self.get_node_count(),
            "relationships": self.get_relationship_count()
        }
        
        # 라벨별 노드 수
        label_query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        ORDER BY count DESC
        """
        stats["node_labels"] = self.execute_query(label_query)
        
        # 관계 타입별 수
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """
        stats["relationship_types"] = self.execute_query(rel_query)
        
        return stats


# 편의 함수
def get_connector(config: Optional[Neo4jConfig] = None) -> Neo4jConnector:
    """Neo4j 커넥터 인스턴스 생성"""
    if config is None:
        config = Neo4jConfig.from_env()
    return Neo4jConnector(config)


if __name__ == "__main__":
    # 테스트
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        stats = conn.get_stats()
        print("📊 Neo4j 데이터베이스 통계:")
        print(f"  - 총 노드 수: {stats['nodes']}")
        print(f"  - 총 관계 수: {stats['relationships']}")

