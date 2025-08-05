import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd

# 웹 드라이버 설정
# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # 헤드리스 모드
chrome_options.add_argument("--no-sandbox")  # 보안 모드 해제
chrome_options.add_argument("--disable-dev-shm-usage")  # 자원 사용 최적화

# Chrome 드라이버 경로 설정
service = Service(ChromeDriverManager().install())  # chromedriver 경로

# 드라이버 초기화
driver = webdriver.Chrome(service=service, options=chrome_options)

# 페이지 열기
url = 'https://www.modetour.com/flights/discount-flight?query=%7B%22departureCity%22%3A%22%22%2C%22arrivalCity%22%3A%22%22%2C%22continentCode%22%3A%22EUR%22%2C%22departureDate%22%3A%222025-02-23%22%2C%22arrivalDate%22%3A%222025-03-25%22%7D'  # 여기에 실제 URL을 입력하세요.
driver.get(url)

# '유럽' 버튼 클릭
try:
    # 버튼이 클릭 가능할 때까지 대기
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[text()='유럽']"))
    )
    # 클릭하기 전에 스크롤
    driver.execute_script("arguments[0].scrollIntoView();", button)
    
    # JavaScript로 클릭
    driver.execute_script("arguments[0].click();", button)

    # 페이지가 로드될 때까지 대기
    time.sleep(5)  # 필요에 따라 대기 시간 조정

except Exception as e:
    print(f"예외가 발생했습니다: {e}")

# HTML 파싱
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# 항공편 정보 추출
def parse_flight_data(soup):
    flights = []
    for flight_div in soup.find_all('div', class_='rounded-[10px]'):
        airline = flight_div.find('span', class_='font-bold')
        if airline:
            airline = airline.text.strip()
        else:
            print("항공사 이름을 찾을 수 없습니다.")
            continue  # 항공사 이름이 없으면 다음으로 넘어감

        destination = flight_div.find_all('span', class_='text-[14px] font-medium text-[#555555]')
        if len(destination) > 1:
            destination = destination[1].text.strip()
        else:
            print("목적지를 찾을 수 없습니다.")
            continue  # 목적지가 없으면 다음으로 넘어감

        direct_flight = flight_div.find('span', class_='rounded-[13px] bg-primary2')
        direct_flight = direct_flight.text.strip() == "직항" if direct_flight else False

        price_text = flight_div.find('span', class_='text-[24px] font-bold')
        if price_text:
            price = int(price_text.text.replace(',', '').replace('원', '').strip())
        else:
            print("가격 정보를 찾을 수 없습니다.")
            continue  # 가격 정보가 없으면 다음으로 넘어감

        flights.append({
            'airline': airline,
            'destination': destination,
            'direct_flight': direct_flight,
            'price': price
        })
    return flights

# 항공편 데이터 파싱
flights = parse_flight_data(soup)

# 가장 낮은 가격의 항공편을 찾는 함수
def find_lowest_price_flights(flights):
    df = pd.DataFrame(flights)
    lowest_prices = df.groupby(['destination', 'direct_flight']).apply(lambda x: x.loc[x['price'].idxmin()])
    return lowest_prices.reset_index(drop=True)

# 가장 낮은 가격 항공편 찾기
lowest_price_flights = find_lowest_price_flights(flights)

# JSON으로 변환 및 출력
result_json = lowest_price_flights.to_json(orient='records', force_ascii=False)
print(result_json)

# 웹 드라이버 종료
driver.quit()