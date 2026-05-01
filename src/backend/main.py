from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import os
from datetime import datetime

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

@app.get("/")
async def root():
    return {"message": "VLA Backend is running"}

@app.post("/predict", response_model=PoseResponse)
async def predict(image: UploadFile = File(...)):
    # ここで画像を処理して VLA モデルに渡す予定
    contents = await image.read()
    
    if SAVE_DEBUG_IMAGES:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filepath = os.path.join(DEBUG_DIR, f"input_{timestamp}.png")
            with open(filepath, "wb") as f:
                f.write(contents)
            print(f"Saved debug image: {filepath}")
        except Exception as e:
            print(f"Failed to save debug image: {e}")

    # ダミーの推論結果 (四角柱付近を狙うポーズ)
    return PoseResponse(
        x=-0.2,
        y=0.25,
        z=0.25,
        roll=180.0,
        pitch=0.0,
        yaw=0.0,
        gripper=0.0
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
