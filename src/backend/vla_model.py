import os
import sys

# GPUメモリの競合を防ぐための設定
os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import traceback

try:
    import ml_dtypes
    print(f"DEBUG: ml_dtypes version: {ml_dtypes.__version__}", flush=True)
    print(f"DEBUG: ml_dtypes file: {ml_dtypes.__file__}", flush=True)
    
    import jax
    print(f"DEBUG: jax version: {jax.__version__}", flush=True)
    print(f"DEBUG: jax devices: {jax.devices()}", flush=True)

    # 互換性パッチ: 新しい JAX で廃止された KeyArray を octo のために追加
    if not hasattr(jax.random, "KeyArray"):
        jax.random.KeyArray = jax.Array
        print("DEBUG: Patched jax.random.KeyArray with jax.Array", flush=True)
    
    # ml_dtypes の属性を全表示して確認（デバッグ用）
    # print(f"DEBUG: ml_dtypes attributes: {[a for a in dir(ml_dtypes) if 'float8' in a]}", flush=True)

except Exception as e:
    print(f"DEBUG: JAX/ml_dtypes setup failed: {e}", flush=True)
    traceback.print_exc()

import jax.numpy as jnp
import numpy as np
from PIL import Image
import io
import cv2

# 遅延インポート
OctoModel = None

class OctoVLA:
    def __init__(self, model_id="hf://rail-berkeley/octo-small-1.5"):
        global OctoModel
        if OctoModel is None:
            try:
                from octo.model.octo_model import OctoModel
            except Exception as e:
                print(f"Error during octo import: {e}", flush=True)
                traceback.print_exc() # 詳細なエラー箇所を表示
                raise e

        print(f"Loading Official Octo model: {model_id}...", flush=True)
        
        try:
            # 本家 Octo (JAX/Flax) のロード
            self.model = OctoModel.load_pretrained(model_id)
            self.rng = jax.random.PRNGKey(0)
            
            print("Official Octo model loaded successfully.", flush=True)

            # ウォームアップ (JITコンパイルと言語モデルのロードを事前に行う)
            self._warmup()

        except Exception as e:
            print(f"Error loading Octo model: {e}", flush=True)
            raise e

    def _warmup(self):
        print("Starting model warm-up (JIT compilation)...", flush=True)
        try:
            # ダミー画像（黒塗り）で一度推論を実行
            dummy_image = np.zeros((256, 256, 3), dtype=np.uint8)
            _, img_encoded = cv2.imencode(".png", dummy_image)
            self.predict(img_encoded.tobytes(), "warmup")
            print("Model warm-up complete.", flush=True)
        except Exception as e:
            print(f"Warm-up failed (non-fatal): {e}", flush=True)

    def predict(self, image_bytes: bytes, instruction: str = "pick up the blue block"):
        # 画像の読み込みとリサイズ (Octo は 256x256 を期待)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)
        image_np = cv2.resize(image_np, (256, 256))
        
        # [batch, window, height, width, channels]
        # モデルが window=2 を期待しているため、現在のフレームを2回重ねて入力
        img_input = image_np[None, None, ...] # (1, 1, 256, 256, 3)
        img_input = np.repeat(img_input, 2, axis=1) # (1, 2, 256, 256, 3)
        
        observations = {
            "image_primary": img_input,
            "image_wrist": np.zeros((1, 2, 128, 128, 3), dtype=np.uint8), # 手首カメラは 128x128 を期待
            "timestep": np.array([[0, 1]], dtype=np.int32),
            "timestep_pad_mask": np.array([[True, True]], dtype=bool),
            "pad_mask_dict": {
                "image_primary": np.array([[True, True]], dtype=bool),
                "image_wrist": np.array([[False, False]], dtype=bool), # 手首は無効化
                "timestep": np.array([[True, True]], dtype=bool),
            }
        }
        
        # タスク（命令）の作成
        task = self.model.create_tasks(texts=[instruction])
        
        # 推論実行
        self.rng, key = jax.random.split(self.rng)
        
        # actions: [batch, window, action_dim]
        actions = self.model.sample_actions(observations, task, rng=key)
        
        # 最新のアクションを取得 (windowの最後のステップ)
        action = np.array(actions[0, -1]) 
        
        return action

# シングルトン管理
vla_model = None

def get_model():
    global vla_model
    if vla_model is None:
        vla_model = OctoVLA()
    return vla_model
