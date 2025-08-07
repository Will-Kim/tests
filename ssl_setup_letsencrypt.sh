#!/bin/bash

# Let's Encrypt SSL 인증서 발급 스크립트
# 사용법: ./ssl_setup_letsencrypt.sh

DOMAIN="appcognito5.asuscomm.com"
EMAIL="your-email@example.com"  # 실제 이메일로 변경 필요

echo "=== Let's Encrypt SSL 인증서 발급 시작 ==="
echo "도메인: $DOMAIN"

# 1. certbot 설치 확인
if ! command -v certbot &> /dev/null; then
    echo "certbot 설치 중..."
    brew install certbot
else
    echo "✅ certbot이 이미 설치되어 있습니다."
fi

# 2. 도메인 확인
echo "도메인 연결 확인 중..."
if nslookup $DOMAIN | grep -q "NXDOMAIN"; then
    echo "❌ 도메인 $DOMAIN이 해석되지 않습니다."
    echo "ASUS 공유기에서 DDNS 설정을 확인해주세요."
    exit 1
else
    echo "✅ 도메인 $DOMAIN이 정상적으로 해석됩니다."
fi

# 3. 이메일 주소 입력
echo ""
read -p "Let's Encrypt 인증서 발급용 이메일 주소를 입력하세요: " EMAIL
if [ -z "$EMAIL" ]; then
    echo "❌ 이메일 주소가 필요합니다."
    exit 1
fi

# 4. 기존 자체 서명 인증서 백업
echo "기존 인증서 백업 중..."
sudo cp /opt/homebrew/etc/nginx/ssl/cert.pem /opt/homebrew/etc/nginx/ssl/cert.pem.backup
sudo cp /opt/homebrew/etc/nginx/ssl/key.pem /opt/homebrew/etc/nginx/ssl/key.pem.backup

# 5. 인증서 발급
echo "SSL 인증서 발급 중..."
sudo certbot certonly --standalone -d $DOMAIN --email $EMAIL --agree-tos --non-interactive

if [ $? -eq 0 ]; then
    echo "✅ SSL 인증서 발급 성공!"
else
    echo "❌ SSL 인증서 발급 실패"
    echo "기존 인증서로 복원 중..."
    sudo cp /opt/homebrew/etc/nginx/ssl/cert.pem.backup /opt/homebrew/etc/nginx/ssl/cert.pem
    sudo cp /opt/homebrew/etc/nginx/ssl/key.pem.backup /opt/homebrew/etc/nginx/ssl/key.pem
    exit 1
fi

# 6. SSL 설정 파일 업데이트
echo "SSL 설정 파일 업데이트 중..."
sudo sed -i '' 's|# ssl_certificate /etc/letsencrypt/live/appcognito5.asuscomm.com/fullchain.pem;|ssl_certificate /etc/letsencrypt/live/appcognito5.asuscomm.com/fullchain.pem;|' /opt/homebrew/etc/nginx/sites-available/ssl-bowling.conf
sudo sed -i '' 's|# ssl_certificate_key /etc/letsencrypt/live/appcognito5.asuscomm.com/privkey.pem;|ssl_certificate_key /etc/letsencrypt/live/appcognito5.asuscomm.com/privkey.pem;|' /opt/homebrew/etc/nginx/sites-available/ssl-bowling.conf
sudo sed -i '' 's|ssl_certificate /opt/homebrew/etc/nginx/ssl/cert.pem;|# ssl_certificate /opt/homebrew/etc/nginx/ssl/cert.pem;|' /opt/homebrew/etc/nginx/sites-available/ssl-bowling.conf
sudo sed -i '' 's|ssl_certificate_key /opt/homebrew/etc/nginx/ssl/key.pem;|# ssl_certificate_key /opt/homebrew/etc/nginx/ssl/key.pem;|' /opt/homebrew/etc/nginx/sites-available/ssl-bowling.conf

# 7. Nginx 설정 테스트 및 재시작
echo "Nginx 설정 테스트 중..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx 설정이 유효합니다."
    echo "Nginx 재시작 중..."
    sudo nginx -s reload
    echo "✅ Nginx가 SSL 설정으로 재시작되었습니다."
else
    echo "❌ Nginx 설정에 오류가 있습니다."
    exit 1
fi

# 8. 자동 갱신 설정
echo "자동 갱신 설정 중..."
RENEWAL_SCRIPT="/usr/local/bin/renew-ssl.sh"
sudo tee $RENEWAL_SCRIPT > /dev/null << 'EOF'
#!/bin/bash
# SSL 인증서 자동 갱신 스크립트

DOMAIN="appcognito5.asuscomm.com"

echo "$(date): SSL 인증서 갱신 시도" >> /var/log/ssl-renewal.log

certbot renew --quiet

if [ $? -eq 0 ]; then
    echo "$(date): SSL 인증서 갱신 성공" >> /var/log/ssl-renewal.log
    sudo nginx -s reload
else
    echo "$(date): SSL 인증서 갱신 실패" >> /var/log/ssl-renewal.log
fi
EOF

sudo chmod +x $RENEWAL_SCRIPT

# crontab에 자동 갱신 작업 추가
(crontab -l 2>/dev/null; echo "0 12 * * * $RENEWAL_SCRIPT") | crontab -

echo "✅ 자동 갱신이 설정되었습니다. (매일 오후 12시)"

echo ""
echo "=== SSL 설정 완료 ==="
echo "도메인: https://$DOMAIN"
echo "볼링 서비스: https://$DOMAIN/bowling/"
echo "인증서 위치: /etc/letsencrypt/live/$DOMAIN/"
echo "갱신 스크립트: $RENEWAL_SCRIPT"
echo ""
echo "이제 브라우저에서 경고 없이 접근할 수 있습니다!"
