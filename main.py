import yfinance as yf
from notion_client import Client
from datetime import datetime
import math

# ==========================================
# 1. 노션 설정 (본인의 키값으로 변경하세요)
# ==========================================
NOTION_TOKEN = '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'.strip()
DATABASE_ID = '33fea659791f806d8937cd6a989991a0'.strip() 

notion = Client(auth=NOTION_TOKEN)

# ==========================================
# 2. 데이터 수집 및 계산 함수
# ==========================================
def get_all_market_data():
    print("🌍 글로벌 경제 데이터를 수집하고 계산 중입니다...")
    
    tickers = {
        "코스피": "^KS11",
        "나스닥": "^IXIC",
        "원달러환율": "KRW=X",
        "원엔환율(100엔)": "JPYKRW=X", 
        "달러인덱스": "DX-Y.NYB",
        "WTI(국제유가)": "CL=F"
    }
    
    results = []
    today_str = datetime.now().strftime("%Y-%m-%d")
    
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
                    "날짜": today_str,
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
    market_data = get_all_market_data()
    
    if market_data:
        insert_to_notion(market_data)
        print("\n✨ 모든 지표가 거래량과 함께 노션에 성공적으로 기록되었습니다!")
    else:
        print("❌ 데이터를 수집하지 못했습니다.")