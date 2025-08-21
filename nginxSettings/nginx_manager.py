#!/usr/bin/env python3
"""
Nginx Settings 관리 시스템
포트 8090에서 실행되는 FastAPI 애플리케이션
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import redis

app = FastAPI(title="Nginx Settings Manager", version="1.0.0")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 정적 파일 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# 설정 파일 경로
BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
SERVICES_FILE = BASE_DIR / "services.json"
NGINX_CONFIG_DIR = Path("/opt/homebrew/etc/nginx/sites-available")
NGINX_SITES_DIR = Path("/opt/homebrew/etc/nginx/sites-enabled")

# Redis 연결
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
SERVICES_KEY = "nginx_settings:services"

class Service(BaseModel):
    name: str
    localhost: str
    port: int
    url: str

def load_env():
    """환경 변수 로드"""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    return env_vars

def get_admin_password():
    """관리자 암호 반환"""
    env_vars = load_env()
    return env_vars.get('ADMIN_PASSWORD', 'zaqwsx@1')

def get_default_services() -> List[Service]:
    """기본 서비스 목록 반환"""
    return [
        Service(
            name="nginxSettings",
            localhost="localhost",
            port=8090,
            url="https://appcognito5.asuscomm.com/nginxSettings/"
        ),
        Service(
            name="bowling",
            localhost="localhost",
            port=8091,
            url="https://appcognito5.asuscomm.com/bowling/"
        )
    ]

def load_services() -> List[Service]:
    """Redis에서 서비스 목록 로드"""
    try:
        # Redis에서 서비스 목록 가져오기
        services_data = redis_client.get(SERVICES_KEY)
        if services_data:
            data = json.loads(services_data)
            return [Service(**service) for service in data]
        else:
            # Redis에 데이터가 없으면 기본 서비스들로 초기화
            default_services = get_default_services()
            save_services(default_services)
            return default_services
    except Exception as e:
        print(f"Redis 서비스 로드 오류: {e}")
        # Redis 오류 시 기본 서비스 반환
        return get_default_services()

def save_services(services: List[Service]):
    """Redis에 서비스 목록 저장"""
    try:
        services_data = json.dumps([service.dict() for service in services], ensure_ascii=False)
        redis_client.set(SERVICES_KEY, services_data)
        print(f"Redis에 {len(services)}개 서비스 저장됨")
    except Exception as e:
        print(f"Redis 서비스 저장 오류: {e}")

def create_nginx_config(service: Service):
    """Nginx 설정 파일 생성"""
    config_content = f"""server {{
    listen 80;
    server_name appcognito5.asuscomm.com;
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name appcognito5.asuscomm.com;

    ssl_certificate /etc/letsencrypt/live/appcognito5.asuscomm.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/appcognito5.asuscomm.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location /bowling/ {{
        proxy_pass http://localhost:8091/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    location /nginxSettings/ {{
        proxy_pass http://localhost:8090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    location /{service.name}/ {{
        proxy_pass http://{service.localhost}:{service.port}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    location / {{
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}
}}
"""
    
    config_file = NGINX_CONFIG_DIR / "ssl-bowling.conf"
    try:
        with open(config_file, 'w') as f:
            f.write(config_content)
        return True
    except Exception as e:
        print(f"Nginx 설정 파일 생성 오류: {e}")
        return False

def reload_nginx():
    """Nginx 재시작"""
    try:
        # Nginx 설정 테스트
        result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Nginx 설정 테스트 실패: {result.stderr}")
            return False
        
        # Nginx 재시작
        result = subprocess.run(['brew', 'services', 'restart', 'nginx'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Nginx 재시작 실패: {result.stderr}")
            return False
        
        return True
    except Exception as e:
        print(f"Nginx 재시작 오류: {e}")
        return False

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """메인 페이지 - 로그인 화면"""
    print("루트 페이지 요청 받음")
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(password: str = Form(...)):
    """로그인 처리"""
    print(f"로그인 요청 받음: password={password}")
    admin_password = get_admin_password()
    print(f"로그인 시도: 입력된 암호={password}, 저장된 암호={admin_password}")
    
    if password == admin_password:
        print("로그인 성공")
        return RedirectResponse(url="/nginxSettings/dashboard", status_code=302)
    else:
        print("로그인 실패")
        raise HTTPException(status_code=401, detail="잘못된 암호입니다.")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """대시보드 - 서비스 관리 화면"""
    print("대시보드 페이지 요청 받음")
    services = load_services()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "services": services
    })

@app.post("/add_service")
async def add_service(
    service_name: str = Form(...),
    localhost: str = Form(...),
    port: int = Form(...)
):
    """새 서비스 추가"""
    # 입력 검증
    if not service_name or not localhost or port <= 0:
        raise HTTPException(status_code=400, detail="잘못된 입력입니다.")
    
    # 서비스 URL 생성
    service_url = f"https://appcognito5.asuscomm.com/{service_name}/"
    
    # 새 서비스 생성
    new_service = Service(
        name=service_name,
        localhost=localhost,
        port=port,
        url=service_url
    )
    
    # 기존 서비스 목록에 추가
    services = load_services()
    services.append(new_service)
    save_services(services)
    
    # Nginx 설정 업데이트
    if create_nginx_config(new_service):
        if reload_nginx():
            return RedirectResponse(url="/nginxSettings/dashboard", status_code=302)
        else:
            raise HTTPException(status_code=500, detail="Nginx 재시작에 실패했습니다.")
    else:
        raise HTTPException(status_code=500, detail="Nginx 설정 생성에 실패했습니다.")

@app.delete("/delete_service/{service_name}")
async def delete_service(service_name: str):
    """서비스 삭제"""
    services = load_services()
    services = [s for s in services if s.name != service_name]
    save_services(services)
    
    # Nginx 설정 업데이트 (마지막 서비스 기준으로 재생성)
    if services:
        if create_nginx_config(services[-1]):
            reload_nginx()
    
    return {"message": "서비스가 삭제되었습니다."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("nginx_manager:app", host="0.0.0.0", port=8090, reload=True)
