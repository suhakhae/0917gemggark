import requests
import os
import json
from typing import List, Dict, Optional
import time

API_ITEMS_URL = "https://developer-lostark.game.onstove.com/markets/items"

# ================================================================================================================
# *** 해당 코드는 로스트아크 API 의 자료구조를 파악하기 위해 작성된 파일로 실제 서비스와 관련이 없습니다 참고 바랍니다 ***
# ================================================================================================================


# 실제 데이터 분석을 통해 확인된 정확한 카테고리 코드
GEM_CATEGORY_CODE = 230000  # '강화 재료' > '아크 그리드 재료'

# ===================================================================
# *** 수정된 핵심 상수: 실제 API가 반환하는 이름과 등급 ***
# ===================================================================
TARGET_GEM_NAMES = {"혼돈의 젬 : 왜곡", "혼돈의 젬 : 붕괴", "혼돈의 젬 : 침식", "질서의 젬 : 불변", "질서의 젬 : 견고", "질서의 젬 : 안정"}
TARGET_GEM_GRADES = {"고급", "희귀", "영웅"}
# ===================================================================


def extract_metadata(api_key: str) -> None:
    """
    페이지네이션을 적용하고, '이름'과 '등급'을 개별적으로 필터링하여,
    필요한 18종 젬의 메타데이터를 추출합니다.
    """
    headers = {
        "accept": "application/json",
        "authorization": f"bearer {api_key}",
        "content-type": "application/json",
    }

    print(f"Searching for all pages of gems under category '아크 그리드 재료' (Code: {GEM_CATEGORY_CODE})...")
    
    found_gems = []
    page_no = 1
    
    while True:
        print(f"Fetching page {page_no}...")
        
        search_payload = { "CategoryCode": GEM_CATEGORY_CODE, "PageNo": page_no }

        try:
            response = requests.post(API_ITEMS_URL, headers=headers, json=search_payload)
            response.raise_for_status()
            data = response.json()
            
            if not data or not data.get("Items"):
                print("No more items found. Stopping.")
                break

            for item in data["Items"]:
                item_name = item.get("Name")
                item_grade = item.get("Grade")
                
                # ===================================================================
                # *** 수정된 핵심 로직: 이름과 등급을 별도로, 정확하게 검사 ***
                # ===================================================================
                if item_name in TARGET_GEM_NAMES and item_grade in TARGET_GEM_GRADES:
                    # 사용자가 보기 편한 전체 이름 생성
                    full_name = f"{item_grade} 등급 {item_name}"
                    metadata = {
                        "Id": item.get("Id"),
                        "Name": full_name,
                        "Grade": item_grade,
                    }
                    if all(metadata.values()):
                        found_gems.append(metadata)
                # ===================================================================
            
            page_no += 1
            time.sleep(0.5)

            if page_no > 20: # 페이지 제한을 넉넉하게 늘림
                print("Reached max page limit (20). Stopping.")
                break

        except requests.exceptions.RequestException as e:
            print(f"An error occurred during item search on page {page_no}: {e}")
            break
    
    # 중복 제거: 이제 'Name' 필드는 "영웅 등급 안정의 젬"과 같이 고유하므로,
    # 이 값을 키로 사용하여 중복을 제거할 수 있습니다.
    unique_gems = list({gem['Name']: gem for gem in found_gems}.values())
    
    if len(unique_gems) == 0:
         print("Fatal: Could not find any of the target gems in the API response.")
         return
    
    print(f"\nFound {len(unique_gems)} unique target gems across all pages.")

    with open("gem_metadata.json", "w", encoding="utf-8") as f:
        json.dump(unique_gems, f, ensure_ascii=False, indent=2)
    
    print("Successfully saved metadata to gem_metadata.json")

if __name__ == "__main__":
    api_key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IktYMk40TkRDSTJ5NTA5NWpjTWk5TllqY2lyZyIsImtpZCI6IktYMk40TkRDSTJ5NTA5NWpjTWk5TllqY2lyZyJ9.eyJpc3MiOiJodHRwczovL2x1ZHkuZ2FtZS5vbnN0b3ZlLmNvbSIsImF1ZCI6Imh0dHBzOi8vbHVkeS5nYW1lLm9uc3RvdmUuY29tL3Jlc291cmNlcyIsImNsaWVudF9pZCI6IjEwMDAwMDAwMDA0MjIxNDAifQ.cFbYLDgW2ZxFXBhY71_v2eEkKwgf0I1-2NDZhzdgBiEl9hyTgLjRMCQaSFkZdNnKFK0xe4rGaQe_-nVzbmxyXEHJTVijwEuADOaD-jv5wgSylpZNYqrjH11vmUtPLSWmU7Rel2tXOv9LCs_nd6fCrkDQsyV7ekiM_SyG0gCcB98v-BGfcbPo2Ds-xD5C-_i0BLg7DYHbRw5n1s1Z5lAgv2mP6o0rpd6bSacJUyhwB7UJhbVL4qNcborgKBSJROLOJl9nKsEUTosvARxT0H3boojuZBoqPXy-Uohog2jWfYYXP8uPpwdHgM9ZnBkw-EeKZW3pkm6YHe5dcqRJnnHg6A"

    if "여기에_당신의_API_키를_붙여넣으세요" in api_key:
        print("!!! 오류: 스크립트의 api_key 변수에 실제 API 키를 입력해야 합니다. !!!")
    else:

        extract_metadata(api_key=api_key)

