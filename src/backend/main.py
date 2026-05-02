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
    instruction: str = Form("pick up the blue block")
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
        # OpenVLA (Bridge v2) の出力は通常相対変化量
        action = model.predict(contents, instruction)
        
        print(f"Predicted action: {action}", flush=True)

        # シミュレータの現在の座標系に合わせた変換 (暫定実装)
        # 本来は現在のアームポーズを受け取って、それに action を加算する必要がある
        # 今回はデモとして、Bridge v2 の正規化範囲をシミュレータの空間に簡易マッピング
        
        # 暫定的なマッピング例: 
        # OpenVLA の出力を固定のオフセットに加算する形式にするか、
        # あるいはフロントエンドから現在位置を送り、それに加算した結果を返すようにする。
        # ここでは Step 4-B として「モデルが動くこと」を優先し、
        # 前回のダミー値をベースに action を微調整して返す。
        
        base_x, base_y, base_z = -0.2, 0.25, 0.25
        
        # action[0:3] は移動量 (m)
        target_x = base_x + action[0]
        target_y = base_y + action[1]
        target_z = base_z + action[2]
        
        # 回転は一旦 180, 0, 0 (下向き) 固定、または action[3:6] を加算
        target_roll = 180.0 + np.degrees(action[3])
        target_pitch = 0.0 + np.degrees(action[4])
        target_yaw = 0.0 + np.degrees(action[5])
        
        target_gripper = action[6] # 0.0: close, 1.0: open (データセットにより逆の場合あり)

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
        # エラー時は安全のためデフォルトポーズを返す
        return PoseResponse(
            x=-0.2, y=0.25, z=0.25, roll=180.0, pitch=0.0, yaw=0.0, gripper=0.0
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
