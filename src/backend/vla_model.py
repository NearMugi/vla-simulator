import torch
from PIL import Image
import io
from transformers import AutoModelForVision2Seq, AutoProcessor, BitsAndBytesConfig
import os

class OpenVLAModel:
    def __init__(self, model_id="openvla/openvla-7b"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading OpenVLA model (8-bit with CPU offload): {model_id}...", flush=True)

        # 8-bit 量子化と CPU オフロードの設定
        # 8-bit は 4-bit よりも CPU オフロードの挙動が安定しています
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_enable_fp32_cpu_offload=True
        )

        # GPUメモリの使用制限 (RTX 4060 8GB 用の調整)
        # 3.5GB はシステムで使用中のため、モデル用には 3.5GB 程度を割り当て、残りを CPU (RAM) へ逃がす
        max_memory = {0: "3.5GiB", "cpu": "16GiB"}

        try:
            print("Downloading/Loading processor...", flush=True)
            self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
            
            # オフロード用のフォルダを作成
            if not os.path.exists("offload"):
                os.makedirs("offload")

            print("Loading model (this will use both GPU and System RAM)...", flush=True)
            self.model = AutoModelForVision2Seq.from_pretrained(
                model_id,
                quantization_config=quantization_config,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                device_map="auto",
                max_memory=max_memory,
                offload_folder="offload"
            )
            print("Model loaded successfully using 8-bit and CPU offload.", flush=True)
            if torch.cuda.is_available():
                print(f"Current VRAM allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB", flush=True)

        except Exception as e:
            print(f"Error loading model: {e}", flush=True)
            raise e

    def predict(self, image_bytes: bytes, instruction: str = "pick up the blue block"):
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        prompt = f"In: {instruction}\nOut:"
        inputs = self.processor(prompt, image, return_tensors="pt").to(self.device)
        
        # 8-bit モデルの計算精度に合わせて入力を Float16 にキャスト
        for k, v in inputs.items():
            if torch.is_floating_point(v):
                inputs[k] = v.to(torch.float16)
        
        with torch.no_grad():
            # action: [dx, dy, dz, droll, dpitch, dyaw, gripper]
            # **inputs とすることで、辞書の内容を引数として展開して渡します
            action = self.model.predict_action(**inputs, unnorm_key="bridge_orig", do_sample=False)
        
        return action

# シングルトン的にモデルを管理
vla_model = None

def get_model():
    global vla_model
    if vla_model is None:
        vla_model = OpenVLAModel()
    return vla_model
