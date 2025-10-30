#!/bin/bash
# Hacking Domain Graph DB 설정 스크립트

set -e

echo "=========================================="
echo "Hacking Domain Graph DB 설정"
echo "=========================================="

# 1. 의존성 설치
echo ""
echo "📦 Python 패키지 설치 중..."
pip install -r requirements.txt

# 2. 데이터 디렉토리 생성
echo ""
echo "📁 디렉토리 생성 중..."
mkdir -p data
mkdir -p qa_dataset

# 3. Neo4j 실행
echo ""
echo "🚀 Neo4j 시작 중..."
docker-compose up -d

echo ""
echo "⏳ Neo4j 초기화 대기 (30초)..."
sleep 30

# 4. MITRE ATT&CK 데이터 다운로드
echo ""
echo "📥 MITRE ATT&CK 데이터 다운로드 중..."
python download_mitre_attack.py --domain enterprise

# 5. Neo4j로 임포트
echo ""
echo "🔄 Neo4j 임포트 중..."
python stix_to_neo4j.py \
  --input data/enterprise-attack.json \
  --clear

echo ""
echo "=========================================="
echo "✅ 설정 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "  1. Neo4j Browser: http://localhost:7475"
echo "  2. 사용 예시 실행: python example_usage.py"
echo "  3. QA 생성: python generate_qa_dataset.py"
echo ""



