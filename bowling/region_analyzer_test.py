#!/usr/bin/env python3
import os
import sys
from PIL import Image
from image_analyzer import ImageAnalyzer

class RegionAnalyzerTester:
    def __init__(self):
        self.analyzer = ImageAnalyzer("uploads")
    
    def test_region_analysis(self, image_path: str) -> dict:
        """단일 이미지 영역별 분석 테스트"""
        try:
            print(f"이미지 로딩: {image_path}")
            image = Image.open(image_path)
            
            # 파일명 추출
            filename = os.path.basename(image_path)
            result = self.analyzer.analyze_image(image, original_filename=filename)
            
            region_analysis = result.get('region_analysis')
            if region_analysis:
                name_part = region_analysis.get('name_part', {})
                score_part = region_analysis.get('score_part', {})
                
                print(f"이름 영역 파일: {name_part.get('filepath', 'N/A')}")
                print(f"한글 이름 리스트: {name_part.get('korean_names', [])}")
                print(f"총점 영역 파일: {score_part.get('filepath', 'N/A')}")
                print(f"숫자 리스트: {score_part.get('numbers', [])}")
            else:
                print("영역별 분석 결과가 없습니다")
            
            return result
            
        except Exception as e:
            print(f"테스트 오류: {e}")
            return {'error': str(e)}

def main():
    tester = RegionAnalyzerTester()
    
    # 특정 파일 테스트
    image_path = "uploads/bowling_score_20250806_031233.jpg"
    if os.path.exists(image_path):
        print(f"테스트 파일: {image_path}")
        tester.test_region_analysis(image_path)
    else:
        print(f"테스트 파일을 찾을 수 없습니다: {image_path}")
        print("uploads 폴더의 파일들:")
        if os.path.exists("uploads"):
            for f in os.listdir("uploads"):
                print(f"  - {f}")

if __name__ == "__main__":
    main() 