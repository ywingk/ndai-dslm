"""
MISP 데이터를 Neo4j로 임포트
---------------------------
MISP 이벤트와 객체를 UCO 온톨로지 형태로 Neo4j에 저장

⚙️ 사용법:
    python misp_to_neo4j.py --input misp_events.json --clear
    python misp_to_neo4j.py --input misp_events.json --event-id 12345
    python misp_to_neo4j.py --input misp_events.json --tags malware,ransomware
"""
import json
import argparse
from tqdm import tqdm
from typing import Dict, List, Any, Set, Optional
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig
from uco_mapping import MISPToUCOMapper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MISPToNeo4jImporter:
    """MISP → Neo4j 임포터"""
    
    def __init__(self, connector):
        self.conn = connector
        self.mapper = MISPToUCOMapper()
        self.misp_events = []
        self.misp_objects = []
        self.misp_attributes = []
        self.misp_galaxies = []
        self.misp_tags = []
        
    def load_misp_data(self, file_path: str):
        """MISP 데이터 파일 로드"""
        logger.info(f"🔹 MISP 데이터 로드 중: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # MISP 이벤트 리스트 또는 단일 이벤트
        if isinstance(data, list):
            events = data
        elif isinstance(data, dict):
            if "Event" in data:
                events = [data["Event"]]
            elif "events" in data:
                events = data["events"]
            else:
                events = [data]
        else:
            events = []
        
        self.misp_events = events
        
        # 이벤트에서 객체와 속성 추출
        for event in events:
            self._extract_event_components(event)
        
        logger.info(f"  ✓ MISP 이벤트: {len(self.misp_events):,}개")
        logger.info(f"  ✓ MISP 객체: {len(self.misp_objects):,}개")
        logger.info(f"  ✓ MISP 속성: {len(self.misp_attributes):,}개")
        logger.info(f"  ✓ MISP 갤럭시: {len(self.misp_galaxies):,}개")
        logger.info(f"  ✓ MISP 태그: {len(self.misp_tags):,}개")
        
        # 이벤트별 통계
        if self.misp_events:
            logger.info("  📊 이벤트별 통계:")
            for i, event in enumerate(self.misp_events[:5]):  # 상위 5개만 표시
                event_id = event.get("id", f"event-{i}")
                event_info = event.get("info", "Unknown Event")
                attr_count = len(event.get("Attribute", []))
                obj_count = len(event.get("Object", []))
                logger.info(f"    - {event_id}: {event_info} (속성: {attr_count}개, 객체: {obj_count}개)")
    
    def _extract_event_components(self, event: Dict):
        """이벤트에서 구성 요소들 추출"""
        event_id = event.get("id", "unknown")
        
        # 속성 추출
        for attr in event.get("Attribute", []):
            attr["event_id"] = event_id
            self.misp_attributes.append(attr)
        
        # 객체 추출
        for obj in event.get("Object", []):
            obj["event_id"] = event_id
            self.misp_objects.append(obj)
        
        # 갤럭시 추출
        for galaxy in event.get("Galaxy", []):
            galaxy["event_id"] = event_id
            self.misp_galaxies.append(galaxy)
        
        # 태그 추출
        for tag in event.get("Tag", []):
            tag["event_id"] = event_id
            self.misp_tags.append(tag)
    
    def filter_events(self, event_id: str = None, tags: List[str] = None, 
                     threat_level: str = None, analysis_level: str = None) -> List[Dict]:
        """이벤트 필터링"""
        filtered = self.misp_events
        
        # 이벤트 ID 필터
        if event_id:
            filtered = [event for event in filtered if str(event.get("id")) == str(event_id)]
            logger.info(f"🔹 이벤트 ID 필터 적용: {event_id} → {len(filtered):,}개")
        
        # 태그 필터
        if tags:
            tag_filtered = []
            for event in filtered:
                event_tags = [tag.get("name", "") for tag in event.get("Tag", [])]
                if any(tag.lower() in " ".join(event_tags).lower() for tag in tags):
                    tag_filtered.append(event)
            filtered = tag_filtered
            logger.info(f"🔹 태그 필터 적용: {tags} → {len(filtered):,}개")
        
        # 위협 수준 필터
        if threat_level:
            filtered = [event for event in filtered if event.get("threat_level_id") == threat_level]
            logger.info(f"🔹 위협 수준 필터 적용: {threat_level} → {len(filtered):,}개")
        
        # 분석 수준 필터
        if analysis_level:
            filtered = [event for event in filtered if event.get("analysis") == analysis_level]
            logger.info(f"🔹 분석 수준 필터 적용: {analysis_level} → {len(filtered):,}개")
        
        return filtered
    
    def import_events_batch(self, events: List[Dict], batch_size: int = 100):
        """MISP 이벤트를 배치로 Neo4j에 임포트"""
        logger.info(f"🔹 MISP 이벤트 임포트 중... (총 {len(events):,}개)")
        
        for event in tqdm(events, desc="이벤트 임포트"):
            self._import_single_event(event)
        
        logger.info(f"  ✓ {len(events):,}개 이벤트 임포트 완료")
    
    def _import_single_event(self, event: Dict):
        """단일 이벤트 임포트"""
        event_id = event.get("id", "unknown")
        
        # 이벤트 노드 생성
        event_properties = self.mapper.extract_event_properties(event)
        event_query = """
        CREATE (e:Event:MISPObject)
        SET e += $props
        """
        
        try:
            self.conn.execute_write(event_query, {"props": event_properties})
        except Exception as e:
            logger.warning(f"이벤트 임포트 실패 ({event_id}): {e}")
            return
        
        # 이벤트의 속성들 임포트
        for attr in event.get("Attribute", []):
            self._import_attribute(attr, event_id)
        
        # 이벤트의 객체들 임포트
        for obj in event.get("Object", []):
            self._import_object(obj, event_id)
        
        # 이벤트의 갤럭시들 임포트
        for galaxy in event.get("Galaxy", []):
            self._import_galaxy(galaxy, event_id)
        
        # 이벤트의 태그들 임포트
        for tag in event.get("Tag", []):
            self._import_tag(tag, event_id)
    
    def _import_attribute(self, attr: Dict, event_id: str):
        """MISP 속성 임포트"""
        attr_properties = self.mapper.extract_attribute_properties(attr)
        attr_properties["event_id"] = event_id
        
        # 속성 타입에 따른 레이블 결정
        attr_type = attr.get("type", "unknown")
        category = attr.get("category", "other")
        
        # 레이블에서 공백과 특수문자 제거
        clean_attr_type = attr_type.title().replace("-", "").replace(" ", "")
        clean_category = category.title().replace("-", "").replace(" ", "")
        
        labels = ["Attribute", "MISPObject", clean_attr_type, clean_category]
        labels_str = ":".join(labels)
        
        attr_query = f"""
        MATCH (e:Event {{id: $event_id}})
        CREATE (a:{labels_str})
        SET a += $props
        CREATE (e)-[:HAS_ATTRIBUTE]->(a)
        """
        
        try:
            self.conn.execute_write(attr_query, {
                "event_id": event_id,
                "props": attr_properties
            })
        except Exception as e:
            logger.warning(f"속성 임포트 실패 ({attr.get('uuid', 'unknown')}): {e}")
    
    def _import_object(self, obj: Dict, event_id: str):
        """MISP 객체 임포트"""
        obj_properties = self.mapper.extract_object_properties(obj)
        obj_properties["event_id"] = event_id
        
        # 객체 타입에 따른 레이블 결정
        obj_name = obj.get("name", "unknown")
        obj_template = obj.get("template_uuid", "")
        
        # 레이블에서 공백과 특수문자 제거
        clean_obj_name = obj_name.title().replace("-", "").replace(" ", "").replace(":", "")
        
        labels = ["Object", "MISPObject", clean_obj_name]
        labels_str = ":".join(labels)
        
        obj_query = f"""
        MATCH (e:Event {{id: $event_id}})
        CREATE (o:{labels_str})
        SET o += $props
        CREATE (e)-[:HAS_OBJECT]->(o)
        """
        
        try:
            self.conn.execute_write(obj_query, {
                "event_id": event_id,
                "props": obj_properties
            })
            
            # 객체의 속성들 임포트
            for attr in obj.get("Attribute", []):
                self._import_object_attribute(attr, event_id, obj.get("uuid"))
                
        except Exception as e:
            logger.warning(f"객체 임포트 실패 ({obj.get('uuid', 'unknown')}): {e}")
    
    def _import_object_attribute(self, attr: Dict, event_id: str, object_uuid: str):
        """객체 내 속성 임포트"""
        attr_properties = self.mapper.extract_attribute_properties(attr)
        attr_properties["event_id"] = event_id
        attr_properties["object_uuid"] = object_uuid
        
        attr_type = attr.get("type", "unknown")
        category = attr.get("category", "other")
        
        # 레이블에서 공백과 특수문자 제거
        clean_attr_type = attr_type.title().replace("-", "").replace(" ", "")
        clean_category = category.title().replace("-", "").replace(" ", "")
        
        labels = ["Attribute", "MISPObject", "ObjectAttribute", clean_attr_type, clean_category]
        labels_str = ":".join(labels)
        
        attr_query = f"""
        MATCH (o:Object {{uuid: $object_uuid}})
        CREATE (a:{labels_str})
        SET a += $props
        CREATE (o)-[:HAS_ATTRIBUTE]->(a)
        """
        
        try:
            self.conn.execute_write(attr_query, {
                "object_uuid": object_uuid,
                "props": attr_properties
            })
        except Exception as e:
            logger.warning(f"객체 속성 임포트 실패 ({attr.get('uuid', 'unknown')}): {e}")
    
    def _import_galaxy(self, galaxy: Dict, event_id: str):
        """MISP 갤럭시 임포트"""
        galaxy_properties = self.mapper.extract_galaxy_properties(galaxy)
        galaxy_properties["event_id"] = event_id
        
        galaxy_name = galaxy.get("name", "unknown")
        galaxy_type = galaxy.get("type", "unknown")
        
        # 레이블에서 공백과 특수문자 제거
        clean_galaxy_name = galaxy_name.title().replace("-", "").replace(" ", "").replace(":", "")
        clean_galaxy_type = galaxy_type.title().replace("-", "").replace(" ", "").replace(":", "")
        
        labels = ["Galaxy", "MISPObject", clean_galaxy_name, clean_galaxy_type]
        labels_str = ":".join(labels)
        
        galaxy_query = f"""
        MATCH (e:Event {{id: $event_id}})
        CREATE (g:{labels_str})
        SET g += $props
        CREATE (e)-[:HAS_GALAXY]->(g)
        """
        
        try:
            self.conn.execute_write(galaxy_query, {
                "event_id": event_id,
                "props": galaxy_properties
            })
        except Exception as e:
            logger.warning(f"갤럭시 임포트 실패 ({galaxy.get('uuid', 'unknown')}): {e}")
    
    def _import_tag(self, tag: Dict, event_id: str):
        """MISP 태그 임포트"""
        tag_properties = self.mapper.extract_tag_properties(tag)
        tag_properties["event_id"] = event_id
        
        tag_name = tag.get("name", "unknown")
        tag_colour = tag.get("colour", "#000000")
        
        labels = ["Tag", "MISPObject"]
        labels_str = ":".join(labels)
        
        tag_query = f"""
        MATCH (e:Event {{id: $event_id}})
        MERGE (t:{labels_str} {{name: $tag_name}})
        SET t += $props
        MERGE (e)-[:HAS_TAG]->(t)
        """
        
        try:
            self.conn.execute_write(tag_query, {
                "event_id": event_id,
                "tag_name": tag_name,
                "props": tag_properties
            })
        except Exception as e:
            logger.warning(f"태그 임포트 실패 ({tag_name}): {e}")
    
    def import_bundle(
        self,
        file_path: str,
        clear: bool = False,
        event_id: str = None,
        tags: List[str] = None,
        threat_level: str = None,
        analysis_level: str = None
    ):
        """전체 임포트 프로세스"""
        if clear:
            logger.warning("⚠️  기존 데이터 삭제 중...")
            self.conn.clear_database()
        
        # MISP 데이터 로드
        self.load_misp_data(file_path)
        
        # 필터링
        events_to_import = self.misp_events
        if event_id or tags or threat_level or analysis_level:
            events_to_import = self.filter_events(event_id, tags, threat_level, analysis_level)
        
        # 인덱스 및 제약 조건 생성
        self.conn.create_indexes()
        self.conn.create_constraints()
        
        # 임포트
        self.import_events_batch(events_to_import)
        
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
    parser = argparse.ArgumentParser(description="MISP 데이터를 Neo4j로 임포트")
    parser.add_argument(
        "--input",
        required=True,
        help="MISP 이벤트 JSON 파일 경로"
    )
    parser.add_argument(
        "--event-id",
        help="특정 이벤트 ID만 임포트"
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        help="특정 태그가 포함된 이벤트만 임포트"
    )
    parser.add_argument(
        "--threat-level",
        help="위협 수준 필터 (1-4)"
    )
    parser.add_argument(
        "--analysis-level",
        help="분석 수준 필터 (0-2)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="기존 데이터베이스 초기화"
    )
    parser.add_argument(
        "--uri",
        default="bolt://localhost:7687",
        help="Neo4j URI"
    )
    parser.add_argument(
        "--user",
        default="neo4j",
        help="Neo4j 사용자명"
    )
    parser.add_argument(
        "--password",
        default="domain_slm_2025",
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
        importer = MISPToNeo4jImporter(conn)
        importer.import_bundle(
            file_path=args.input,
            clear=args.clear,
            event_id=args.event_id,
            tags=args.tags,
            threat_level=args.threat_level,
            analysis_level=args.analysis_level
        )


if __name__ == "__main__":
    main()
