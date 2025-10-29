"""
STIX/MISP → UCO (Unified Cyber Ontology) 매핑
"""
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class UCOMapper:
    """STIX 객체를 UCO 온톨로지로 매핑"""
    
    # STIX 타입 → Neo4j 레이블 매핑
    STIX_TO_LABELS = {
        "attack-pattern": ["StixObject", "Action", "AttackPattern"],
        "campaign": ["StixObject", "Action", "Campaign"],
        "course-of-action": ["StixObject", "Mitigation", "CourseOfAction"],
        "identity": ["StixObject", "Identity"],
        "indicator": ["StixObject", "Observable", "Indicator"],
        "intrusion-set": ["StixObject", "Identity", "IntrusionSet"],
        "malware": ["StixObject", "Action", "Malware"],
        "observed-data": ["StixObject", "Observable"],
        "report": ["StixObject", "Report"],
        "threat-actor": ["StixObject", "Identity", "ThreatActor"],
        "tool": ["StixObject", "Action", "Tool"],
        "vulnerability": ["StixObject", "Observable", "Vulnerability"],
    }
    
    # STIX 관계 타입 → Neo4j 관계 타입 매핑
    RELATIONSHIP_MAPPING = {
        "uses": "USES",
        "indicates": "INDICATES",
        "mitigates": "MITIGATES",
        "targets": "TARGETS",
        "attributed-to": "ATTRIBUTED_TO",
        "related-to": "RELATED_TO",
        "variant-of": "VARIANT_OF",
        "impersonates": "IMPERSONATES",
        "derived-from": "DERIVED_FROM",
        "duplicate-of": "DUPLICATE_OF",
        "based-on": "BASED_ON",
        "exploits": "EXPLOITS",
        "delivers": "DELIVERS",
        "compromises": "COMPROMISES",
        "hosts": "HOSTS",
        "owns": "OWNS",
        "authored-by": "AUTHORED_BY",
        "beacons-to": "BEACONS_TO",
        "exfiltrates-to": "EXFILTRATES_TO",
        "downloads": "DOWNLOADS",
        "drops": "DROPS",
        "communicates-with": "COMMUNICATES_WITH",
    }
    
    def get_labels(self, stix_type: str) -> List[str]:
        """STIX 타입에 대한 Neo4j 레이블 반환"""
        return self.STIX_TO_LABELS.get(stix_type, ["StixObject", "Unknown"])
    
    def get_relationship_type(self, stix_rel_type: str) -> str:
        """STIX 관계 타입을 Neo4j 관계 타입으로 변환"""
        return self.RELATIONSHIP_MAPPING.get(stix_rel_type, stix_rel_type.upper().replace("-", "_"))
    
    def extract_node_properties(self, stix_obj: Dict[str, Any]) -> Dict[str, Any]:
        """STIX 객체에서 노드 속성 추출"""
        properties = {
            "id": stix_obj.get("id"),
            "type": stix_obj.get("type"),
            "created": stix_obj.get("created"),
            "modified": stix_obj.get("modified"),
        }
        
        # 공통 속성
        if "name" in stix_obj:
            properties["name"] = stix_obj["name"]
        
        if "description" in stix_obj:
            properties["description"] = stix_obj["description"]
        
        # 타입별 특수 속성
        obj_type = stix_obj.get("type")
        
        if obj_type == "attack-pattern":
            properties.update(self._extract_attack_pattern_props(stix_obj))
        elif obj_type == "malware":
            properties.update(self._extract_malware_props(stix_obj))
        elif obj_type == "threat-actor":
            properties.update(self._extract_threat_actor_props(stix_obj))
        elif obj_type == "vulnerability":
            properties.update(self._extract_vulnerability_props(stix_obj))
        elif obj_type == "indicator":
            properties.update(self._extract_indicator_props(stix_obj))
        elif obj_type == "tool":
            properties.update(self._extract_tool_props(stix_obj))
        elif obj_type == "course-of-action":
            properties.update(self._extract_mitigation_props(stix_obj))
        
        # None 값 제거
        return {k: v for k, v in properties.items() if v is not None}
    
    def _extract_attack_pattern_props(self, obj: Dict) -> Dict:
        """AttackPattern 특화 속성"""
        props = {}
        
        # MITRE ATT&CK 관련
        if "external_references" in obj:
            for ref in obj["external_references"]:
                if ref.get("source_name") == "mitre-attack":
                    props["mitre_id"] = ref.get("external_id")
                    props["mitre_url"] = ref.get("url")
                    break
        
        # Kill Chain Phases
        if "kill_chain_phases" in obj:
            props["kill_chain_phases"] = [
                f"{phase['kill_chain_name']}:{phase['phase_name']}"
                for phase in obj["kill_chain_phases"]
            ]
        
        return props
    
    def _extract_malware_props(self, obj: Dict) -> Dict:
        """Malware 특화 속성"""
        props = {}
        
        if "is_family" in obj:
            props["is_family"] = obj["is_family"]
        
        if "malware_types" in obj:
            props["malware_types"] = obj["malware_types"]
        
        if "aliases" in obj:
            props["aliases"] = obj["aliases"]
        
        return props
    
    def _extract_threat_actor_props(self, obj: Dict) -> Dict:
        """ThreatActor 특화 속성"""
        props = {}
        
        if "aliases" in obj:
            props["aliases"] = obj["aliases"]
        
        if "threat_actor_types" in obj:
            props["threat_actor_types"] = obj["threat_actor_types"]
        
        if "sophistication" in obj:
            props["sophistication"] = obj["sophistication"]
        
        if "resource_level" in obj:
            props["resource_level"] = obj["resource_level"]
        
        if "primary_motivation" in obj:
            props["primary_motivation"] = obj["primary_motivation"]
        
        return props
    
    def _extract_vulnerability_props(self, obj: Dict) -> Dict:
        """Vulnerability 특화 속성"""
        props = {}
        
        # CVE 추출
        if "external_references" in obj:
            for ref in obj["external_references"]:
                if ref.get("source_name") == "cve":
                    props["cve_id"] = ref.get("external_id")
                    break
        
        return props
    
    def _extract_indicator_props(self, obj: Dict) -> Dict:
        """Indicator 특화 속성"""
        props = {}
        
        if "pattern" in obj:
            props["pattern"] = obj["pattern"]
        
        if "pattern_type" in obj:
            props["pattern_type"] = obj["pattern_type"]
        
        if "valid_from" in obj:
            props["valid_from"] = obj["valid_from"]
        
        if "valid_until" in obj:
            props["valid_until"] = obj["valid_until"]
        
        if "indicator_types" in obj:
            props["indicator_types"] = obj["indicator_types"]
        
        return props
    
    def _extract_tool_props(self, obj: Dict) -> Dict:
        """Tool 특화 속성"""
        props = {}
        
        if "tool_types" in obj:
            props["tool_types"] = obj["tool_types"]
        
        if "aliases" in obj:
            props["aliases"] = obj["aliases"]
        
        return props
    
    def _extract_mitigation_props(self, obj: Dict) -> Dict:
        """CourseOfAction 특화 속성"""
        props = {}
        
        # MITRE ATT&CK Mitigation ID
        if "external_references" in obj:
            for ref in obj["external_references"]:
                if ref.get("source_name") == "mitre-attack":
                    props["mitre_id"] = ref.get("external_id")
                    break
        
        return props
    
    def extract_relationship_properties(self, stix_rel: Dict[str, Any]) -> Dict[str, Any]:
        """STIX 관계에서 속성 추출"""
        properties = {
            "id": stix_rel.get("id"),
            "relationship_type": stix_rel.get("relationship_type"),
            "created": stix_rel.get("created"),
            "modified": stix_rel.get("modified"),
        }
        
        if "description" in stix_rel:
            properties["description"] = stix_rel["description"]
        
        # None 값 제거
        return {k: v for k, v in properties.items() if v is not None}


class MISPToUCOMapper:
    """MISP 객체를 UCO 온톨로지로 매핑"""
    
    def extract_node_properties(self, misp_obj: Dict[str, Any]) -> Dict[str, Any]:
        """MISP 객체에서 노드 속성 추출"""
        properties = {
            "id": f"misp-{misp_obj.get('uuid')}",
            "type": "misp-" + misp_obj.get("type", "unknown"),
            "created": misp_obj.get("timestamp"),
        }
        
        if "value" in misp_obj:
            properties["value"] = misp_obj["value"]
        
        if "category" in misp_obj:
            properties["category"] = misp_obj["category"]
        
        if "comment" in misp_obj:
            properties["description"] = misp_obj["comment"]
        
        return {k: v for k, v in properties.items() if v is not None}

