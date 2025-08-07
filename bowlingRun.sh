#!/bin/bash

echo "기존 포트 8091을 사용하는 프로세스를 종료합니다..."

# 포트 8091을 사용하는 프로세스 찾기 및 종료
PIDS=$(lsof -ti:8091)
if [ ! -z "$PIDS" ]; then
    echo "포트 8091을 사용하는 프로세스: $PIDS"
    kill -9 $PIDS
    echo "프로세스가 종료되었습니다."
else
    echo "포트 8091을 사용하는 프로세스가 없습니다."
fi

# 잠시 대기
sleep 2

echo "bowling 폴더로 이동하여 서버를 시작합니다..."
cd bowling

# conda 환경 활성화 및 서버 시작
source ~/miniconda3/etc/profile.d/conda.sh
conda activate tests
python bowling.py 