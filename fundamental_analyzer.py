import yfinance as yf
import pandas as pd
import sys
import re
import requests

def get_fundamental_analysis(ticker):
    """
    yfinance와 웹 스크레이핑을 사용하여 특정 티커에 대한 펀더멘탈 및 애널리스트 분석을 제공합니다.
    """
    print(f"\n--- {ticker} 펀더멘탈 및 애널리스트 분석 ---")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        url = f"https://finance.yahoo.com/quote/{ticker}/analysis"
        content = ""
        try:
            header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
            response = requests.get(url, headers=header, timeout=10)
            response.raise_for_status()
            content = response.text
        except Exception as web_e:
            print(f"  - 참고: Yahoo Finance 웹페이지({url})에 접근 중 오류 발생: {web_e}")

        # --- 1. 애널리스트 종합 의견 (상세) ---
        recommendation = info.get('recommendationKey', 'N/A').replace('_', ' ').title()
        recommendation_details = ""
        if content:
            try:
                rec_trends_html = re.search(r'Recommendation Trends(.*?)</div>', content, re.DOTALL)
                if rec_trends_html:
                    trends = re.findall(r'([\d\.]+)</span.*?([a-zA-Z ]+)</div>', rec_trends_html.group(1))
                    details = []
                    mapping = {'Strong Buy': '강력 매수', 'Buy': '매수', 'Hold': '중립', 'Underperform': '시장 하회', 'Sell': '매도'}
                    for count, key in trends:
                        if key in mapping:
                            details.append(f"{mapping[key]}: {count}")
                    if details:
                        recommendation_details = f" ({', '.join(details)})"
            except Exception as parse_e:
                pass # 파싱 실패는 무시
        
        final_recommendation = f"{recommendation}{recommendation_details}"

        target_price = info.get('targetMeanPrice')
        current_price = info.get('regularMarketPrice') or info.get('currentPrice')
        analyst_count = info.get('numberOfAnalystOpinions')
        
        upside_potential = None
        if target_price and current_price:
            upside_potential = ((target_price - current_price) / current_price) * 100

        # --- 2. 성장성 전망 ---
        yoy_growth, five_year_growth = None, None
        if content:
            try:
                earnings_table = re.search(r"Earnings Estimate(.*?)Revenue Estimate", content, re.DOTALL)
                if earnings_table:
                    estimates = re.findall(r"Avg. Estimate</td>.*?<span>([\d\.\-]+)</span>", earnings_table.group(1))
                    if len(estimates) >= 2:
                        current_year_eps = float(estimates[0])
                        next_year_eps = float(estimates[1])
                        if current_year_eps > 0:
                            yoy_growth = ((next_year_eps - current_year_eps) / current_year_eps) * 100
                
                growth_match = re.search(r"Next 5 Years \(per annum\)</td>.*?<span>([\d\.\-%]+)</span>", content)
                if growth_match:
                    five_year_growth = float(growth_match.group(1).strip('%'))
            except Exception as web_e:
                pass # 웹 스크레이핑 실패는 무시

        # --- 3. 핵심 통계 ---
        forward_pe = info.get('forwardPE')
        profit_margin = info.get('profitMargins', 0) * 100
        roe = info.get('returnOnEquity', 0) * 100

        # --- 4. 결과 취합 및 출력 ---
        results = {
            "Analyst Recommendation": final_recommendation,
            "Number of Analysts": analyst_count,
            "Mean Target Price": f"{target_price:.2f}" if target_price else "N/A",
            "Current Price": f"{current_price:.2f}" if current_price else "N/A",
            "Upside Potential": f"{upside_potential:.2f}%" if upside_potential is not None else "N/A",
            "Next Year EPS Growth (YoY)": f"{yoy_growth:.2f}%" if yoy_growth is not None else "N/A",
            "5-Year Growth Estimate (p.a.)": f"{five_year_growth:.2f}%" if five_year_growth is not None else "N/A",
            "Forward P/E": f"{forward_pe:.2f}" if forward_pe else "N/A",
            "Profit Margin": f"{profit_margin:.2f}%",
            "Return on Equity (ROE)": f"{roe:.2f}%"
        }

        print("\n--- 분석 결과 ---")
        for key, value in results.items():
            print(f"  - {key}: {value}")

        # --- 5. 종합 분석 요약 ---
        summary = []
        if analyst_count and recommendation != 'N/A':
            summary.append(f"애널리스트들은 '{recommendation}' 의견이며, 평균적으로 {results['Upside Potential']}의 주가 상승 여력을 기대합니다 ({analyst_count}명 참여). ")
        
        if yoy_growth is not None or five_year_growth is not None:
            growth_summary = "이는 "
            if yoy_growth is not None:
                growth_summary += f"다음 연도 예상 EPS 성장률 {results['Next Year EPS Growth (YoY)']}"
                if five_year_growth is not None:
                    growth_summary += " 및 "
            if five_year_growth is not None:
                growth_summary += f"향후 5년 연평균 성장률 전망 {results['5-Year Growth Estimate (p.a.)']}"
            growth_summary += "에 기반한 것으로 보입니다. "
            summary.append(growth_summary)

        summary.append(f"현재 Forward P/E는 {results['Forward P/E']}이며, 수익성은 순이익률 {results['Profit Margin']}, 자기자본이익률 {results['Return on Equity (ROE)']}로 나타납니다.")

        print("\n--- 종합 요약 ---")
        print(' '.join(summary))
        
        return results

    except Exception as e:
        print(f"'{ticker}' 분석 중 오류 발생: {e}")
        return None

if __name__ == '__main__':
    if len(sys.argv) > 1:
        ticker_to_analyze = sys.argv[1].upper()
    else:
        ticker_to_analyze = input("분석할 티커를 입력하세요 (예: AAPL): ").upper()

    if ticker_to_analyze:
        get_fundamental_analysis(ticker_to_analyze)
    else:
        print("티커가 입력되지 않아 분석을 시작할 수 없습니다.")