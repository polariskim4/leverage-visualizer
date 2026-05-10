import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import numpy as np

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
    
    if data.empty or len(data) < (years * 200): # 상장 기간이 분석 기간보다 짧으면 제외
        return None, None
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
        
    price_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
    
    daily_returns = data[price_col].pct_change().dropna()
    leveraged_returns = daily_returns * leverage
    
    # CAGR
    cumulative_return = (1 + leveraged_returns).prod()
    cagr = (cumulative_return ** (1 / years)) - 1
    
    # MDD
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
            
            tickers_to_analyze = []
            for t in benchmarks.keys(): tickers_to_analyze.append((t, 1, f"{t} (BM)"))
            tickers_to_analyze.append((target_ticker, 1, f"{target_ticker} (1x)"))
            tickers_to_analyze.append((target_ticker, 2, f"{target_ticker} (2x Sim)"))

            for symbol, lev, label in tickers_to_analyze:
                row = {"Asset": label}
                for yr in periods:
                    cagr, mdd = get_metrics(symbol, yr, leverage=lev)
                    if cagr is not None and not np.isnan(cagr):
                        # 수익률 옆에 MDD를 괄호로 표기
                        row[f"{yr}Y (MDD)"] = f"{cagr:.1f}% ({mdd:.1f}%)"
                    else:
                        row[f"{yr}Y (MDD)"] = "N/A"
                results.append(row)
            
            df = pd.DataFrame(results)
            
            # 스타일링 함수: 괄호 안의 MDD 부분만 빨간색으로 보이게 하는 것은 HTML 렌더링이 필요함
            # 여기서는 전체 셀의 가독성을 높이기 위해 배경색 스타일링 적용
            st.subheader(f"📊 {target_ticker} 성과 요약 (수익률 (MDD) 순)")
            
            # HTML로 변환하여 출력 (색상 적용을 위해)
            html_table = df.to_html(escape=False, index=False)
            
            # 정규식을 활용해 괄호 안의 숫자(MDD)를 빨간색으로 치환
            import re
            html_table = re.sub(r'(\(-?\d+\.\d+%\))', r'<span style="color: #ff4b4b; font-weight: bold;">\1</span>', html_table)
            
            st.markdown(
                """
                <style>
                table { width: 100%; border-collapse: collapse; }
                th { background-color: #f0f2f6; text-align: center; padding: 10px; }
                td { text-align: center; padding: 10px; border-bottom: 1px solid #ddd; }
                </style>
                """, unsafe_allow_html=True
            )
            st.write(html_table, unsafe_allow_html=True)
            
            st.info("💡 **가이드**: 연평균 수익률 옆 괄호 안의 **빨간색 수치**는 해당 기간의 최대 낙폭(MDD)입니다.")

    except Exception as e:
        st.error(f"오류 발생: {e}")
