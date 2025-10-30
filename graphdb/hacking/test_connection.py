#!/usr/bin/env python3
"""Neo4j 연결 테스트"""
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig

print("=" * 60)
print("Neo4j 연결 테스트")
print("=" * 60)

config = Neo4jConfig.default()
print(f"\n설정:")
print(f"  URI: {config.uri}")
print(f"  User: {config.user}")
print(f"  Password: {config.password}")

try:
    with get_connector(config) as conn:
        # 데이터베이스 통계
        stats = conn.get_stats()
        print(f"\n✅ 연결 성공!")
        print(f"\n데이터베이스 통계:")
        print(f"  총 노드: {stats['nodes']:,}개")
        print(f"  총 관계: {stats['relationships']:,}개")
        
except Exception as e:
    print(f"\n❌ 연결 실패: {e}")
    print("\n해결 방법:")
    print("  1. Neo4j가 실행 중인지 확인: docker ps | grep neo4j")
    print("  2. 포트 확인: netstat -tuln | grep 7687")
    print("  3. 로그 확인: docker logs neo4j-hacking")

print("\n" + "=" * 60)


