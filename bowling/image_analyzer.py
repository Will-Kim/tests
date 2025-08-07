import logging
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import io
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from google.cloud import vision
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .env 파일 로드 (부모 폴더에서)
load_dotenv("../.env")

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

class ImageAnalyzer:
    """이미지 분석을 담당하는 클래스"""
    
    def __init__(self, upload_dir: str = "uploads"):
        # 환경 변수 로드
        load_dotenv("../.env")
        
        # Google Cloud Vision API 클라이언트 초기화 (timeout 30초 설정)
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path:
            credentials_path = os.path.expanduser(credentials_path)
            if os.path.exists(credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                # timeout 30초로 설정
                from google.api_core import client_options
                client_options_obj = client_options.ClientOptions(
                    api_endpoint="vision.googleapis.com",
                    api_audience=None,
                    quota_project_id=None,
                    api_key=None,
                    scopes=None
                )
                self.client = vision.ImageAnnotatorClient(client_options=client_options_obj)
            else:
                self.client = None
        else:
            self.client = None
        
        # 업로드 디렉토리 생성
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        
        # 분석 결과 저장 디렉토리 생성
        self.analyzed_dir = "analyzed"
        os.makedirs(self.analyzed_dir, exist_ok=True)
    
    def save_uploaded_image(self, image: Image.Image, filename: str = None) -> str:
        """업로드된 이미지 저장 (웹페이지용) - 더 이상 사용하지 않음"""
        try:
            # 항상 bowling_score_ 형식으로 강제 저장
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"bowling_score_{timestamp}.jpg"
            
            # uploads 폴더에 저장
            filepath = os.path.join(self.upload_dir, filename)
            image.save(filepath, "JPEG", quality=95)
            logger.info(f"업로드된 이미지 저장: {filepath}")
            
            return filename
            
        except Exception as e:
            logger.error(f"이미지 저장 오류: {e}")
            return ""
    
    def preprocess_image(self, image: Image.Image, method: str = "auto") -> Image.Image:
        """이미지 전처리 - 이전에 잘 되었던 방식"""
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            height, width = opencv_image.shape[:2]
            if width > 1200:
                scale = 1200 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                opencv_image = cv2.resize(opencv_image, (new_width, new_height))
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            dark_gray = cv2.convertScaleAbs(gray, alpha=0.7, beta=-30)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(dark_gray)
            denoised = cv2.fastNlMeansDenoising(enhanced)
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_image = Image.fromarray(binary)
            return processed_image
        except Exception as e:
            logger.error(f"이미지 전처리 오류: {e}")
            return image

    def apply_score_postprocess(self, image: Image.Image) -> Image.Image:
        """score_part에만 적용할 후처리: 파란색 배경 + 반사광 제거"""
        try:
            if image.mode != 'L':
                image = image.convert('L')
            arr = np.array(image)
            
            # 1. 반사광 제거를 위한 어둡게 처리
            darkened = cv2.convertScaleAbs(arr, alpha=0.7, beta=-40)
            
            # 2. 파란색 배경에 최적화된 대비 향상
            enhanced = cv2.convertScaleAbs(darkened, alpha=1.3, beta=20)
            
            # 3. 노이즈 제거
            denoised = cv2.fastNlMeansDenoising(enhanced)
            
            # 4. 대비 향상 (CLAHE) - 반사광과 파란색 배경 모두 고려
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            clahe_enhanced = clahe.apply(denoised)
            
            # 5. 적응형 이진화 (반사광에 강함)
            binary = cv2.adaptiveThreshold(clahe_enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5)
            
            # 6. 모폴로지 연산으로 노이즈 제거
            kernel = np.ones((1,1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return Image.fromarray(cleaned)
        except Exception as e:
            logger.error(f"score_part 후처리 오류: {e}")
            return image

    def extract_text_with_positions(self, image: Image.Image, lang: str = "kor+eng") -> Dict[str, Any]:
        """텍스트와 위치 정보 추출 - 숫자 우선 감지 방식"""
        try:
            # PIL Image를 bytes로 변환
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Vision API 요청 생성
            image_vision = vision.Image(content=img_byte_arr)
            
            # 1단계: 숫자 우선 감지 (빠른 스캔)
            number_blocks = self._detect_numbers_only(image_vision)
            
            # 2단계: 스코어보드 영역 확정
            scoreboard_region = self._identify_scoreboard_region(number_blocks, image.size)
            if scoreboard_region:
                # 해당 영역만 정밀 분석
                return self._analyze_scoreboard_region(image, scoreboard_region)
            else:
                return self._analyze_full_image(image_vision)
            
        except Exception as e:
            return {'full_text': '', 'blocks': [], 'method': 'error'}
    
    def save_and_analyze_regions(self, processed_image: Image.Image, region: Dict, original_filename: str) -> Dict[str, Any]:
        """영역별 이미지 분석 및 저장"""
        try:
            base_name = os.path.splitext(original_filename)[0]
            name_image = processed_image.crop((region['name_x1'], region['y1'], region['name_x2'], region['y2']))
            name_filename = f"{original_filename}_name_part.jpg"
            name_filepath = os.path.join(self.analyzed_dir, name_filename)
            name_image.save(name_filepath, "JPEG", quality=95)
            logger.info(f"이름 영역 이미지 저장: {name_filepath}")
            # 기존 스코어 영역 (전처리 적용)
            score_image = processed_image.crop((region['total_x1'], region['total_y1'], region['total_x2'], region['total_y2']))
            score_image = self.apply_score_postprocess(score_image)
            score_filename = f"{original_filename}_score_part.jpg"
            score_filepath = os.path.join(self.analyzed_dir, score_filename)
            score_image.save(score_filepath, "JPEG", quality=95)
            logger.info(f"스코어 영역 이미지 저장 (전처리): {score_filepath}")
            
            # 새로운 스코어 영역 (전처리 없음) - name_part와 동일한 Y좌표 사용
            score_x1 = region['total_x2']  # 546
            score_y1 = region['y1']  # name_part와 동일한 Y좌표 (3D 변환 적용됨)
            score_x2 = score_x1 + (region['total_x2'] - region['total_x1'])  # 546 + (546-488) = 604
            score_y2 = region['y2']  # name_part와 동일한 Y좌표 (3D 변환 적용됨)
            
            score_image2 = processed_image.crop((score_x1, score_y1, score_x2, score_y2))
            score_filename2 = f"{original_filename}_score_part2.jpg"
            score_filepath2 = os.path.join(self.analyzed_dir, score_filename2)
            score_image2.save(score_filepath2, "JPEG", quality=95)
            logger.info(f"스코어 영역 이미지 저장 (전처리 없음): {score_filepath2}")
            # 이름 분석
            name_result = self._analyze_korean_text(name_image)
            korean_names = self._extract_korean_names(name_result)
            name_count = len(korean_names)
            
            # score_part2 먼저 시도 (전처리 없음)
            score_result2 = self._analyze_numbers_only(score_image2)
            numbers2 = self._extract_numbers(score_result2)
            numbers2_count = len(numbers2) if numbers2 else 0
            
            logger.info(f"이름 개수: {name_count}, score_part2 개수: {numbers2_count}")
            
            # score_part2에서 숫자 개수가 이름 개수와 같으면 바로 사용 (score_part 확인 안함)
            if numbers2_count == name_count and numbers2:
                final_numbers = numbers2
                final_score_result = score_result2
                final_score_filepath = score_filepath2
                logger.info(f"score_part2 사용 (이름 {name_count}명, 숫자 {numbers2_count}개 완벽 매칭) - score_part 확인 안함")
            else:
                # score_part2가 매칭 안 되면 score_part 시도
                score_result = self._analyze_numbers_only(score_image)
                numbers = self._extract_numbers(score_result)
                numbers_count = len(numbers) if numbers else 0
                
                logger.info(f"score_part 개수: {numbers_count}")
                
                # 복잡한 점수 매칭 로직 (기존 방식)
                if numbers_count == name_count and numbers:
                    final_numbers = numbers
                    final_score_result = score_result
                    final_score_filepath = score_filepath
                    logger.info(f"score_part 사용 (이름 {name_count}명, 숫자 {numbers_count}개 완벽 매칭)")
                
                # 둘 다 사람 수보다 적게 나온 경우
                elif numbers2_count < name_count and numbers_count < name_count:
                    # 개수가 많은 걸 선택
                    if numbers2_count > numbers_count:
                        final_numbers = numbers2
                        final_score_result = score_result2
                        final_score_filepath = score_filepath2
                        logger.info(f"score_part2 선택 (개수 우선: {numbers2_count} > {numbers_count})")
                    elif numbers_count > numbers2_count:
                        final_numbers = numbers
                        final_score_result = score_result
                        final_score_filepath = score_filepath
                        logger.info(f"score_part 선택 (개수 우선: {numbers_count} > {numbers2_count})")
                    else:
                        # 개수가 같으면 합계가 높은 걸 선택
                        sum2 = sum(numbers2) if numbers2 else 0
                        sum1 = sum(numbers) if numbers else 0
                        if sum2 >= sum1:
                            final_numbers = numbers2
                            final_score_result = score_result2
                            final_score_filepath = score_filepath2
                            logger.info(f"score_part2 선택 (합계 우선: {sum2} >= {sum1})")
                        else:
                            final_numbers = numbers
                            final_score_result = score_result
                            final_score_filepath = score_filepath
                            logger.info(f"score_part 선택 (합계 우선: {sum1} > {sum2})")
                
                # 하나는 사람 수보다 많고 하나는 적은 경우
                elif (numbers2_count > name_count and numbers_count < name_count) or (numbers2_count < name_count and numbers_count > name_count):
                    if numbers2_count > name_count:
                        final_numbers = numbers2[:name_count]
                        final_score_result = score_result2
                        final_score_filepath = score_filepath2
                        logger.info(f"score_part2 사용 (앞에서 {name_count}개 선택)")
                    else:
                        final_numbers = numbers[:name_count]
                        final_score_result = score_result
                        final_score_filepath = score_filepath
                        logger.info(f"score_part 사용 (앞에서 {name_count}개 선택)")
                
                # 둘 다 사람 수보다 많은 경우
                elif numbers2_count > name_count and numbers_count > name_count:
                    if numbers2_count <= numbers_count:
                        final_numbers = numbers2[:name_count]
                        final_score_result = score_result2
                        final_score_filepath = score_filepath2
                        logger.info(f"score_part2 선택 (개수 적음: {numbers2_count} <= {numbers_count})")
                    else:
                        final_numbers = numbers[:name_count]
                        final_score_result = score_result
                        final_score_filepath = score_filepath
                        logger.info(f"score_part 선택 (개수 적음: {numbers_count} < {numbers2_count})")
                
                # 기본값
                else:
                    final_numbers = numbers2 if numbers2 else numbers
                    final_score_result = score_result2 if numbers2 else score_result
                    final_score_filepath = score_filepath2 if numbers2 else score_filepath
                    logger.info(f"기본값 사용 (이름 {name_count}명, 숫자 {len(final_numbers)}개)")
            
            logger.info(f"=== 분석 결과 ===")
            logger.info(f"한글 이름 리스트: {korean_names}")
            logger.info(f"숫자 리스트 (전처리): {numbers}")
            logger.info(f"숫자 리스트 (전처리 없음): {numbers2}")
            logger.info(f"최종 사용 숫자 리스트: {final_numbers}")
            
            return {
                'name_part': {
                    'filepath': name_filepath,
                    'text': name_result,
                    'korean_names': korean_names
                },
                'score_part': {
                    'filepath': score_filepath,
                    'text': score_result,
                    'numbers': numbers
                },
                'score_part2': {
                    'filepath': score_filepath2,
                    'text': score_result2,
                    'numbers': numbers2
                },
                'final_score': {
                    'filepath': final_score_filepath,
                    'text': final_score_result,
                    'numbers': final_numbers
                }
            }
        except Exception as e:
            logger.error(f"save_and_analyze_regions 오류: {e}")
            return {}
    
    def _extract_korean_names(self, text: str) -> List[str]:
        """한글 이름 추출"""
        try:
            import re
            
            # 한글 패턴 (2글자 이상)
            korean_pattern = r'[가-힣]{2,}'
            korean_names = re.findall(korean_pattern, text)
            
            # 중복 제거 및 정렬
            unique_names = list(set(korean_names))
            unique_names.sort()
            
            return unique_names
            
        except Exception as e:
            return []
    
    def _extract_numbers(self, text: str) -> List[int]:
        """숫자 추출"""
        try:
            import re
            
            # 숫자 패턴 (1자리 이상)
            number_pattern = r'\d+'
            numbers = re.findall(number_pattern, text)
            
            # 정수로 변환
            number_list = [int(num) for num in numbers]
            
            return number_list
            
        except Exception as e:
            return []
    
    def _analyze_korean_text(self, image: Image.Image) -> str:
        """한글 텍스트 전용 분석"""
        try:
            logger.info("한글 텍스트 분석 시작")
            
            # Vision API 요청 생성
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            logger.info(f"이미지 바이트 변환 완료: {len(img_byte_arr)} bytes")
            
            image_vision = vision.Image(content=img_byte_arr)
            logger.info("Vision API 이미지 객체 생성 완료")
            
            # 한글 텍스트 감지
            logger.info("Google Cloud Vision API text_detection 호출 시작...")
            response = self.client.text_detection(image=image_vision)
            logger.info("Google Cloud Vision API text_detection 호출 완료")
            
            if response.text_annotations:
                # 첫 번째는 전체 텍스트
                full_text = response.text_annotations[0].description
                logger.info(f"한글 텍스트 분석 결과: {full_text[:100]}...")
                return full_text
            else:
                logger.warning("한글 텍스트 분석 결과 없음")
                return ""
                
        except Exception as e:
            logger.error(f"한글 텍스트 분석 오류: {e}")
            return ""
    
    def _analyze_numbers_only(self, image: Image.Image) -> str:
        """숫자 전용 분석"""
        try:
            logger.info("숫자 분석 시작")
            
            # Vision API 요청 생성
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            logger.info(f"숫자 분석 이미지 바이트 변환 완료: {len(img_byte_arr)} bytes")
            
            image_vision = vision.Image(content=img_byte_arr)
            logger.info("숫자 분석 Vision API 이미지 객체 생성 완료")
            
            # 숫자만 감지
            logger.info("Google Cloud Vision API 숫자 분석 호출 시작...")
            response = self.client.text_detection(image=image_vision)
            logger.info("Google Cloud Vision API 숫자 분석 호출 완료")
            
            numbers = []
            if response.text_annotations:
                for annotation in response.text_annotations[1:]:  # 첫 번째는 전체 텍스트
                    text = annotation.description.strip()
                    # 숫자만 필터링
                    if text.isdigit():
                        numbers.append(text)
            
            result = " ".join(numbers)
            logger.info(f"숫자 분석 결과: {result}")
            return result
                
        except Exception as e:
            logger.error(f"숫자 분석 오류: {e}")
            return ""
    
    def _detect_numbers_only(self, image_vision) -> List[Dict]:
        """숫자만 감지 (빠른 스캔)"""
        try:
            logger.info("숫자 감지 (빠른 스캔) 시작")
            # 숫자만 감지하는 빠른 API 호출
            logger.info("Google Cloud Vision API 숫자 감지 호출 시작...")
            response = self.client.text_detection(image=image_vision)
            logger.info("Google Cloud Vision API 숫자 감지 호출 완료")
            
            number_blocks = []
            if response.text_annotations:
                for annotation in response.text_annotations[1:]:  # 첫 번째는 전체 텍스트
                    text = annotation.description.strip()
                    # 숫자만 필터링 (1-10 범위)
                    if text.isdigit() and 1 <= int(text) <= 10:
                        vertices = annotation.bounding_poly.vertices
                        if len(vertices) >= 4:
                            x_coords = [vertex.x for vertex in vertices]
                            y_coords = [vertex.y for vertex in vertices]
                            bbox_rect = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                            number_blocks.append({
                                'text': text,
                                'bbox': bbox_rect,
                                'confidence': annotation.confidence if hasattr(annotation, 'confidence') else 0.8
                            })
                            print(f"숫자 감지: {text} at ({bbox_rect[0]}, {bbox_rect[1]}, {bbox_rect[2]}, {bbox_rect[3]})")
            
            print(f"감지된 숫자 블록 수: {len(number_blocks)}")
            return number_blocks
            
        except Exception as e:
            return []
    
    def _calculate_scoreboard_slope(self, consecutive_pattern: List[Dict]) -> dict:
        """1-10 프레임의 기울기와 높이 변화 계산"""
        try:
            if len(consecutive_pattern) < 2:
                return {"slope": 0.0, "height_change": 0.0, "perspective_factor": 0.0}
            
            # 각 프레임의 중심점과 높이 계산
            centers = []
            heights = []
            for block in consecutive_pattern:
                bbox = block['bbox']
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                height = bbox[3] - bbox[1]  # 높이
                centers.append((center_x, center_y))
                heights.append(height)
            
            # 선형 회귀로 기울기 계산
            x_coords = [center[0] for center in centers]
            y_coords = [center[1] for center in centers]
            
            n = len(centers)
            if n < 2:
                return {"slope": 0.0, "height_change": 0.0, "perspective_factor": 0.0}
            
            sum_x = sum(x_coords)
            sum_y = sum(y_coords)
            sum_xy = sum(x * y for x, y in zip(x_coords, y_coords))
            sum_x2 = sum(x * x for x in x_coords)
            
            # 기울기 계산
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # 높이 변화 계산 (원근감)
            first_height = heights[0]  # 1프레임 높이
            last_height = heights[-1]  # 10프레임 높이
            height_change = last_height - first_height
            
            # 원근감 계수 (높이 변화율)
            total_width = x_coords[-1] - x_coords[0]
            perspective_factor = height_change / total_width if total_width > 0 else 0.0
            
            logger.info(f"스코어보드 기울기: {slope:.4f}, 높이 변화: {height_change:.2f}, 원근감 계수: {perspective_factor:.4f}")
            
            return {
                "slope": slope,
                "height_change": height_change,
                "perspective_factor": perspective_factor,
                "first_height": first_height,
                "last_height": last_height
            }
            
        except Exception as e:
            logger.error(f"기울기 계산 오류: {e}")
            return {"slope": 0.0, "height_change": 0.0, "perspective_factor": 0.0}
    
    def _calculate_tilted_region(self, frame_1: Dict, frame_10: Dict, scoreboard_width: int, 
                                slope_info: dict, region_type: str, gap_half: float) -> tuple:
        """기울기와 원근감을 적용한 3D 영역 계산"""
        try:
            # 기본 좌표
            frame_1_left = frame_1['bbox'][0]
            frame_1_bottom = frame_1['bbox'][3]
            frame_10_right = frame_10['bbox'][2]
            frame_10_bottom = frame_10['bbox'][3]
            
            slope = slope_info.get("slope", 0.0)
            perspective_factor = slope_info.get("perspective_factor", 0.0)
            first_height = slope_info.get("first_height", 0.0)
            last_height = slope_info.get("last_height", 0.0)
            
            if region_type == "name":
                # 이름 영역: 1프레임 왼쪽 30% 공간
                base_x1 = max(0, frame_1_left - int(scoreboard_width * 0.3))
                base_x2 = frame_1_left
                base_y1 = frame_1_bottom
                base_y2 = base_y1 + int(scoreboard_width * 0.5)
                
                # 3D 변환 적용
                if abs(slope) > 0.01 or abs(perspective_factor) > 0.001:
                    # 기울기 적용
                    adjusted_y1 = base_y1 + int(slope * (base_x1 - frame_1_left))
                    adjusted_y2 = base_y2 + int(slope * (base_x2 - frame_1_left))
                    
                    # 원근감 적용 (높이 변화)
                    perspective_adjustment = int(perspective_factor * (base_x1 - frame_1_left))
                    adjusted_y1 += perspective_adjustment
                    adjusted_y2 += perspective_adjustment
                    
                    logger.info(f"이름 영역 3D 변환: 기울기={slope:.4f}, 원근감={perspective_factor:.4f}")
                    return (base_x1, adjusted_y1, base_x2, adjusted_y2)
                else:
                    return (base_x1, base_y1, base_x2, base_y2)
                    
            elif region_type == "score":
                # 스코어 영역: 10프레임 기준 동적 간격
                base_x1 = frame_10['bbox'][0] - gap_half
                base_x2 = frame_10_right + gap_half
                base_y1 = frame_10_bottom
                base_y2 = base_y1 + int(scoreboard_width * 0.5)
                
                # 3D 변환 적용
                if abs(slope) > 0.01 or abs(perspective_factor) > 0.001:
                    # 기울기 적용
                    adjusted_y1 = base_y1 + int(slope * (base_x1 - frame_10_right))
                    adjusted_y2 = base_y2 + int(slope * (base_x2 - frame_10_right))
                    
                    # 원근감 적용 (높이 변화)
                    perspective_adjustment = int(perspective_factor * (base_x1 - frame_10_right))
                    adjusted_y1 += perspective_adjustment
                    adjusted_y2 += perspective_adjustment
                    
                    logger.info(f"스코어 영역 3D 변환: 기울기={slope:.4f}, 원근감={perspective_factor:.4f}")
                    return (base_x1, adjusted_y1, base_x2, adjusted_y2)
                else:
                    return (base_x1, base_y1, base_x2, base_y2)
            
            return (0, 0, 0, 0)
            
        except Exception as e:
            logger.error(f"3D 영역 계산 오류: {e}")
            # 오류 시 기본값 반환
            if region_type == "name":
                return (max(0, frame_1_left - int(scoreboard_width * 0.3)), 
                       frame_1_bottom, frame_1_left, 
                       frame_1_bottom + int(scoreboard_width * 0.5))
            else:
                return (frame_10['bbox'][0] - gap_half, frame_10_bottom,
                       frame_10_right + gap_half, 
                       frame_10_bottom + int(scoreboard_width * 0.5))
    
    def _identify_scoreboard_region(self, number_blocks: List[Dict], image_size) -> Optional[Dict]:
        """스코어보드 영역 식별 (인식된 순서대로 1-10 패턴 찾기)"""
        try:
            if len(number_blocks) < 5:  # 최소 5개 숫자 필요
                return None
            
            # 인식된 순서 그대로 사용 (Y좌표 그룹화 제거)
            consecutive_pattern = self._find_consecutive_1_to_10(number_blocks)
            if consecutive_pattern:
                        
                        # 1과 10의 위치 찾기
                        frame_1 = consecutive_pattern[0]  # 첫 번째가 1
                        frame_10 = consecutive_pattern[-1]  # 마지막이 10
                        
                        # 9와 10 사이의 간격 계산
                        frame_9 = None
                        for block in consecutive_pattern:
                            if block['text'] == '9':
                                frame_9 = block
                                break
                        
                        # 9와 10 사이 간격의 절반 계산
                        if frame_9:
                            gap_half = (frame_10['bbox'][0] - frame_9['bbox'][2]) / 2
                        else:
                            # 9가 없으면 기본값 사용
                            gap_half = 30
                        
                        # 프레임 헤더 영역 계산 (1-10 프레임 범위)
                        frame_1_left = frame_1['bbox'][0]    # 1프레임 왼쪽 경계
                        frame_10_right = frame_10['bbox'][2]  # 10프레임 오른쪽 경계
                        header_top = min(block['bbox'][1] for block in consecutive_pattern)    # 헤더 최상단
                        header_bottom = max(block['bbox'][3] for block in consecutive_pattern)  # 헤더 최하단
                        
                        # 스코어보드 전체 너비 (1-10 프레임 범위)
                        scoreboard_width = frame_10_right - frame_1_left
            
                        # 1-10 프레임의 기울기와 원근감 계산
                        slope_info = self._calculate_scoreboard_slope(consecutive_pattern)
                        
                        # 이름 영역 (3D 변환 적용)
                        name_region = self._calculate_tilted_region(
                            frame_1, frame_10, scoreboard_width, slope_info, 
                            region_type="name", gap_half=gap_half
                        )
                        name_x1, name_y1, name_x2, name_y2 = name_region
                        
                        # 스코어 영역 (3D 변환 적용)
                        score_region = self._calculate_tilted_region(
                            frame_1, frame_10, scoreboard_width, slope_info,
                            region_type="score", gap_half=gap_half
                        )
                        total_x1, total_y1, total_x2, total_y2 = score_region
                        
                        # 전체 스코어보드 영역 계산
                        region = {
                            'x1': name_x1,
                            'y1': name_y1,
                            'x2': total_x2,
                            'y2': name_y2,
                            'header_x1': frame_1_left,
                            'header_x2': frame_10_right,
                            'name_x1': name_x1,
                            'name_x2': name_x2,
                            'name_y1': name_y1,
                            'name_y2': name_y2,
                            'total_x1': total_x1,
                            'total_x2': total_x2,
                            'total_y1': total_y1,
                            'total_y2': total_y2
                        }
                        
                        print(f"=== 좌표 정보 ===")
                        print(f"1-10 영역: ({frame_1_left}, {header_top}, {frame_10_right}, {header_bottom})")
                        print(f"이름 영역: ({name_x1}, {name_y1}, {name_x2}, {name_y2})")
                        print(f"스코어 영역: ({total_x1}, {total_y1}, {total_x2}, {total_y2})")
                        
                        return region
            
            return None
            
        except Exception as e:
            logger.error(f"스코어보드 영역 식별 오류: {e}")
            return None
    
    def _find_consecutive_1_to_10(self, sorted_blocks: List[Dict]) -> Optional[List[Dict]]:
        """인식된 순서대로 1-10 패턴 찾기 (중간 빠진 숫자는 다른 위치에서 찾기)"""
        try:
            if len(sorted_blocks) < 10:
                return None
            
            # 1-10 범위의 숫자만 필터링 (인식된 순서 유지)
            valid_blocks = [block for block in sorted_blocks if 1 <= int(block['text']) <= 10]
            if len(valid_blocks) < 10:
                return None
            
            print(f"인식된 순서: {[block['text'] for block in valid_blocks]}")
            
            # 1을 찾을 때까지 스킵
            start_idx = 0
            for i, block in enumerate(valid_blocks):
                if block['text'] == '1':
                    start_idx = i
                    break
            else:
                return None  # 1을 찾지 못함
            
            # 1부터 시작해서 순차적으로 찾기
            pattern = [valid_blocks[start_idx]]
            current_idx = start_idx + 1
            
            for target_num in range(2, 11):
                found = False
                
                # 현재 위치부터 순서대로 찾기
                for i in range(current_idx, len(valid_blocks)):
                    if valid_blocks[i]['text'] == str(target_num):
                        # 이전 숫자와 현재 숫자 사이의 박스에 target_num이 들어있는지 확인
                        prev_block = pattern[-1]
                        current_block = valid_blocks[i]
                        
                        # 박스 범위 계산 (이전 숫자 왼쪽 ~ 현재 숫자 오른쪽)
                        box_left = prev_block['bbox'][0]
                        box_right = current_block['bbox'][2]
                        
                        # target_num이 박스 안에 있는지 확인
                        if (current_block['bbox'][0] >= box_left and 
                            current_block['bbox'][2] <= box_right):
                            pattern.append(current_block)
                            current_idx = i + 1
                            found = True
                            break
                
                # 순서대로 못 찾았으면, 다른 위치에서 찾기
                if not found:
                    for i, block in enumerate(valid_blocks):
                        if block['text'] == str(target_num):
                            # 이전 숫자와 다음 숫자 사이의 박스에 있는지 확인
                            prev_block = pattern[-1]
                            next_target = target_num + 1
                            
                            # 다음 숫자 찾기
                            next_block = None
                            for j in range(current_idx, len(valid_blocks)):
                                if valid_blocks[j]['text'] == str(next_target):
                                    next_block = valid_blocks[j]
                                    break
                            
                            if next_block:
                                # 박스 범위 계산 (이전 숫자 왼쪽 ~ 다음 숫자 오른쪽)
                                box_left = prev_block['bbox'][0]
                                box_right = next_block['bbox'][2]
                                
                                # target_num이 박스 안에 있는지 확인
                                if (block['bbox'][0] >= box_left and 
                                    block['bbox'][2] <= box_right):
                                    pattern.append(block)
                                    found = True
                                    break
                
                if not found:
                    break
            
            # 1-10이 모두 찾아졌으면 성공
            if len(pattern) == 10:
                numbers = [int(block['text']) for block in pattern]
                print(f"1-10 순차 패턴 발견: {numbers}")
                return pattern
            
            return None
            
        except Exception as e:
            return None
    
    def _is_frame_header_pattern(self, numbers: List[int]) -> bool:
        """1-10 프레임 헤더 패턴 확인"""
        try:
            # 1-10 범위의 숫자들이 연속적으로 있는지 확인
            valid_numbers = [n for n in numbers if 1 <= n <= 10]
            if len(valid_numbers) >= 5:  # 최소 5개 숫자
                # 연속성 확인 (순서는 중요하지 않음)
                unique_numbers = set(valid_numbers)
                return len(unique_numbers) >= 5
            return False
        except Exception as e:
            return False
    
    def _analyze_scoreboard_region(self, image: Image.Image, region: Dict) -> Dict[str, Any]:
        """스코어보드 영역만 정밀 분석 (저장하지 않음)"""
        try:
            # 영역 자르기
            cropped_image = image.crop((region['x1'], region['y1'], region['x2'], region['y2']))
            
            # PIL Image를 bytes로 변환 (저장하지 않음)
            img_byte_arr = io.BytesIO()
            cropped_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Vision API 요청 생성
            image_vision = vision.Image(content=img_byte_arr)
            
            # 정밀 분석
            analysis_result = self._analyze_full_image(image_vision)
            
            # 스코어보드 영역 정보 추가
            analysis_result['scoreboard_region'] = region
            
            return analysis_result
            
        except Exception as e:
            return {'full_text': '', 'blocks': [], 'method': 'error'}
    
    def _analyze_full_image(self, image_vision: vision.Image) -> Dict[str, Any]:
        """전체 이미지 정밀 분석 (기존 방식)"""
        try:
            logger.info("전체 이미지 정밀 분석 시작")
            
            # 방법 1: 일반 텍스트 감지 (타임아웃 없음)
            text_response = None
            try:
                logger.info("Google Cloud Vision API text_detection 호출 시작...")
                text_response = self.client.text_detection(image=image_vision)
                logger.info("Google Cloud Vision API text_detection 호출 완료")
            except Exception as e:
                logger.error(f"text_detection 오류: {e}")
                text_response = None
            
            # 방법 2: 문서 텍스트 감지 (타임아웃 없음)
            doc_response = None
            try:
                logger.info("Google Cloud Vision API document_text_detection 호출 시작...")
                doc_response = self.client.document_text_detection(image=image_vision)
                logger.info("Google Cloud Vision API document_text_detection 호출 완료")
            except Exception as e:
                logger.error(f"document_text_detection 오류: {e}")
                doc_response = None
            
            # 두 방법의 결과 비교
            text_blocks = []
            doc_blocks = []
            
            # 방법 1 결과 처리
            if text_response and text_response.text_annotations:
                text_full_text = text_response.text_annotations[0].description
                logger.info(f"방법 1 전체 텍스트: {text_full_text}")
                
                for annotation in text_response.text_annotations[1:]:
                    text = annotation.description.strip()
                    confidence = annotation.confidence if hasattr(annotation, 'confidence') else 0.8
                    
                    if text and confidence > 0.3:
                        vertices = annotation.bounding_poly.vertices
                        if len(vertices) >= 4:
                            x_coords = [vertex.x for vertex in vertices]
                            y_coords = [vertex.y for vertex in vertices]
                            bbox_rect = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                            text_blocks.append({'text': text, 'confidence': confidence, 'bbox': bbox_rect})
            
            # 방법 2 결과 처리
            if doc_response and doc_response.full_text_annotation:
                doc_full_text = doc_response.full_text_annotation.text
                
                for page in doc_response.full_text_annotation.pages:
                    for block in page.blocks:
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                word_text = ''.join([symbol.text for symbol in word.symbols])
                                
                                if word_text.strip():
                                    vertices = word.bounding_box.vertices
                                    if len(vertices) >= 4:
                                        x_coords = [vertex.x for vertex in vertices]
                                        y_coords = [vertex.y for vertex in vertices]
                                        bbox_rect = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                                        confidence = sum(symbol.confidence for symbol in word.symbols) / len(word.symbols) if word.symbols else 0.8
                                        doc_blocks.append({'text': word_text, 'confidence': confidence, 'bbox': bbox_rect})
            
            # 두 방법 모두 실패한 경우
            if not text_blocks and not doc_blocks:
                return {
                    'full_text': '',
                    'blocks': [],
                    'method': 'error'
                }
            
            # 더 많은 블록을 가진 방법 선택 (더 상세한 정보)
            if len(doc_blocks) >= len(text_blocks):
                return {
                    'full_text': doc_full_text if doc_response and doc_response.full_text_annotation else '',
                    'blocks': doc_blocks,
                    'method': 'document_detection'
                }
            else:
                return {
                    'full_text': text_full_text if text_response and text_response.text_annotations else '',
                    'blocks': text_blocks,
                    'method': 'text_detection'
                }
            
        except Exception as e:
            return {'full_text': '', 'blocks': [], 'method': 'error'}
    
    def analyze_image(self, image: Image.Image, original_filename: str = None, preprocessing: str = "auto") -> Dict[str, Any]:
        """이미지 분석 전체 과정"""
        try:
            # 파일명 처리
            if original_filename:
                # 파일 경로가 전달된 경우
                if os.path.exists(original_filename):
                    # 전체 경로인 경우
                    filename = os.path.basename(original_filename)
                else:
                    # 파일명만 전달된 경우
                    filename = original_filename
            else:
                # 파일명이 없으면 타임스탬프로 생성
                import time
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"bowling_score_{timestamp}.jpg"
            
            logger.info(f"analyze_image 호출됨 - filename: {filename}")
            
            # 이미지 전처리
            processed_image = self.preprocess_image(image, preprocessing)
            
            # 전처리된 이미지 저장
            preprocessing_filename = f"{filename}_preprocessing.jpg"
            preprocessing_filepath = os.path.join(self.analyzed_dir, preprocessing_filename)
            processed_image.save(preprocessing_filepath, "JPEG", quality=95)
            logger.info(f"전처리된 이미지 저장: {preprocessing_filepath}")
            
            # OCR 수행
            ocr_result = self.extract_text_with_positions(processed_image)
            
            # 스코어보드 영역이 발견된 경우 영역별 분석 수행
            region_analysis = None
            if ocr_result.get('method') != 'error' and 'scoreboard_region' in ocr_result:
                region_analysis = self.save_and_analyze_regions(processed_image, ocr_result['scoreboard_region'], filename)
            
            return {
                'saved_path': filename,
                'ocr_result': ocr_result,
                'region_analysis': region_analysis,
                'preprocessing': preprocessing
            }
            
        except Exception as e:
            return {
                'saved_path': '',
                'ocr_result': {'full_text': '', 'blocks': [], 'method': 'error'},
                'region_analysis': None,
                'preprocessing': preprocessing
            } 