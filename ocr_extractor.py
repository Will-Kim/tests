import argparse
import sys
import os
from typing import List, Dict, Tuple
import re

try:
    from paddleocr import PaddleOCR
except ImportError:
    print("PaddleOCR가 설치되지 않았습니다. 다음 명령어로 설치하세요:")
    print("pip install paddleocr")
    sys.exit(1)


class MultiLanguageOCR:
    """한글, 영어, 숫자를 추출하는 PaddleOCR 클래스"""
    
    def __init__(self, use_gpu: bool = False):
        """
        OCR 객체 초기화
        
        Args:
            use_gpu (bool): GPU 사용 여부 (기본값: False)
        """
        # 한글과 영어를 모두 지원하는 언어 설정
        self.ocr = PaddleOCR(
            use_angle_cls=True,  # 텍스트 각도 보정
            lang='korean',       # 한글 지원 (영어도 포함됨)
            use_gpu=use_gpu,
            show_log=False
        )
    
    def extract_text(self, image_path: str) -> Dict[str, List[str]]:
        """
        이미지에서 한글, 영어, 숫자를 추출
        
        Args:
            image_path (str): 이미지 파일 경로
            
        Returns:
            Dict[str, List[str]]: 분류된 텍스트 결과
                - 'korean': 한글이 포함된 텍스트
                - 'english': 영어만 포함된 텍스트  
                - 'numbers': 숫자만 포함된 텍스트
                - 'mixed': 혼합된 텍스트
                - 'all': 모든 추출된 텍스트
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        
        # OCR 수행
        result = self.ocr.ocr(image_path, cls=True)
        
        if not result or not result[0]:
            return {
                'korean': [],
                'english': [],
                'numbers': [],
                'mixed': [],
                'all': []
            }
        
        # 텍스트 분류
        korean_texts = []
        english_texts = []
        number_texts = []
        mixed_texts = []
        all_texts = []
        
        for line in result[0]:
            if line and len(line) > 1:
                text = line[1][0].strip()  # 추출된 텍스트
                confidence = line[1][1]    # 신뢰도
                
                # 신뢰도가 0.5 이상인 것만 처리
                if confidence < 0.5:
                    continue
                    
                all_texts.append(text)
                
                # 텍스트 분류
                if self._is_korean_text(text):
                    korean_texts.append(text)
                elif self._is_english_only(text):
                    english_texts.append(text)
                elif self._is_number_only(text):
                    number_texts.append(text)
                else:
                    mixed_texts.append(text)
        
        return {
            'korean': korean_texts,
            'english': english_texts,
            'numbers': number_texts,
            'mixed': mixed_texts,
            'all': all_texts
        }
    
    def _is_korean_text(self, text: str) -> bool:
        """한글이 포함된 텍스트인지 확인"""
        korean_pattern = re.compile(r'[ㄱ-ㅎㅏ-ㅣ가-힣]')
        return bool(korean_pattern.search(text))
    
    def _is_english_only(self, text: str) -> bool:
        """영어만 포함된 텍스트인지 확인 (공백, 구두점 포함 가능)"""
        english_pattern = re.compile(r'^[a-zA-Z\s\.,!?;:\-\'\"()]+$')
        return bool(english_pattern.match(text)) and not self._is_korean_text(text)
    
    def _is_number_only(self, text: str) -> bool:
        """숫자만 포함된 텍스트인지 확인 (콤마, 점, 하이픈 포함 가능)"""
        number_pattern = re.compile(r'^[\d\s\.,\-+%$₩원]+$')
        return bool(number_pattern.match(text))


def print_results(results: Dict[str, List[str]], image_path: str):
    """결과를 보기 좋게 출력"""
    print(f"\n{'='*50}")
    print(f"이미지 파일: {image_path}")
    print(f"{'='*50}")
    
    categories = [
        ('한글 텍스트', 'korean'),
        ('영어 텍스트', 'english'), 
        ('숫자 텍스트', 'numbers'),
        ('혼합 텍스트', 'mixed')
    ]
    
    for category_name, key in categories:
        texts = results[key]
        print(f"\n📝 {category_name} ({len(texts)}개):")
        if texts:
            for i, text in enumerate(texts, 1):
                print(f"  {i}. {text}")
        else:
            print("  (없음)")
    
    print(f"\n📋 전체 추출된 텍스트 ({len(results['all'])}개):")
    if results['all']:
        for i, text in enumerate(results['all'], 1):
            print(f"  {i}. {text}")
    else:
        print("  (텍스트를 찾을 수 없습니다)")


def main():
    """메인 함수 - 커맨드라인 인터페이스"""
    parser = argparse.ArgumentParser(
        description="PaddleOCR을 사용해서 이미지에서 한글, 영어, 숫자를 추출합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python ocr_extractor.py image.jpg
  python ocr_extractor.py image.png --gpu
  python ocr_extractor.py image.jpg --output result.txt
        """
    )
    
    parser.add_argument(
        'image_path',
        help='OCR을 수행할 이미지 파일 경로'
    )
    
    parser.add_argument(
        '--gpu',
        action='store_true',
        help='GPU를 사용해서 OCR 수행 (기본값: CPU)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='결과를 저장할 텍스트 파일 경로 (선택사항)'
    )
    
    args = parser.parse_args()
    
    try:
        # OCR 객체 생성
        print("OCR 엔진을 초기화하는 중...")
        ocr = MultiLanguageOCR(use_gpu=args.gpu)
        
        # OCR 수행
        print(f"이미지 '{args.image_path}'에서 텍스트를 추출하는 중...")
        results = ocr.extract_text(args.image_path)
        
        # 결과 출력
        print_results(results, args.image_path)
        
        # 파일로 저장 (옵션)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(f"이미지 파일: {args.image_path}\n")
                f.write("="*50 + "\n\n")
                
                categories = [
                    ('한글 텍스트', 'korean'),
                    ('영어 텍스트', 'english'),
                    ('숫자 텍스트', 'numbers'),
                    ('혼합 텍스트', 'mixed')
                ]
                
                for category_name, key in categories:
                    f.write(f"{category_name}:\n")
                    for text in results[key]:
                        f.write(f"  - {text}\n")
                    f.write("\n")
                
                f.write("전체 추출된 텍스트:\n")
                for text in results['all']:
                    f.write(f"  - {text}\n")
            
            print(f"\n💾 결과가 '{args.output}' 파일에 저장되었습니다.")
        
    except FileNotFoundError as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 예상치 못한 오류가 발생했습니다: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()