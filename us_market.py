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
