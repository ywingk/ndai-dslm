"""
사용 예시: Hacking Domain Neo4j
"""
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig
from neo4j_query_utils import Neo4jQueryUtils


def main():
    print("=" * 60)
    print("Hacking Domain Neo4j 사용 예시")
    print("=" * 60)
    
    # Neo4j 연결
    config = Neo4jConfig.default()
    
    with get_connector(config) as conn:
        utils = Neo4jQueryUtils(conn)
        
        # 1. 공격 패턴 검색
        print("\n1️⃣  공격 패턴 검색: Phishing")
        print("-" * 60)
        attack = utils.get_attack_pattern_by_name("Phishing")
        if attack:
            print(f"  이름: {attack['name']}")
            print(f"  MITRE ID: {attack.get('mitre_id', 'N/A')}")
            print(f"  설명: {attack.get('description', 'N/A')[:200]}...")
            
            # 관련 악성코드
            print("\n  🔹 관련 악성코드:")
            malware = utils.get_related_malware(attack['id'])
            for m in malware[:5]:
                print(f"    - {m['name']}")
            
            # 사용하는 위협 주체
            print("\n  🔹 사용하는 위협 주체:")
            actors = utils.get_threat_actors_using_attack(attack['id'])
            for actor in actors[:5]:
                print(f"    - {actor['name']}")
            
            # 대응 방안
            print("\n  🔹 대응 방안:")
            mitigations = utils.get_mitigations(attack['id'])
            for mit in mitigations[:3]:
                print(f"    - {mit['name']}")
        
        # 2. 악성코드 분석
        print("\n\n2️⃣  악성코드 검색")
        print("-" * 60)
        malware_result = utils.get_malware_by_name("ransomware")
        if malware_result:
            print(f"  이름: {malware_result['name']}")
            print(f"  타입: {malware_result.get('malware_types', 'N/A')}")
            print(f"  설명: {malware_result.get('description', 'N/A')[:200]}...")
        
        # 3. 공격 체인 분석
        print("\n\n3️⃣  공격 체인 분석")
        print("-" * 60)
        if attack:
            chains = utils.get_attack_chains(attack['id'], max_hops=3, limit=3)
            for i, chain in enumerate(chains, 1):
                print(f"\n  체인 {i} ({chain['hops']} hops):")
                steps = chain['steps']
                if steps:
                    print(f"    {' → '.join(steps[:5])}")
        
        # 4. 가장 많이 사용되는 공격 패턴
        print("\n\n4️⃣  가장 많이 사용되는 공격 패턴 TOP 10")
        print("-" * 60)
        top_attacks = utils.get_most_used_attack_patterns(limit=10)
        for i, attack in enumerate(top_attacks, 1):
            print(f"  {i}. {attack['name']} ({attack.get('mitre_id', 'N/A')})")
            print(f"     사용 횟수: {attack['usage_count']}")
        
        # 5. Tactic별 공격 기법
        print("\n\n5️⃣  특정 Tactic의 공격 기법: Initial Access")
        print("-" * 60)
        tactic_attacks = utils.get_attack_patterns_by_tactic("initial-access")
        for attack in tactic_attacks[:5]:
            print(f"  - {attack['name']} ({attack.get('mitre_id', 'N/A')})")
        
        # 6. 데이터베이스 통계
        print("\n\n6️⃣  데이터베이스 통계")
        print("-" * 60)
        stats = conn.get_stats()
        print(f"  총 노드 수: {stats['nodes']:,}개")
        print(f"  총 관계 수: {stats['relationships']:,}개")
        
        if stats.get('by_label'):
            print("\n  레이블별 노드 수:")
            for label, count in list(stats['by_label'].items())[:10]:
                print(f"    - {label}: {count:,}개")
        
        if stats.get('by_relationship'):
            print("\n  관계 타입별 수:")
            for rel_type, count in list(stats['by_relationship'].items())[:10]:
                print(f"    - {rel_type}: {count:,}개")
    
    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()



