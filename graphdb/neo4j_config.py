"""
Neo4j 데이터베이스 연결 설정
----------------------------
환경 변수 또는 직접 설정으로 Neo4j 연결 정보 관리
"""
import os
from dataclasses import dataclass

@dataclass
class Neo4jConfig:
    """Neo4j 연결 설정"""
    uri: str
    user: str
    password: str
    database: str = "neo4j"
    
    @classmethod
    def from_env(cls):
        """환경 변수에서 설정 로드"""
        return cls(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "dental_slm_2025"),
            database=os.getenv("NEO4J_DATABASE", "neo4j")
        )
    
    @classmethod
    def default(cls):
        """기본 로컬 설정"""
        return cls(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="dental_slm_2025",  # 실제 비밀번호로 변경 필요
            database="neo4j"
        )

