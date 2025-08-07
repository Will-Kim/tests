#!/bin/bash

# 볼링 서비스 설치 및 등록 스크립트
# 사용법: ./bowling_service_install.sh

SERVICE_NAME="bowling"
SERVICE_DESCRIPTION="볼링 스코어보드 인식 서비스"
PYTHON_PATH="/opt/homebrew/Caskroom/miniconda/base/envs/tests/bin/python"
WORKING_DIR="/Users/will/github/tests"
SCRIPT_PATH="$WORKING_DIR/bowling/bowling.py"
LOG_DIR="/Users/will/Library/Logs/bowling"
PLIST_PATH="$HOME/Library/LaunchAgents/com.user.bowling.plist"

echo "=== 볼링 서비스 설치 시작 ==="

# 1. 로그 디렉토리 생성
echo "로그 디렉토리 생성 중..."
mkdir -p "$LOG_DIR"
echo "로그 디렉토리: $LOG_DIR"

# 2. LaunchAgent plist 파일 생성
echo "LaunchAgent 설정 파일 생성 중..."
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.bowling</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$SCRIPT_PATH</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$WORKING_DIR</string>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/bowling.out.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/bowling.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>GOOGLE_APPLICATION_CREDENTIALS</key>
        <string>/Users/will/github/myCV/bowling-project-436705-2c76e537e70d.json</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ProcessType</key>
    <string>Background</string>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF

echo "LaunchAgent 설정 파일 생성 완료: $PLIST_PATH"

# 3. 권한 설정
echo "권한 설정 중..."
chmod 644 "$PLIST_PATH"
echo "권한 설정 완료"

# 4. 서비스 등록
echo "서비스 등록 중..."
launchctl load "$PLIST_PATH"
if [ $? -eq 0 ]; then
    echo "✅ 서비스 등록 성공!"
else
    echo "❌ 서비스 등록 실패"
    exit 1
fi

# 5. 서비스 상태 확인
echo "서비스 상태 확인 중..."
sleep 2
if launchctl list | grep -q "com.user.bowling"; then
    echo "✅ 서비스가 정상적으로 등록되었습니다."
else
    echo "❌ 서비스 등록에 문제가 있습니다."
    exit 1
fi

# 6. 포트 확인
echo "포트 8091 확인 중..."
sleep 3
if lsof -i :8091 | grep -q "LISTEN"; then
    echo "✅ 서비스가 포트 8091에서 정상 실행 중입니다."
else
    echo "⚠️  서비스가 아직 포트 8091에서 실행되지 않았습니다. 잠시 후 다시 확인해주세요."
fi

echo ""
echo "=== 설치 완료 ==="
echo "서비스 이름: $SERVICE_NAME"
echo "설정 파일: $PLIST_PATH"
echo "로그 파일: $LOG_DIR/"
echo "작업 디렉토리: $WORKING_DIR"
echo "실행 명령: $PYTHON_PATH $SCRIPT_PATH"
echo ""
echo "서비스 관리 명령:"
echo "  시작: launchctl load $PLIST_PATH"
echo "  중지: launchctl unload $PLIST_PATH"
echo "  상태: launchctl list | grep bowling"
echo "  로그: tail -f $LOG_DIR/bowling.out.log"
echo ""
echo "서비스가 자동으로 시작되며, 시스템 재부팅 시에도 자동으로 실행됩니다."
