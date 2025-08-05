import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os
from datetime import datetime
import platform
from scipy.ndimage import gaussian_filter, sobel

class RealisticNameplateGenerator:
    """고급 문패 생성기 - 사실적인 재질과 각인 효과"""
    
    def __init__(self, width=350, height=700):
        self.width = width
        self.height = height
        
    def create_realistic_wood_texture(self):
        """매우 사실적인 나무 재질 생성"""
        # 기본 캔버스
        texture = np.zeros((self.height, self.width, 3), dtype=np.float32)
        
        # 다양한 나무 색상 레이어
        wood_colors = [
            [88, 57, 39],    # 매우 어두운 갈색
            [101, 67, 33],   # 어두운 갈색
            [139, 90, 43],   # 중간 갈색
            [160, 110, 70],  # 밝은 갈색
            [184, 134, 80],  # 매우 밝은 갈색
        ]
        
        # 복잡한 나무결 패턴 생성
        for y in range(self.height):
            for x in range(self.width):
                # 주요 나무결 (세로 방향)
                grain1 = np.sin(y * 0.005 + np.sin(x * 0.02) * 5) * 0.5 + 0.5
                grain2 = np.sin(y * 0.01 + np.cos(x * 0.015) * 3) * 0.3
                grain3 = np.sin(y * 0.002) * np.cos(x * 0.08) * 0.2
                
                # 나이테 패턴
                ring_center_x = self.width // 2 + np.sin(y * 0.001) * 50
                ring_distance = np.sqrt((x - ring_center_x) ** 2)
                rings = np.sin(ring_distance * 0.05) * 0.1
                
                # 미세한 섬유질 패턴
                fiber = np.random.normal(0, 0.05)
                
                # 전체 패턴 조합
                pattern = np.clip(grain1 + grain2 + grain3 + rings + fiber, 0, 1)
                
                # 색상 매핑
                color_index = pattern * (len(wood_colors) - 1)
                idx_low = int(color_index)
                idx_high = min(idx_low + 1, len(wood_colors) - 1)
                alpha = color_index - idx_low
                
                color = (1 - alpha) * np.array(wood_colors[idx_low]) + \
                        alpha * np.array(wood_colors[idx_high])
                
                texture[y, x] = color
        
        # 나무 옹이 추가 (더 자연스럽게)
        num_knots = np.random.randint(2, 4)
        for _ in range(num_knots):
            knot_x = np.random.randint(50, self.width - 50)
            knot_y = np.random.randint(100, self.height - 100)
            
            # 타원형 옹이
            knot_width = np.random.randint(25, 40)
            knot_height = np.random.randint(20, 35)
            
            for y in range(max(0, knot_y - knot_height), min(self.height, knot_y + knot_height)):
                for x in range(max(0, knot_x - knot_width), min(self.width, knot_x + knot_width)):
                    dist_x = (x - knot_x) / knot_width
                    dist_y = (y - knot_y) / knot_height
                    dist = np.sqrt(dist_x**2 + dist_y**2)
                    
                    if dist < 1:
                        # 옹이 중심은 더 어둡게, 주변은 점진적으로
                        darkness = (1 - dist) ** 2
                        # 옹이 내부의 나이테 패턴
                        ring_pattern = np.sin(dist * 20) * 0.1 + 1
                        texture[y, x] *= (1 - darkness * 0.5) * ring_pattern
        
        # 나무 표면의 미세한 흠집과 스크래치
        num_scratches = np.random.randint(10, 20)
        for _ in range(num_scratches):
            scratch_y = np.random.randint(0, self.height)
            scratch_length = np.random.randint(30, 100)
            scratch_x_start = np.random.randint(0, self.width - scratch_length)
            
            for x in range(scratch_x_start, scratch_x_start + scratch_length):
                y_offset = int(np.sin(x * 0.1) * 3)
                y = scratch_y + y_offset
                if 0 <= y < self.height:
                    texture[y, x] *= np.random.uniform(0.7, 0.9)
        
        # 광택 처리 (불균일한 광택)
        gloss_map = np.random.normal(1.0, 0.05, (self.height, self.width))
        gloss_map = gaussian_filter(gloss_map, sigma=20)
        
        for c in range(3):
            texture[:, :, c] *= gloss_map
        
        # 최종 노이즈 추가
        noise = np.random.normal(0, 2, texture.shape)
        texture += noise
        
        return Image.fromarray(np.clip(texture, 0, 255).astype(np.uint8))
    
    def create_realistic_marble_texture(self):
        """매우 사실적인 대리석 재질 생성"""
        # 기본 대리석 색상 (약간 따뜻한 흰색)
        base_color = np.array([245, 242, 238])
        texture = np.ones((self.height, self.width, 3), dtype=np.float32) * base_color
        
        # 복잡한 대리석 정맥 패턴
        # 1. 주요 정맥
        num_main_veins = np.random.randint(2, 4)
        for _ in range(num_main_veins):
            # 정맥 경로 생성 (베지어 곡선 사용)
            points = []
            num_points = 5
            for i in range(num_points):
                x = np.random.randint(0, self.width)
                y = (self.height // (num_points - 1)) * i
                points.append((x, y))
            
            # 정맥 그리기
            for t in np.linspace(0, 1, 1000):
                # 베지어 곡선 계산
                x, y = self._bezier_curve(points, t)
                x, y = int(x), int(y)
                
                if 0 <= x < self.width and 0 <= y < self.height:
                    # 정맥 중심
                    vein_color = np.array([120, 110, 105])
                    for dx in range(-4, 5):
                        for dy in range(-4, 5):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                dist = np.sqrt(dx**2 + dy**2)
                                if dist < 4:
                                    alpha = (1 - dist / 4) ** 2
                                    texture[ny, nx] = texture[ny, nx] * (1 - alpha) + vein_color * alpha
        
        # 2. 보조 정맥 (더 얇고 연함)
        num_sub_veins = np.random.randint(5, 10)
        for _ in range(num_sub_veins):
            start_x = np.random.randint(0, self.width)
            start_y = np.random.randint(0, self.height)
            length = np.random.randint(50, 150)
            angle = np.random.uniform(0, 2 * np.pi)
            
            for l in range(length):
                x = int(start_x + l * np.cos(angle) + np.sin(l * 0.1) * 10)
                y = int(start_y + l * np.sin(angle))
                
                if 0 <= x < self.width and 0 <= y < self.height:
                    vein_color = np.array([180, 175, 170])
                    alpha = 0.3
                    texture[y, x] = texture[y, x] * (1 - alpha) + vein_color * alpha
        
        # 3. 클라우드 패턴 (대리석의 자연스러운 무늬)
        cloud_scales = [0.005, 0.01, 0.02, 0.04]
        cloud_weights = [1.0, 0.5, 0.25, 0.125]
        
        cloud_pattern = np.zeros((self.height, self.width))
        for scale, weight in zip(cloud_scales, cloud_weights):
            for y in range(self.height):
                for x in range(self.width):
                    value = (np.sin(x * scale) * np.sin(y * scale) + 
                            np.cos(x * scale * 1.5) * np.cos(y * scale * 1.5))
                    cloud_pattern[y, x] += value * weight
        
        # 정규화 및 적용
        cloud_pattern = (cloud_pattern - cloud_pattern.min()) / (cloud_pattern.max() - cloud_pattern.min())
        cloud_color_variation = np.array([20, 15, 10])
        
        for c in range(3):
            texture[:, :, c] += cloud_color_variation[c] * (cloud_pattern - 0.5)
        
        # 4. 미세한 결정 구조
        crystal_pattern = np.random.random((self.height, self.width)) > 0.98
        crystal_positions = np.where(crystal_pattern)
        for y, x in zip(crystal_positions[0], crystal_positions[1]):
            if 0 < x < self.width - 1 and 0 < y < self.height - 1:
                # 작은 반짝이는 점
                texture[y, x] = np.array([255, 255, 255])
        
        # 5. 표면 광택 효과
        # 불균일한 광택 맵 생성
        gloss_map = np.ones((self.height, self.width))
        for _ in range(5):
            x_center = np.random.randint(0, self.width)
            y_center = np.random.randint(0, self.height)
            radius = np.random.randint(50, 150)
            
            y_coords, x_coords = np.ogrid[:self.height, :self.width]
            mask = (x_coords - x_center)**2 + (y_coords - y_center)**2 <= radius**2
            gloss_map[mask] *= 1.05
        
        gloss_map = gaussian_filter(gloss_map, sigma=30)
        gloss_map = np.clip(gloss_map, 0.95, 1.05)
        
        for c in range(3):
            texture[:, :, c] *= gloss_map
        
        return Image.fromarray(np.clip(texture, 0, 255).astype(np.uint8))
    
    def _bezier_curve(self, points, t):
        """베지어 곡선 계산"""
        n = len(points) - 1
        x = 0
        y = 0
        for i, (px, py) in enumerate(points):
            b = self._bernstein(n, i, t)
            x += px * b
            y += py * b
        return x, y
    
    def _bernstein(self, n, i, t):
        """베른슈타인 다항식"""
        from math import comb
        return comb(n, i) * (t ** i) * ((1 - t) ** (n - i))
    
    def create_engraved_text(self, base_image, text, position, font_size, is_vertical=True,
                           material='wood'):
        """실제 각인 효과 생성"""
        # numpy 배열로 변환
        base_array = np.array(base_image).astype(np.float32)
        
        # 텍스트 마스크 생성
        mask_img = Image.new('L', (self.width, self.height), 0)
        mask_draw = ImageDraw.Draw(mask_img)
        
        # 폰트 가져오기
        font = self.get_korean_font(font_size)
        
        x, y = position
        if is_vertical:
            for i, char in enumerate(text):
                mask_draw.text((x, y + i * font_size), char, font=font, fill=255)
        else:
            mask_draw.text((x, y), text, font=font, fill=255)
        
        # 마스크를 numpy 배열로 변환
        mask_array = np.array(mask_img).astype(np.float32) / 255
        
        # 가우시안 블러로 부드러운 엣지
        mask_blurred = gaussian_filter(mask_array, sigma=1.5)
        
        # 깊이 맵 생성 (각인 깊이)
        depth_map = mask_blurred * 30  # 최대 깊이 30
        
        # 법선 맵 계산 (Sobel 필터 사용)
        grad_x = sobel(depth_map, axis=1)
        grad_y = sobel(depth_map, axis=0)
        
        # 조명 계산
        light_dir = np.array([0.3, -0.3, 0.9])  # 우상단에서 비추는 조명
        light_dir = light_dir / np.linalg.norm(light_dir)
        
        # 각 픽셀에 대한 조명 효과 계산
        for y in range(self.height):
            for x in range(self.width):
                if mask_blurred[y, x] > 0:
                    # 법선 벡터
                    normal = np.array([-grad_x[y, x], -grad_y[y, x], 1])
                    normal = normal / (np.linalg.norm(normal) + 1e-6)
                    
                    # 조명 강도
                    light_intensity = max(0, np.dot(normal, light_dir))
                    
                    # 각인 부분 어둡게
                    engraving_darkness = 0.3 + 0.2 * light_intensity
                    
                    # 재질별 처리
                    if material == 'wood':
                        # 나무는 각인 부분이 더 어둡고 거침
                        base_array[y, x] *= engraving_darkness
                        # 나무결이 끊기는 효과
                        if mask_array[y, x] > 0.5:
                            base_array[y, x] *= 0.8
                    else:  # marble
                        # 대리석은 각인 부분이 매끄럽고 그림자가 강함
                        base_array[y, x] *= (0.4 + 0.4 * light_intensity)
                        # 각인 엣지 하이라이트
                        if 0.1 < mask_blurred[y, x] < 0.5:
                            base_array[y, x] *= 1.2
        
        # 앰비언트 오클루전 (각인 깊이에 따른 추가 그림자)
        ao_map = gaussian_filter(depth_map, sigma=5)
        ao_factor = 1 - (ao_map / ao_map.max()) * 0.3
        
        for c in range(3):
            base_array[:, :, c] *= ao_factor
        
        return Image.fromarray(np.clip(base_array, 0, 255).astype(np.uint8))
    
    def get_korean_font(self, font_size):
        """한글 폰트 찾기"""
        system = platform.system()
        
        font_paths = []
        if system == "Darwin":  # macOS
            font_paths = [
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                "/Library/Fonts/AppleGothic.ttf",
                "/System/Library/Fonts/Supplemental/AppleMyungjo.ttf",
            ]
        elif system == "Windows":
            font_paths = [
                "C:/Windows/Fonts/malgun.ttf",
                "C:/Windows/Fonts/gulim.ttc",
            ]
        else:  # Linux
            font_paths = [
                "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
            ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, font_size)
            except:
                continue
                
        return ImageFont.load_default()
    
    def add_depth_shadow(self, image):
        """3D 깊이감을 위한 그림자 추가"""
        # 이미지 크기보다 약간 큰 캔버스
        shadow_size = 10
        canvas = Image.new('RGBA', 
                          (image.width + shadow_size * 2, image.height + shadow_size * 2), 
                          (0, 0, 0, 0))
        
        # 그림자 레이어
        shadow = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        
        # 여러 레이어의 그림자로 부드러운 효과
        for i in range(shadow_size):
            alpha = int(80 * (1 - i / shadow_size))
            offset = i + 5
            shadow_draw.rounded_rectangle(
                [(offset, offset), 
                 (image.width + offset, image.height + offset)],
                radius=20,
                fill=(0, 0, 0, alpha)
            )
        
        # 블러 효과
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))
        
        # 합성
        canvas.paste(shadow, (0, 0), shadow)
        canvas.paste(image, (shadow_size, shadow_size), image)
        
        return canvas
    
    def create_nameplate(self, main_text="홍길동", sub_text="충북 청산면 백운리", 
                        material='wood', save_path=None, transparent_bg=True):
        """최종 문패 생성"""
        # 재질 생성
        if material == 'wood':
            base_image = self.create_realistic_wood_texture()
        else:
            base_image = self.create_realistic_marble_texture()
        
        # 텍스트 각인
        # 메인 텍스트 (큰 글씨, 중앙)
        result = self.create_engraved_text(
            base_image,
            main_text,
            position=(self.width // 2 - 50, 100),
            font_size=90,
            is_vertical=True,
            material=material
        )
        
        # 서브 텍스트 (작은 글씨, 오른쪽)
        result = self.create_engraved_text(
            result,
            sub_text,
            position=(self.width // 2 + 70, 150),
            font_size=28,
            is_vertical=True,
            material=material
        )
        
        # 문패 모양으로 자르기 (둥근 사각형)
        if transparent_bg:
            # 알파 채널 추가
            result_rgba = result.convert('RGBA')
            
            # 마스크 생성
            mask = Image.new('L', (self.width, self.height), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle([(0, 0), (self.width, self.height)], 
                                       radius=30, fill=255)
            
            # 알파 채널 적용
            result_rgba.putalpha(mask)
            
            # 3D 그림자 추가
            result_with_shadow = self.add_depth_shadow(result_rgba)
            
            final_result = result_with_shadow
        else:
            final_result = result
        
        # 저장
        if save_path is None:
            save_path = f"nameplate_{material}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        final_result.save(save_path, quality=95)
        print(f"{material} 문패가 저장되었습니다: {save_path}")
        
        return final_result

# 사용 예시
if __name__ == "__main__":
    # 문패 생성기 초기화
    generator = RealisticNameplateGenerator(width=350, height=700)
    
    # 나무 문패 생성 (투명 배경)
    wood_nameplate = generator.create_nameplate(
        main_text="홍길동",
        sub_text="충북 청산면 백운리",
        material='wood',
        save_path='nameplate_wood_realistic.png',
        transparent_bg=True
    )
    
    # 대리석 문패 생성 (투명 배경)
    marble_nameplate = generator.create_nameplate(
        main_text="홍길동",
        sub_text="충북 청산면 백운리",
        material='marble',
        save_path='nameplate_marble_realistic.png',
        transparent_bg=True
    )
    
    print("\n생성 완료!")
    print("- nameplate_wood_realistic.png: 사실적인 나무 문패 (투명 배경)")
    print("- nameplate_marble_realistic.png: 사실적인 대리석 문패 (투명 배경)")
    
    # 배경이 있는 버전도 생성 (선택사항)
    """
    generator.create_nameplate(
        main_text="홍길동",
        sub_text="충북 청산면 백운리",
        material='wood',
        save_path='nameplate_wood_with_bg.png',
        transparent_bg=False
    )
    """