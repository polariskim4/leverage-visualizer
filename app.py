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
    "FNGO": "FNGS 2x",  # 추가
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
    
    cumulative_return = (1 + leveraged_returns).prod()
    cagr = (cumulative_return ** (1 / years)) - 1
    
    cum_returns = (1 + leveraged_returns).cumprod()
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    mdd = drawdown.min()
    
    return cagr * 100, mdd * 100

target_ticker = st.text_input("분석할 종목 티커를 입력하세요:", value="AAPL").upper()

if target_ticker:
    try:
        with st.spinner(f'{target_ticker} 데이터 분석 중...'):
            results = []
            periods = [1, 3, 5, 10]
            
            tickers_to_analyze = []
            for t in benchmarks.keys(): 
                tickers_to_analyze.append((t, 1, f"{t} (BM)"))
            tickers_to_analyze.append((target_ticker, 1, f"{target_ticker} (1x)"))
            tickers_to_analyze.append((target_ticker, 2, f"{target_ticker} (2x Sim)"))

            for symbol, lev, label in tickers_to_analyze:
                row = {"Asset": label}
                for yr in periods:
                    cagr, mdd = get_metrics(symbol, yr, leverage=lev)
                    if cagr is not None:
                        row[f"{yr}Y (MDD)"] = f"{cagr:.1f}% ({mdd:.1f}%)"
                    else:
                        row[f"{yr}Y (MDD)"] = "N/A"
                results.append(row)
            
            df = pd.DataFrame(results)
            
            # HTML 생성 및 텍스트 후처리
            html_table = df.to_html(index=False)
            
            # 1. MDD 빨간색 강조
            html_table = re.sub(r'(\(-?\d+\.\d+%\))', r'<span style="color: #ff4b4b; font-weight: bold;">\1</span>', html_table)
            
            # 2. 강조 항목 스타일 적용 (QLD, USD, Target 1x, 2x)
            highlight_targets = ["QLD (BM)", "USD (BM)", f"{target_ticker} (1x)", f"{target_ticker} (2x Sim)"]
            for target in highlight_targets:
                # <tr> 태그 바로 뒤에 스타일 삽입 (가장 원시적이지만 확실한 방법)
                html_table = html_table.replace(f'<tr>\n      <td>{target}</td>', f'<tr style="background-color: #fafff0; font-weight: bold;">\n      <td>{target}</td>')
                # 혹시 모를 공백 차이 대응
                html_table = html_table.replace(f'<tr><td>{target}</td>', f'<tr style="background-color: #fafff0; font-weight: bold;"><td>{target}</td>')

            # 스타일 정의
            style = """
            <style>
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 10px 0;
                    font-size: 15px;
                    text-align: center;
                }
                th {
                    background-color: #f0f2f6;
                    padding: 12px;
                    border: 1px solid #dee2e6;
                }
                td {
                    padding: 12px;
                    border: 1px solid #dee2e6;
                }
            </style>
            """
            
            st.subheader(f"📊 {target_ticker} vs 벤치마크 성과 비교")
            # 스타일과 테이블을 분리하여 렌더링
            st.markdown(style, unsafe_allow_html=True)
            st.markdown(html_table, unsafe_allow_html=True)
            st.info(f"💡 강조 항목: QLD, USD, {target_ticker} (괄호 안 빨간색은 MDD)")

    except Exception as e:
        st.error(f"오류 발생: {e}")
