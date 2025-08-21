#!/bin/bash

# Nginx Settings 서비스 제거 스크립트

SERVICE_NAME="nginx-settings"
LOG_DIR="$HOME/Library/Logs/$SERVICE_NAME"
PLIST_FILE="$HOME/Library/LaunchAgents/com.$SERVICE_NAME.plist"

echo "🗑️ Nginx Settings 서비스 제거를 시작합니다..."

# 서비스 중지
echo "⏹️ 서비스를 중지합니다..."
launchctl stop "com.$SERVICE_NAME" 2>/dev/null || true

# LaunchAgent 제거
echo "📝 LaunchAgent를 제거합니다..."
launchctl unload "$PLIST_FILE" 2>/dev/null || true

# plist 파일 삭제
if [ -f "$PLIST_FILE" ]; then
    echo "🗂️ plist 파일을 삭제합니다..."
    rm "$PLIST_FILE"
fi

# 로그 디렉토리 삭제 (선택사항)
read -p "로그 디렉토리($LOG_DIR)도 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📁 로그 디렉토리를 삭제합니다..."
    rm -rf "$LOG_DIR"
fi

echo "✅ Nginx Settings 서비스가 성공적으로 제거되었습니다!"
echo ""
echo "📋 제거된 항목:"
echo "   - LaunchAgent: com.$SERVICE_NAME"
echo "   - plist 파일: $PLIST_FILE"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   - 로그 디렉토리: $LOG_DIR"
fi
