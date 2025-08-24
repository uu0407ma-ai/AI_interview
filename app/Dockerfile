# 使用官方 Python 镜像
FROM python:3.10-slim


# 安装 ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*


# 设置工作目录
WORKDIR /app


# 复制整个 app 目录（包含子目录和静态文件）
COPY . .


# 更新 pip
RUN pip install --upgrade pip

# 复制并安装依赖
RUN pip install --no-cache-dir -r requirements.txt 


# 暴露端口
EXPOSE 8000


# 运行 start.sh 脚本
RUN chmod +x start.sh
CMD ["./start.sh"]
