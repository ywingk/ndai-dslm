"""
Neo4j 그래프로부터 Hacking Domain QA 데이터셋 생성
"""
import json
import argparse
from typing import List, Dict, Any
from datetime import datetime
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig
from neo4j_query_utils import Neo4jQueryUtils
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HackingQAGenerator:
    """Hacking 도메인 QA 생성기"""
    
    def __init__(self, connector):
        self.conn = connector
        self.utils = Neo4jQueryUtils(connector)
        self.qa_samples = []
    
    def generate_all(
        self,
        num_easy: int = 300,
        num_medium: int = 400,
        num_hard: int = 300
    ):
        """모든 난이도의 QA 생성"""
        logger.info("🔹 QA 데이터셋 생성 시작...")
        
        if num_easy > 0:
            logger.info(f"  - Easy 난이도: {num_easy}개")
            self.generate_easy_qa(num_easy)
        
        if num_medium > 0:
            logger.info(f"  - Medium 난이도: {num_medium}개")
            self.generate_medium_qa(num_medium)
        
        if num_hard > 0:
            logger.info(f"  - Hard 난이도: {num_hard}개")
            self.generate_hard_qa(num_hard)
        
        logger.info(f"\n✓ 총 {len(self.qa_samples)}개 QA 샘플 생성 완료")
    
    def generate_easy_qa(self, num_samples: int):
        """Easy: 단일 hop 쿼리"""
        templates = [
            self._template_attack_pattern_description,
            self._template_malware_type,
            self._template_threat_actor_motivation,
            self._template_vulnerability_cve,
            self._template_tool_usage,
            self._template_mitigation_for_attack,
        ]
        
        samples_per_template = num_samples // len(templates)
        
        for template_func in templates:
            try:
                samples = template_func(samples_per_template)
                self.qa_samples.extend(samples)
            except Exception as e:
                logger.warning(f"템플릿 실패: {template_func.__name__} - {e}")
    
    def generate_medium_qa(self, num_samples: int):
        """Medium: 2-3 hop 쿼리"""
        templates = [
            self._template_malware_attack_chain,
            self._template_threat_actor_ttps,
            self._template_campaign_analysis,
            self._template_attack_pattern_relationships,
            self._template_vulnerability_exploitation,
        ]
        
        samples_per_template = num_samples // len(templates)
        
        for template_func in templates:
            try:
                samples = template_func(samples_per_template)
                self.qa_samples.extend(samples)
            except Exception as e:
                logger.warning(f"템플릿 실패: {template_func.__name__} - {e}")
    
    def generate_hard_qa(self, num_samples: int):
        """Hard: 4+ hop 복잡한 추론"""
        templates = [
            self._template_complex_attack_chain,
            self._template_comparative_analysis,
            self._template_threat_intelligence_synthesis,
            self._template_defensive_strategy,
        ]
        
        samples_per_template = num_samples // len(templates)
        
        for template_func in templates:
            try:
                samples = template_func(samples_per_template)
                self.qa_samples.extend(samples)
            except Exception as e:
                logger.warning(f"템플릿 실패: {template_func.__name__} - {e}")
    
    # ========================================
    # Easy Templates (1-hop)
    # ========================================
    
    def _template_attack_pattern_description(self, num: int) -> List[Dict]:
        """공격 패턴 설명"""
        patterns = self.utils.get_most_used_attack_patterns(limit=num * 2)
        samples = []
        
        for pattern in patterns[:num]:
            if not pattern.get('name'):
                continue
            
            # 상세 정보 가져오기
            detail = self.utils.get_attack_pattern_by_name(pattern['name'])
            if not detail or not detail.get('description'):
                continue
            
            samples.append({
                "question": f"{pattern['name']} 공격 기법은 무엇인가?",
                "answer": detail['description'],
                "difficulty": "easy",
                "type": "attack_pattern_description",
                "metadata": {
                    "mitre_id": pattern.get('mitre_id'),
                    "entity_id": pattern['id']
                }
            })
        
        return samples
    
    def _template_malware_type(self, num: int) -> List[Dict]:
        """악성코드 타입"""
        query = """
        MATCH (m:Malware)
        WHERE m.malware_types IS NOT NULL AND size(m.malware_types) > 0
        RETURN m.id as id, m.name as name, m.malware_types as types,
               m.description as description
        LIMIT $limit
        """
        malware_list = self.conn.execute_read(query, {"limit": num * 2})
        samples = []
        
        for malware in malware_list[:num]:
            if not malware.get('name') or not malware.get('types'):
                continue
            
            types_str = ", ".join(malware['types'])
            samples.append({
                "question": f"{malware['name']}는 어떤 종류의 악성코드인가?",
                "answer": f"{malware['name']}는 {types_str} 유형의 악성코드이다.",
                "difficulty": "easy",
                "type": "malware_type",
                "metadata": {
                    "entity_id": malware['id'],
                    "types": malware['types']
                }
            })
        
        return samples
    
    def _template_threat_actor_motivation(self, num: int) -> List[Dict]:
        """위협 주체 동기"""
        query = """
        MATCH (ta:ThreatActor)
        WHERE ta.primary_motivation IS NOT NULL
        RETURN ta.id as id, ta.name as name,
               ta.primary_motivation as motivation,
               ta.description as description
        LIMIT $limit
        """
        actors = self.conn.execute_read(query, {"limit": num * 2})
        samples = []
        
        for actor in actors[:num]:
            if not actor.get('name') or not actor.get('motivation'):
                continue
            
            samples.append({
                "question": f"{actor['name']}의 주요 동기는 무엇인가?",
                "answer": f"{actor['name']}의 주요 동기는 {actor['motivation']}이다.",
                "difficulty": "easy",
                "type": "threat_actor_motivation",
                "metadata": {
                    "entity_id": actor['id']
                }
            })
        
        return samples
    
    def _template_vulnerability_cve(self, num: int) -> List[Dict]:
        """취약점 CVE 정보"""
        query = """
        MATCH (v:Vulnerability)
        WHERE v.cve_id IS NOT NULL
        RETURN v.id as id, v.name as name, v.cve_id as cve_id,
               v.description as description
        LIMIT $limit
        """
        vulns = self.conn.execute_read(query, {"limit": num * 2})
        samples = []
        
        for vuln in vulns[:num]:
            if not vuln.get('cve_id'):
                continue
            
            samples.append({
                "question": f"{vuln.get('name', vuln['cve_id'])}의 CVE ID는 무엇인가?",
                "answer": f"CVE ID는 {vuln['cve_id']}이다.",
                "difficulty": "easy",
                "type": "vulnerability_cve",
                "metadata": {
                    "entity_id": vuln['id'],
                    "cve_id": vuln['cve_id']
                }
            })
        
        return samples
    
    def _template_tool_usage(self, num: int) -> List[Dict]:
        """도구 사용"""
        query = """
        MATCH (t:Tool)-[:USES]->(ap:AttackPattern)
        RETURN t.id as tool_id, t.name as tool_name,
               collect(ap.name)[0..3] as attack_patterns
        LIMIT $limit
        """
        tools = self.conn.execute_read(query, {"limit": num * 2})
        samples = []
        
        for tool in tools[:num]:
            if not tool.get('tool_name') or not tool.get('attack_patterns'):
                continue
            
            patterns_str = ", ".join(tool['attack_patterns'][:2])
            samples.append({
                "question": f"{tool['tool_name']} 도구는 어떤 공격 기법에 사용되는가?",
                "answer": f"{tool['tool_name']}는 {patterns_str} 등의 공격 기법에 사용된다.",
                "difficulty": "easy",
                "type": "tool_usage",
                "metadata": {
                    "entity_id": tool['tool_id']
                }
            })
        
        return samples
    
    def _template_mitigation_for_attack(self, num: int) -> List[Dict]:
        """공격에 대한 대응 방안"""
        query = """
        MATCH (coa:CourseOfAction)-[:MITIGATES]->(ap:AttackPattern)
        WHERE coa.description IS NOT NULL
        RETURN ap.id as attack_id, ap.name as attack_name,
               coa.name as mitigation_name,
               coa.description as mitigation_description
        LIMIT $limit
        """
        mitigations = self.conn.execute_read(query, {"limit": num * 2})
        samples = []
        
        for mit in mitigations[:num]:
            if not mit.get('attack_name') or not mit.get('mitigation_description'):
                continue
            
            samples.append({
                "question": f"{mit['attack_name']} 공격에 대한 대응 방안은 무엇인가?",
                "answer": mit['mitigation_description'],
                "difficulty": "easy",
                "type": "mitigation",
                "metadata": {
                    "attack_id": mit['attack_id'],
                    "mitigation": mit['mitigation_name']
                }
            })
        
        return samples
    
    # ========================================
    # Medium Templates (2-3 hop)
    # ========================================
    
    def _template_malware_attack_chain(self, num: int) -> List[Dict]:
        """악성코드 공격 체인"""
        malware_data = self.utils.get_qa_malware_analysis(limit=num * 2)
        samples = []
        
        for data in malware_data[:num]:
            if not data.get('malware_name') or not data.get('attack_patterns'):
                continue
            
            patterns_str = ", ".join(data['attack_patterns'][:3])
            answer = f"{data['malware_name']}는 {patterns_str} 등의 공격 패턴을 사용한다."
            
            if data.get('threat_actors'):
                actors_str = ", ".join(data['threat_actors'][:2])
                answer += f" 이 악성코드는 {actors_str} 등의 위협 주체가 사용하는 것으로 알려져 있다."
            
            samples.append({
                "question": f"{data['malware_name']} 악성코드는 어떤 공격 패턴을 사용하는가?",
                "answer": answer,
                "difficulty": "medium",
                "type": "malware_attack_chain",
                "metadata": {
                    "malware": data['malware_name'],
                    "attack_patterns": data['attack_patterns']
                }
            })
        
        return samples
    
    def _template_threat_actor_ttps(self, num: int) -> List[Dict]:
        """위협 주체 TTP 분석"""
        query = """
        MATCH (ta:ThreatActor)-[:USES]->(m:Malware)
        MATCH (ta)-[:USES]->(ap:AttackPattern)
        RETURN ta.name as threat_actor,
               collect(DISTINCT m.name)[0..3] as malware,
               collect(DISTINCT ap.name)[0..5] as attack_patterns
        LIMIT $limit
        """
        actors_data = self.conn.execute_read(query, {"limit": num * 2})
        samples = []
        
        for data in actors_data[:num]:
            if not data.get('threat_actor') or not data.get('attack_patterns'):
                continue
            
            patterns_str = ", ".join(data['attack_patterns'][:3])
            answer = f"{data['threat_actor']}는 {patterns_str} 등의 공격 기법을 사용한다."
            
            if data.get('malware'):
                malware_str = ", ".join(data['malware'][:2])
                answer += f" 주로 {malware_str} 등의 악성코드를 활용한다."
            
            samples.append({
                "question": f"{data['threat_actor']} 그룹은 어떤 TTP(전술, 기법, 절차)를 사용하는가?",
                "answer": answer,
                "difficulty": "medium",
                "type": "threat_actor_ttps",
                "metadata": {
                    "threat_actor": data['threat_actor']
                }
            })
        
        return samples
    
    def _template_campaign_analysis(self, num: int) -> List[Dict]:
        """캠페인 분석"""
        query = """
        MATCH (c:Campaign)
        WHERE c.description IS NOT NULL
        OPTIONAL MATCH (c)-[:USES]->(m:Malware)
        OPTIONAL MATCH (c)-[:USES]->(ap:AttackPattern)
        RETURN c.id as campaign_id, c.name as campaign_name,
               c.description as description,
               collect(DISTINCT m.name)[0..3] as malware,
               collect(DISTINCT ap.name)[0..5] as attack_patterns
        LIMIT $limit
        """
        campaigns = self.conn.execute_read(query, {"limit": num * 2})
        samples = []
        
        for camp in campaigns[:num]:
            if not camp.get('campaign_name'):
                continue
            
            answer = camp.get('description', '')
            
            if camp.get('malware'):
                malware_str = ", ".join(camp['malware'])
                answer += f" 이 캠페인은 {malware_str} 등의 악성코드를 사용한다."
            
            if camp.get('attack_patterns'):
                patterns_str = ", ".join(camp['attack_patterns'][:3])
                answer += f" 주요 공격 기법은 {patterns_str} 등이다."
            
            samples.append({
                "question": f"{camp['campaign_name']} 캠페인의 특징은 무엇인가?",
                "answer": answer,
                "difficulty": "medium",
                "type": "campaign_analysis",
                "metadata": {
                    "campaign_id": camp['campaign_id']
                }
            })
        
        return samples
    
    def _template_attack_pattern_relationships(self, num: int) -> List[Dict]:
        """공격 패턴 간 관계"""
        attack_chains = self.utils.get_qa_attack_chains(min_hops=2, max_hops=3, limit=num * 2)
        samples = []
        
        for chain in attack_chains[:num]:
            if not chain.get('nodes') or len(chain['nodes']) < 3:
                continue
            
            start_node = chain['nodes'][0]
            end_node = chain['nodes'][-1]
            middle_nodes = chain['nodes'][1:-1]
            
            if not start_node.get('name') or not end_node.get('name'):
                continue
            
            path_names = [n['name'] for n in middle_nodes if n.get('name')]
            if path_names:
                path_str = " → ".join(path_names)
                answer = f"{start_node['name']}와 {end_node['name']}는 {path_str}를 통해 연결되어 있다."
            else:
                answer = f"{start_node['name']}는 {end_node['name']}와 관련이 있다."
            
            samples.append({
                "question": f"{start_node['name']}와 {end_node['name']}의 관계는 무엇인가?",
                "answer": answer,
                "difficulty": "medium",
                "type": "attack_pattern_relationships",
                "metadata": {
                    "hops": chain['hops']
                }
            })
        
        return samples
    
    def _template_vulnerability_exploitation(self, num: int) -> List[Dict]:
        """취약점 활용 분석"""
        query = """
        MATCH (v:Vulnerability)<-[:EXPLOITS]-(ap:AttackPattern)
        OPTIONAL MATCH (m:Malware)-[:USES]->(ap)
        RETURN v.cve_id as cve_id, v.name as vuln_name,
               collect(DISTINCT ap.name)[0..3] as attack_patterns,
               collect(DISTINCT m.name)[0..3] as malware
        LIMIT $limit
        """
        vulns = self.conn.execute_read(query, {"limit": num * 2})
        samples = []
        
        for vuln in vulns[:num]:
            if not vuln.get('cve_id') or not vuln.get('attack_patterns'):
                continue
            
            patterns_str = ", ".join(vuln['attack_patterns'])
            answer = f"{vuln['cve_id']} 취약점은 {patterns_str} 등의 공격 기법으로 악용될 수 있다."
            
            if vuln.get('malware'):
                malware_str = ", ".join(vuln['malware'][:2])
                answer += f" {malware_str} 등의 악성코드가 이 취약점을 이용하는 것으로 알려져 있다."
            
            samples.append({
                "question": f"{vuln['cve_id']} 취약점은 어떻게 악용되는가?",
                "answer": answer,
                "difficulty": "medium",
                "type": "vulnerability_exploitation",
                "metadata": {
                    "cve_id": vuln['cve_id']
                }
            })
        
        return samples
    
    # ========================================
    # Hard Templates (4+ hop)
    # ========================================
    
    def _template_complex_attack_chain(self, num: int) -> List[Dict]:
        """복잡한 공격 체인 분석"""
        attack_chains = self.utils.get_qa_attack_chains(min_hops=4, max_hops=6, limit=num * 2)
        samples = []
        
        for chain in attack_chains[:num]:
            if not chain.get('nodes') or len(chain['nodes']) < 4:
                continue
            
            node_names = [n['name'] for n in chain['nodes'] if n.get('name')]
            if len(node_names) < 4:
                continue
            
            path_str = " → ".join(node_names)
            answer = f"공격 체인은 다음과 같다: {path_str}. "
            answer += f"이는 {chain['hops']}-단계의 복잡한 공격 경로를 보여준다."
            
            samples.append({
                "question": f"{node_names[0]}에서 시작하여 {node_names[-1]}까지 이어지는 공격 체인을 설명하라.",
                "answer": answer,
                "difficulty": "hard",
                "type": "complex_attack_chain",
                "metadata": {
                    "hops": chain['hops'],
                    "chain_length": len(node_names)
                }
            })
        
        return samples
    
    def _template_comparative_analysis(self, num: int) -> List[Dict]:
        """비교 분석"""
        comparisons = self.utils.get_comparison_data("malware", limit=num * 2)
        samples = []
        
        for comp in comparisons[:num]:
            if not comp.get('entity1_name') or not comp.get('entity2_name'):
                continue
            
            answer = f"{comp['entity1_name']}와 {comp['entity2_name']}는 {comp['common_count']}개의 공통 요소를 가지고 있다. "
            
            if comp.get('entity1_description') and comp.get('entity2_description'):
                answer += f"{comp['entity1_name']}는 {comp['entity1_description'][:100]}... "
                answer += f"{comp['entity2_name']}는 {comp['entity2_description'][:100]}..."
            
            samples.append({
                "question": f"{comp['entity1_name']}와 {comp['entity2_name']}의 유사점과 차이점을 비교하라.",
                "answer": answer,
                "difficulty": "hard",
                "type": "comparative_analysis",
                "metadata": {
                    "common_count": comp['common_count']
                }
            })
        
        return samples
    
    def _template_threat_intelligence_synthesis(self, num: int) -> List[Dict]:
        """위협 인텔리전스 종합 분석"""
        ti_data = self.utils.get_qa_threat_intelligence(limit=num * 2)
        samples = []
        
        for data in ti_data[:num]:
            if not data.get('threat_actor') or not data.get('malware'):
                continue
            
            answer = f"{data['threat_actor']} 그룹은 {data['malware']} 악성코드를 사용하여 "
            answer += f"{data['attack_pattern']} 공격 기법을 구사한다. "
            
            if data.get('mitigations'):
                mit_str = ", ".join(data['mitigations'][:2])
                answer += f"이에 대한 대응 방안으로는 {mit_str} 등이 있다."
            
            samples.append({
                "question": f"{data['threat_actor']} 그룹의 공격 방식과 대응 전략을 종합적으로 설명하라.",
                "answer": answer,
                "difficulty": "hard",
                "type": "threat_intelligence_synthesis",
                "metadata": {
                    "threat_actor": data['threat_actor'],
                    "malware": data['malware']
                }
            })
        
        return samples
    
    def _template_defensive_strategy(self, num: int) -> List[Dict]:
        """방어 전략 수립"""
        query = """
        MATCH (ap:AttackPattern)<-[:USES]-(m:Malware)
        MATCH (coa:CourseOfAction)-[:MITIGATES]->(ap)
        RETURN ap.name as attack_pattern,
               collect(DISTINCT m.name)[0..3] as malware,
               collect(DISTINCT coa.name)[0..3] as mitigations,
               coa.description as mitigation_description
        LIMIT $limit
        """
        strategies = self.conn.execute_read(query, {"limit": num * 2})
        samples = []
        
        for strat in strategies[:num]:
            if not strat.get('attack_pattern') or not strat.get('mitigations'):
                continue
            
            malware_str = ", ".join(strat['malware'][:2]) if strat.get('malware') else "여러 악성코드"
            mit_str = ", ".join(strat['mitigations'][:2])
            
            answer = f"{strat['attack_pattern']} 공격 기법에 대응하기 위해서는 {mit_str} 등의 방어 조치가 필요하다. "
            
            if strat.get('malware'):
                answer += f"특히 {malware_str}를 사용한 공격을 방어하는 것이 중요하다."
            
            samples.append({
                "question": f"{strat['attack_pattern']}을 사용하는 공격에 대한 종합적인 방어 전략을 수립하라.",
                "answer": answer,
                "difficulty": "hard",
                "type": "defensive_strategy",
                "metadata": {
                    "attack_pattern": strat['attack_pattern']
                }
            })
        
        return samples
    
    # ========================================
    # Export
    # ========================================
    
    def save_to_json(self, output_path: str):
        """JSON 파일로 저장"""
        output_data = {
            "metadata": {
                "domain": "hacking",
                "total_samples": len(self.qa_samples),
                "generated_at": datetime.now().isoformat(),
                "difficulty_distribution": {
                    "easy": sum(1 for s in self.qa_samples if s['difficulty'] == 'easy'),
                    "medium": sum(1 for s in self.qa_samples if s['difficulty'] == 'medium'),
                    "hard": sum(1 for s in self.qa_samples if s['difficulty'] == 'hard'),
                }
            },
            "qa_samples": self.qa_samples
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n✓ QA 데이터셋 저장 완료: {output_path}")
        logger.info(f"  - Easy: {output_data['metadata']['difficulty_distribution']['easy']}개")
        logger.info(f"  - Medium: {output_data['metadata']['difficulty_distribution']['medium']}개")
        logger.info(f"  - Hard: {output_data['metadata']['difficulty_distribution']['hard']}개")


def main():
    parser = argparse.ArgumentParser(description="Hacking Domain QA 데이터셋 생성")
    parser.add_argument(
        "--output",
        default="qa_dataset/hacking_qa.json",
        help="출력 JSON 파일 경로"
    )
    parser.add_argument(
        "--num-easy",
        type=int,
        default=300,
        help="Easy 난이도 샘플 수"
    )
    parser.add_argument(
        "--num-medium",
        type=int,
        default=400,
        help="Medium 난이도 샘플 수"
    )
    parser.add_argument(
        "--num-hard",
        type=int,
        default=300,
        help="Hard 난이도 샘플 수"
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
    
    # 출력 디렉토리 생성
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Neo4j 연결
    config = Neo4jConfig(
        uri=args.uri,
        user=args.user,
        password=args.password
    )
    
    with get_connector(config) as conn:
        generator = HackingQAGenerator(conn)
        generator.generate_all(
            num_easy=args.num_easy,
            num_medium=args.num_medium,
            num_hard=args.num_hard
        )
        generator.save_to_json(args.output)


if __name__ == "__main__":
    main()


