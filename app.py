import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import numpy as np

# 페이지 설정
st.set_page_config(page_title="Leverage Visualizer", layout="wide")

st.title("📈 레버리지 수익률(CAGR) 및 리스크(MDD) 분석")

# 벤치마크 티커 설정
benchmarks = {
    "QLD": "Nasdaq 100 2x",
    "TQQQ": "Nasdaq 100 3x",
    "TECL": "Technology 3x",
    "USD": "Semiconductor 2x",
    "SOXL": "Semiconductor 3x"
}

def get_metrics(ticker_symbol, years, leverage=1):
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=int(years * 365.25))
    
    # auto_adjust=False로 설정하여 Adj Close를 확실히 가져오거나, 
    # 데이터 구조가 복잡할 경우 Close를 사용하도록 처리
    data = yf.download(ticker_symbol, start=start_date, end=end_date, progress=False)
    
    if data.empty or len(data) < 10:
        return None, None
    
    # 최신 yfinance의 MultiIndex 대응: 
    # 'Adj Close'가 없으면 'Close'를 사용하고, 컬럼이 다중 레벨이면 단일 레벨로 변환
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
        
    price_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
    
    # 일일 수익률 계산 및 레버리지 적용
    daily_returns = data[price_col].pct_change().dropna()
    leveraged_returns = daily_returns * leverage
    
    # 1. CAGR 계산
    cumulative_return = (1 + leveraged_returns).prod()
    cagr = (cumulative_return ** (1 / years)) - 1
    
    # 2. MDD 계산
    cum_returns = (1 + leveraged_returns).cumprod()
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    mdd = drawdown.min()
    
    return cagr * 100, mdd * 100

# 사용자 입력
target_ticker = st.text_input("분석할 종목 티커를 입력하세요:", value="NVDA").upper()

if target_ticker:
    try:
        with st.spinner(f'{target_ticker} 데이터를 불러오는 중...'):
            results = []
            periods = [1, 3, 5, 10]
            
            # 분석 대상 리스트
            tickers_to_analyze = []
            for t in benchmarks.keys(): 
                tickers_to_analyze.append((t, 1, f"{t} (BM)"))
            tickers_to_analyze.append((target_ticker, 1, f"{target_ticker} (1x)"))
            tickers_to_analyze.append((target_ticker, 2, f"{target_ticker} (2x Sim)"))

            for symbol, lev, label in tickers_to_analyze:
                row = {"Asset": label}
                for yr in periods:
                    cagr, mdd = get_metrics(symbol, yr, leverage=lev)
                    # 데이터가 없는 경우 처리
                    row[f"{yr}Y CAGR"] = f"{cagr:.1f}%" if (cagr is not None and not np.isnan(cagr)) else "N/A"
                    row[f"{yr}Y MDD"] = f"{mdd:.1f}%" if (mdd is not None and not np.isnan(mdd)) else "N/A"
                results.append(row)
            
            df = pd.DataFrame(results)
            
            st.subheader(f"📊 {target_ticker} vs 벤치마크 상세 비교")
            st.dataframe(df, use_container_width=True)
            st.info("💡 N/A는 해당 종목의 상장 기간이 분석 기간보다 짧음을 의미합니다.")

    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
