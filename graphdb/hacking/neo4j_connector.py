"""
Neo4j 연결 및 기본 작업 - Hacking Domain
"""
from neo4j import GraphDatabase
from neo4j_config import Neo4jConfig
import logging
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jConnector:
    """Neo4j 데이터베이스 연결 및 기본 작업"""
    
    def __init__(self, config: Neo4jConfig):
        self.config = config
        self.driver = None
        
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password)
            )
            # 연결 테스트
            self.driver.verify_connectivity()
            logger.info(f"✓ Neo4j 연결 성공: {self.config.uri}")
        except Exception as e:
            logger.error(f"❌ Neo4j 연결 실패: {e}")
            raise
    
    def close(self):
        """연결 종료"""
        if self.driver:
            self.driver.close()
            logger.info("✓ Neo4j 연결 종료")
    
    def execute_read(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """읽기 쿼리 실행"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def execute_write(self, query: str, parameters: Optional[Dict] = None) -> Any:
        """쓰기 쿼리 실행"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, parameters or {})
            return result.consume()
    
    def clear_database(self):
        """데이터베이스 초기화 (모든 노드와 관계 삭제)"""
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        self.execute_write(query)
        logger.info("✓ 데이터베이스 초기화 완료")
    
    def create_indexes(self):
        """인덱스 생성"""
        indexes = [
            # STIX 관련 인덱스
            "CREATE INDEX stix_id_idx IF NOT EXISTS FOR (n:StixObject) ON (n.id)",
            "CREATE INDEX attack_pattern_name_idx IF NOT EXISTS FOR (n:AttackPattern) ON (n.name)",
            "CREATE INDEX malware_name_idx IF NOT EXISTS FOR (n:Malware) ON (n.name)",
            "CREATE INDEX threat_actor_name_idx IF NOT EXISTS FOR (n:ThreatActor) ON (n.name)",
            "CREATE INDEX tool_name_idx IF NOT EXISTS FOR (n:Tool) ON (n.name)",
            "CREATE INDEX vulnerability_cve_idx IF NOT EXISTS FOR (n:Vulnerability) ON (n.cve_id)",
            "CREATE INDEX indicator_pattern_idx IF NOT EXISTS FOR (n:Indicator) ON (n.pattern)",
            "CREATE INDEX observable_value_idx IF NOT EXISTS FOR (n:Observable) ON (n.value)",
            
            # MISP 관련 인덱스
            "CREATE INDEX misp_event_id_idx IF NOT EXISTS FOR (n:Event) ON (n.id)",
            "CREATE INDEX misp_event_uuid_idx IF NOT EXISTS FOR (n:Event) ON (n.uuid)",
            "CREATE INDEX misp_attribute_uuid_idx IF NOT EXISTS FOR (n:Attribute) ON (n.uuid)",
            "CREATE INDEX misp_attribute_value_idx IF NOT EXISTS FOR (n:Attribute) ON (n.value)",
            "CREATE INDEX misp_attribute_type_idx IF NOT EXISTS FOR (n:Attribute) ON (n.type_name)",
            "CREATE INDEX misp_object_uuid_idx IF NOT EXISTS FOR (n:Object) ON (n.uuid)",
            "CREATE INDEX misp_object_name_idx IF NOT EXISTS FOR (n:Object) ON (n.name)",
            "CREATE INDEX misp_galaxy_uuid_idx IF NOT EXISTS FOR (n:Galaxy) ON (n.uuid)",
            "CREATE INDEX misp_galaxy_name_idx IF NOT EXISTS FOR (n:Galaxy) ON (n.name)",
            "CREATE INDEX misp_tag_name_idx IF NOT EXISTS FOR (n:Tag) ON (n.name)",
        ]
        
        for index_query in indexes:
            try:
                self.execute_write(index_query)
                logger.info(f"✓ 인덱스 생성: {index_query.split('FOR')[0].strip()}")
            except Exception as e:
                logger.warning(f"⚠️  인덱스 생성 실패 (이미 존재할 수 있음): {e}")
    
    def create_constraints(self):
        """제약 조건 생성"""
        constraints = [
            # STIX 관련 제약 조건
            "CREATE CONSTRAINT stix_id_unique IF NOT EXISTS FOR (n:StixObject) REQUIRE n.id IS UNIQUE",
            
            # MISP 관련 제약 조건
            "CREATE CONSTRAINT misp_event_id_unique IF NOT EXISTS FOR (n:Event) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT misp_event_uuid_unique IF NOT EXISTS FOR (n:Event) REQUIRE n.uuid IS UNIQUE",
            "CREATE CONSTRAINT misp_attribute_uuid_unique IF NOT EXISTS FOR (n:Attribute) REQUIRE n.uuid IS UNIQUE",
            "CREATE CONSTRAINT misp_object_uuid_unique IF NOT EXISTS FOR (n:Object) REQUIRE n.uuid IS UNIQUE",
            "CREATE CONSTRAINT misp_galaxy_uuid_unique IF NOT EXISTS FOR (n:Galaxy) REQUIRE n.uuid IS UNIQUE",
        ]
        
        for constraint_query in constraints:
            try:
                self.execute_write(constraint_query)
                logger.info(f"✓ 제약 조건 생성: {constraint_query.split('FOR')[0].strip()}")
            except Exception as e:
                logger.warning(f"⚠️  제약 조건 생성 실패 (이미 존재할 수 있음): {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """데이터베이스 통계"""
        stats = {}
        
        # 노드 수
        result = self.execute_read("MATCH (n) RETURN count(n) as count")
        stats['nodes'] = result[0]['count'] if result else 0
        
        # 관계 수
        result = self.execute_read("MATCH ()-[r]->() RETURN count(r) as count")
        stats['relationships'] = result[0]['count'] if result else 0
        
        # 레이블별 노드 수
        result = self.execute_read("""
            MATCH (n)
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
        """)
        stats['by_label'] = {str(r['labels']): r['count'] for r in result}
        
        # 관계 타입별 수
        result = self.execute_read("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
        """)
        stats['by_relationship'] = {r['type']: r['count'] for r in result}
        
        return stats


@contextmanager
def get_connector(config: Neo4jConfig):
    """컨텍스트 매니저로 연결 관리"""
    connector = Neo4jConnector(config)
    try:
        connector.connect()
        yield connector
    finally:
        connector.close()



