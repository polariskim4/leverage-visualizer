import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import numpy as np

# 페이지 설정
st.set_page_config(page_title="Leverage Benchmark & MDD", layout="wide")

st.title("📈 레버리지 수익률(CAGR) 및 리스크(MDD) 분석")
st.markdown("""
이 대시보드는 벤치마크 레버리지 ETF와 입력하신 종목의 **연평균 수익률(CAGR)** 및 **최대 낙폭(MDD)**을 비교합니다.
* MDD는 해당 기간 중 고점 대비 가장 많이 하락했던 비율을 의미합니다.
""")

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
    
    data = yf.download(ticker_symbol, start=start_date, end=end_date, progress=False)
    
    if data.empty or len(data) < 10: # 데이터가 너무 적으면 무시
        return None, None
    
    # 일일 수익률 계산 및 레버리지 적용
    daily_returns = data['Adj Close'].pct_change().dropna()
    leveraged_returns = daily_returns * leverage
    
    # 1. CAGR 계산
    cumulative_return = (1 + leveraged_returns).prod()
    cagr = (cumulative_return ** (1 / years)) - 1
    
    # 2. MDD 계산 (누적 수익 곡선 기준)
    cum_returns = (1 + leveraged_returns).cumprod()
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    mdd = drawdown.min()
    
    return cagr * 100, mdd * 100

# 사용자 입력
target_ticker = st.text_input("분석할 종목 티커를 입력하세요:", value="NVDA").upper()

if target_ticker:
    with st.spinner('데이터를 분석 중입니다...'):
        results = []
        periods = [1, 3, 5, 10]
        
        # 분석 대상 리스트 구성
        tickers_to_analyze = []
        for t in benchmarks.keys(): tickers_to_analyze.append((t, 1, f"{t} (BM)"))
        tickers_to_analyze.append((target_ticker, 1, f"{target_ticker} (1x)"))
        tickers_to_analyze.append((target_ticker, 2, f"{target_ticker} (2x Sim)"))

        for symbol, lev, label in tickers_to_analyze:
            row = {"Asset": label}
            for yr in periods:
                cagr, mdd = get_metrics(symbol, yr, leverage=lev)
                row[f"{yr}Y CAGR"] = f"{cagr:.1f}%" if cagr is not None else "N/A"
                row[f"{yr}Y MDD"] = f"{mdd:.1f}%" if mdd is not None else "N/A"
            results.append(row)
        
        df = pd.DataFrame(results)
        
        # 결과 표 출력
        st.subheader(f"📊 {target_ticker} vs 벤치마크 상세 비교")
        st.dataframe(df, use_container_width=True)

        # 시각적 가이드
        st.warning("⚠️ **MDD 해석 주의**: MDD가 -50%라면 원금의 절반이 사라진 적이 있다는 뜻이며, -80% 이상은 사실상 퇴출 위기를 의미합니다.")
