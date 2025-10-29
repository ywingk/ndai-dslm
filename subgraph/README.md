
## SNOMED - Concept Subgraph 만들기 (2025.10.21, Kyi)

## RF2 raw data 이용 방식 --> OK 
 - pip install pandas networkx pyvis==0.2.1
 - python snomed_rf2_subgraph.py 

## ECL API 방식 -> 실패 (relationships 를 한번가 가져오기 힘듬)
pip install requests networkx pyvis
python snomed_ecl_subgraph.py


