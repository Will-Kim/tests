#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
한글 이름 유사도 테스트 프로그램
fuzzywuzzy를 사용하여 입력된 이름과 회원목록의 유사도를 계산
"""

import sys
import os
from typing import List, Tuple
from difflib import SequenceMatcher

# fuzzywuzzy 라이브러리 import (없으면 설치 필요)
try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    print("fuzzywuzzy 라이브러리가 설치되지 않았습니다.")
    print("설치 명령어: pip install fuzzywuzzy python-Levenshtein")

# jamo 라이브러리 import (한글 자모 분해/조합)
try:
    import jamo
    JAMO_AVAILABLE = True
except ImportError:
    JAMO_AVAILABLE = False
    print("jamo 라이브러리가 설치되지 않았습니다.")
    print("설치 명령어: pip install jamo")

# 현재 회원목록 (bowling.py에서 가져온 것과 동일)
MEMBER_NAMES = [
    "김경희",
    "김환규", 
    "박철수",
    "이영희",
    "최민수",
    "정수진",
    "한지영",
    "윤성호",
    "임태현",
    "송미영"
]

def calculate_similarity_fuzzywuzzy(target_name: str, member_name: str) -> float:
    """fuzzywuzzy를 사용한 유사도 계산"""
    if not FUZZYWUZZY_AVAILABLE:
        return 0.0
    
    # 여러 유사도 메트릭 사용
    ratio = fuzz.ratio(target_name, member_name)
    partial_ratio = fuzz.partial_ratio(target_name, member_name)
    token_sort_ratio = fuzz.token_sort_ratio(target_name, member_name)
    token_set_ratio = fuzz.token_set_ratio(target_name, member_name)
    
    # 평균 유사도 반환
    return (ratio + partial_ratio + token_sort_ratio + token_set_ratio) / 4

def calculate_similarity_difflib(target_name: str, member_name: str) -> float:
    """difflib을 사용한 유사도 계산 (기존 방식)"""
    return SequenceMatcher(None, target_name, member_name).ratio() * 100

def calculate_similarity_jamo(target_name: str, member_name: str) -> float:
    """jamo를 사용한 위치별 자모 단위 유사도 계산"""
    if not JAMO_AVAILABLE or not FUZZYWUZZY_AVAILABLE:
        return 0.0
    
    try:
        # 한글 자모 분해 (올바른 API 사용)
        target_jamos = jamo.h2j(target_name)
        member_jamos = jamo.h2j(member_name)
        
        # 위치별 자모 비교
        position_similarity = calculate_positional_jamo_similarity(target_jamos, member_jamos)
        
        # 전체 문자열 유사도와 위치별 자모 유사도의 가중 평균
        char_similarity = fuzz.ratio(target_name, member_name)
        
        # 위치별 자모 유사도에 더 높은 가중치
        return (position_similarity * 0.8 + char_similarity * 0.2)
    except Exception as e:
        # jamo 처리 중 오류 발생시 기본 유사도 반환
        return fuzz.ratio(target_name, member_name)

def calculate_positional_jamo_similarity(target_jamos: str, member_jamos: str) -> float:
    """정확한 자모 단위 유사도 계산"""
    if not target_jamos or not member_jamos:
        return 0.0
    
    # 자모별 비교 (위치별)
    total_jamos = len(target_jamos)
    matches = 0
    
    for i in range(total_jamos):
        if i < len(member_jamos):
            target_jamo = target_jamos[i]
            member_jamo = member_jamos[i]
            if target_jamo == member_jamo:
                matches += 1
    
    return (matches / total_jamos * 100) if total_jamos > 0 else 0.0

def find_similar_names(target_name: str, member_list: List[str], method: str = "fuzzywuzzy") -> List[Tuple[str, float, str]]:
    """유사한 이름 찾기"""
    results = []
    
    for member_name in member_list:
        if method == "jamo" and JAMO_AVAILABLE and FUZZYWUZZY_AVAILABLE:
            similarity = calculate_similarity_jamo(target_name, member_name)
            method_name = "jamo"
        elif method == "fuzzywuzzy" and FUZZYWUZZY_AVAILABLE:
            similarity = calculate_similarity_fuzzywuzzy(target_name, member_name)
            method_name = "fuzzywuzzy"
        else:
            similarity = calculate_similarity_difflib(target_name, member_name)
            method_name = "difflib"
        
        results.append((member_name, similarity, method_name))
    
    # 유사도 높은 순으로 정렬
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def print_results(target_name: str, results: List[Tuple[str, float, str]]):
    """결과 출력"""
    print(f"\n=== '{target_name}' 유사도 분석 결과 ===")
    print(f"회원목록 ({len(MEMBER_NAMES)}명): {', '.join(MEMBER_NAMES)}")
    print("-" * 60)
    print(f"{'순위':<4} {'회원명':<10} {'유사도':<8} {'방법':<12}")
    print("-" * 60)
    
    for i, (member_name, similarity, method) in enumerate(results, 1):
        print(f"{i:<4} {member_name:<10} {similarity:>6.1f}% {method:<12}")
    
    # 최고 유사도 결과
    best_match = results[0]
    print("-" * 60)
    print(f"최고 유사도: {best_match[0]} ({best_match[1]:.1f}%)")
    
    if best_match[1] >= 80:
        print("✅ 높은 유사도 - 매칭 가능")
    elif best_match[1] >= 60:
        print("⚠️  중간 유사도 - 확인 필요")
    else:
        print("❌ 낮은 유사도 - 매칭 어려움")

def interactive_test():
    """대화형 테스트"""
    print("한글 이름 유사도 테스트 프로그램")
    print("=" * 50)
    
    while True:
        print(f"\n현재 회원목록 ({len(MEMBER_NAMES)}명):")
        for i, name in enumerate(MEMBER_NAMES, 1):
            print(f"{i:2d}. {name}")
        
        print("\n테스트할 이름을 입력하세요 (종료: q, quit)")
        target_name = input("이름: ").strip()
        
        if target_name.lower() in ['q', 'quit', 'exit']:
            print("프로그램을 종료합니다.")
            break
        
        if not target_name:
            print("이름을 입력해주세요.")
            continue
        
        # jamo 사용 (자모 단위 비교)
        if JAMO_AVAILABLE and FUZZYWUZZY_AVAILABLE:
            print(f"\n[jamo 방식 - 자모 단위 비교]")
            results_jamo = find_similar_names(target_name, MEMBER_NAMES, method="jamo")
            print_results(target_name, results_jamo)
        
        # fuzzywuzzy 사용
        if FUZZYWUZZY_AVAILABLE:
            print(f"\n[fuzzywuzzy 방식]")
            results_fuzzy = find_similar_names(target_name, MEMBER_NAMES, method="fuzzywuzzy")
            print_results(target_name, results_fuzzy)
        
        # difflib 사용 (비교용)
        print(f"\n[difflib 방식]")
        results_difflib = find_similar_names(target_name, MEMBER_NAMES, method="difflib")
        print_results(target_name, results_difflib)

def test_specific_cases():
    """특정 케이스 테스트"""
    test_cases = [
        "김한규",  # 김환규와 유사
        "김경희",  # 정확히 일치
        "박철수",  # 정확히 일치
        "김경이",  # 김경희와 유사
        "이영이",  # 이영희와 유사
        "최민수",  # 정확히 일치
        "정수진",  # 정확히 일치
        "한지영",  # 정확히 일치
        "윤성호",  # 정확히 일치
        "임태현",  # 정확히 일치
        "송미영",  # 정확히 일치
        "김철수",  # 박철수와 유사
        "이민수",  # 최민수와 유사
        "박영희",  # 이영희와 유사
    ]
    
    print("특정 케이스 테스트")
    print("=" * 50)
    
    for target_name in test_cases:
        print(f"\n{'='*20} {target_name} {'='*20}")
        
        if JAMO_AVAILABLE and FUZZYWUZZY_AVAILABLE:
            results_jamo = find_similar_names(target_name, MEMBER_NAMES, method="jamo")
            print(f"[jamo] 최고 유사도: {results_jamo[0][0]} ({results_jamo[0][1]:.1f}%)")
        
        if FUZZYWUZZY_AVAILABLE:
            results_fuzzy = find_similar_names(target_name, MEMBER_NAMES, method="fuzzywuzzy")
            print(f"[fuzzywuzzy] 최고 유사도: {results_fuzzy[0][0]} ({results_fuzzy[0][1]:.1f}%)")
        
        results_difflib = find_similar_names(target_name, MEMBER_NAMES, method="difflib")
        print(f"[difflib] 최고 유사도: {results_difflib[0][0]} ({results_difflib[0][1]:.1f}%)")

def main():
    """메인 함수"""
    print("한글 이름 유사도 테스트 프로그램")
    print("=" * 50)
    
    if not FUZZYWUZZY_AVAILABLE:
        print("⚠️  fuzzywuzzy 라이브러리가 설치되지 않았습니다.")
        print("설치 명령어: pip install fuzzywuzzy python-Levenshtein")
    
    if not JAMO_AVAILABLE:
        print("⚠️  jamo 라이브러리가 설치되지 않았습니다.")
        print("설치 명령어: pip install jamo")
    
    if not FUZZYWUZZY_AVAILABLE and not JAMO_AVAILABLE:
        print("difflib만 사용하여 테스트를 진행합니다.")
    
    if len(sys.argv) > 1:
        # 명령행 인수로 테스트
        target_name = sys.argv[1]
        print(f"테스트 이름: {target_name}")
        
        if JAMO_AVAILABLE and FUZZYWUZZY_AVAILABLE:
            results_jamo = find_similar_names(target_name, MEMBER_NAMES, method="jamo")
            print_results(target_name, results_jamo)
        
        if FUZZYWUZZY_AVAILABLE:
            results_fuzzy = find_similar_names(target_name, MEMBER_NAMES, method="fuzzywuzzy")
            print_results(target_name, results_fuzzy)
        
        results_difflib = find_similar_names(target_name, MEMBER_NAMES, method="difflib")
        print_results(target_name, results_difflib)
    else:
        # 대화형 모드
        print("1. 대화형 테스트")
        print("2. 특정 케이스 테스트")
        choice = input("선택하세요 (1/2): ").strip()
        
        if choice == "2":
            test_specific_cases()
        else:
            interactive_test()

if __name__ == "__main__":
    main() 