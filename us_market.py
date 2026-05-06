import yfinance as yf
from notion_client import Client
import math
import os

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
notion = Client(auth=NOTION_TOKEN)

def get_us_data():
    tickers = {
        "나스닥": "^IXIC",
        "달러인덱스": "DX-Y.NYB",
        "WTI(국제유가)": "CL=F"
    }
    results = []
    
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            
            if len(hist) >= 2:
                # 💡 서버 시차를 무시하는 완벽한 날짜 추출!
                actual_date = hist.index[-1].strftime("%Y-%m-%d")
                
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                
                volume = 0
                if 'Volume' in hist.columns:
                    vol_data = hist['Volume'].iloc[-1]
                    if not math.isnan(vol_data):
                        volume = int(vol_data)
                
                vs = current_price - prev_price
                fltrt = (vs / prev_price) * 100
                
                results.append({
                    "날짜": actual_date,  
                    "지수명": name,
                    "현재가": round(current_price, 2),
                    "전일대비": round(vs, 2),
                    "등락률": round(fltrt, 2),
                    "거래량": volume
                })
        except Exception as e:
            print(f"⚠️ {name} 데이터 수집 실패: {e}")
            
    return results

# ==========================================
# 3. 노션 전송 함수 (이 부분이 빠져있었습니다!)
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
                    "거래량": {"number": data['거래량']} 
                }
            )
            print(f"✅ {data['지수명']} 저장 완료!")
        except Exception as e:
            print(f"❌ {data['지수명']} 저장 중 에러 발생: {e}")

# ==========================================
# 4. 메인 실행부 (실제 코드를 작동시키는 스위치!)
# ==========================================
if __name__ == "__main__":
    market_data = get_us_data()
    
    if market_data:
        insert_to_notion(market_data)
        print("\n✨ 미국장 지표가 거래량과 함께 노션에 성공적으로 기록되었습니다!")
    else:
        print("❌ 데이터를 수집하지 못했습니다.")
