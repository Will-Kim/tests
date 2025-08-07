#!/bin/bash

# SSL 인증서 설정 스크립트 (Let's Encrypt)
# 사용법: ./ssl_setup.sh

DOMAIN="bowling.appcognito5.asuscomm.com"
EMAIL="your-email@example.com"  # 실제 이메일로 변경 필요

echo "=== SSL 인증서 설정 시작 ==="
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

# 4. 인증서 발급
echo "SSL 인증서 발급 중..."
certbot certonly --standalone -d $DOMAIN --email $EMAIL --agree-tos --non-interactive

if [ $? -eq 0 ]; then
    echo "✅ SSL 인증서 발급 성공!"
else
    echo "❌ SSL 인증서 발급 실패"
    exit 1
fi

# 5. Nginx SSL 설정 생성
echo "Nginx SSL 설정 생성 중..."
SSL_CONF="/opt/homebrew/etc/nginx/sites-available/ssl-bowling.conf"

sudo tee $SSL_CONF > /dev/null << EOF
# SSL 설정 - bowling.appcognito5.asuscomm.com
server {
    listen 80;
    server_name bowling.appcognito5.asuscomm.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bowling.appcognito5.asuscomm.com;
    
    # SSL 인증서 설정
    ssl_certificate /etc/letsencrypt/live/bowling.appcognito5.asuscomm.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bowling.appcognito5.asuscomm.com/privkey.pem;
    
    # SSL 보안 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS 설정
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    location / {
        proxy_pass http://localhost:8091;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket 지원
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

echo "SSL 설정 파일 생성 완료: $SSL_CONF"

# 6. Nginx 설정 테스트 및 재시작
echo "Nginx 설정 테스트 중..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx 설정이 유효합니다."
    echo "Nginx 재시작 중..."
    brew services restart nginx
    echo "✅ Nginx가 SSL 설정으로 재시작되었습니다."
else
    echo "❌ Nginx 설정에 오류가 있습니다."
    exit 1
fi

# 7. 자동 갱신 설정
echo "자동 갱신 설정 중..."
RENEWAL_SCRIPT="/usr/local/bin/renew-ssl.sh"
sudo tee $RENEWAL_SCRIPT > /dev/null << 'EOF'
#!/bin/bash
# SSL 인증서 자동 갱신 스크립트

DOMAIN="bowling.appcognito5.asuscomm.com"

echo "$(date): SSL 인증서 갱신 시도" >> /var/log/ssl-renewal.log

certbot renew --quiet

if [ $? -eq 0 ]; then
    echo "$(date): SSL 인증서 갱신 성공" >> /var/log/ssl-renewal.log
    brew services reload nginx
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
echo "인증서 위치: /etc/letsencrypt/live/$DOMAIN/"
echo "갱신 스크립트: $RENEWAL_SCRIPT"
echo ""
echo "테스트 명령:"
echo "  curl -I https://$DOMAIN"
echo "  openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"
