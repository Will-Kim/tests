# 도메인 설정 완료 현황

## 📋 최종 적용된 설정

### 🎯 **도메인 정보**
- **메인 도메인**: `appcognito5.asuscomm.com`
- **서비스 분기**: 경로 기반 라우팅
- **프로토콜**: HTTPS (SSL 강제 리다이렉트)

### 🔧 **서비스 URL**
- **관리자 모드**: `https://appcognito5.asuscomm.com/nginxSettings/`
- **볼링 서비스**: `https://appcognito5.asuscomm.com/bowling/`
- **Ginie 서비스**: `https://appcognito5.asuscomm.com/ginie/` (외부 서비스 프록시)

### 🛡️ **SSL 인증서**
- **인증서 타입**: Let's Encrypt (무료)
- **만료일**: 2025-11-03 (88일 남음)
- **자동 갱신**: 매일 오후 12시 실행
- **갱신 스크립트**: `/usr/local/bin/renew-ssl.sh`

### ⚙️ **Nginx 설정**
- **설정 파일**: `/opt/homebrew/etc/nginx/sites-available/ssl-nginx.conf`
- **포트**: 80 (HTTP → HTTPS 리다이렉트), 443 (HTTPS)
- **라우팅**: 경로 기반 분기 (`/nginxSettings/` → `localhost:8090`, `/bowling/` → `localhost:8091`, `/ginie/` → 외부 서비스)
- **실행 권한**: **root 권한 필요** (포트 443 사용으로 인해 `sudo nginx` 명령어 사용)

### 🗄️ **Redis 기반 서비스 관리**
- **Redis 서버**: Homebrew로 설치, 자동 시작
- **데이터 저장**: 서비스 목록 영구 저장
- **기본 서비스**: nginxSettings, bowling 자동 등록
- **서버 재시작**: Redis에서 자동 복원

### 🔐 **보안 설정**
- **관리자 암호**: 환경 변수로 관리 (기본값: zaqwsx@1)
- **로그인 페이지**: 암호 표시 제거
- **HTTPS 강제**: 모든 HTTP 요청을 HTTPS로 리다이렉트
- **HSTS 헤더**: 보안 강화 헤더 설정

### 🔄 **자동 갱신 시스템**
```bash
# 자동 갱신 스크립트
sudo /usr/local/bin/renew-ssl.sh

# 수동 갱신
./manual_renew_ssl.sh

# 인증서 상태 확인
sudo certbot certificates
```

### 📊 **ASUS 공유기 설정**
```
규칙 1: HTTPS (SSL)
- 외부 포트: 443 → 내부: 192.168.50.97:443

규칙 2: HTTP (리다이렉트용)
- 외부 포트: 80 → 내부: 192.168.50.97:80
```

### 🧪 **테스트 명령**
```bash
# 로컬 테스트
curl -k https://localhost/bowling/health
curl -k https://localhost/nginxSettings/
curl -k https://localhost/ginie/

# 외부 테스트 (ASUS 설정 후)
curl https://appcognito5.asuscomm.com/bowling/health
curl https://appcognito5.asuscomm.com/nginxSettings/
curl https://appcognito5.asuscomm.com/ginie/

# Redis 서비스 목록 확인
redis-cli get nginx_settings:services

# Nginx 관리 명령어
sudo nginx -t                    # 설정 테스트
sudo nginx                       # nginx 시작
sudo nginx -s reload             # 설정 리로드
sudo nginx -s stop               # nginx 중지
```

### 📁 **관련 파일들**
- `ssl-bowling.conf`: Nginx SSL 설정
- `ssl_setup_letsencrypt.sh`: SSL 인증서 발급 스크립트
- `renew_ssl.sh`: 자동 갱신 스크립트
- `manual_renew_ssl.sh`: 수동 갱신 스크립트
- `nginxSettings/nginx_manager.py`: 관리자 모드 애플리케이션
- `requirements_pip.txt`: Python 패키지 목록

### ✅ **완료된 작업**
1. ✅ Let's Encrypt SSL 인증서 발급
2. ✅ HTTPS 강제 리다이렉트 설정
3. ✅ 경로 기반 서비스 분기 (`/nginxSettings/`, `/bowling/`, `/ginie/`)
4. ✅ 자동 갱신 시스템 구축
5. ✅ 보안 헤더 설정 (HSTS)
6. ✅ Redis 기반 서비스 관리 시스템 구축
7. ✅ 관리자 모드 보안 강화
8. ✅ 서비스 영구 저장 및 자동 복원
9. ✅ 외부 서비스 프록시 설정 (Ginie 서비스)
10. ✅ 정적 파일 프록시 및 HTML 내용 수정
11. ✅ **Ginie 서비스 외부 프록시 완전 구현** (2025-08-21)
12. ✅ **Nginx sub_filter를 통한 경로 자동 변환** (2025-08-21)
13. ✅ **압축 비활성화로 sub_filter 정상 작동** (2025-08-21)
14. ✅ **DNS 리졸버 설정으로 외부 도메인 해석** (2025-08-21)
15. ✅ **시스템 최적화 (Power Nap, Wake on Network)** (2025-08-21)

### 🚀 **최종 상태**
- **HTTPS**: 활성화 ✅
- **자동 갱신**: 설정됨 ✅
- **보안**: 강화됨 ✅
- **브라우저 경고**: 해결됨 ✅
- **서비스 관리**: Redis 기반 영구 저장 ✅
- **관리자 모드**: 보안 강화됨 ✅
- **외부 서비스 프록시**: Ginie 서비스 정상 작동 ✅
- **정적 파일**: CSS, JS, 이미지 정상 로드 ✅
- **경로 자동 변환**: sub_filter로 HTML/JS 내 절대 경로 자동 처리 ✅
- **압축 최적화**: gzip 비활성화로 sub_filter 정상 작동 ✅
- **DNS 해석**: 외부 도메인 정상 해석 ✅
- **시스템 최적화**: 슬립 모드에서도 네트워크 응답 ✅

### 📝 **최근 수정 사항 (2025-08-21)**

#### 1. Ginie 서비스 외부 프록시 완전 구현
- **외부 서비스**: `https://aedpxqkesydwjprw.tunnel.elice.io/`
- **프록시 경로**: `/ginie/`
- **기능**: AI 기반 스마트 회의록 생성기
- **문제 해결**: 502 Bad Gateway → 정상 작동

#### 2. Nginx sub_filter를 통한 경로 자동 변환
```nginx
# HTML/JS 내 절대 경로를 /ginie/ 경로로 자동 변환
sub_filter_types text/html text/css text/javascript application/javascript;
sub_filter_once off;
sub_filter 'href="/' 'href="/ginie/';
sub_filter 'src="/' 'src="/ginie/';
sub_filter 'url("/' 'url("/ginie/';
sub_filter 'action="/' 'action="/ginie/';
sub_filter 'data-url="/' 'data-url="/ginie/';
sub_filter 'fetch("/' 'fetch("/ginie/';
sub_filter 'get("/' 'get("/ginie/';
sub_filter 'post("/' 'post("/ginie/';
sub_filter '/api/' '/ginie/api/';
```

#### 3. 압축 비활성화로 sub_filter 정상 작동
- **문제**: 브라우저가 gzip 압축 요청 → sub_filter 작동 안함
- **해결**: `/ginie/` location 블록에서 압축 완전 비활성화
```nginx
gzip off;
gunzip off;
proxy_set_header Accept-Encoding "";
```

#### 4. DNS 리졸버 설정으로 외부 도메인 해석
- **문제**: `no resolver defined to resolve aedpxqkesydwjprw.tunnel.elice.io`
- **해결**: Google DNS 리졸버 추가
```nginx
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

#### 5. 시스템 최적화 (Power Nap, Wake on Network)
- **Power Nap**: `powernap 1` - 슬립 중에도 네트워크 응답
- **Wake on Network**: `womp 1` - 외부 요청 시 자동 깨어남
- **TCP Keep Alive**: `tcpkeepalive 1` - 연결 유지로 빠른 응답

### 🔧 **관리자 모드 사용법**
1. **접속**: `https://appcognito5.asuscomm.com/nginxSettings/`
2. **로그인**: 관리자 암호 입력
3. **서비스 관리**: 등록된 서비스 목록 확인 및 관리
4. **새 서비스 추가**: 웹 인터페이스를 통한 쉬운 서비스 등록
5. **서비스 삭제**: 불필요한 서비스 제거

### 📈 **확장성**
- **새 서비스 추가**: 웹 인터페이스에서 간편하게 추가
- **자동 Nginx 설정**: 서비스 추가 시 자동으로 Nginx 설정 업데이트
- **영구 저장**: Redis를 통한 서비스 정보 영구 보존
- **서버 재시작**: 자동으로 기존 서비스 복원
