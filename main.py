# main.py (젬 시세 API 추가 버전)
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os

import logging
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import uuid
import asyncio
import json

from lostark_api import LostArkAPI
from validator import check_feasibility
from final_optimizer import FinalOptimizer

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("gemggark_api.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

task_manager: Dict[str, Dict] = {}

class HeldGem(BaseModel):
    name: str = Field(...)
    core_point: int = Field(..., ge=1, le=5)
    efficiency: int = Field(..., ge=1, le=5)
class OptimizeRequest(BaseModel):
    cores: Dict[str, List[str]] = Field(...)
    held_gems: List[HeldGem] = Field([])
    simulations_per_gem: int = Field(default=100, ge=50, le=1000)
    blue_crystal_price: int = Field(...)

app = FastAPI(title="Gemggark API", version="1.5.0") # 버전 업데이트
origins = ["http://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

api_client: LostArkAPI
final_optimizer: FinalOptimizer

def run_optimization_task(task_id: str, request: OptimizeRequest):
    # ... (기존과 동일) ...
    try:
        logger.info(f"Task {task_id}: Starting optimization.")
        task_manager[task_id] = {"status": "processing", "progress": 0, "message": "최신 젬 시세를 불러오는 중입니다...", "result": None}
        current_gem_prices = api_client.get_gem_prices()
        crystal_gold_price = request.blue_crystal_price
        core_groups = {"질서": request.cores.get("질서", []), "혼돈": request.cores.get("혼돈", [])}
        held_gem_groups = {"질서": [], "혼돈": []}
        for gem in request.held_gems:
            if "질서" in gem.name: held_gem_groups["질서"].append(gem.dict())
            elif "혼돈" in gem.name: held_gem_groups["혼돈"].append(gem.dict())
        final_result = {"total_cost": 0, "strategy_details": {}}
        total_cores = len([c for c_list in core_groups.values() for c in c_list if c])
        processed_cores = 0
        for core_type in ["질서", "혼돈"]:
            if not core_groups[core_type]: continue
            task_manager[task_id]["message"] = f"{core_type} 그룹 보유 젬 구성을 검증하는 중입니다..."
            is_feasible, remaining_info = check_feasibility({core_type: core_groups[core_type]}, held_gem_groups[core_type])
            if not is_feasible: raise ValueError(f"{core_type} 그룹 보유 젬 구성 실현 불가: {remaining_info.get('reason')}")
            if any(core['remaining_slots'] > 0 for core in remaining_info):
                task_manager[task_id]["message"] = f"{core_type} 코어 최적화 전략을 AI가 시뮬레이션 중입니다..."
                best_strategy = final_optimizer.find_best_strategy(remaining_info, current_gem_prices, crystal_gold_price, request.simulations_per_gem)
                final_result["strategy_details"][core_type] = best_strategy
                final_result["total_cost"] += best_strategy.get("total_cost", 0)
            processed_cores += len(core_groups[core_type])
            task_manager[task_id]["progress"] = int((processed_cores / total_cores) * 100) if total_cores > 0 else 100
        task_manager[task_id] = {"status": "completed", "progress": 100, "message": "최적화 완료!", "result": final_result}
        logger.info(f"Task {task_id}: Optimization completed successfully.")
    except Exception as e:
        logger.error(f"Task {task_id}: An error occurred during optimization: {e}", exc_info=True)
        task_manager[task_id] = {"status": "failed", "progress": 100, "message": f"오류 발생: {e}", "result": None}

@app.on_event("startup")
def startup_event():
    global api_client, final_optimizer
    api_key = os.getenv("LOSTARK_API_KEY")
    if not api_key: raise RuntimeError("LOSTARK_API_KEY environment variable not set.")
    api_client = LostArkAPI(api_key=api_key)
    final_optimizer = FinalOptimizer(models_dir='./models/')

@app.post("/optimize")
async def optimize_gems_async(request: OptimizeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    task_manager[task_id] = {"status": "pending", "progress": 0, "message": "작업을 준비 중입니다...", "result": None}
    background_tasks.add_task(run_optimization_task, task_id, request)
    logger.info(f"Task {task_id} has been created and is running in the background.")
    return {"task_id": task_id}
    
# <<< 1. 새로운 젬 시세 API 엔드포인트 추가
@app.get("/markets/gems")
async def get_gem_market_prices():
    """
    현재 18종 젬의 실시간 시세를 조회하여 반환합니다.
    """
    try:
        logger.info("Request received for /markets/gems")
        gem_prices = api_client.get_gem_prices()
        return gem_prices
    except Exception as e:
        logger.error(f"Failed to fetch gem prices from Lost Ark API: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="로스트아크 API 서버로부터 시세 정보를 가져오는 데 실패했습니다.")


@app.websocket("/ws/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    # ... (기존과 동일) ...
    await websocket.accept()
    logger.info(f"WebSocket connection established for task {task_id}")
    try:
        while True:
            task_status = task_manager.get(task_id)
            if task_status:
                await websocket.send_json(task_status)
                if task_status["status"] in ["completed", "failed"]:
                    logger.info(f"Task {task_id} finished. Closing WebSocket.")
                    del task_manager[task_id]
                    break
            else:
                await websocket.send_json({"status": "not_found", "message": "작업을 찾을 수 없습니다."})
                break
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.warning(f"WebSocket connection closed for task {task_id}")
    except Exception as e:
        logger.error(f"An error occurred in WebSocket for task {task_id}: {e}")
    finally:
        if task_id in task_manager:
            del task_manager[task_id]