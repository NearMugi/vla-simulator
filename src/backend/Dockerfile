FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# タイムゾーンの設定
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Python の出力をバッファリングしないように設定 (ログがすぐに表示されるようにする)
ENV PYTHONUNBUFFERED=1

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# 非ルートユーザーを作成
RUN useradd -m -u 1000 backenduser

WORKDIR /app

# pip のアップグレード
RUN python3.10 -m pip install --upgrade pip

COPY requirements.txt .
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R backenduser:backenduser /app

USER backenduser

CMD ["python3.10", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
