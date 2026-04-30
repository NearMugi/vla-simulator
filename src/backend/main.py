from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

app = FastAPI(title="VLA Simulator Backend")

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
    # 今回は疎通確認のため、ダミーの目標座標を返す
    
    # 画像の読み込み（動作確認用）
    contents = await image.read()
    print(f"Received image: {len(contents)} bytes")

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
