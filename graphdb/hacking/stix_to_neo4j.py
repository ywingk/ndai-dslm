"""
STIX 2.x 데이터를 Neo4j로 임포트
----------------------------------
STIX Bundle을 UCO 온톨로지 형태로 Neo4j에 저장

⚙️ 사용법:
    python stix_to_neo4j.py --input enterprise-attack.json --clear
"""
import json
import argparse
from tqdm import tqdm
from typing import Dict, List, Any, Set
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig
from uco_mapping import UCOMapper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StixToNeo4jImporter:
    """STIX → Neo4j 임포터"""
    
    def __init__(self, connector):
        self.conn = connector
        self.mapper = UCOMapper()
        self.stix_objects = []
        self.stix_relationships = []
        
    def load_stix_bundle(self, file_path: str):
        """STIX Bundle 파일 로드"""
        logger.info(f"🔹 STIX Bundle 로드 중: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Bundle 또는 직접 객체 리스트
        if "objects" in data:
            objects = data["objects"]
        elif isinstance(data, list):
            objects = data
        else:
            objects = [data]
        
        # 객체와 관계 분리
        for obj in objects:
            if obj.get("type") == "relationship":
                self.stix_relationships.append(obj)
            else:
                self.stix_objects.append(obj)
        
        logger.info(f"  ✓ STIX 객체: {len(self.stix_objects):,}개")
        logger.info(f"  ✓ STIX 관계: {len(self.stix_relationships):,}개")
        
        # 타입별 통계
        type_counts = {}
        for obj in self.stix_objects:
            obj_type = obj.get("type", "unknown")
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
        
        logger.info("  📊 타입별 통계:")
        for obj_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            logger.info(f"    - {obj_type}: {count}개")
    
    def filter_objects(self, filter_type: str = None, keywords: List[str] = None) -> List[Dict]:
        """객체 필터링"""
        filtered = self.stix_objects
        
        # 타입 필터
        if filter_type:
            filtered = [obj for obj in filtered if obj.get("type") == filter_type]
            logger.info(f"🔹 타입 필터 적용: {filter_type} → {len(filtered):,}개")
        
        # 키워드 필터
        if keywords:
            keyword_str = "|".join(keywords)
            filtered = [
                obj for obj in filtered
                if any(
                    keyword.lower() in str(obj.get(field, "")).lower()
                    for keyword in keywords
                    for field in ["name", "description"]
                )
            ]
            logger.info(f"🔹 키워드 필터 적용: {keywords} → {len(filtered):,}개")
        
        return filtered
    
    def import_objects_batch(self, objects: List[Dict], batch_size: int = 500):
        """STIX 객체를 배치로 Neo4j에 임포트"""
        logger.info(f"🔹 STIX 객체 임포트 중... (총 {len(objects):,}개)")
        
        # 타입별로 그룹화
        by_type = {}
        for obj in objects:
            obj_type = obj.get("type", "unknown")
            if obj_type not in by_type:
                by_type[obj_type] = []
            by_type[obj_type].append(obj)
        
        # 각 타입별로 임포트
        for obj_type, type_objects in tqdm(by_type.items(), desc="타입별 임포트"):
            self._import_type_batch(obj_type, type_objects, batch_size)
    
    def _import_type_batch(self, obj_type: str, objects: List[Dict], batch_size: int):
        """특정 타입의 객체를 배치로 임포트"""
        node_data = []
        
        for obj in objects:
            labels = self.mapper.get_labels(obj_type)
            properties = self.mapper.extract_node_properties(obj)
            
            node_data.append({
                "labels": labels,
                "properties": properties
            })
        
        # 배치 임포트
        query = """
        UNWIND $nodes AS node
        CALL apoc.create.node(node.labels, node.properties) YIELD node as n
        RETURN count(n)
        """
        
        # APOC이 없는 경우를 위한 대체 쿼리
        fallback_query = """
        UNWIND $nodes AS node
        CREATE (n)
        SET n = node.properties
        WITH n, node.labels as labels
        CALL apoc.create.addLabels(n, labels) YIELD node as labeled
        RETURN count(labeled)
        """
        
        # 레이블별로 개별 쿼리 생성 (APOC 없이)
        for label_set in set(tuple(sorted(nd["labels"])) for nd in node_data):
            labels_str = ":".join(label_set)
            batch_for_labels = [nd for nd in node_data if tuple(sorted(nd["labels"])) == label_set]
            
            simple_query = f"""
            UNWIND $nodes AS node
            CREATE (n:{labels_str})
            SET n = node.properties
            """
            
            for i in range(0, len(batch_for_labels), batch_size):
                batch = batch_for_labels[i:i + batch_size]
                properties_only = [nd["properties"] for nd in batch]
                try:
                    self.conn.execute_write(simple_query, {"nodes": properties_only})
                except Exception as e:
                    logger.warning(f"배치 임포트 실패: {e}")
        
        logger.info(f"  ✓ {obj_type}: {len(objects)}개 임포트 완료")
    
    def import_relationships_batch(self, batch_size: int = 500):
        """STIX 관계를 배치로 Neo4j에 임포트"""
        logger.info(f"🔹 STIX 관계 임포트 중... (총 {len(self.stix_relationships):,}개)")
        
        # 관계 타입별로 그룹화
        by_rel_type = {}
        for rel in self.stix_relationships:
            rel_type = rel.get("relationship_type", "related-to")
            neo4j_rel_type = self.mapper.get_relationship_type(rel_type)
            
            if neo4j_rel_type not in by_rel_type:
                by_rel_type[neo4j_rel_type] = []
            
            properties = self.mapper.extract_relationship_properties(rel)
            by_rel_type[neo4j_rel_type].append({
                "source_id": rel.get("source_ref"),
                "target_id": rel.get("target_ref"),
                "properties": properties
            })
        
        logger.info(f"  ✓ {len(by_rel_type)}개의 관계 타입 발견")
        
        # 각 관계 타입별로 배치 임포트
        total_imported = 0
        for rel_type, relationships in tqdm(by_rel_type.items(), desc="관계 임포트"):
            query = f"""
            UNWIND $rels AS rel
            MATCH (source {{id: rel.source_id}})
            MATCH (target {{id: rel.target_id}})
            MERGE (source)-[r:{rel_type}]->(target)
            SET r = rel.properties
            """
            
            for i in range(0, len(relationships), batch_size):
                batch = relationships[i:i + batch_size]
                try:
                    self.conn.execute_write(query, {"rels": batch})
                except Exception as e:
                    logger.warning(f"관계 임포트 실패 ({rel_type}): {e}")
            
            total_imported += len(relationships)
            logger.info(f"    - {rel_type}: {len(relationships)}개")
        
        logger.info(f"  ✓ 총 {total_imported:,}개 관계 임포트 완료")
    
    def import_bundle(
        self,
        file_path: str,
        clear: bool = False,
        filter_type: str = None,
        keywords: List[str] = None
    ):
        """전체 임포트 프로세스"""
        if clear:
            logger.warning("⚠️  기존 데이터 삭제 중...")
            self.conn.clear_database()
        
        # STIX Bundle 로드
        self.load_stix_bundle(file_path)
        
        # 필터링
        objects_to_import = self.stix_objects
        if filter_type or keywords:
            objects_to_import = self.filter_objects(filter_type, keywords)
        
        # 인덱스 및 제약 조건 생성
        self.conn.create_indexes()
        self.conn.create_constraints()
        
        # 임포트
        self.import_objects_batch(objects_to_import)
        self.import_relationships_batch()
        
        # 통계 출력
        stats = self.conn.get_stats()
        logger.info("\n📊 임포트 완료 통계:")
        logger.info(f"  - 총 노드: {stats['nodes']:,}개")
        logger.info(f"  - 총 관계: {stats['relationships']:,}개")
        
        if stats.get('by_label'):
            logger.info("\n  📋 레이블별 노드 수:")
            for label, count in list(stats['by_label'].items())[:10]:
                logger.info(f"    - {label}: {count:,}개")
        
        if stats.get('by_relationship'):
            logger.info("\n  🔗 관계 타입별 수:")
            for rel_type, count in list(stats['by_relationship'].items())[:10]:
                logger.info(f"    - {rel_type}: {count:,}개")


def main():
    parser = argparse.ArgumentParser(description="STIX 2.x를 Neo4j로 임포트")
    parser.add_argument(
        "--input",
        required=True,
        help="STIX Bundle JSON 파일 경로"
    )
    parser.add_argument(
        "--filter-type",
        help="특정 STIX 타입만 임포트 (예: attack-pattern, malware)"
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        help="필터링할 키워드 (name, description 필드에서 검색)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="기존 데이터베이스 초기화"
    )
    parser.add_argument(
        "--uri",
        default="bolt://localhost:7688",
        help="Neo4j URI"
    )
    parser.add_argument(
        "--user",
        default="neo4j",
        help="Neo4j 사용자명"
    )
    parser.add_argument(
        "--password",
        default="hacking_slm_2025",
        help="Neo4j 비밀번호"
    )
    
    args = parser.parse_args()
    
    # Neo4j 연결
    config = Neo4jConfig(
        uri=args.uri,
        user=args.user,
        password=args.password
    )
    
    with get_connector(config) as conn:
        importer = StixToNeo4jImporter(conn)
        importer.import_bundle(
            file_path=args.input,
            clear=args.clear,
            filter_type=args.filter_type,
            keywords=args.keywords
        )


if __name__ == "__main__":
    main()

