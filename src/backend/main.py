from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import os
from datetime import datetime
from vla_model import get_model
import numpy as np
import torch

app = FastAPI(title="VLA Simulator Backend")

# デバッグ用画像の保存設定
SAVE_DEBUG_IMAGES = os.getenv("SAVE_DEBUG_IMAGES", "false").lower() == "true"
DEBUG_DIR = "debug_images"

if SAVE_DEBUG_IMAGES and not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

# CORS設定 (Vite Frontend からのアクセスを許可)
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

# モデルのロード状態
model_ready = False

@app.on_event("startup")
async def startup_event():
    global model_ready
    # 起動時にモデルのロードを開始
    print("Starting VLA model initialization...", flush=True)
    try:
        get_model()
        model_ready = True
        print("VLA model initialization complete.", flush=True)
    except Exception as e:
        print(f"Failed to initialize VLA model on startup: {e}", flush=True)

@app.get("/health")
async def health():
    return {
        "status": "ready" if model_ready else "loading",
        "gpu_available": torch.cuda.is_available(),
        "vram_gb": round(torch.cuda.memory_allocated() / 1024**3, 2) if torch.cuda.is_available() else 0
    }

@app.get("/")
async def root():
    return {"message": "VLA Backend is running"}

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
    contents = await image.read()
    
    if SAVE_DEBUG_IMAGES:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filepath = os.path.join(DEBUG_DIR, f"input_{timestamp}.png")
            with open(filepath, "wb") as f:
                f.write(contents)
            print(f"Saved debug image: {filepath}, Instruction: {instruction}")
        except Exception as e:
            print(f"Failed to save debug image: {e}")

    # モデルの取得と推論
    try:
        model = get_model()
        # action: [dx, dy, dz, droll, dpitch, dyaw, gripper]
        action = model.predict(contents, instruction)
        
        print(f"Predicted action delta: {action}", flush=True)

        # 現在の座標にモデルの出力を加算
        # Octo の出力 (dx, dy, dz) はメートル単位の相対変化量
        target_x = current_x + action[0]
        target_y = current_y + action[1]
        target_z = current_z + action[2]
        
        # 回転の変化量を加算 (ラジアン -> 度)
        target_roll = current_roll + np.degrees(action[3])
        target_pitch = current_pitch + np.degrees(action[4])
        target_yaw = current_yaw + np.degrees(action[5])
        
        # グリッパーの状態 (0.0 - 1.0)
        # モデルの出力をそのまま目標値として使用、または変化量として扱うかはデータセットに依存
        # ここでは Octo (Bridge v2) の慣習に従い、0.0 (閉) - 1.0 (開) の絶対目標値として扱う
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
        # エラー時は現在地を維持
        return PoseResponse(
            x=current_x, y=current_y, z=current_z, 
            roll=current_roll, pitch=current_pitch, yaw=current_yaw, 
            gripper=current_gripper
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
