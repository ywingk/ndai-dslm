"""
MISP 데이터 다운로드
------------------
MISP 서버에서 이벤트 데이터를 다운로드하여 JSON 파일로 저장

⚙️ 사용법:
    python download_misp_data.py --url https://misp.example.com --key YOUR_API_KEY
    python download_misp_data.py --url https://misp.example.com --key YOUR_API_KEY --event-id 12345
    python download_misp_data.py --url https://misp.example.com --key YOUR_API_KEY --tags malware,ransomware
"""
import requests
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MISPDownloader:
    """MISP 데이터 다운로더"""
    
    def __init__(self, url: str, api_key: str):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> bool:
        """MISP 서버 연결 테스트"""
        try:
            response = requests.get(
                f"{self.url}/servers/getVersion",
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                version_info = response.json()
                logger.info(f"✓ MISP 서버 연결 성공: {version_info.get('version', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ MISP 서버 연결 실패: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ MISP 서버 연결 오류: {e}")
            return False
    
    def get_events(self, event_id: str = None, tags: List[str] = None, 
                   threat_level: str = None, analysis_level: str = None,
                   limit: int = 1000) -> List[Dict]:
        """이벤트 목록 조회"""
        params = {
            'limit': limit,
            'page': 1,
            'order': 'Event.timestamp desc'
        }
        
        # 필터 파라미터 추가
        if event_id:
            params['eventid'] = event_id
        
        if tags:
            params['tags'] = ','.join(tags)
        
        if threat_level:
            params['threatlevel'] = threat_level
        
        if analysis_level:
            params['analysis'] = analysis_level
        
        try:
            response = requests.get(
                f"{self.url}/events/index",
                headers=self.headers,
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('Event', [])
                logger.info(f"✓ {len(events)}개 이벤트 조회 완료")
                return events
            else:
                logger.error(f"❌ 이벤트 조회 실패: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 이벤트 조회 오류: {e}")
            return []
    
    def get_event_details(self, event_id: str) -> Dict:
        """특정 이벤트 상세 정보 조회"""
        try:
            response = requests.get(
                f"{self.url}/events/view/{event_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                event = data.get('Event', {})
                logger.info(f"✓ 이벤트 {event_id} 상세 정보 조회 완료")
                return event
            else:
                logger.error(f"❌ 이벤트 {event_id} 조회 실패: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ 이벤트 {event_id} 조회 오류: {e}")
            return {}
    
    def download_events(self, event_id: str = None, tags: List[str] = None,
                       threat_level: str = None, analysis_level: str = None,
                       limit: int = 1000, include_attributes: bool = True) -> List[Dict]:
        """이벤트 다운로드 (상세 정보 포함)"""
        if event_id:
            # 특정 이벤트 다운로드
            event = self.get_event_details(event_id)
            if event:
                return [event]
            else:
                return []
        else:
            # 이벤트 목록 조회
            events = self.get_events(event_id, tags, threat_level, analysis_level, limit)
            
            if not events:
                return []
            
            # 각 이벤트의 상세 정보 조회
            detailed_events = []
            for event in events:
                event_id = event.get('id')
                if event_id:
                    detailed_event = self.get_event_details(event_id)
                    if detailed_event:
                        detailed_events.append(detailed_event)
            
            return detailed_events
    
    def save_events(self, events: List[Dict], filename: str = None) -> str:
        """이벤트를 JSON 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"misp_events_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ 이벤트 저장 완료: {filename}")
        return filename


def main():
    parser = argparse.ArgumentParser(description="MISP 데이터 다운로드")
    parser.add_argument(
        "--url",
        required=True,
        help="MISP 서버 URL (예: https://misp.example.com)"
    )
    parser.add_argument(
        "--key",
        required=True,
        help="MISP API 키"
    )
    parser.add_argument(
        "--event-id",
        help="특정 이벤트 ID 다운로드"
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        help="특정 태그가 포함된 이벤트만 다운로드"
    )
    parser.add_argument(
        "--threat-level",
        help="위협 수준 필터 (1-4)"
    )
    parser.add_argument(
        "--analysis-level",
        help="분석 수준 필터 (0-2)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="최대 이벤트 수 (기본값: 1000)"
    )
    parser.add_argument(
        "--output",
        help="출력 파일명 (기본값: misp_events_YYYYMMDD_HHMMSS.json)"
    )
    
    args = parser.parse_args()
    
    # MISP 다운로더 생성
    downloader = MISPDownloader(args.url, args.key)
    
    # 연결 테스트
    if not downloader.test_connection():
        logger.error("MISP 서버 연결에 실패했습니다.")
        return
    
    # 이벤트 다운로드
    logger.info("🔹 MISP 이벤트 다운로드 시작...")
    events = downloader.download_events(
        event_id=args.event_id,
        tags=args.tags,
        threat_level=args.threat_level,
        analysis_level=args.analysis_level,
        limit=args.limit
    )
    
    if not events:
        logger.warning("다운로드할 이벤트가 없습니다.")
        return
    
    # 파일 저장
    filename = downloader.save_events(events, args.output)
    
    # 통계 출력
    logger.info(f"\n📊 다운로드 완료 통계:")
    logger.info(f"  - 총 이벤트: {len(events):,}개")
    
    # 이벤트별 속성 수 통계
    total_attributes = 0
    total_objects = 0
    for event in events:
        total_attributes += len(event.get('Attribute', []))
        total_objects += len(event.get('Object', []))
    
    logger.info(f"  - 총 속성: {total_attributes:,}개")
    logger.info(f"  - 총 객체: {total_objects:,}개")
    
    # 태그 통계
    all_tags = set()
    for event in events:
        for tag in event.get('Tag', []):
            all_tags.add(tag.get('name', ''))
    
    logger.info(f"  - 고유 태그: {len(all_tags):,}개")
    
    logger.info(f"\n💾 저장된 파일: {filename}")
    logger.info(f"📝 사용법: python misp_to_neo4j.py --input {filename} --clear")


if __name__ == "__main__":
    main()
