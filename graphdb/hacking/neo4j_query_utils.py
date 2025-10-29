"""
Neo4j 쿼리 유틸리티 - Hacking Domain
"""
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class Neo4jQueryUtils:
    """Hacking 도메인 특화 Neo4j 쿼리 유틸리티"""
    
    def __init__(self, connector):
        self.conn = connector
    
    # ============================================
    # 1. 기본 검색
    # ============================================
    
    def get_attack_pattern_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 공격 패턴 검색"""
        query = """
        MATCH (a:AttackPattern)
        WHERE toLower(a.name) CONTAINS toLower($name)
        RETURN a.id as id, a.name as name, a.description as description,
               a.mitre_id as mitre_id, a.kill_chain_phases as kill_chain_phases
        LIMIT 1
        """
        result = self.conn.execute_read(query, {"name": name})
        return result[0] if result else None
    
    def get_attack_pattern_by_mitre_id(self, mitre_id: str) -> Optional[Dict]:
        """MITRE ATT&CK ID로 검색"""
        query = """
        MATCH (a:AttackPattern {mitre_id: $mitre_id})
        RETURN a.id as id, a.name as name, a.description as description,
               a.mitre_id as mitre_id, a.kill_chain_phases as kill_chain_phases
        """
        result = self.conn.execute_read(query, {"mitre_id": mitre_id})
        return result[0] if result else None
    
    def get_malware_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 악성코드 검색"""
        query = """
        MATCH (m:Malware)
        WHERE toLower(m.name) CONTAINS toLower($name)
        RETURN m.id as id, m.name as name, m.description as description,
               m.malware_types as malware_types, m.aliases as aliases
        LIMIT 1
        """
        result = self.conn.execute_read(query, {"name": name})
        return result[0] if result else None
    
    def get_threat_actor_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 위협 주체 검색"""
        query = """
        MATCH (t:ThreatActor)
        WHERE toLower(t.name) CONTAINS toLower($name)
        RETURN t.id as id, t.name as name, t.description as description,
               t.threat_actor_types as threat_actor_types,
               t.aliases as aliases, t.sophistication as sophistication
        LIMIT 1
        """
        result = self.conn.execute_read(query, {"name": name})
        return result[0] if result else None
    
    def get_vulnerability_by_cve(self, cve_id: str) -> Optional[Dict]:
        """CVE ID로 취약점 검색"""
        query = """
        MATCH (v:Vulnerability {cve_id: $cve_id})
        RETURN v.id as id, v.name as name, v.description as description,
               v.cve_id as cve_id
        """
        result = self.conn.execute_read(query, {"cve_id": cve_id})
        return result[0] if result else None
    
    def get_tool_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 도구 검색"""
        query = """
        MATCH (t:Tool)
        WHERE toLower(t.name) CONTAINS toLower($name)
        RETURN t.id as id, t.name as name, t.description as description,
               t.tool_types as tool_types, t.aliases as aliases
        LIMIT 1
        """
        result = self.conn.execute_read(query, {"name": name})
        return result[0] if result else None
    
    # ============================================
    # 2. 관계 분석
    # ============================================
    
    def get_direct_relationships(self, stix_id: str) -> List[Dict]:
        """특정 객체의 직접 관계 조회"""
        query = """
        MATCH (source {id: $id})-[r]->(target)
        RETURN type(r) as relation,
               target.id as target_id,
               target.name as target_name,
               labels(target) as target_labels,
               r.description as rel_description
        """
        return self.conn.execute_read(query, {"id": stix_id})
    
    def get_related_malware(self, attack_pattern_id: str) -> List[Dict]:
        """공격 패턴과 관련된 악성코드"""
        query = """
        MATCH (a:AttackPattern {id: $id})<-[:USES]-(m:Malware)
        RETURN m.id as id, m.name as name, m.description as description,
               m.malware_types as malware_types
        """
        return self.conn.execute_read(query, {"id": attack_pattern_id})
    
    def get_related_tools(self, attack_pattern_id: str) -> List[Dict]:
        """공격 패턴과 관련된 도구"""
        query = """
        MATCH (a:AttackPattern {id: $id})<-[:USES]-(t:Tool)
        RETURN t.id as id, t.name as name, t.description as description,
               t.tool_types as tool_types
        """
        return self.conn.execute_read(query, {"id": attack_pattern_id})
    
    def get_threat_actors_using_attack(self, attack_pattern_id: str) -> List[Dict]:
        """특정 공격 기법을 사용하는 위협 주체"""
        query = """
        MATCH (ta:ThreatActor)-[:USES]->(a:AttackPattern {id: $id})
        RETURN ta.id as id, ta.name as name, ta.description as description,
               ta.threat_actor_types as threat_actor_types
        """
        return self.conn.execute_read(query, {"id": attack_pattern_id})
    
    def get_mitigations(self, attack_pattern_id: str) -> List[Dict]:
        """공격 패턴에 대한 대응 방안"""
        query = """
        MATCH (coa:CourseOfAction)-[:MITIGATES]->(a:AttackPattern {id: $id})
        RETURN coa.id as id, coa.name as name, coa.description as description
        """
        return self.conn.execute_read(query, {"id": attack_pattern_id})
    
    def get_vulnerabilities_for_attack(self, attack_pattern_id: str) -> List[Dict]:
        """공격 패턴과 연결된 취약점"""
        query = """
        MATCH (a:AttackPattern {id: $id})-[:TARGETS|EXPLOITS*1..2]-(v:Vulnerability)
        RETURN DISTINCT v.id as id, v.name as name, v.cve_id as cve_id,
               v.description as description
        """
        return self.conn.execute_read(query, {"id": attack_pattern_id})
    
    # ============================================
    # 3. Multi-hop 분석 (공격 체인)
    # ============================================
    
    def get_attack_chains(
        self,
        start_id: str,
        max_hops: int = 3,
        limit: int = 10
    ) -> List[Dict]:
        """공격 체인/킬체인 분석"""
        query = f"""
        MATCH path = (start {{id: $start_id}})-[*1..{max_hops}]->(end)
        WHERE start <> end
        WITH path, length(path) as hops
        ORDER BY hops DESC
        LIMIT {limit}
        RETURN 
            [node in nodes(path) | node.name] as steps,
            [node in nodes(path) | labels(node)] as node_types,
            [rel in relationships(path) | type(rel)] as relations,
            hops
        """
        return self.conn.execute_read(query, {"start_id": start_id})
    
    def find_attack_path(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 5
    ) -> Optional[Dict]:
        """두 객체 간 공격 경로 찾기"""
        query = f"""
        MATCH path = shortestPath(
            (source {{id: $source_id}})-[*1..{max_hops}]-(target {{id: $target_id}})
        )
        RETURN 
            [node in nodes(path) | node.name] as steps,
            [node in nodes(path) | labels(node)] as node_types,
            [rel in relationships(path) | type(rel)] as relations,
            length(path) as hops
        """
        result = self.conn.execute_read(query, {
            "source_id": source_id,
            "target_id": target_id
        })
        return result[0] if result else None
    
    def find_common_ttps(self, threat_actor_ids: List[str]) -> List[Dict]:
        """여러 위협 주체의 공통 TTP (Tactics, Techniques, Procedures)"""
        query = """
        UNWIND $actor_ids as actor_id
        MATCH (ta:ThreatActor {id: actor_id})-[:USES]->(ap:AttackPattern)
        WITH ap, count(DISTINCT ta) as actor_count
        WHERE actor_count >= 2
        RETURN ap.id as id, ap.name as name, ap.mitre_id as mitre_id,
               actor_count,
               ap.kill_chain_phases as kill_chain_phases
        ORDER BY actor_count DESC
        """
        return self.conn.execute_read(query, {"actor_ids": threat_actor_ids})
    
    def get_campaign_analysis(self, campaign_id: str) -> Dict:
        """캠페인 분석 (사용된 모든 TTP, 악성코드, 도구)"""
        # 공격 패턴
        attack_patterns = self.conn.execute_read("""
            MATCH (c:Campaign {id: $id})-[:USES]->(ap:AttackPattern)
            RETURN ap.name as name, ap.mitre_id as mitre_id
        """, {"id": campaign_id})
        
        # 악성코드
        malware = self.conn.execute_read("""
            MATCH (c:Campaign {id: $id})-[:USES]->(m:Malware)
            RETURN m.name as name, m.malware_types as types
        """, {"id": campaign_id})
        
        # 도구
        tools = self.conn.execute_read("""
            MATCH (c:Campaign {id: $id})-[:USES]->(t:Tool)
            RETURN t.name as name, t.tool_types as types
        """, {"id": campaign_id})
        
        # 표적
        targets = self.conn.execute_read("""
            MATCH (c:Campaign {id: $id})-[:TARGETS]->(i:Identity)
            RETURN i.name as name, i.description as description
        """, {"id": campaign_id})
        
        return {
            "attack_patterns": attack_patterns,
            "malware": malware,
            "tools": tools,
            "targets": targets
        }
    
    # ============================================
    # 4. 그래프 분석
    # ============================================
    
    def get_most_used_attack_patterns(self, limit: int = 20) -> List[Dict]:
        """가장 많이 사용되는 공격 패턴"""
        query = f"""
        MATCH (ap:AttackPattern)<-[:USES]-()
        WITH ap, count(*) as usage_count
        ORDER BY usage_count DESC
        LIMIT {limit}
        RETURN ap.id as id, ap.name as name, ap.mitre_id as mitre_id,
               usage_count
        """
        return self.conn.execute_read(query)
    
    def get_most_dangerous_threat_actors(self, limit: int = 20) -> List[Dict]:
        """가장 위험한 위협 주체 (많은 TTP 사용)"""
        query = f"""
        MATCH (ta:ThreatActor)-[:USES]->()
        WITH ta, count(*) as ttp_count
        ORDER BY ttp_count DESC
        LIMIT {limit}
        RETURN ta.id as id, ta.name as name,
               ta.threat_actor_types as types,
               ta.sophistication as sophistication,
               ttp_count
        """
        return self.conn.execute_read(query)
    
    def get_attack_patterns_by_tactic(self, tactic: str) -> List[Dict]:
        """특정 Tactic에 속하는 공격 기법들"""
        query = """
        MATCH (ap:AttackPattern)
        WHERE any(phase in ap.kill_chain_phases WHERE toLower(phase) CONTAINS toLower($tactic))
        RETURN ap.id as id, ap.name as name, ap.mitre_id as mitre_id,
               ap.kill_chain_phases as kill_chain_phases,
               ap.description as description
        """
        return self.conn.execute_read(query, {"tactic": tactic})
    
    def get_relationship_distribution(self) -> List[Dict]:
        """관계 타입별 분포"""
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as relationship_type, count(r) as count
        ORDER BY count DESC
        """
        return self.conn.execute_read(query)
    
    # ============================================
    # 5. QA 생성용 쿼리
    # ============================================
    
    def get_qa_attack_chains(self, min_hops: int = 2, max_hops: int = 4, limit: int = 100) -> List[Dict]:
        """QA 생성용 공격 체인"""
        query = f"""
        MATCH path = (start:AttackPattern)-[*{min_hops}..{max_hops}]->(end)
        WHERE start <> end
        WITH path, nodes(path) as path_nodes, length(path) as hops
        WHERE all(node in path_nodes WHERE node.name IS NOT NULL)
        RETURN 
            [node in path_nodes | {{
                name: node.name,
                type: labels(node)[0],
                description: node.description
            }}] as nodes,
            [rel in relationships(path) | type(rel)] as relations,
            hops
        ORDER BY rand()
        LIMIT {limit}
        """
        return self.conn.execute_read(query)
    
    def get_qa_malware_analysis(self, limit: int = 100) -> List[Dict]:
        """QA 생성용 악성코드 분석 데이터"""
        query = f"""
        MATCH (m:Malware)-[r1:USES]->(ap:AttackPattern)
        OPTIONAL MATCH (m)-[r2:TARGETS]->(target)
        OPTIONAL MATCH (ta:ThreatActor)-[:USES]->(m)
        WITH m, ap,
             collect(DISTINCT target.name) as targets,
             collect(DISTINCT ta.name) as threat_actors
        RETURN 
            m.name as malware_name,
            m.description as malware_description,
            m.malware_types as malware_types,
            collect(DISTINCT ap.name) as attack_patterns,
            targets,
            threat_actors
        LIMIT {limit}
        """
        return self.conn.execute_read(query)
    
    def get_qa_threat_intelligence(self, limit: int = 100) -> List[Dict]:
        """QA 생성용 위협 인텔리전스 데이터"""
        query = f"""
        MATCH (ta:ThreatActor)-[:USES]->(m:Malware)
        MATCH (m)-[:USES]->(ap:AttackPattern)
        OPTIONAL MATCH (coa:CourseOfAction)-[:MITIGATES]->(ap)
        WITH ta, m, ap,
             collect(DISTINCT coa.name) as mitigations
        RETURN 
            ta.name as threat_actor,
            ta.description as actor_description,
            m.name as malware,
            ap.name as attack_pattern,
            ap.mitre_id as mitre_id,
            mitigations
        ORDER BY rand()
        LIMIT {limit}
        """
        return self.conn.execute_read(query)
    
    def get_comparison_data(self, entity_type: str, limit: int = 50) -> List[Dict]:
        """비교 QA용 유사 엔티티 쌍"""
        label_map = {
            "malware": "Malware",
            "threat-actor": "ThreatActor",
            "attack-pattern": "AttackPattern",
            "tool": "Tool"
        }
        
        label = label_map.get(entity_type, "StixObject")
        
        query = f"""
        MATCH (e1:{label})-[r1]->(common)<-[r2]-(e2:{label})
        WHERE e1.id < e2.id
        WITH e1, e2, count(DISTINCT common) as common_count
        WHERE common_count >= 2
        RETURN 
            e1.name as entity1_name,
            e1.description as entity1_description,
            e2.name as entity2_name,
            e2.description as entity2_description,
            common_count
        ORDER BY common_count DESC
        LIMIT {limit}
        """
        return self.conn.execute_read(query)

