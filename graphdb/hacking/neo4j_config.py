"""
Neo4j 연결 설정 - Hacking Domain
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Neo4jConfig:
    """Neo4j 연결 설정"""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "domain_slm_2025"
    database: str = "neo4j"
    
    @classmethod
    def from_env(cls) -> 'Neo4jConfig':
        """환경 변수에서 설정 로드"""
        return cls(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "domain_slm_2025"),
            database=os.getenv("NEO4J_DATABASE", "neo4j")
        )
    
    @classmethod
    def default(cls) -> 'Neo4jConfig':
        """기본 설정"""
        return cls()


