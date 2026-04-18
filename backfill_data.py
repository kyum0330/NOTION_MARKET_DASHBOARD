import yfinance as yf
from notion_client import Client
import math
import time
import os

# 💡 깃허브 클라우드용: Secrets 금고에서 키 값을 안전하게 가져옵니다!
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')

notion = Client(auth=NOTION_TOKEN)

def backfill_data():
    print("⏳ 과거 데이터를 수집합니다 (2026-02-20 ~ 최근)...")
    
    tickers = {
        "코스피": "^KS11",
        "나스닥": "^IXIC",
        "원달러환율": "KRW=X",
        "원엔환율(100엔)": "JPYKRW=X", 
        "달러인덱스": "DX-Y.NYB",
        "WTI(국제유가)": "CL=F"
    }
    
    START_FETCH = "2026-02-10"
    TARGET_START = "2026-02-20"
    
    results = []
    
    for name, ticker in tickers.items():
        print(f"📊 {name} 데이터 분석 중...")
        try:
            data = yf.Ticker(ticker).history(start=START_FETCH)
            
            for i in range(1, len(data)):
                # 💡 서버 시간(datetime.now)을 쓰지 않고 데이터의 실제 거래일을 씁니다!
                current_date_str = data.index[i].strftime("%Y-%m-%d")
                
                if current_date_str < TARGET_START:
                    continue
                    
                current_price = data['Close'].iloc[i]
                prev_price = data['Close'].iloc[i-1]
                
                volume = 0
                if 'Volume' in data.columns:
                    vol_data = data['Volume'].iloc[i]
                    if not math.isnan(vol_data):
                        volume = int(vol_data)
                        
                if ticker == "JPYKRW=X":
                    current_price *= 100
                    prev_price *= 100
                    
                vs = current_price - prev_price
                fltrt = (vs / prev_price) * 100
                
                results.append({
                    "날짜": current_date_str,
                    "지수명": name,
                    "현재가": round(current_price, 2),
                    "전일대비": round(vs, 2),
                    "등락률": round(fltrt, 2),
                    "거래량": volume
                })
        except Exception as e:
            print(f"⚠️ {name} 과거 데이터 수집 실패: {e}")
            
    return results

def insert_to_notion(data_list):
    print(f"\n📝 총 {len(data_list)}개의 데이터를 노션에 입력합니다.")
    print("너무 빨리 보내면 노션 API가 차단할 수 있어 천천히 입력됩니다.")
    
    success_cnt = 0
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
            success_cnt += 1
            time.sleep(0.3)
            
            if success_cnt % 50 == 0:
                print(f"🔄 진행 중... ({success_cnt}/{len(data_list)})")
                
        except Exception as e:
            print(f"❌ {data['날짜']} {data['지수명']} 에러: {e}")
            
    print(f"\n✅ 완료! 총 {success_cnt}개의 과거 데이터가 노션에 저장되었습니다.")

if __name__ == "__main__":
    past_data = backfill_data()
    if past_data:
        insert_to_notion(past_data)
    else:
        print("데이터를 가져오지 못했습니다.")
