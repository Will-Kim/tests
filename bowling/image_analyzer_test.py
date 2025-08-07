#!/usr/bin/env python3
"""
이미지 분석기 테스트 스크립트
업로드 폴더의 이미지들을 테스트하여 image_analyzer.py의 기능을 검증합니다.
"""

import os
import sys
import logging
from PIL import Image
from typing import List, Dict, Any
import json
from datetime import datetime

# image_analyzer 모듈 import
from image_analyzer import ImageAnalyzer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageAnalyzerTester:
    """이미지 분석기 테스트 클래스"""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        self.analyzer = ImageAnalyzer(upload_dir)
        logger.info(f"ImageAnalyzerTester 초기화 완료. 업로드 디렉토리: {upload_dir}")
    
    def list_uploaded_images(self) -> List[Dict]:
        """업로드된 이미지 목록 조회"""
        try:
            if not os.path.exists(self.upload_dir):
                logger.warning(f"업로드 디렉토리가 존재하지 않습니다: {self.upload_dir}")
                return []
            
            images = []
            for filename in os.listdir(self.upload_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    filepath = os.path.join(self.upload_dir, filename)
                    stat = os.stat(filepath)
                    images.append({
                        "filename": filename,
                        "filepath": filepath,
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })
            
            # 수정 시간 역순으로 정렬
            images.sort(key=lambda x: x["modified"], reverse=True)
            
            logger.info(f"업로드된 이미지 수: {len(images)}")
            return images
            
        except Exception as e:
            logger.error(f"이미지 목록 조회 오류: {e}")
            return []
    
    def test_single_image(self, image_path: str) -> Dict[str, Any]:
        """단일 이미지 테스트"""
        try:
            logger.info(f"이미지 테스트 시작: {image_path}")
            
            # 이미지 로드
            image = Image.open(image_path)
            logger.info(f"이미지 로드 완료: {image.size}, 모드: {image.mode}")
            
            # RGB 변환
            if image.mode != 'RGB':
                image = image.convert('RGB')
                logger.info("RGB 변환 완료")
            
            # 이미지 분석
            analysis_result = self.analyzer.analyze_image(image, "auto")
            
            # 결과 정리
            result = {
                "image_path": image_path,
                "image_size": image.size,
                "saved_path": analysis_result.get('saved_path', ''),
                "preprocessing": analysis_result.get('preprocessing', ''),
                "ocr_result": analysis_result.get('ocr_result', {}),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"이미지 테스트 완료: {image_path}")
            return result
            
        except Exception as e:
            logger.error(f"이미지 테스트 오류: {e}")
            return {
                "image_path": image_path,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def test_all_images(self) -> List[Dict[str, Any]]:
        """모든 업로드된 이미지 테스트"""
        try:
            images = self.list_uploaded_images()
            if not images:
                logger.warning("테스트할 이미지가 없습니다.")
                return []
            
            results = []
            for i, image_info in enumerate(images, 1):
                logger.info(f"테스트 진행률: {i}/{len(images)} - {image_info['filename']}")
                
                result = self.test_single_image(image_info['filepath'])
                results.append(result)
                
                # 결과 요약 출력
                self._print_result_summary(result)
            
            return results
            
        except Exception as e:
            logger.error(f"전체 이미지 테스트 오류: {e}")
            return []
    
    def _print_result_summary(self, result: Dict[str, Any]):
        """결과 요약 출력"""
        try:
            if "error" in result:
                print(f"❌ {result['image_path']}: {result['error']}")
                return
            
            ocr_result = result.get('ocr_result', {})
            method = ocr_result.get('method', 'unknown')
            full_text = ocr_result.get('full_text', '')
            blocks = ocr_result.get('blocks', [])
            
            print(f"✅ {result['image_path']}")
            print(f"   - 방법: {method}")
            print(f"   - 블록 수: {len(blocks)}")
            print(f"   - 텍스트 길이: {len(full_text)}")
            if full_text:
                print(f"   - 텍스트 미리보기: {full_text[:100]}...")
            print()
            
        except Exception as e:
            logger.error(f"결과 요약 출력 오류: {e}")
    
    def save_test_results(self, results: List[Dict[str, Any]], output_file: str = None):
        """테스트 결과를 JSON 파일로 저장"""
        try:
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"test_results_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"테스트 결과 저장됨: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"테스트 결과 저장 오류: {e}")
            return None

def main():
    """메인 함수"""
    print("=" * 60)
    print("이미지 분석기 테스트 스크립트")
    print("=" * 60)
    
    # 테스터 초기화
    tester = ImageAnalyzerTester()
    
    # 업로드된 이미지 목록 확인
    images = tester.list_uploaded_images()
    if not images:
        print("❌ 업로드된 이미지가 없습니다.")
        print(f"   업로드 디렉토리: {tester.upload_dir}")
        return
    
    print(f"📁 발견된 이미지: {len(images)}개")
    for i, image in enumerate(images, 1):
        print(f"   {i}. {image['filename']} ({image['size']} bytes)")
    print()
    
    # 사용자 선택
    while True:
        print("테스트 옵션을 선택하세요:")
        print("1. 모든 이미지 테스트")
        print("2. 특정 이미지 테스트")
        print("3. 종료")
        
        choice = input("선택 (1-3): ").strip()
        
        if choice == "1":
            print("\n🔄 모든 이미지 테스트 시작...")
            results = tester.test_all_images()
            
            if results:
                output_file = tester.save_test_results(results)
                print(f"\n✅ 테스트 완료! 결과 저장됨: {output_file}")
            else:
                print("\n❌ 테스트 실패")
            break
            
        elif choice == "2":
            print("\n📋 이미지 목록:")
            for i, image in enumerate(images, 1):
                print(f"   {i}. {image['filename']}")
            
            try:
                idx = int(input("테스트할 이미지 번호를 입력하세요: ")) - 1
                if 0 <= idx < len(images):
                    selected_image = images[idx]
                    print(f"\n🔄 이미지 테스트 시작: {selected_image['filename']}")
                    
                    result = tester.test_single_image(selected_image['filepath'])
                    tester._print_result_summary(result)
                    
                    # 결과 저장
                    output_file = tester.save_test_results([result])
                    print(f"\n✅ 테스트 완료! 결과 저장됨: {output_file}")
                else:
                    print("❌ 잘못된 번호입니다.")
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
            except Exception as e:
                print(f"❌ 오류: {e}")
            break
            
        elif choice == "3":
            print("👋 테스트를 종료합니다.")
            break
            
        else:
            print("❌ 1-3 중에서 선택해주세요.")

if __name__ == "__main__":
    main() 