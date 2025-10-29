import pandas as pd
import networkx as nx
from pyvis.network import Network
import os

# -----------------------------
# 1️⃣ RF2 파일 경로 설정
# -----------------------------
FULL_PATH = "/mls/_downloads/SNOMED/data/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/Full/Terminology/"
#SNAP_PATH = "/home/kyi/mls/_downloads/SNOMED/data/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/SnomedCT_InternationalRF2_PRODUCTION_20251001T120000Z/Snapshot/Terminology"
CONCEPT_FILE = os.path.join(FULL_PATH, "sct2_Concept_Full_INT_20251001.txt")
DESCRIPTION_FILE = os.path.join(FULL_PATH, "sct2_Description_Full-en_INT_20251001.txt") 
RELATIONSHIP_FILE = os.path.join(FULL_PATH, "sct2_Relationship_Full_INT_20251001.txt") 

# -----------------------------
# 2️⃣ 데이터 로드
# -----------------------------
print("🔹 Concept 파일 로드 중...")
concept_df = pd.read_csv(CONCEPT_FILE, sep="\t", dtype=str)
concept_df = concept_df[concept_df["active"] == "1"]  # 활성 concept만

print("🔹 Description 파일 로드 중...")
desc_df = pd.read_csv(DESCRIPTION_FILE, sep="\t", dtype=str)
# FSN만 필터링 (typeId=900000000000003001) 
# -- fsn_df for concepts term detection -- 
fsn_df = desc_df[(desc_df["typeId"] == "900000000000003001") & (desc_df["active"] == "1")]
fsn_df = fsn_df.set_index("conceptId")
# -- fsn2_df for relationships term detection -- 
#fsn2_df = desc_df[(desc_df["typeId"] == "900000000000013009") & (desc_df["active"] == "1")]
#fsn2_df = fsn2_df.set_index("conceptId") 

print("🔹 Relationship 파일 로드 중...")
rels_df = pd.read_csv(RELATIONSHIP_FILE, sep="\t", dtype=str)
rels_df = rels_df[rels_df["active"] == "1"]  # 활성 관계만

# -----------------------------
# 3️⃣ 서브그래프 필터링 (예: 치과 관련)
# -----------------------------
#keywords = ["tooth", "dental", "periodont"]  # -> relationships 16721, nodes 5820 
#keywords = ["implant"] # -> relationships 6028, nodes 1988
keywords = ["dental caries"] # -> relationships 662, nodes 184 

dental_concepts = fsn_df[fsn_df["term"].str.contains("|".join(keywords), case=False, na=False)]
dental_ids = set(dental_concepts.index)

# 해당 concepts의 관계만 필터링
dental_rels = rels_df[
    (rels_df["sourceId"].isin(dental_ids)) &
    (rels_df["destinationId"].isin(dental_ids))
]

print(f"서브그래프 관계 수: {len(dental_rels)}")
print(f"서브그래프 노드 수: {len(dental_ids)}")

#import pdb; pdb.set_trace()

# -----------------------------
# 4️⃣ 관계 타입별 색상 사전 정의
# -----------------------------
REL_TYPE_COLORS = {
    "116680003": "#888888",  # is-a → 회색
    "123005000": "#1f77b4",  # part-of → 파랑
    "47429007": "#ff7f0e",   # associated-with → 주황
    "363698007": "#2ca02c",  # finding-site → 초록
    "370135005": "#d62728",  # pathologic-process → 빨강
    # 기타 타입은 자동으로 랜덤 색상
}
# REL_TYPE_IDS = {
#     "116680003": "is-a",  # is-a → 회색
#     "123005000": "part-of",  # part-of → 파랑
#     "47429007": "associated-with",   # associated-with → 주황
#     "363698007": "finding-site",  # finding-site → 초록
#     "370135005": "pathologic-process",  # pathologic-process → 빨강    
# }

# -----------------------------
# PyVis 직접 구성 (중요!)
# -----------------------------
net = Network(height="800px", width="100%", directed=True, notebook=False)

# 노드 추가
for cid in dental_ids:
    try:
        # .at[cid, "term"]로 단일 값 추출
        term = str(dental_concepts.at[cid, "term"])
    except KeyError:
        term = cid  # FSN 없으면 conceptId 사용
    net.add_node(cid, label=term, title=term)

# 엣지 추가
for _, row in dental_rels.iterrows():
    src, dst, type_id = row["sourceId"], row["destinationId"], row["typeId"]
    #rel_label = all_fsn_df["term"].get(type_id, "is-a" if type_id == "116680003" else f"Unknown ({type_id})")
    #rel_label = REL_TYPE_IDS.get(type_id, "Unknown")
    #import pdb; pdb.set_trace()
    rel_label = str(desc_df[(desc_df["conceptId"] == type_id) & (desc_df["typeId"] == '900000000000013009')]["term"].iloc[0])
    color = REL_TYPE_COLORS.get(type_id, "#9999cc")
    
    # label을 문자열로 강제 변환
    rel_label = str(rel_label)
    net.add_edge(
        src, dst,
        label=rel_label,
        title=f"{rel_label} ({type_id})",
        color=color,
        font={"align": "middle", "size": 12, "color": color}
    )

net.repulsion(node_distance=350, spring_length=200, damping=0.8)

OUTPUT_HTML = "dental_rf2_graph_labels_fixed.html"
net.show(OUTPUT_HTML)
print(f"✅ 그래프 생성 완료: {OUTPUT_HTML}")
