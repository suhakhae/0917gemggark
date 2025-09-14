import requests
import os
import json
from typing import Dict, Optional, List
import time

API_ITEMS_URL = "https://developer-lostark.game.onstove.com/markets/items"
METADATA_FILE = "gem_metadata.json"

class LostArkAPI:
    """
    gem_metadata.json을 기반으로 로스트아크 API와 통신하여
    정확한 젬 시세를 가져오는 클래스. (로직 개선 버전)
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key cannot be empty.")
        self.headers = {
            "accept": "application/json",
            "authorization": f"bearer {api_key}",
            "content-type": "application/json",
        }
        # 메타데이터에서 우리가 찾아야 할 젬의 전체 이름 목록을 미리 만들어 둡니다.
        self.target_gem_names = self._get_target_names_from_metadata()

    def _get_target_names_from_metadata(self) -> set:
        """gem_metadata.json에서 타겟 젬의 전체 이름(set)을 로드합니다."""
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                return {gem['Name'] for gem in metadata}
        except FileNotFoundError:
            print(f"Error: {METADATA_FILE} not found. Run extract_gem_metadata.py first.")
            return set()

    # ===================================================================
    # *** 수정된 핵심 로직: 더 단순하고 직접적인 조회 방식 ***
    # ===================================================================
    def get_gem_prices(self) -> Dict[str, Optional[int]]:
        """
        '아크 그리드 재료' 카테고리의 모든 페이지를 순회하여,
        메타데이터에 명시된 18종 젬의 현재 시세를 직접 찾아 반환합니다.
        """
        if not self.target_gem_names:
            return {}

        # 결과를 저장할 딕셔너리를 타겟 젬 이름으로 미리 초기화
        prices = {name: None for name in self.target_gem_names}
        found_count = 0
        
        page_no = 1
        print("Fetching all pages from '아크 그리드 재료' category...")

        while True:
            print(f"  - Fetching page {page_no}...")
            payload = {
                "CategoryCode": 230000,
                "PageNo": page_no,
                "Sort": "GRADE",
                "SortCondition": "DESC",
            }

            try:
                response = requests.post(API_ITEMS_URL, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                if not data or not data.get("Items"):
                    print("  - No more items found. Stopping page scan.")
                    break

                # 페이지의 아이템들 중에서 우리가 찾는 젬이 있는지 확인
                for item in data["Items"]:
                    # API가 반환하는 이름은 등급이 포함되지 않음
                    item_name_from_api = item.get("Name")
                    item_grade_from_api = item.get("Grade")
                    
                    # 우리가 사용할 전체 이름 형식으로 재구성
                    full_name = f"{item_grade_from_api} 등급 {item_name_from_api}"

                    # 재구성한 이름이 우리의 타겟 목록에 있다면 가격을 저장
                    if full_name in self.target_gem_names:
                        prices[full_name] = item.get("CurrentMinPrice")
                        found_count += 1
                
                # 최적화: 만약 모든 젬을 찾았다면, 더 이상 페이지를 조회할 필요가 없음
                if found_count == len(self.target_gem_names):
                    print("  - Found all target gems. Stopping early.")
                    break
                
                page_no += 1
                time.sleep(0.5)
                if page_no > 20:
                    print("  - Reached max page limit (20).")
                    break
            
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page_no}: {e}")
                break
        
        print("Finished fetching gem prices.")
        return prices
    # ===================================================================

# --- (하단 if __name__ == "__main__": 부분은 이전과 동일) ---
if __name__ == "__main__":
    api_key = os.getenv("LOSTARK_API_KEY", "YOUR_API_KEY_HERE")
    if "YOUR_API_KEY_HERE" in api_key:
        print("Please set LOSTARK_API_KEY environment variable.")
    else:
        client = LostArkAPI(api_key=api_key)
        gem_prices = client.get_gem_prices()
        print("\n--- Fetched Gem Prices (Optimized Logic) ---")
        import pprint
        pprint.pprint(gem_prices)
