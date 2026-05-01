FROM python:3.10-slim

# タイムゾーンの設定
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 非ルートユーザーを作成
RUN useradd -m -u 1000 backenduser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R backenduser:backenduser /app

USER backenduser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
