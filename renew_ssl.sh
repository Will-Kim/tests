#!/bin/bash

# SSL 인증서 자동 갱신 스크립트
# 매일 실행되어 인증서가 만료되기 전에 자동으로 갱신

DOMAIN="appcognito5.asuscomm.com"
LOG_FILE="/var/log/ssl-renewal.log"

echo "$(date): SSL 인증서 갱신 시도 시작" >> $LOG_FILE

# certbot 갱신 실행
sudo certbot renew --quiet --no-self-upgrade

if [ $? -eq 0 ]; then
    echo "$(date): SSL 인증서 갱신 성공" >> $LOG_FILE
    
    # Nginx 설정 재로드
    sudo nginx -t
    if [ $? -eq 0 ]; then
        sudo nginx -s reload
        echo "$(date): Nginx 설정 재로드 완료" >> $LOG_FILE
    else
        echo "$(date): Nginx 설정 오류 - 재로드 실패" >> $LOG_FILE
    fi
else
    echo "$(date): SSL 인증서 갱신 실패" >> $LOG_FILE
fi

# 인증서 만료일 확인
EXPIRY_DATE=$(sudo certbot certificates | grep "VALID:" | awk '{print $2}')
echo "$(date): 인증서 만료일: $EXPIRY_DATE" >> $LOG_FILE

# 로그 파일 크기 관리 (1MB 이상이면 압축)
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE") -gt 1048576 ]; then
    gzip -f "$LOG_FILE"
    echo "$(date): 로그 파일 압축 완료" >> "$LOG_FILE.1"
fi
