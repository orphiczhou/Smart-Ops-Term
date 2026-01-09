#!/bin/bash
# Smart-Ops-Term 启动脚本 (Linux/Mac)

echo "Starting Smart-Ops-Term..."
echo

cd "$(dirname "$0")"
python src/main.py
