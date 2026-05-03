import os
import sys
import traceback
import io
import cv2
import jax
import jax.numpy as jnp
import numpy as np
from PIL import Image

# GPU/Library settings
os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# 互換性パッチ: 新しい JAX で廃止された KeyArray を octo のために追加
if not hasattr(jax.random, "KeyArray"):
    jax.random.KeyArray = jax.Array

# 遅延インポート用
OctoModel = None

class OctoVLA:
    def __init__(self, model_id="hf://rail-berkeley/octo-small-1.5"):
        global OctoModel
        if OctoModel is None:
            try:
                from octo.model.octo_model import OctoModel
            except Exception as e:
                print(f"Error during octo import: {e}", flush=True)
                traceback.print_exc()
                raise e

        print(f"Loading Octo model: {model_id}...", flush=True)
        
        try:
            self.model = OctoModel.load_pretrained(model_id)
            self.rng = jax.random.PRNGKey(0)
            print("Octo model loaded successfully.", flush=True)

            # JITコンパイルと言語モデルのロードを事前に行う
            self._warmup()

        except Exception as e:
            print(f"Error loading Octo model: {e}", flush=True)
            raise e

    def _warmup(self):
        print("Starting model warm-up (JIT compilation)...", flush=True)
        try:
            dummy_image = np.zeros((256, 256, 3), dtype=np.uint8)
            _, img_encoded = cv2.imencode(".png", dummy_image)
            self.predict(img_encoded.tobytes(), "warmup")
            print("Model warm-up complete.", flush=True)
        except Exception as e:
            print(f"Warm-up failed (non-fatal): {e}", flush=True)

    def predict(self, image_bytes: bytes, instruction: str = "pick up the blue block"):
        # 画像の読み込みとリサイズ (Octoは256x256を期待)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)
        image_np = cv2.resize(image_np, (256, 256))
        
        # [batch, window, height, width, channels]
        # window=2 を作成（現在のフレームを2回重ねる）
        img_input = image_np[None, None, ...]
        img_input = np.repeat(img_input, 2, axis=1)
        
        observations = {
            "image_primary": img_input,
            "image_wrist": np.zeros((1, 2, 128, 128, 3), dtype=np.uint8),
            "timestep": np.array([[0, 1]], dtype=np.int32),
            "timestep_pad_mask": np.array([[True, True]], dtype=bool),
            "pad_mask_dict": {
                "image_primary": np.array([[True, True]], dtype=bool),
                "image_wrist": np.array([[False, False]], dtype=bool),
                "timestep": np.array([[True, True]], dtype=bool),
            }
        }
        
        task = self.model.create_tasks(texts=[instruction])
        
        self.rng, key = jax.random.split(self.rng)
        
        # 推論実行
        actions = self.model.sample_actions(observations, task, rng=key)
        
        # 最新のアクションを取得 (windowの最後のステップ)
        action = np.array(actions[0, -1]) 
        
        return action

vla_model = None

def get_model():
    global vla_model
    if vla_model is None:
        vla_model = OctoVLA()
    return vla_model
