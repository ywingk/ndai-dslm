"""
SNOMED CT 데이터를 Neo4j로 임포트
----------------------------------
RF2 파일에서 치과 서브그래프를 추출하여 Neo4j에 저장

⚙️ 사용법:
    python snomed_to_neo4j.py --keywords "dental caries" --clear
"""
import pandas as pd
import os
import argparse
from tqdm import tqdm
from typing import Set, List, Dict
from neo4j_connector import get_connector
from neo4j_config import Neo4jConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SNOMED CT RF2 파일 경로
#FULL_PATH = "/mls/_downloads/SNOMED/data/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/Full/Terminology/"
FULL_PATH = "/user/data/SNOMED/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/Full/Terminology/"
CONCEPT_FILE = os.path.join(FULL_PATH, "sct2_Concept_Full_INT_20251001.txt")
DESCRIPTION_FILE = os.path.join(FULL_PATH, "sct2_Description_Full-en_INT_20251001.txt")
RELATIONSHIP_FILE = os.path.join(FULL_PATH, "sct2_Relationship_Full_INT_20251001.txt")


class SnomedToNeo4jImporter:
    """SNOMED CT → Neo4j 임포터"""
    
    def __init__(self, connector):
        self.conn = connector
        self.concept_df = None
        self.desc_df = None
        self.rels_df = None
        
    def load_snomed_data(self):
        """SNOMED CT RF2 파일 로드"""
        logger.info("🔹 SNOMED CT 데이터 로드 중...")
        
        # Concept 로드
        self.concept_df = pd.read_csv(CONCEPT_FILE, sep="\t", dtype=str)
        self.concept_df = self.concept_df[self.concept_df["active"] == "1"]
        logger.info(f"  ✓ Concept: {len(self.concept_df):,}개")
        
        # Description 로드
        self.desc_df = pd.read_csv(DESCRIPTION_FILE, sep="\t", dtype=str)
        self.desc_df = self.desc_df[self.desc_df["active"] == "1"]
        logger.info(f"  ✓ Description: {len(self.desc_df):,}개")
        
        # Relationship 로드
        self.rels_df = pd.read_csv(RELATIONSHIP_FILE, sep="\t", dtype=str)
        self.rels_df = self.rels_df[self.rels_df["active"] == "1"]
        logger.info(f"  ✓ Relationship: {len(self.rels_df):,}개")
    
    def filter_dental_subgraph(self, keywords: List[str]) -> tuple[Set[str], pd.DataFrame]:
        """치과 관련 서브그래프 필터링"""
        logger.info(f"🔹 키워드로 서브그래프 필터링: {keywords}")
        
        # FSN(Fully Specified Name)에서 키워드 검색
        fsn_df = self.desc_df[
            (self.desc_df["typeId"] == "900000000000003001") & 
            (self.desc_df["active"] == "1")
        ]
        fsn_df = fsn_df.set_index("conceptId")
        
        # 키워드 포함 concept 찾기
        dental_concepts = fsn_df[
            fsn_df["term"].str.contains("|".join(keywords), case=False, na=False)
        ]
        dental_ids = set(dental_concepts.index)
        
        # 관계 필터링 (양방향)
        dental_rels = self.rels_df[
            (self.rels_df["sourceId"].isin(dental_ids)) |
            (self.rels_df["destinationId"].isin(dental_ids))
        ]
        
        # 관계에 포함된 모든 concept ID 추가
        all_concept_ids = set(dental_rels["sourceId"]).union(set(dental_rels["destinationId"]))
        
        logger.info(f"  ✓ 필터링된 노드: {len(all_concept_ids):,}개")
        logger.info(f"  ✓ 필터링된 관계: {len(dental_rels):,}개")
        
        return all_concept_ids, dental_rels
    
    def get_concept_term(self, concept_id: str) -> str:
        """Concept ID의 FSN 조회"""
        term_row = self.desc_df[
            (self.desc_df["conceptId"] == concept_id) &
            (self.desc_df["typeId"] == "900000000000003001")  # FSN
        ]
        if not term_row.empty:
            return term_row.iloc[0]["term"]
        return f"Concept_{concept_id}"
    
    def get_relationship_term(self, type_id: str) -> str:
        """Relationship Type ID의 용어 조회"""
        term_row = self.desc_df[
            (self.desc_df["conceptId"] == type_id) &
            (self.desc_df["typeId"] == "900000000000013009")  # Synonym
        ]
        if not term_row.empty:
            return term_row.iloc[0]["term"]
        return f"Relationship_{type_id}"
    
    def convert_to_neo4j_rel_type(self, term: str) -> str:
        """SNOMED 관계 용어를 Neo4j 관계 타입으로 변환
        
        예: "Is a" -> "IS_A", "Finding site" -> "FINDING_SITE"
        """
        # 공백과 특수문자를 언더스코어로 변환하고 대문자로
        rel_type = term.upper()
        rel_type = rel_type.replace(" ", "_")
        rel_type = rel_type.replace("-", "_")
        rel_type = rel_type.replace("(", "")
        rel_type = rel_type.replace(")", "")
        rel_type = rel_type.replace(",", "")
        # 연속된 언더스코어를 하나로
        while "__" in rel_type:
            rel_type = rel_type.replace("__", "_")
        return rel_type
    
    def import_concepts_batch(self, concept_ids: Set[str], batch_size: int = 1000):
        """Concept 노드를 배치로 Neo4j에 임포트"""
        logger.info("🔹 Concept 노드 임포트 중...")
        
        concept_list = []
        for cid in tqdm(concept_ids, desc="Concept 처리"):
            term = self.get_concept_term(cid)
            concept_list.append({
                "conceptId": cid,
                "term": term
            })
        
        # 배치 임포트
        query = """
        UNWIND $concepts AS concept
        MERGE (c:Concept {conceptId: concept.conceptId})
        SET c.term = concept.term
        """
        
        for i in range(0, len(concept_list), batch_size):
            batch = concept_list[i:i + batch_size]
            self.conn.execute_write(query, {"concepts": batch})
        
        logger.info(f"  ✓ {len(concept_list):,}개 Concept 임포트 완료")
    
    def import_relationships_batch(self, dental_rels: pd.DataFrame, batch_size: int = 1000):
        """관계를 배치로 Neo4j에 임포트 (관계 타입별로 구분)"""
        logger.info("🔹 Relationship 임포트 중...")
        
        # 관계 타입별로 그룹화
        relationship_groups = {}
        for _, row in tqdm(dental_rels.iterrows(), total=len(dental_rels), desc="Relationship 처리"):
            rel_term = self.get_relationship_term(row["typeId"])
            neo4j_rel_type = self.convert_to_neo4j_rel_type(rel_term)
            
            if neo4j_rel_type not in relationship_groups:
                relationship_groups[neo4j_rel_type] = []
            
            relationship_groups[neo4j_rel_type].append({
                "sourceId": row["sourceId"],
                "destinationId": row["destinationId"],
                "typeId": row["typeId"],
                "typeTerm": rel_term,
                "relType": neo4j_rel_type
            })
        
        logger.info(f"  ✓ {len(relationship_groups)}개의 관계 타입 발견")
        
        # 각 관계 타입별로 배치 임포트
        total_imported = 0
        for rel_type, relationships in relationship_groups.items():
            # 동적으로 관계 타입을 생성하는 쿼리
            query = f"""
            UNWIND $relationships AS rel
            MATCH (source:Concept {{conceptId: rel.sourceId}})
            MATCH (dest:Concept {{conceptId: rel.destinationId}})
            MERGE (source)-[r:{rel_type}]->(dest)
            SET r.typeId = rel.typeId,
                r.typeTerm = rel.typeTerm
            """
            
            for i in range(0, len(relationships), batch_size):
                batch = relationships[i:i + batch_size]
                self.conn.execute_write(query, {"relationships": batch})
            
            total_imported += len(relationships)
            logger.info(f"    - {rel_type}: {len(relationships)}개")
        
        logger.info(f"  ✓ 총 {total_imported:,}개 Relationship 임포트 완료")
    
    def import_subgraph(self, keywords: List[str], clear: bool = False):
        """전체 임포트 프로세스"""
        if clear:
            logger.warning("⚠️  기존 데이터 삭제 중...")
            self.conn.clear_database()
        
        # 데이터 로드
        self.load_snomed_data()
        
        # 서브그래프 필터링
        concept_ids, dental_rels = self.filter_dental_subgraph(keywords)
        
        # 인덱스 생성
        self.conn.create_indexes()
        
        # 임포트
        self.import_concepts_batch(concept_ids)
        self.import_relationships_batch(dental_rels)
        
        # 통계 출력
        stats = self.conn.get_stats()
        logger.info("\n📊 임포트 완료 통계:")
        logger.info(f"  - 총 노드: {stats['nodes']:,}개")
        logger.info(f"  - 총 관계: {stats['relationships']:,}개")


def main():
    parser = argparse.ArgumentParser(description="SNOMED CT를 Neo4j로 임포트")
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=["dental caries"],
        help="필터링할 키워드 (예: dental caries, tooth, implant)"
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
        default="dental_slm_2025",
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
        importer = SnomedToNeo4jImporter(conn)
        importer.import_subgraph(args.keywords, clear=args.clear)


if __name__ == "__main__":
    main()

