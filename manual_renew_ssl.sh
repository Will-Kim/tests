#!/bin/bash

# SSL 인증서 수동 갱신 스크립트
# 사용법: ./manual_renew_ssl.sh

echo "=== SSL 인증서 수동 갱신 시작 ==="

# 1. 현재 인증서 상태 확인
echo "현재 인증서 상태 확인 중..."
sudo certbot certificates

# 2. 갱신 가능한 인증서 확인
echo ""
echo "갱신 가능한 인증서 확인 중..."
sudo certbot renew --dry-run

if [ $? -eq 0 ]; then
    echo "✅ 갱신 가능한 인증서가 있습니다."
    
    # 3. 실제 갱신 실행
    echo "실제 갱신을 실행하시겠습니까? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "인증서 갱신 중..."
        sudo certbot renew
        
        if [ $? -eq 0 ]; then
            echo "✅ 인증서 갱신 성공!"
            
            # 4. Nginx 설정 재로드
            echo "Nginx 설정 재로드 중..."
            sudo nginx -t
            if [ $? -eq 0 ]; then
                sudo nginx -s reload
                echo "✅ Nginx 설정 재로드 완료"
            else
                echo "❌ Nginx 설정 오류"
                exit 1
            fi
        else
            echo "❌ 인증서 갱신 실패"
            exit 1
        fi
    else
        echo "갱신이 취소되었습니다."
    fi
else
    echo "❌ 갱신 가능한 인증서가 없습니다."
fi

# 5. 갱신 후 상태 확인
echo ""
echo "갱신 후 인증서 상태:"
sudo certbot certificates

echo ""
echo "=== 수동 갱신 완료 ==="
