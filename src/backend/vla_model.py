import os
import sys

# GPUメモリの競合を防ぐための設定
os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"

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

        except Exception as e:
            print(f"Error loading Octo model: {e}", flush=True)
            raise e

    def predict(self, image_bytes: bytes, instruction: str = "pick up the blue block"):
        # 画像の読み込みとリサイズ (Octo は 224x224)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)
        image_np = cv2.resize(image_np, (224, 224))
        
        # [batch, window, height, width, channels]
        # JAX版 Octo は H, W, C の順を期待
        img_input = image_np[None, None, ...] # (1, 1, 224, 224, 3)
        
        observations = {
            "image_primary": img_input
        }
        
        # タスク（命令）の作成
        task = self.model.create_tasks(texts=[instruction])
        
        # 推論実行 (JAX PRNG を使用)
        self.rng, key = jax.random.split(self.rng)
        
        # actions: [batch, window, action_dim]
        # Octo-Small は非常に高速
        actions = self.model.sample_actions(observations, task, rng=key)
        
        # 最新のアクションを取得
        # アクション形式: [dx, dy, dz, droll, dpitch, dyaw, gripper]
        action = np.array(actions[0, 0]) 
        
        return action

# シングルトン管理
vla_model = None

def get_model():
    global vla_model
    if vla_model is None:
        vla_model = OctoVLA()
    return vla_model
