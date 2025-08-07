from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import re
import difflib
from typing import List, Dict, Any, Optional
import io
import base64
import json
import time
from pydantic import BaseModel
import logging
from dotenv import load_dotenv
import os
from image_analyzer import ImageAnalyzer

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 확인
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if credentials_path:
    # ~ 확장
    credentials_path = os.path.expanduser(credentials_path)
    logger.info(f"Google Cloud 인증 파일 경로: {credentials_path}")
    if os.path.exists(credentials_path):
        logger.info("Google Cloud 인증 파일이 존재합니다.")
    else:
        logger.warning("Google Cloud 인증 파일이 존재하지 않습니다.")
else:
    logger.warning("GOOGLE_APPLICATION_CREDENTIALS 환경 변수가 설정되지 않았습니다.")

app = FastAPI(title="볼링 스코어보드 인식 API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터 모델
class OCRRequest(BaseModel):
    image_data: str
    language: str = "kor+eng"
    preprocessing: str = "auto"

class ScoreData(BaseModel):
    original_name: str
    matched_name: str
    scores: List[int]
    total: int
    confidence: float
    match_confidence: float

class OCRResponse(BaseModel):
    success: bool
    data: List[ScoreData]
    message: str = ""

# 등록된 회원 목록 (실제로는 데이터베이스에서 관리)
MEMBER_NAMES = [
    "김환규", "허영범", "김희조", "김정원", "표경희", 
    "김경희", "이동현", "박서연", "윤정호", "조민지",
    "강태준", "임수빈", "신우진", "한소영", "오재민"
]

class BowlingScoreRecognizer:
    """볼링 스코어보드 인식을 위한 메인 클래스"""
    
    def __init__(self):
        # 이미지 분석기 초기화
        self.image_analyzer = ImageAnalyzer("uploads")
        logger.info("BowlingScoreRecognizer 초기화 완료")
        
    def analyze_image(self, image: Image.Image, original_filename: str = None, preprocessing: str = "auto") -> Dict[str, Any]:
        """이미지 분석 (ImageAnalyzer 사용)"""
        return self.image_analyzer.analyze_image(image, original_filename=original_filename, preprocessing=preprocessing)
    
    def parse_scoreboard_data(self, ocr_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """스코어보드 데이터 파싱 - 볼링 점수판 구조에 맞게 수정"""
        try:
            text = ocr_result['full_text']
            blocks = ocr_result['blocks']
            method = ocr_result.get('method', 'unknown')
            
            logger.info(f"사용된 OCR 방법: {method}")
            logger.info(f"OCR 텍스트: {text}")
            logger.info(f"OCR 블록 수: {len(blocks)}")
            
            # 블록들을 Y 좌표로 정렬 (위에서 아래로)
            sorted_blocks = sorted(blocks, key=lambda x: x['bbox'][1])
            logger.info(f"정렬된 블록 수: {len(sorted_blocks)}")
            
            # 프레임 헤더 찾기 (1,2,3...10이 포함된 블록들)
            frame_headers = []
            for block in sorted_blocks:
                text = block['text'].strip()
                # 1-10 숫자가 포함된 블록 찾기
                if any(str(i) in text for i in range(1, 11)):
                    frame_headers.append(block)
                    logger.info(f"프레임 헤더 발견: {text}")
            
            if not frame_headers:
                logger.warning("프레임 헤더를 찾을 수 없습니다.")
                return []
            
            # 프레임 헤더의 Y 좌표 범위 계산
            header_y_min = min(block['bbox'][1] for block in frame_headers)
            header_y_max = max(block['bbox'][3] for block in frame_headers)
            logger.info(f"헤더 Y 범위: {header_y_min} - {header_y_max}")
            
            # 헤더 아래의 데이터 블록들 찾기
            data_blocks = []
            for block in sorted_blocks:
                if block['bbox'][1] > header_y_max:  # 헤더 아래에 있는 블록들
                    data_blocks.append(block)
                    logger.info(f"데이터 블록: {block['text']} at Y={block['bbox'][1]}")
            
            # 데이터 블록들을 행으로 그룹화
            rows = self._group_blocks_into_rows(data_blocks)
            logger.info(f"분석된 행 수: {len(rows)}")
            
            parsed_data = []
            for row_idx, row_blocks in enumerate(rows):
                if not row_blocks:
                    continue
                
                # 행 블록들을 X 좌표로 정렬 (왼쪽에서 오른쪽으로)
                sorted_row = sorted(row_blocks, key=lambda x: x['bbox'][0])
                logger.info(f"행 {row_idx + 1} 블록들: {[b['text'] for b in sorted_row]}")
                
                if len(sorted_row) < 2:
                    continue
                
                # 첫 번째 블록 (이름)
                name_block = sorted_row[0]
                name_text = name_block['text'].strip()
                
                # 마지막 블록 (총점)
                total_score_block = sorted_row[-1]
                total_score_text = total_score_block['text'].strip()
                
                # 총점이 숫자인지 확인
                if not total_score_text.isdigit():
                    logger.warning(f"총점이 숫자가 아님: {total_score_text}")
                    continue
                
                # 중간 점수들 추출 (2번째부터 마지막-1까지)
                frame_scores = []
                for block in sorted_row[1:-1]:
                    score_text = block['text'].strip()
                    if score_text.isdigit():
                        frame_scores.append(int(score_text))
                
                logger.info(f"이름: {name_text}, 프레임 점수: {frame_scores}, 총점: {total_score_text}")
                
                parsed_item = {
                    'original_name': name_text,
                    'scores': frame_scores,
                    'total': int(total_score_text),
                    'confidence': name_block['confidence']
                }
                
                parsed_data.append(parsed_item)
                logger.info(f"파싱된 항목: {parsed_item}")
            
            logger.info(f"최종 파싱된 데이터 수: {len(parsed_data)}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Scoreboard parsing error: {e}")
            import traceback
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            return []
    
    def _group_blocks_into_rows(self, blocks, y_tolerance=20):
        """블록들을 행으로 그룹화합니다."""
        if not blocks:
            return []
        
        # Y 좌표로 정렬
        sorted_blocks = sorted(blocks, key=lambda x: x['bbox'][1])
        
        rows = []
        current_row = []
        current_y = None
        
        for block in sorted_blocks:
            y_center = (block['bbox'][1] + block['bbox'][3]) / 2
            
            if current_y is None:
                current_y = y_center
                current_row.append(block)
            elif abs(y_center - current_y) <= y_tolerance:
                # 같은 행에 속함
                current_row.append(block)
            else:
                # 새로운 행 시작
                if current_row:
                    rows.append(current_row)
                current_row = [block]
                current_y = y_center
        
        # 마지막 행 추가
        if current_row:
            rows.append(current_row)
        
        return rows
    
    def match_names(self, parsed_data: List[Dict[str, Any]], member_list: List[str]) -> List[ScoreData]:
        """이름 매칭"""
        try:
            matched_results = []
            
            for data in parsed_data:
                original_name = data['original_name']
                best_match = self.find_best_name_match(original_name, member_list)
                
                matched_results.append(ScoreData(
                    original_name=original_name,
                    matched_name=best_match['name'],
                    scores=data['scores'],
                    total=data['total'],
                    confidence=data['confidence'],
                    match_confidence=best_match['confidence']
                ))
            
            return matched_results
            
        except Exception as e:
            logger.error(f"Name matching error: {e}")
            return []
    
    def find_best_name_match(self, target_name: str, member_list: List[str]) -> Dict[str, Any]:
        """최적의 이름 매칭 찾기"""
        try:
            best_match = {'name': target_name, 'confidence': 0.0}
            
            for member_name in member_list:
                # 기본 문자열 유사도
                similarity = difflib.SequenceMatcher(None, target_name, member_name).ratio()
                
                # 한글 자모 분해 유사도
                jamo_similarity = self.calculate_hangul_similarity(target_name, member_name)
                
                # 최종 유사도 (가중 평균)
                final_similarity = (similarity * 0.6) + (jamo_similarity * 0.4)
                
                if final_similarity > best_match['confidence']:
                    best_match = {'name': member_name, 'confidence': final_similarity}
            
            # 신뢰도가 너무 낮으면 원본 이름 유지
            if best_match['confidence'] < 0.3:
                best_match = {'name': target_name, 'confidence': 0.0}
            
            return best_match
            
        except Exception as e:
            logger.error(f"Name matching error: {e}")
            return {'name': target_name, 'confidence': 0.0}
    
    def calculate_hangul_similarity(self, str1: str, str2: str) -> float:
        """한글 자모 분해 기반 유사도 계산"""
        try:
            # 간단한 한글 유사도 계산 (초성, 중성, 종성 고려)
            def decompose_hangul(char):
                if '가' <= char <= '힣':
                    code = ord(char) - ord('가')
                    cho = code // 588
                    jung = (code % 588) // 28
                    jong = code % 28
                    return f"{cho}_{jung}_{jong}"
                return char
            
            decomposed1 = ''.join(decompose_hangul(c) for c in str1)
            decomposed2 = ''.join(decompose_hangul(c) for c in str2)
            
            return difflib.SequenceMatcher(None, decomposed1, decomposed2).ratio()
            
        except Exception as e:
            logger.error(f"Hangul similarity calculation error: {e}")
            return 0.0

# 전역 인식기 인스턴스
recognizer = BowlingScoreRecognizer()

@app.get("/", response_class=HTMLResponse)
async def root():
    """메인 페이지"""
    return FileResponse("bowling/bowling.html")

@app.get("/members")
async def get_members():
    """등록된 회원 목록 조회"""
    return {"members": MEMBER_NAMES}

@app.post("/members")
async def add_member(member_name: str):
    """새 회원 추가"""
    if member_name not in MEMBER_NAMES:
        MEMBER_NAMES.append(member_name)
        return {"message": f"회원 '{member_name}'이 추가되었습니다.", "members": MEMBER_NAMES}
    else:
        return {"message": f"회원 '{member_name}'은 이미 존재합니다.", "members": MEMBER_NAMES}

@app.post("/recognize-scoreboard", response_model=OCRResponse)
async def recognize_scoreboard(
    file: UploadFile = File(...),
    language: str = "kor+eng",
    preprocessing: str = "auto"
):
    """볼링 스코어보드 이미지 인식"""
    try:
        # 파일 검증
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
        
        # 이미지 로드
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # RGB 변환
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 이미지 저장
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"bowling_score_{timestamp}.jpg"
        filepath = os.path.join("uploads", filename)
        image.save(filepath, "JPEG", quality=95)
        logger.info(f"업로드된 이미지 저장: {filepath}")
        
        # 이미지 분석 (전처리, OCR 포함)
        analysis_result = recognizer.analyze_image(image, original_filename=filename, preprocessing=preprocessing)
        ocr_result = analysis_result['ocr_result']
        saved_path = analysis_result['saved_path']
        
        logger.info(f"이미지 저장 경로: {saved_path}")
        
        # 스코어보드 영역 인식 확인
        if not analysis_result.get('region_analysis'):
            logger.warning("스코어보드 헤더(1-10) 인식 안됨")
            return OCRResponse(
                success=False,
                data=[],
                message="스코어보드 헤더(1-10) 인식 안됨"
            )
        
        # region_analysis 결과 사용 - 이름과 점수 매칭 (부분 인식 지원)
        region_data = analysis_result['region_analysis']
        korean_names = region_data.get('name_part', {}).get('korean_names', [])
        numbers = region_data.get('final_score', {}).get('numbers', [])
        
        logger.info(f"한글 이름: {korean_names}")
        logger.info(f"숫자 점수: {numbers}")
        
        # 부분 인식 결과 생성 (이름과 점수 개수가 달라도 처리)
        parsed_data = []
        max_count = max(len(korean_names), len(numbers))
        
        for i in range(max_count):
            name = korean_names[i] if i < len(korean_names) else ""
            score = numbers[i] if i < len(numbers) else 0
            
            parsed_data.append({
                'original_name': name,
                'scores': [],  # 프레임별 점수는 별도 추출 필요
                'total': score,
                'confidence': 0.9 if name and score else 0.5
            })
        
        logger.info(f"부분 인식 결과: {parsed_data}")
        
        # 이름 매칭
        matched_data = recognizer.match_names(parsed_data, MEMBER_NAMES)
        
        # 부분 인식 메시지 생성
        name_count = len([d for d in parsed_data if d['original_name']])
        score_count = len([d for d in parsed_data if d['total'] > 0])
        total_count = len(parsed_data)
        
        if name_count == score_count == total_count:
            message = f"{total_count}개의 스코어 데이터를 완전히 인식했습니다."
        else:
            message = f"부분 인식: 이름 {name_count}개, 점수 {score_count}개 (총 {total_count}개)"
        
        return OCRResponse(
            success=True,
            data=matched_data,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Scoreboard recognition error: {e}")
        raise HTTPException(status_code=500, detail=f"인식 처리 중 오류가 발생했습니다: {str(e)}")

@app.post("/recognize-base64", response_model=OCRResponse)
async def recognize_scoreboard_base64(request: OCRRequest):
    """Base64 이미지 데이터로 스코어보드 인식"""
    try:
        logger.info("Base64 인식 요청 받음")
        logger.info(f"언어: {request.language}, 전처리: {request.preprocessing}")
        logger.info(f"요청 헤더: {request.headers if hasattr(request, 'headers') else 'N/A'}")
        
        # Base64 디코딩
        if request.image_data.startswith('data:image'):
            image_data = request.image_data.split(',')[1]
            logger.info("data:image 형식 감지됨")
        else:
            image_data = request.image_data
            logger.info("일반 Base64 형식 감지됨")
        
        logger.info(f"Base64 데이터 길이: {len(image_data)}")
        
        try:
            image_bytes = base64.b64decode(image_data)
            logger.info(f"이미지 바이트 크기: {len(image_bytes)}")
        except Exception as e:
            logger.error(f"Base64 디코딩 오류: {e}")
            raise HTTPException(status_code=400, detail="잘못된 Base64 데이터입니다.")
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"이미지 로드 완료: {image.size}, 모드: {image.mode}")
        except Exception as e:
            logger.error(f"이미지 로드 오류: {e}")
            raise HTTPException(status_code=400, detail="이미지 파일을 읽을 수 없습니다.")
        
        # RGB 변환
        if image.mode != 'RGB':
            image = image.convert('RGB')
            logger.info("RGB 변환 완료")
        
        # 이미지 저장
        logger.info("이미지 분석 시작")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"bowling_score_{timestamp}.jpg"
        filepath = os.path.join("uploads", filename)
        image.save(filepath, "JPEG", quality=95)
        logger.info(f"업로드된 이미지 저장: {filepath}")
        
        # 이미지 분석 (전처리, OCR 포함)
        analysis_result = recognizer.analyze_image(image, original_filename=filename, preprocessing=request.preprocessing)
        ocr_result = analysis_result['ocr_result']
        saved_path = analysis_result['saved_path']
        logger.info(f"이미지 저장 경로: {saved_path}")
        logger.info(f"OCR 결과: {ocr_result['full_text'][:100]}...")
        
        # 스코어보드 영역 인식 확인
        if not analysis_result.get('region_analysis'):
            logger.warning("스코어보드 헤더(1-10) 인식 안됨")
            return OCRResponse(
                success=False,
                data=[],
                message="스코어보드 헤더(1-10) 인식 안됨"
            )
        
        # region_analysis 결과 사용 - 이름과 점수 매칭 (부분 인식 지원)
        region_data = analysis_result['region_analysis']
        korean_names = region_data.get('name_part', {}).get('korean_names', [])
        numbers = region_data.get('final_score', {}).get('numbers', [])
        
        logger.info(f"한글 이름: {korean_names}")
        logger.info(f"숫자 점수: {numbers}")
        
        # 부분 인식 결과 생성 (이름과 점수 개수가 달라도 처리)
        parsed_data = []
        max_count = max(len(korean_names), len(numbers))
        
        for i in range(max_count):
            name = korean_names[i] if i < len(korean_names) else ""
            score = numbers[i] if i < len(numbers) else 0
            
            parsed_data.append({
                'original_name': name,
                'scores': [],  # 프레임별 점수는 별도 추출 필요
                'total': score,
                'confidence': 0.9 if name and score else 0.5
            })
        
        logger.info(f"부분 인식 결과: {parsed_data}")
        logger.info(f"파싱된 데이터 수: {len(parsed_data)}")
        
        # 이름 매칭
        logger.info("이름 매칭 시작")
        matched_data = recognizer.match_names(parsed_data, MEMBER_NAMES)
        logger.info(f"매칭된 데이터 수: {len(matched_data)}")
        
        # 부분 인식 메시지 생성
        name_count = len([d for d in parsed_data if d['original_name']])
        score_count = len([d for d in parsed_data if d['total'] > 0])
        total_count = len(parsed_data)
        
        if name_count == score_count == total_count:
            message = f"{total_count}개의 스코어 데이터를 완전히 인식했습니다."
        else:
            message = f"부분 인식: 이름 {name_count}개, 점수 {score_count}개 (총 {total_count}개)"
        
        logger.info("인식 완료")
        return OCRResponse(
            success=True,
            data=matched_data,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Base64 recognition error: {e}")
        logger.error(f"오류 타입: {type(e)}")
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"인식 처리 중 오류가 발생했습니다: {str(e)}")

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "healthy", "message": "볼링 스코어보드 인식 서버가 정상 작동 중입니다."}

@app.get("/test-saved-image/{filename}")
async def test_saved_image(filename: str):
    """저장된 이미지로 테스트"""
    try:
        import os
        filepath = os.path.join("uploads", filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}")
        
        # 이미지 로드
        image = Image.open(filepath)
        
        # RGB 변환
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 이미지 분석
        analysis_result = recognizer.analyze_image(image, original_filename=None, preprocessing="auto")
        ocr_result = analysis_result['ocr_result']
        
        # 스코어보드 데이터 파싱
        parsed_data = recognizer.parse_scoreboard_data(ocr_result)
        
        if not parsed_data:
            return OCRResponse(
                success=False,
                data=[],
                message=f"저장된 이미지 '{filename}'에서 스코어보드 데이터를 찾을 수 없습니다."
            )
        
        # 이름 매칭
        matched_data = recognizer.match_names(parsed_data, MEMBER_NAMES)
        
        return OCRResponse(
            success=True,
            data=matched_data,
            message=f"저장된 이미지 '{filename}'에서 {len(matched_data)}개의 스코어 데이터를 인식했습니다."
        )
        
    except Exception as e:
        logger.error(f"Saved image test error: {e}")
        raise HTTPException(status_code=500, detail=f"저장된 이미지 테스트 중 오류가 발생했습니다: {str(e)}")

@app.get("/list-saved-images")
async def list_saved_images():
    """저장된 이미지 목록 조회"""
    try:
        import os
        upload_dir = "uploads"
        if not os.path.exists(upload_dir):
            return {"images": []}
        
        images = []
        for filename in os.listdir(upload_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                filepath = os.path.join(upload_dir, filename)
                stat = os.stat(filepath)
                images.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
        
        # 수정 시간 역순으로 정렬
        images.sort(key=lambda x: x["modified"], reverse=True)
        
        return {"images": images}
        
    except Exception as e:
        logger.error(f"List saved images error: {e}")
        raise HTTPException(status_code=500, detail=f"저장된 이미지 목록 조회 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bowling:app", host="0.0.0.0", port=8091, reload=True)