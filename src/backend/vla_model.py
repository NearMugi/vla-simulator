import torch
from PIL import Image
import io
from transformers import AutoModelForVision2Seq, AutoProcessor, BitsAndBytesConfig

class OpenVLAModel:
    def __init__(self, model_id="openvla/openvla-7b"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading OpenVLA model: {model_id} on {self.device}...", flush=True)
        
        # 4-bit 量子化設定
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

        try:
            print("Downloading/Loading processor...", flush=True)
            self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
            
            print("Loading model onto GPU (this may take a few minutes)...", flush=True)
            self.model = AutoModelForVision2Seq.from_pretrained(
                model_id,
                quantization_config=quantization_config,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                device_map={"": 0}
            )
            print("Model loaded successfully.", flush=True)
            if torch.cuda.is_available():
                print(f"Memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB", flush=True)

        except Exception as e:
            print(f"Error loading model: {e}", flush=True)
            raise e

    def predict(self, image_bytes: bytes, instruction: str = "pick up the blue block"):
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # OpenVLA の入力プロンプト形式
        prompt = f"In: {instruction}\nOut:"
        
        # プロセッサで入力を準備
        inputs = self.processor(prompt, image, return_tensors="pt").to(self.device)
        
        # 推論実行
        with torch.no_grad():
            # action: [dx, dy, dz, droll, dpitch, dyaw, gripper]
            action = self.model.predict_action(inputs, unnorm_key="bridge_orig", do_sample=False)
        
        return action

# シングルトン的にモデルを管理
vla_model = None

def get_model():
    global vla_model
    if vla_model is None:
        vla_model = OpenVLAModel()
    return vla_model
