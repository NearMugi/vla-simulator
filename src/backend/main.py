import os
import numpy as np
import jax
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from vla_model import get_model

app = FastAPI(title="VLA Simulator Backend")

# 環境変数
SAVE_DEBUG_IMAGES = os.getenv("SAVE_DEBUG_IMAGES", "false").lower() == "true"
DEBUG_DIR = "debug_images"

if SAVE_DEBUG_IMAGES and not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

DATASETS_DIR = "datasets"
os.makedirs(DATASETS_DIR, exist_ok=True)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PoseResponse(BaseModel):
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float
    gripper: float

# モデルの状態管理
# loading: 初期化中, ready: 利用可能, error: 初期化失敗
model_status = "loading"
executor = ThreadPoolExecutor(max_workers=1)

def initialize_model():
    global model_status
    print("Starting VLA model initialization (Background)...", flush=True)
    try:
        # get_model() 内で OctoVLA() が呼ばれ、その中で _warmup() も実行される
        get_model()
        model_status = "ready"
        print("VLA model initialization and warm-up complete.", flush=True)
    except Exception as e:
        print(f"Failed to initialize VLA model: {e}", flush=True)
        model_status = "error"

@app.on_event("startup")
async def startup_event():
    # サーバー起動を妨げないよう、バックグラウンドでロードを開始
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, initialize_model)

@app.get("/health")
async def health():
    try:
        gpu_available = len(jax.devices("gpu")) > 0
    except:
        gpu_available = False
        
    return {
        "status": model_status,
        "gpu_available": gpu_available,
        "backend": "jax"
    }

@app.get("/")
async def root():
    return {"message": "VLA Backend is running", "status": model_status}

@app.post("/predict", response_model=PoseResponse)
async def predict(
    image: UploadFile = File(...),
    instruction: str = Form("pick up the blue block"),
    current_x: float = Form(-0.2),
    current_y: float = Form(0.25),
    current_z: float = Form(0.25),
    current_roll: float = Form(180.0),
    current_pitch: float = Form(0.0),
    current_yaw: float = Form(0.0),
    current_gripper: float = Form(0.0)
):
    if model_status != "ready":
        # 準備ができていない場合は現在地を返す
        return PoseResponse(
            x=current_x, y=current_y, z=current_z, 
            roll=current_roll, pitch=current_pitch, yaw=current_yaw, 
            gripper=current_gripper
        )

    contents = await image.read()
    
    if SAVE_DEBUG_IMAGES:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filepath = os.path.join(DEBUG_DIR, f"input_{timestamp}.png")
            with open(filepath, "wb") as f:
                f.write(contents)
        except Exception as e:
            print(f"Failed to save debug image: {e}")

    try:
        model = get_model()
        action = model.predict(contents, instruction)
        
        target_x = current_x + action[0]
        target_y = current_y + action[1]
        target_z = current_z + action[2]
        
        target_roll = current_roll + np.degrees(action[3])
        target_pitch = current_pitch + np.degrees(action[4])
        target_yaw = current_yaw + np.degrees(action[5])
        
        target_gripper = action[6] 

        return PoseResponse(
            x=float(target_x),
            y=float(target_y),
            z=float(target_z),
            roll=float(target_roll),
            pitch=float(target_pitch),
            yaw=float(target_yaw),
            gripper=float(target_gripper)
        )
    except Exception as e:
        print(f"Inference error: {e}", flush=True)
        return PoseResponse(
            x=current_x, y=current_y, z=current_z, 
            roll=current_roll, pitch=current_pitch, yaw=current_yaw, 
            gripper=current_gripper
        )

@app.post("/save_step")
async def save_step(
    episode_id: str = Form(...),
    step_index: int = Form(...),
    image: UploadFile = File(...),
    instruction: str = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    z: float = Form(...),
    roll: float = Form(...),
    pitch: float = Form(...),
    yaw: float = Form(...),
    gripper: float = Form(...)
):
    episode_dir = os.path.join(DATASETS_DIR, episode_id)
    os.makedirs(episode_dir, exist_ok=True)
    
    # 画像の保存
    image_filename = f"step_{step_index:03d}.png"
    image_path = os.path.join(episode_dir, image_filename)
    contents = await image.read()
    with open(image_path, "wb") as f:
        f.write(contents)
        
    # アクションデータの保存
    metadata_filename = f"step_{step_index:03d}.json"
    metadata_path = os.path.join(episode_dir, metadata_filename)
    metadata = {
        "step_index": step_index,
        "instruction": instruction,
        "pose": {
            "x": x, "y": y, "z": z,
            "roll": roll, "pitch": pitch, "yaw": yaw,
            "gripper": gripper
        },
        "timestamp": datetime.now().isoformat()
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
        
    return {"status": "success", "episode_id": episode_id, "step_index": step_index}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
