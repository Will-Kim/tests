#!/bin/bash

# 볼링 서비스 제거 및 중지 스크립트
# 사용법: ./bowling_service_uninstall.sh

SERVICE_NAME="bowling"
PLIST_PATH="$HOME/Library/LaunchAgents/com.user.bowling.plist"
LOG_DIR="/Users/will/Library/Logs/bowling"

echo "=== 볼링 서비스 제거 시작 ==="

# 1. 서비스 중지
echo "서비스 중지 중..."
if launchctl list | grep -q "com.user.bowling"; then
    launchctl unload "$PLIST_PATH"
    if [ $? -eq 0 ]; then
        echo "✅ 서비스 중지 성공!"
    else
        echo "❌ 서비스 중지 실패"
        exit 1
    fi
else
    echo "⚠️  서비스가 이미 중지되어 있습니다."
fi

# 2. 프로세스 강제 종료 (포트 8091 사용 중인 프로세스)
echo "포트 8091 프로세스 확인 및 종료 중..."
PIDS=$(lsof -ti:8091)
if [ ! -z "$PIDS" ]; then
    echo "포트 8091을 사용하는 프로세스 발견: $PIDS"
    kill -9 $PIDS
    echo "✅ 프로세스 강제 종료 완료"
else
    echo "포트 8091을 사용하는 프로세스가 없습니다."
fi

# 3. 설정 파일 제거
echo "설정 파일 제거 중..."
if [ -f "$PLIST_PATH" ]; then
    rm "$PLIST_PATH"
    echo "✅ 설정 파일 제거 완료: $PLIST_PATH"
else
    echo "⚠️  설정 파일이 이미 존재하지 않습니다: $PLIST_PATH"
fi

# 4. 로그 디렉토리 정리 (선택사항)
echo ""
read -p "로그 디렉토리도 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "$LOG_DIR" ]; then
        rm -rf "$LOG_DIR"
        echo "✅ 로그 디렉토리 삭제 완료: $LOG_DIR"
    else
        echo "⚠️  로그 디렉토리가 이미 존재하지 않습니다: $LOG_DIR"
    fi
else
    echo "로그 디렉토리는 유지됩니다: $LOG_DIR"
fi

# 5. 최종 상태 확인
echo ""
echo "최종 상태 확인 중..."
sleep 2

if launchctl list | grep -q "com.user.bowling"; then
    echo "❌ 서비스가 여전히 등록되어 있습니다."
else
    echo "✅ 서비스가 완전히 제거되었습니다."
fi

if lsof -i :8091 | grep -q "LISTEN"; then
    echo "❌ 포트 8091이 여전히 사용 중입니다."
else
    echo "✅ 포트 8091이 해제되었습니다."
fi

echo ""
echo "=== 제거 완료 ==="
echo "서비스가 완전히 제거되었습니다."
echo ""
echo "수동으로 프로세스를 확인하려면:"
echo "  포트 확인: lsof -i :8091"
echo "  프로세스 확인: ps aux | grep bowling"
echo "  서비스 확인: launchctl list | grep bowling"
