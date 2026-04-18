import yfinance as yf
from notion_client import Client
import math
import time

# 💡 내 컴퓨터에서 딱 한 번만 돌리는 용도이므로 실제 키를 직접 입력합니다.
NOTION_TOKEN = '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'.strip()
DATABASE_ID = '33fea659791f8077ac00000c9bc10a8b'.strip()

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
    
    # 전일 대비를 구하려면 그 전날의 종가가 필요하므로, 수집은 2월 10일부터 넉넉히 시작합니다.
    START_FETCH = "2026-02-10"
    # 실제 노션에 기록을 시작할 타겟 날짜입니다.
    TARGET_START = "2026-02-20"
    
    results = []
    
    for name, ticker in tickers.items():
        print(f"📊 {name} 데이터 분석 중...")
        try:
            # end 파라미터를 생략하면 지정한 시작일부터 어제/오늘 최신 데이터까지 전부 가져옵니다.
            data = yf.Ticker(ticker).history(start=START_FETCH)
            
            # 첫 번째 날짜는 전일 데이터가 없으므로 인덱스 1부터 반복합니다.
            for i in range(1, len(data)):
                current_date_str = data.index[i].strftime("%Y-%m-%d")
                
                # 2월 20일 이전의 데이터는 계산용일 뿐이므로 노션 전송 목록에서 제외합니다!
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

# ==========================================
# 노션 대량 전송 함수
# ==========================================
def insert_to_notion(data_list):
    # 약 6개 지표 * 40 영업일 = 240개 이상의 데이터를 쏠 예정입니다.
    print(f"\n📝 총 {len(data_list)}개의 데이터를 노션에 입력합니다.")
    print("너무 빨리 보내면 노션 API가 차단할 수 있어 천천히 입력됩니다. (커피 한 잔 드시고 오세요!)")
    
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
            
            # 💡 핵심: API 호출 속도 제한(Rate Limit)을 피하기 위해 0.3초씩 쉬어줍니다.
            time.sleep(0.3)
            
            # 50개마다 콘솔에 진행 상황을 알려줍니다.
            if success_cnt % 50 == 0:
                print(f"🔄 진행 중... ({success_cnt}/{len(data_list)})")
                
        except Exception as e:
            print(f"❌ {data['날짜']} {data['지수명']} 에러: {e}")
            
    print(f"\n✅ 드디어 완료! 총 {success_cnt}개의 과거 데이터가 노션에 안전하게 저장되었습니다.")

if __name__ == "__main__":
    past_data = backfill_data()
    
    if past_data:
        insert_to_notion(past_data)
    else:
        print("데이터를 가져오지 못했습니다.")
