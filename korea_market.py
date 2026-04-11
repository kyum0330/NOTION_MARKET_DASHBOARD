import yfinance as yf
from notion_client import Client
from datetime import datetime
import math
import os

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
notion = Client(auth=NOTION_TOKEN)

def get_korea_data():
    tickers = {
        "코스피": "^KS11",
        "원달러환율": "KRW=X",
        "원엔환율(100엔)": "JPYKRW=X"
    }
    results = []
    # 💡 한국장용: 수집하는 당일이 곧 기준일 (오늘)
    target_date = datetime.now().strftime("%Y-%m-%d")
    
      
    for name, ticker in tickers.items():
        try:
            # 안전하게 최근 5일치 데이터를 불러옵니다.
            hist = yf.Ticker(ticker).history(period="5d")
            
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                
                # 거래량 가져오기 (결측치나 데이터가 없는 경우 0으로 처리)
                volume = 0
                if 'Volume' in hist.columns:
                    vol_data = hist['Volume'].iloc[-1]
                    if not math.isnan(vol_data):
                        volume = int(vol_data)
                
                # 원엔환율 100엔 단위 조정
                if ticker == "JPYKRW=X":
                    current_price *= 100
                    prev_price *= 100
                
                vs = current_price - prev_price
                fltrt = (vs / prev_price) * 100
                
                results.append({
                    "날짜": target_date,
                    "지수명": name,
                    "현재가": round(current_price, 2),
                    "전일대비": round(vs, 2),
                    "등락률": round(fltrt, 2),
                    "거래량": volume  # 거래량 추가!
                })
        except Exception as e:
            print(f"⚠️ {name} 데이터 수집 실패: {e}")
            
    return results

# ==========================================
# 3. 노션 전송 함수
# ==========================================
def insert_to_notion(data_list):
    print("📝 노션 데이터베이스에 입력을 시작합니다...")
    for data in data_list:
        try:
            notion.pages.create(
                parent={"database_id": DATABASE_ID},
                properties={
                    "날짜": {"title": [{"text": {"content": data['날짜']}}]},
                    "지수명": {"rich_text": [{"text": {"content": data['지수명']}}]},
                    "현재가": {"number": data['현재가']},
                    "전일대비": {"number": data['전일대비']},
                    "등락률": {"number": data['등락률']},
                    "거래량": {"number": data['거래량']}  # 거래량 추가!
                }
            )
            print(f"✅ {data['지수명']} 저장 완료!")
        except Exception as e:
            print(f"❌ {data['지수명']} 저장 중 에러 발생: {e}")

# ==========================================
# 4. 메인 실행부
# ==========================================
if __name__ == "__main__":
    market_data = get_korea_data()
    
    if market_data:
        insert_to_notion(market_data)
        print("\n✨ 모든 지표가 거래량과 함께 노션에 성공적으로 기록되었습니다!")
    else:
        print("❌ 데이터를 수집하지 못했습니다.")
