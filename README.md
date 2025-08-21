# Nginx Settings Manager & Service Proxy

## 프로젝트 개요
Nginx를 사용한 다중 서비스 프록시 및 관리 시스템입니다. 외부 서비스들을 단일 도메인으로 통합 관리할 수 있습니다.

## 주요 기능
- **Nginx Settings Manager**: 웹 기반 Nginx 설정 관리
- **Bowling Service**: 볼링 관련 서비스
- **Ginie Service**: 외부 회의록 생성 서비스 프록시
- **Redis 기반 서비스 관리**: 서비스 목록 영구 저장
- **SSL/HTTPS 지원**: Let's Encrypt 인증서 사용

## 서비스 URL
- **관리자 모드**: `https://appcognito5.asuscomm.com/nginxSettings/`
- **볼링 서비스**: `https://appcognito5.asuscomm.com/bowling/`
- **Ginie 서비스**: `https://appcognito5.asuscomm.com/ginie/`

## 최근 수정 사항 (2025-08-21)

### 1. Ginie 서비스 외부 프록시 추가
- **외부 서비스**: `https://aedpxqkesydwjprw.tunnel.elice.io/`
- **프록시 경로**: `/ginie/`
- **기능**: AI 기반 스마트 회의록 생성기

### 2. Nginx 설정 최적화
- **DNS 리졸버 추가**: `resolver 8.8.8.8 8.8.4.4 valid=300s;`
- **압축 비활성화**: sub_filter 작동을 위한 gzip off 설정
- **경로 변환**: HTML/JS 내 절대 경로를 `/ginie/` 경로로 자동 변환

### 3. sub_filter 설정 상세
```nginx
# HTML 내의 절대 경로를 /ginie/ 경로로 변환
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

### 4. 보안 강화
- **관리자 암호 숨김**: 로그인 페이지에서 기본 암호 제거
- **Redis 기반 서비스 관리**: 서버 재시작 후에도 서비스 목록 유지

### 5. 시스템 최적화
- **Power Nap 활성화**: 슬립 모드에서도 네트워크 응답
- **Wake on Network**: 외부 요청 시 자동 깨어남
- **TCP Keep Alive**: 연결 유지로 빠른 응답

## 기술 스택
- **Nginx**: Reverse Proxy & SSL
- **FastAPI**: Nginx Settings Manager
- **Redis**: 서비스 목록 영구 저장
- **Python**: 백엔드 서비스
- **Let's Encrypt**: SSL 인증서

## 설치 및 실행
```bash
# Redis 시작
brew services start redis

# Nginx 시작 (root 권한 필요)
sudo nginx

# Nginx Settings Manager 시작
cd nginxSettings
python nginx_manager.py
```

## 주의사항
- Nginx는 포트 443 사용으로 인해 root 권한 필요
- SSL 인증서는 Let's Encrypt 사용
- 외부 서비스 프록시 시 DNS 리졸버 설정 필수
