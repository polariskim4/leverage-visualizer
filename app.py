import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import numpy as np
import re

# 페이지 설정
st.set_page_config(page_title="Leverage Visualizer", layout="wide")

st.title("📈 레버리지 수익률 및 MDD 분석")

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
    
    if data.empty or len(data) < (years * 200):
        return None, None
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
        
    price_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
    
    daily_returns = data[price_col].pct_change().dropna()
    leveraged_returns = daily_returns * leverage
    
    # CAGR 계산
    cumulative_return = (1 + leveraged_returns).prod()
    cagr = (cumulative_return ** (1 / years)) - 1
    
    # MDD 계산
    cum_returns = (1 + leveraged_returns).cumprod()
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    mdd = drawdown.min()
    
    return cagr * 100, mdd * 100

target_ticker = st.text_input("분석할 종목 티커를 입력하세요:", value="NVDA").upper()

if target_ticker:
    try:
        with st.spinner(f'{target_ticker} 데이터를 분석 중...'):
            results = []
            periods = [1, 3, 5, 10]
            
            # 분석 리스트 구성
            tickers_to_analyze = []
            for t in benchmarks.keys(): 
                tickers_to_analyze.append((t, 1, f"{t} (BM)"))
            tickers_to_analyze.append((target_ticker, 1, f"{target_ticker} (1x)"))
            tickers_to_analyze.append((target_ticker, 2, f"{target_ticker} (2x Sim)"))

            for symbol, lev, label in tickers_to_analyze:
                row = {"Asset": label}
                for yr in periods:
                    cagr, mdd = get_metrics(symbol, yr, leverage=lev)
                    if cagr is not None and not np.isnan(cagr):
                        row[f"{yr}Y (MDD)"] = f"{cagr:.1f}% ({mdd:.1f}%)"
                    else:
                        row[f"{yr}Y (MDD)"] = "N/A"
                results.append(row)
            
            df = pd.DataFrame(results)
            
            st.subheader(f"📊 {target_ticker} vs 벤치마크 성과 비교")
            
            # HTML 변환
            html_table = df.to_html(escape=False, index=False)
            
            # MDD 빨간색 강조
            html_table = re.sub(r'(\(-?\d+\.\d+%\))', r'<span style="color: #ff4b4b; font-weight: bold;">\1</span>', html_table)
            
            # 핵심 항목 강조 (QLD, USD, Target 1x, Target 2x)
            highlight_targets = ["QLD (BM)", "USD (BM)", f"{target_ticker} (1x)", f"{target_ticker} (2x Sim)"]
            for target in highlight_targets:
                pattern = rf'<tr>\s*<td>{re.escape(target)}</td>'
                replacement = f'<tr style="background-color: #fafff0; font-weight: bold; border: 2px solid #d4edda;"><td>{target}</td>'
                html_table = re.sub(pattern, replacement, html_table)

            # CSS 및 테이블 출력
            st.markdown(
                """
                <style>
                .custom-table table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
                .custom-table th { background-color: #f0f2f6; color: #31333F; text-align: center; padding: 12px; border: 1px solid #dee2e6; }
                .custom-table td { text-align: center; padding: 12px; border: 1px solid #dee2e6; }
                </style>
                <div class="custom-table">
                """ + html_table + "</div>", 
                unsafe_allow_html=True
            )
            
            st.info(f"💡 강조 항목: QLD, USD, {target_ticker} (괄호 안 빨간색 수치는 MDD입니다)")

    except Exception as e:
        st.error(f"오류 발생: {e}")
