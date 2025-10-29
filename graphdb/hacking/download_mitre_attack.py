"""
MITRE ATT&CK 데이터 다운로드
"""
import requests
import json
import os
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MitreAttackDownloader:
    """MITRE ATT&CK STIX 데이터 다운로더"""
    
    URLS = {
        "enterprise": "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json",
        "mobile": "https://raw.githubusercontent.com/mitre/cti/master/mobile-attack/mobile-attack.json",
        "ics": "https://raw.githubusercontent.com/mitre/cti/master/ics-attack/ics-attack.json",
    }
    
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def download(self, domain: str = "enterprise") -> str:
        """MITRE ATT&CK 데이터 다운로드"""
        if domain not in self.URLS:
            raise ValueError(f"지원하지 않는 도메인: {domain}. 사용 가능: {list(self.URLS.keys())}")
        
        url = self.URLS[domain]
        output_file = os.path.join(self.output_dir, f"{domain}-attack.json")
        
        logger.info(f"🔹 MITRE ATT&CK {domain} 다운로드 중...")
        logger.info(f"  URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 통계
            objects = data.get('objects', [])
            type_counts = {}
            for obj in objects:
                obj_type = obj.get('type', 'unknown')
                type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
            
            logger.info(f"✓ 다운로드 완료: {output_file}")
            logger.info(f"  - 총 객체 수: {len(objects):,}개")
            logger.info(f"  📊 타입별 통계:")
            for obj_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                logger.info(f"    - {obj_type}: {count}개")
            
            return output_file
            
        except requests.RequestException as e:
            logger.error(f"❌ 다운로드 실패: {e}")
            raise
    
    def download_all(self) -> Dict[str, str]:
        """모든 도메인 다운로드"""
        results = {}
        for domain in self.URLS.keys():
            try:
                output_file = self.download(domain)
                results[domain] = output_file
            except Exception as e:
                logger.warning(f"⚠️  {domain} 다운로드 실패: {e}")
        
        return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="MITRE ATT&CK 데이터 다운로드")
    parser.add_argument(
        "--domain",
        choices=["enterprise", "mobile", "ics", "all"],
        default="enterprise",
        help="다운로드할 도메인"
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="출력 디렉토리"
    )
    
    args = parser.parse_args()
    
    downloader = MitreAttackDownloader(output_dir=args.output_dir)
    
    if args.domain == "all":
        downloader.download_all()
    else:
        downloader.download(args.domain)


if __name__ == "__main__":
    main()

