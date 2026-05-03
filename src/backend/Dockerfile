FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# タイムゾーンの設定
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Python の出力をバッファリングしないように設定
ENV PYTHONUNBUFFERED=1

# システム依存関係のインストール (OpenCV用のライブラリを含む)
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 非ルートユーザーを作成
RUN useradd -m -u 1000 backenduser

WORKDIR /app

# pip のアップグレード
RUN python3.10 -m pip install --upgrade pip

# requirements.txt のコピーとインストール
COPY requirements.txt .
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt

# dlimp (Octo の依存関係) をインストール
RUN git clone https://github.com/kvablack/dlimp.git /tmp/dlimp && \
    cd /tmp/dlimp && \
    python3.10 -m pip install . && \
    rm -rf /tmp/dlimp

# Octo 公式リポジトリをクローンして確実にインストール
RUN git clone https://github.com/octo-models/octo.git /tmp/octo && \
    cd /tmp/octo && \
    python3.10 -m pip install . && \
    rm -rf /tmp/octo

# 1. 既存の関連パッケージを物理削除
RUN rm -rf /usr/local/lib/python3.10/dist-packages/ml_dtypes* && \
    rm -rf /usr/local/lib/python3.10/dist-packages/jax* && \
    rm -rf /usr/local/lib/python3.10/dist-packages/tensorstore* && \
    rm -rf /usr/local/lib/python3.10/dist-packages/orbax*

# 2. 整合性のある安定バージョンセットをクリーンインストール
RUN python3.10 -m pip install --no-cache-dir --force-reinstall \
    "ml_dtypes==0.4.0" \
    "jax==0.4.28" \
    "jaxlib==0.4.28+cuda12.cudnn89" -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html \
    "orbax-checkpoint==0.4.4" \
    "transformers==4.40.2" \
    "tensorflow-cpu==2.18.0" \
    "tensorflow-probability==0.25.0" \
    "tf-keras>=2.18.0" \
    "numpy<2.0"

# 3. ビルド時にインストールされた場所を確認（デバッグ用）
RUN python3.10 -c "import ml_dtypes; print(f'INSTALLED ML_DTYPES VERSION: {ml_dtypes.__version__}'); print(f'INSTALLED PATH: {ml_dtypes.__file__}')"

# アプリケーションコードのコピー
COPY . .
RUN chown -R backenduser:backenduser /app

USER backenduser

CMD ["python3.10", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]
