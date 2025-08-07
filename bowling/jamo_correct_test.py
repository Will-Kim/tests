#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
정확한 자모 단위 비교 테스트
"""

try:
    import jamo
    print("라이브러리 설치됨")
    
    def calculate_correct_jamo_similarity(target_name: str, member_name: str) -> float:
        """정확한 자모 단위 유사도 계산"""
        if not target_name or not member_name:
            return 0.0
        
        try:
            # 자모 분해
            target_jamos = jamo.h2j(target_name)
            member_jamos = jamo.h2j(member_name)
            
            print(f"  {target_name} → {target_jamos}")
            print(f"  {member_name} → {member_jamos}")
            
            # 자모별 비교 (위치별)
            total_jamos = len(target_jamos)
            matches = 0
            
            for i in range(total_jamos):
                if i < len(member_jamos):
                    target_jamo = target_jamos[i]
                    member_jamo = member_jamos[i]
                    match = target_jamo == member_jamo
                    if match:
                        matches += 1
                    print(f"    자모 {i+1}: '{target_jamo}' vs '{member_jamo}' → {'✅' if match else '❌'}")
                else:
                    print(f"    자모 {i+1}: '{target_jamos[i]}' vs '' → ❌")
            
            similarity = (matches / total_jamos * 100) if total_jamos > 0 else 0.0
            print(f"    결과: {matches}/{total_jamos} = {similarity:.1f}%")
            return similarity
            
        except Exception as e:
            print(f"    오류: {e}")
            return 0.0

    # 테스트 케이스들
    test_cases = [
        ("김한규", "김환규"),
        ("김한규", "한지영"),
        ("김한규", "김경희"),
        ("김한규", "박철수"),
    ]
    
    print("=== 정확한 자모 단위 비교 테스트 ===")
    for target_name, member_name in test_cases:
        print(f"\n{'='*20} {target_name} vs {member_name} {'='*20}")
        
        similarity = calculate_correct_jamo_similarity(target_name, member_name)
        print(f"\n최종 유사도: {similarity:.1f}%")
        
except ImportError as e:
    print(f"라이브러리 오류: {e}")
    print("설치: pip install jamo") 