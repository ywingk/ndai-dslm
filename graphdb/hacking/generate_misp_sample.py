"""
MISP 샘플 데이터 생성
-------------------
테스트용 MISP 이벤트 데이터를 생성하여 JSON 파일로 저장

⚙️ 사용법:
    python generate_misp_sample.py --output misp_sample.json
    python generate_misp_sample.py --output misp_sample.json --count 5
"""
import json
import argparse
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MISPSampleGenerator:
    """MISP 샘플 데이터 생성기"""
    
    def __init__(self):
        self.sample_events = []
        self.sample_tags = [
            {"name": "malware", "colour": "#ff0000"},
            {"name": "ransomware", "colour": "#ff6600"},
            {"name": "apt", "colour": "#0066ff"},
            {"name": "phishing", "colour": "#00ff00"},
            {"name": "ioc", "colour": "#ffff00"},
            {"name": "threat-actor", "colour": "#ff00ff"},
            {"name": "campaign", "colour": "#00ffff"},
            {"name": "vulnerability", "colour": "#ff6666"},
        ]
        
        self.attribute_types = [
            "md5", "sha1", "sha256", "filename", "ip-src", "ip-dst", 
            "domain", "url", "email-src", "email-dst", "regkey", 
            "mutex", "user-agent", "http-method", "uri", "port"
        ]
        
        self.object_templates = [
            "file", "ip-port", "domain-ip", "email", "url", "registry-key",
            "mutex", "network-connection", "process", "user-account"
        ]
    
    def generate_sample_event(self, event_id: int) -> Dict[str, Any]:
        """샘플 이벤트 생성"""
        base_time = datetime.now() - timedelta(days=event_id)
        
        event = {
            "id": str(event_id),
            "uuid": str(uuid.uuid4()),
            "info": f"Sample Security Event {event_id}",
            "date": base_time.strftime("%Y-%m-%d"),
            "timestamp": str(int(base_time.timestamp())),
            "published": event_id % 2 == 0,
            "threat_level_id": str((event_id % 4) + 1),
            "analysis": str(event_id % 3),
            "distribution": str(event_id % 4),
            "sharing_group_id": "",
            "org_id": "1",
            "orgc_id": "1",
            "publish_timestamp": str(int(base_time.timestamp()) + 3600) if event_id % 2 == 0 else "",
            "attribute_count": 0,
            "object_count": 0,
            "Attribute": [],
            "Object": [],
            "Galaxy": [],
            "Tag": []
        }
        
        # 태그 추가
        num_tags = (event_id % 3) + 1
        selected_tags = self.sample_tags[:num_tags]
        event["Tag"] = selected_tags
        
        # 속성 생성
        num_attributes = (event_id % 5) + 3
        for i in range(num_attributes):
            attr = self.generate_sample_attribute(event_id, i)
            event["Attribute"].append(attr)
        
        event["attribute_count"] = len(event["Attribute"])
        
        # 객체 생성 (50% 확률)
        if event_id % 2 == 0:
            num_objects = (event_id % 3) + 1
            for i in range(num_objects):
                obj = self.generate_sample_object(event_id, i)
                event["Object"].append(obj)
        
        event["object_count"] = len(event["Object"])
        
        # 갤럭시 생성 (30% 확률)
        if event_id % 3 == 0:
            galaxy = self.generate_sample_galaxy(event_id)
            event["Galaxy"].append(galaxy)
        
        return event
    
    def generate_sample_attribute(self, event_id: int, attr_index: int) -> Dict[str, Any]:
        """샘플 속성 생성"""
        attr_type = self.attribute_types[attr_index % len(self.attribute_types)]
        
        # 속성 타입에 따른 샘플 값 생성
        sample_values = {
            "md5": "5d41402abc4b2a76b9719d911017c592",
            "sha1": "356a192b7913b04c54574d18c28d46e6395428ab",
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "filename": f"malware_{event_id}_{attr_index}.exe",
            "ip-src": f"192.168.1.{100 + attr_index}",
            "ip-dst": f"10.0.0.{200 + attr_index}",
            "domain": f"malicious{event_id}{attr_index}.com",
            "url": f"http://malicious{event_id}{attr_index}.com/payload",
            "email-src": f"attacker{event_id}@evil.com",
            "email-dst": f"victim{attr_index}@company.com",
            "regkey": f"HKEY_CURRENT_USER\\Software\\Malware{event_id}",
            "mutex": f"Global\\MalwareMutex{event_id}{attr_index}",
            "user-agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Malware{event_id}",
            "http-method": "POST",
            "uri": f"/api/v1/exploit/{event_id}",
            "port": str(8080 + attr_index)
        }
        
        value = sample_values.get(attr_type, f"sample_value_{event_id}_{attr_index}")
        
        attribute = {
            "uuid": str(uuid.uuid4()),
            "event_id": str(event_id),
            "category": ["Payload delivery", "Artifacts dropped", "Network activity", "External analysis"][attr_index % 4],
            "type": attr_type,
            "value": value,
            "comment": f"Sample {attr_type} attribute for event {event_id}",
            "to_ids": attr_index % 2 == 0,
            "distribution": str(attr_index % 4),
            "sharing_group_id": "",
            "timestamp": str(int(datetime.now().timestamp())),
            "disable_correlation": False,
            "object_relation": "",
            "Tag": []
        }
        
        # 속성에 태그 추가 (30% 확률)
        if attr_index % 3 == 0:
            attribute["Tag"] = [self.sample_tags[attr_index % len(self.sample_tags)]]
        
        return attribute
    
    def generate_sample_object(self, event_id: int, obj_index: int) -> Dict[str, Any]:
        """샘플 객체 생성"""
        template_name = self.object_templates[obj_index % len(self.object_templates)]
        
        obj = {
            "uuid": str(uuid.uuid4()),
            "event_id": str(event_id),
            "name": template_name,
            "meta-category": ["file", "network", "email", "system"][obj_index % 4],
            "description": f"Sample {template_name} object for event {event_id}",
            "template_uuid": str(uuid.uuid4()),
            "template_version": "1",
            "timestamp": str(int(datetime.now().timestamp())),
            "distribution": str(obj_index % 4),
            "sharing_group_id": "",
            "Attribute": []
        }
        
        # 객체의 속성 생성
        num_obj_attrs = (obj_index % 3) + 2
        for i in range(num_obj_attrs):
            attr = self.generate_sample_attribute(event_id, i + 100)  # 다른 인덱스 사용
            attr["object_relation"] = f"relation_{i}"
            obj["Attribute"].append(attr)
        
        return obj
    
    def generate_sample_galaxy(self, event_id: int) -> Dict[str, Any]:
        """샘플 갤럭시 생성"""
        galaxy_types = ["mitre-attack-pattern", "mitre-malware", "mitre-tool", "mitre-intrusion-set"]
        galaxy_type = galaxy_types[event_id % len(galaxy_types)]
        
        galaxy = {
            "uuid": str(uuid.uuid4()),
            "event_id": str(event_id),
            "name": f"Sample {galaxy_type} Galaxy",
            "type": galaxy_type,
            "description": f"Sample galaxy for {galaxy_type}",
            "version": "1",
            "namespace": f"sample.{galaxy_type}",
            "kill_chain_order": "mitre-attack",
            "GalaxyCluster": [
                {
                    "uuid": str(uuid.uuid4()),
                    "value": f"Sample Cluster {event_id}",
                    "description": f"Sample cluster for event {event_id}",
                    "type": galaxy_type
                }
            ]
        }
        
        return galaxy
    
    def generate_events(self, count: int = 3) -> List[Dict[str, Any]]:
        """여러 샘플 이벤트 생성"""
        events = []
        for i in range(1, count + 1):
            event = self.generate_sample_event(i)
            events.append(event)
        
        return events


def main():
    parser = argparse.ArgumentParser(description="MISP 샘플 데이터 생성")
    parser.add_argument(
        "--output",
        default="misp_sample.json",
        help="출력 파일명 (기본값: misp_sample.json)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="생성할 이벤트 수 (기본값: 3)"
    )
    
    args = parser.parse_args()
    
    # 샘플 데이터 생성기
    generator = MISPSampleGenerator()
    
    # 이벤트 생성
    logger.info(f"🔹 {args.count}개 샘플 이벤트 생성 중...")
    events = generator.generate_events(args.count)
    
    # 파일 저장
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ 샘플 데이터 저장 완료: {args.output}")
    
    # 통계 출력
    total_attributes = sum(len(event.get('Attribute', [])) for event in events)
    total_objects = sum(len(event.get('Object', [])) for event in events)
    total_galaxies = sum(len(event.get('Galaxy', [])) for event in events)
    total_tags = sum(len(event.get('Tag', [])) for event in events)
    
    logger.info(f"\n📊 생성된 샘플 데이터 통계:")
    logger.info(f"  - 이벤트: {len(events)}개")
    logger.info(f"  - 속성: {total_attributes}개")
    logger.info(f"  - 객체: {total_objects}개")
    logger.info(f"  - 갤럭시: {total_galaxies}개")
    logger.info(f"  - 태그: {total_tags}개")
    
    logger.info(f"\n💾 사용법:")
    logger.info(f"  python misp_to_neo4j.py --input {args.output} --clear")


if __name__ == "__main__":
    main()
