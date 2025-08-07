# 볼링 서비스 설정 완료 현황

## 🎳 볼링 스코어보드 인식 서비스

### 📋 **서비스 정보**
- **서비스명**: bowling
- **포트**: 8091
- **프로토콜**: HTTP (내부) → HTTPS (외부)
- **접근 URL**: `https://appcognito5.asuscomm.com/bowling/`

### 🔧 **서비스 관리**

#### **서비스 설치**
```bash
./bowling_service_install.sh
```

#### **서비스 제거**
```bash
./bowling_service_uninstall.sh
```

#### **서비스 상태 확인**
```bash
# 서비스 상태
launchctl list | grep bowling

# 포트 확인
lsof -i :8091

# 로그 확인
tail -f /Users/will/Library/Logs/bowling/bowling.out.log
```

### 📁 **관련 파일들**

#### **서비스 관리 스크립트**
- `bowling_service_install.sh`: 서비스 설치 및 등록
- `bowling_service_uninstall.sh`: 서비스 제거 및 중지

#### **애플리케이션 파일**
- `bowling/bowling.py`: FastAPI 메인 애플리케이션
- `bowling/image_analyzer.py`: 이미지 분석 및 OCR 처리
- `bowling/bowling.html`: 웹 인터페이스

#### **설정 파일**
- `requirements_pip.txt`: Python 패키지 목록
- `subdomain-proxy.conf`: Nginx 프록시 설정 (삭제됨)

### ⚙️ **기술 스택**

#### **백엔드**
- **FastAPI**: 웹 프레임워크
- **Uvicorn**: ASGI 서버 (reload=True)
- **PIL/Pillow**: 이미지 처리
- **OpenCV**: 이미지 전처리
- **Google Cloud Vision**: OCR 처리

#### **프론트엔드**
- **HTML/CSS/JavaScript**: 웹 인터페이스
- **드래그 앤 드롭**: 이미지 업로드
- **실시간 처리**: AJAX 기반 API 호출

### 🔄 **서비스 특징**

#### **자동 재시작**
- **LaunchAgent**: 시스템 재부팅 시 자동 시작
- **KeepAlive**: 프로세스 죽으면 자동 재시작
- **로그 관리**: 자동 로그 파일 생성

#### **개발 편의성**
- **Hot Reload**: 코드 변경 시 자동 재시작
- **환경 변수**: Google Cloud 인증 자동 로드
- **에러 처리**: 상세한 로그 및 에러 메시지

### 🛠️ **수정된 내용들**

#### **bowling.py**
- ✅ reload 옵션 추가: `uvicorn.run("bowling:app", host="0.0.0.0", port=8091, reload=True)`
- ✅ HTML 파일 경로 수정: `FileResponse("bowling/bowling.html")`

#### **image_analyzer.py**
- ✅ Google Cloud Vision ClientOptions 매개변수 수정
- ✅ 중복된 `default_scopes` 제거
- ✅ 지원되지 않는 매개변수들 제거

#### **라이브러리 설치**
- ✅ FastAPI, Uvicorn, Pydantic
- ✅ Pillow, OpenCV, NumPy
- ✅ Google Cloud Vision, python-dotenv
- ✅ python-multipart

### 🧪 **API 엔드포인트**

#### **기본 엔드포인트**
- `GET /`: 메인 웹페이지
- `GET /health`: 서버 상태 확인
- `GET /members`: 등록된 회원 목록

#### **OCR 엔드포인트**
- `POST /recognize-scoreboard`: 파일 업로드 OCR
- `POST /recognize-base64`: Base64 이미지 OCR

#### **관리 엔드포인트**
- `GET /test-saved-image/{filename}`: 저장된 이미지 테스트
- `GET /list-saved-images`: 저장된 이미지 목록

### 📊 **서비스 상태**

#### **현재 상태**
- ✅ **서비스 등록**: LaunchAgent로 등록됨
- ✅ **포트 실행**: 8091번 포트에서 실행 중
- ✅ **HTTPS 접근**: `/bowling/` 경로로 접근 가능
- ✅ **자동 재시작**: 프로세스 죽으면 자동 재시작

#### **로그 위치**
- **출력 로그**: `/Users/will/Library/Logs/bowling/bowling.out.log`
- **에러 로그**: `/Users/will/Library/Logs/bowling/bowling.err.log`

### 🚀 **최종 결과**
- **서비스**: 정상 실행 중 ✅
- **HTTPS**: 접근 가능 ✅
- **자동 재시작**: 설정됨 ✅
- **개발 환경**: Hot Reload 활성화 ✅
