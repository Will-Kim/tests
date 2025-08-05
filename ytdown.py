#!/usr/bin/env python3
"""
YouTube 동영상 다운로더
AquaNote 테스트용 YouTube 동영상을 MP4로 다운로드
"""

import yt_dlp
import os
import sys
from pathlib import Path

def download_youtube_video(url: str, output_dir: str = "test_videos") -> str:
    """
    YouTube 동영상을 MP4로 다운로드
    
    Args:
        url: YouTube URL
        output_dir: 저장할 디렉토리
        
    Returns:
        다운로드된 파일 경로
    """
    # 출력 디렉토리 생성
    Path(output_dir).mkdir(exist_ok=True)
    
    # yt-dlp 옵션 설정
    ydl_opts = {
        'format': 'best[ext=mp4]/best',  # 최고 품질 MP4 우선
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',  # 파일명 형식
        'writesubtitles': False,  # 자막 다운로드 안함
        'writeautomaticsub': False,  # 자동 자막 다운로드 안함
        'ignoreerrors': False,
        'no_warnings': False,
        'quiet': False,
        'verbose': True,
        'progress_hooks': [progress_hook],  # 진행률 표시
    }
    
    try:
        print(f"🎬 YouTube 동영상 다운로드 시작: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 동영상 정보 가져오기
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'unknown')
            duration = info.get('duration', 0)
            
            print(f"📹 제목: {title}")
            print(f"⏱️  길이: {duration//60}분 {duration%60}초")
            
            # 다운로드 실행
            ydl.download([url])
            
            # 다운로드된 파일 경로 찾기
            downloaded_file = find_downloaded_file(output_dir, title)
            
            if downloaded_file:
                print(f"✅ 다운로드 완료: {downloaded_file}")
                return downloaded_file
            else:
                print("❌ 다운로드된 파일을 찾을 수 없습니다.")
                return None
                
    except Exception as e:
        print(f"❌ 다운로드 실패: {str(e)}")
        return None

def progress_hook(d):
    """다운로드 진행률 표시"""
    if d['status'] == 'downloading':
        if 'total_bytes' in d and d['total_bytes']:
            percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            print(f"\r📥 다운로드 중... {percent:.1f}%", end='', flush=True)
    elif d['status'] == 'finished':
        print(f"\n✅ 다운로드 완료: {d['filename']}")

def find_downloaded_file(directory: str, title: str) -> str:
    """다운로드된 파일 찾기"""
    try:
        for file in Path(directory).glob("*.mp4"):
            if title.lower() in file.name.lower():
                return str(file)
        # 제목으로 찾지 못하면 가장 최근 파일 반환
        files = list(Path(directory).glob("*.mp4"))
        if files:
            return str(max(files, key=lambda x: x.stat().st_mtime))
    except Exception as e:
        print(f"파일 찾기 오류: {e}")
    return None

def main():
    """메인 함수"""
    print("🎬 YouTube 동영상 다운로더")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("사용법: python youtube_downloader.py <YouTube_URL>")
        print("예시: python youtube_downloader.py https://www.youtube.com/watch?v=VIDEO_ID")
        return
    
    url = sys.argv[1]
    
    # URL 유효성 검사
    if "youtube.com" not in url and "youtu.be" not in url:
        print("❌ 유효한 YouTube URL이 아닙니다.")
        return
    
    # 다운로드 실행
    downloaded_file = download_youtube_video(url)
    
    if downloaded_file:
        print(f"\n🎉 다운로드 성공!")
        print(f"📁 파일 위치: {downloaded_file}")
        print(f"📏 파일 크기: {os.path.getsize(downloaded_file) / (1024*1024):.1f} MB")
        print(f"\n💡 이제 이 파일을 AquaNote에 업로드해서 테스트해보세요!")
    else:
        print("❌ 다운로드에 실패했습니다.")

if __name__ == "__main__":
    main() 