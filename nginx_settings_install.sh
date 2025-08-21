#!/bin/bash

# Nginx Settings 서비스 설치 스크립트
# 포트 8090에서 실행되는 FastAPI 애플리케이션

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="nginx-settings"
LOG_DIR="$HOME/Library/Logs/$SERVICE_NAME"
PLIST_FILE="$HOME/Library/LaunchAgents/com.$SERVICE_NAME.plist"

echo "🔧 Nginx Settings 서비스 설치를 시작합니다..."

# 로그 디렉토리 생성
echo "📁 로그 디렉토리를 생성합니다..."
mkdir -p "$LOG_DIR"

# LaunchAgent plist 파일 생성
echo "📝 LaunchAgent 설정 파일을 생성합니다..."
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.$SERVICE_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $SCRIPT_DIR/nginxSettings && /opt/homebrew/Caskroom/miniconda/base/envs/tests/bin/python nginx_manager.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR/nginxSettings</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>CONDA_DEFAULT_ENV</key>
        <string>tests</string>
    </dict>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/nginx-settings.out.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/nginx-settings.err.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF

# LaunchAgent 등록
echo "🚀 LaunchAgent를 등록합니다..."
launchctl load "$PLIST_FILE"

# 권한 설정
chmod 644 "$PLIST_FILE"

echo "✅ Nginx Settings 서비스가 성공적으로 설치되었습니다!"
echo ""
echo "📋 서비스 정보:"
echo "   - 서비스명: $SERVICE_NAME"
echo "   - 포트: 8090"
echo "   - 접속 URL: https://appcognito5.asuscomm.com/nginxSettings/"
echo "   - 로그 위치: $LOG_DIR"
echo ""
echo "🔧 관리 명령어:"
echo "   - 서비스 시작: launchctl start com.$SERVICE_NAME"
echo "   - 서비스 중지: launchctl stop com.$SERVICE_NAME"
echo "   - 서비스 제거: ./nginx_settings_uninstall.sh"
echo ""
echo "🌐 웹 브라우저에서 https://appcognito5.asuscomm.com/nginxSettings/ 에 접속하여 관리하세요."
echo "   초기 암호: zaqwsx@1"
