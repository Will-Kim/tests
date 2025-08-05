import torch
from diffusers import StableDiffusionPipeline
from huggingface_hub import HfApi, login
from transformers import pipeline
from PIL import Image
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime


# 환경변수 로드
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 키와 설정을 환경변수에서 가져옵니다
openai_api_key = os.getenv('OPENAI_API_KEY', '')
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'CompVis/stable-diffusion-v1-4')

def recommend_model(user_input):
    try:
        # OpenAI GPT API 호출 예시
        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4",  # 또는 "gpt-3.5-turbo"
            "messages": [
                {"role": "system", "content": "다음 입력에 적합한 스테이블 디퓨전 모델을 추천해주세요. 결과는 csv로 다음과 같이 결과값만 돌려주세요. CompVis/stable-diffusion-v1-4,stabilityai/stable-diffusion-2-1"},
                {"role": "user", "content": user_input}
            ]
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        response_json = response.json()
        print(response_json)
        recommended_model = response_json["choices"][0]["message"]["content"]
        print(recommended_model)
        return recommended_model
    
    except Exception as e:
        print(f"모델 추천 중 오류 발생: {e}")
        return DEFAULT_MODEL


# Hugging Face 토큰은 환경변수에서 가져옵니다
hf_token = os.getenv('HF_TOKEN', '')
if hf_token:
    login(hf_token)
else:
    print("⚠️  HF_TOKEN이 설정되지 않았습니다. .env 파일을 확인해주세요.")

# Hugging Face API 인스턴스 생성
api = HfApi()

# # LLaMA 모델 로드
# llm = pipeline("text-generation", model="gpt2")

# def get_model_recommendation(prompt):
#     llm_prompt = f"Suggest a suitable stable diffusion model for generating an image based on the following description: '{prompt}'"
#     response = llm(llm_prompt, max_new_tokens=50, num_return_sequences=1, truncation=True)
#     recommended_model = response[0]['generated_text'].strip()
#     return recommended_model

def find_model(prompt):
    try: 
        # 모델 추천 받기
        recommended_model = recommend_model(prompt) #get_model_recommendation(prompt)
        
        # 추천된 모델을 Hugging Face Hub에서 검색
        models = api.list_models(filter=recommended_model)
        if len(models) > 0:
            print(f'model: {models[0].modelId}')
            return models[0].modelId  # 첫 번째 모델 반환
        else:
            print("적절한 모델을 찾을 수 없습니다. 기본 모델을 사용합니다.")
            return DEFAULT_MODEL  # 기본 모델을 지정
    except Exception as ex:
        print(f'Exception in find_model({prompt}): {ex}')
        return DEFAULT_MODEL  # 기본 모델을 지정

# 2. 적절한 모델 목록에서 첫번째 모델을 가져와서 유저의 입력텍스트에 맞게 이미지를 생성
def generate_image_from_text(user_input):
    # 모델 찾기
    model_name = find_model(user_input)
    
    # 디바이스 설정 (MPS, CUDA, CPU 중 선택)
    if torch.backends.mps.is_available():
        os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
        torch.mps.empty_cache()
        device = "mps"  # MPS (Mac GPU) 사용
        torch_dtype = torch.float32  # MPS는 float16을 완벽히 지원하지 않음
    elif torch.cuda.is_available():
        device = "cuda"  # CUDA (NVIDIA GPU) 사용
        torch_dtype = torch.float16
    else:
        device = "cpu"  # CPU 사용
        torch_dtype = torch.float32
    
    try:
        # 파이프라인 로드
        pipe = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=torch_dtype)
        pipe = pipe.to(device)
    except Exception as ex:
        print(f'Error in pipline: {ex}')
        # 파이프라인 로드
        pipe = StableDiffusionPipeline.from_pretrained(DEFAULT_MODEL, torch_dtype=torch_dtype)  
        pipe = pipe.to(device)
    
    # 이미지 생성
    if device == "cuda":
        with torch.autocast("cuda"):
            image = pipe(user_input).images[0]
    else:
        image = pipe(user_input).images[0]
    
    # 이미지 저장
    image.save(f'results/sd_{datetime.now()}.png')  # 이미지를 "output_image.png"로 저장
    
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