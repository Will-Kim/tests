import torch
from diffusers import StableDiffusionPipeline
from PIL import Image
import matplotlib.pyplot as plt

# 1. 유저가 입력한 내용에 적합한 모델을 찾는 함수
def find_suitable_model(user_input):
    # 여기서는 간단히 기본 모델을 사용하지만, 실제로는 사용자 입력에 따라 다른 모델을 선택할 수 있습니다.
    model_name = "CompVis/stable-diffusion-v1-4"
    return model_name

# 2. 적절한 모델 목록에서 첫번째 모델을 가져와서 유저의 입력텍스트에 맞게 이미지를 생성
def generate_image_from_text(user_input):
    # 모델 찾기
    model_name = find_suitable_model(user_input)
    
    # 파이프라인 로드
    if torch.cuda.is_available():
        # GPU가 있는 경우 float16 사용
        pipe = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=torch.float16)
        pipe = pipe.to("cuda")
    else:
        # CPU인 경우 float32 사용
        pipe = StableDiffusionPipeline.from_pretrained(model_name)
        pipe = pipe.to("cpu")
    
    # 이미지 생성
    with torch.autocast("cuda" if torch.cuda.is_available() else "cpu"):
        image = pipe(user_input).images[0]
    
    return image

# 3. 이미지를 보여줌
def display_image(image):
    plt.imshow(image)
    plt.axis('off')  # 축 제거
    plt.show()

# 메인 함수
def main():
    user_input = '토끼 옷을 입은 여성' #input("이미지를 생성할 텍스트를 입력하세요: ")
    image = generate_image_from_text(user_input)
    display_image(image)

if __name__ == "__main__":
    main()