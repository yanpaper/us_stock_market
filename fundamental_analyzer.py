import yfinance as yf
import pandas as pd
import sys
import re
import requests
import time # time 모듈 임포트

def get_fundamental_analysis(ticker, sector_avg_pe=None):
    """
    yfinance와 웹 스크레이핑을 사용하여 특정 티커에 대한 펀더멘탈 및 애널리스트 분석을 제공합니다.
    sector_avg_pe 딕셔너리를 받아 산업 평균 P/E를 결과에 포함할 수 있습니다.
    """
    print(f"\n--- {ticker} 펀더멘탈 및 애널리스트 분석 ---")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        url = f"https://finance.yahoo.com/quote/{ticker}/analysis/"
        content = ""
        
        # 웹 스크레이핑 시도 (yfinance .analysis 데이터가 없을 경우 폴백용)
        for attempt in range(3): # 최대 3번 재시도
            try:
                header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
                response = requests.get(url, headers=header, timeout=10)
                response.raise_for_status()
                content = response.text
                break # 성공 시 루프 탈출
            except requests.exceptions.HTTPError as http_err:
                if http_err.response.status_code == 404:
                    print(f"  - 디버그: Yahoo Finance 웹페이지({url}) 접근 중 404 오류 발생")
                    break
                elif http_err.response.status_code == 503:
                    print(f"  - 디버그: Yahoo Finance 웹페이지({url}) 접근 중 503 오류 발생 (재시도 {attempt + 1}/3)... {http_err}")
                    time.sleep(2) # 2초 대기 후 재시도
                else:
                    print(f"  - 디버그: Yahoo Finance 웹페이지({url}) 접근 중 HTTP 오류 발생: {http_err}")
                    break # 다른 HTTP 오류는 재시도 안 함
            except Exception as web_e:
                print(f"  - 디버그: Yahoo Finance 웹페이지({url}) 접근 중 기타 오류 발생: {web_e}")
                break # 기타 오류는 재시도 안 함

        # --- 1. 애널리스트 종합 의견 (상세) ---
        recommendation = info.get('recommendationKey', 'N/A').replace('_', ' ').title()
        recommendation_details = ""

        # yfinance의 stock.recommendations 데이터 사용 시도
        try:
            recs = stock.recommendations
            if recs is not None and not recs.empty:
                # 최신 추천 데이터만 사용
                latest_recs = recs.iloc[-1]
                details_list = []
                # 컬럼 이름을 순회하며 0보다 큰 값을 가진 항목만 추가
                for rec_type in ['strongBuy', 'buy', 'hold', 'sell', 'strongSell']:
                    if rec_type in latest_recs and latest_recs[rec_type] > 0:
                        # 컬럼 이름에서 카멜 케이스를 분리 (예: strongBuy -> Strong Buy)
                        label = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', rec_type).title()
                        details_list.append(f"{label}:{int(latest_recs[rec_type])}")

                if details_list:
                    recommendation_details = f" ({', '.join(details_list)})"
        except Exception as e:
            print(f"  - 디버그: yfinance stock.recommendations 접근 중 오류: {e}")
            pass # 오류 발생 시 웹 스크레이핑 폴백으로 진행

        # stock.recommendations에서 상세 정보를 얻지 못했고, 웹 스크레이핑 content가 있다면 파싱 시도
        if not recommendation_details and content: 
            try:
                rec_trends_html = re.search(r'Recommendation Trends(.*?)</div>', content, re.DOTALL)
                if rec_trends_html:
                    trends = re.findall(r'([\d\.]+)</span.*?([a-zA-Z ]+)</div>', rec_trends_html.group(1))
                    details = []
                    mapping = {'Strong Buy': '강력 매수', 'Buy': '매수', 'Hold': '중립', 'Underperform': '시장 하회', 'Sell': '매도'}
                    for count, key in trends:
                        if key in mapping:
                            details.append(f"{mapping[key]}:{count}")
                    if details:
                        recommendation_details = f" ({', '.join(details)})"
            except Exception as parse_e:
                print(f"  - 디버그: 애널리스트 의견 웹 파싱 실패: {parse_e}")
        
        final_recommendation = f"{recommendation}{recommendation_details}"

        target_price = info.get('targetMeanPrice')
        current_price = info.get('regularMarketPrice') or info.get('currentPrice')
        analyst_count = info.get('numberOfAnalystOpinions')
        
        upside_potential = None
        if target_price and current_price:
            upside_potential = ((target_price - current_price) / current_price) * 100

        # --- 2. 성장성 전망 ---
        yoy_growth, five_year_growth = None, None
        
        # yfinance .analysis 데이터 우선 사용
        try:
            analysis = stock.analysis
            if analysis is None or analysis.empty:
                print("  - 디버그: yfinance .analysis 데이터가 비어있습니다. 웹 스크레이핑 시도.")
                raise ValueError("Empty analysis data") # 웹 스크레이핑 폴백 로직을 타도록 예외 발생

            # yfinance 라이브러리에서 데이터 추출
            eps_estimate = analysis.loc['Earnings Estimate']
            current_year_eps = eps_estimate[eps_estimate.index == '0y']['Avg. Estimate'].iloc[0]
            next_year_eps = eps_estimate[eps_estimate.index == '+1y']['Avg. Estimate'].iloc[0]
            if current_year_eps and next_year_eps and current_year_eps > 0:
                yoy_growth = ((next_year_eps - current_year_eps) / current_year_eps) * 100

            growth_estimate = analysis.loc['Growth']
            five_year_growth_str = growth_estimate[growth_estimate.index == '+5y']['Avg. Estimate'].iloc[0]
            if isinstance(five_year_growth_str, str) and '%' in five_year_growth_str:
                five_year_growth = float(five_year_growth_str.strip('%'))

        except Exception:
            # 폴백(Fallback) 로직: Yahoo Finance 웹에서 직접 데이터 가져오기
            if content: # 웹 스크레이핑 성공했을 경우에만 파싱 시도
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
                    print(f"    - 디버그: 웹 데이터 파싱 실패: {web_e}")

        # --- 3. 핵심 통계 ---
        forward_pe = info.get('forwardPE')
        profit_margin = info.get('profitMargins', 0) * 100
        roe = info.get('returnOnEquity', 0) * 100
        sector = info.get('sector')
        avg_pe_for_sector = sector_avg_pe.get(sector) if sector_avg_pe and sector else None

        # P/E 비교 문자열 생성
        pe_display_string = "N/A"
        if forward_pe and avg_pe_for_sector:
            pe_diff = forward_pe - avg_pe_for_sector
            pe_display_string = f"{forward_pe:.2f} (평균 대비 {pe_diff:+.2f})"
        elif forward_pe:
            pe_display_string = f"{forward_pe:.2f} (산업 평균 N/A)"

        # 애널리스트 분석 문자열 생성
        recommendation_breakdown = recommendation_details.strip(" ()")

        # 현재가 및 상승여력 문자열 생성
        price_display_string = "N/A"
        if current_price and upside_potential is not None:
            price_display_string = f"{current_price:.2f} (Target Upside: {upside_potential:+.2f}%)"
        elif current_price:
            price_display_string = f"{current_price:.2f}"

        # --- 4. 결과 취합 및 출력 ---
        results = {
            "Analyst Recommendation": recommendation,
            "Detailed": recommendation_breakdown if recommendation_breakdown else "N/A",
            "Current Price": price_display_string,
            "Next Year EPS Growth (YoY)": f"{yoy_growth:.2f}%" if yoy_growth is not None else "N/A",
            "5-Year Growth Estimate": f"{five_year_growth:.2f}%" if five_year_growth is not None else "N/A",
            "Forward P/E (vs Sector)": pe_display_string,
            "Profit Margin": f"{profit_margin:.2f}%",
            "Return on Equity (ROE)": f"{roe:.2f}%"
        }

        print("\n--- 분석 결과 ---")
        for key, value in results.items():
            print(f"  - {key}: {value}")

        # --- 5. 종합 분석 요약 ---
        summary = []
        if analyst_count and recommendation != 'N/A':
            if upside_potential is not None:
                summary.append(f"애널리스트들은 '{recommendation}' 의견이며, 평균적으로 {upside_potential:.2f}%의 주가 상승 여력을 기대합니다 ({analyst_count}명 참여). ")
            else:
                summary.append(f"애널리스트들은 '{recommendation}' 의견입니다 ({analyst_count}명 참여). ")
        
        if yoy_growth is not None or five_year_growth is not None:
            growth_summary = "이는 "
            if yoy_growth is not None:
                growth_summary += f"다음 연도 예상 EPS 성장률 {results['Next Year EPS Growth (YoY)']}"
                if five_year_growth is not None:
                    growth_summary += " 및 "
            if five_year_growth is not None:
                growth_summary += f"향후 5년 연평균 성장률 전망 {results['5-Year Growth Estimate']}"
            growth_summary += "에 기반한 것으로 보입니다. "
            summary.append(growth_summary)

        summary.append(f"현재 {results['Forward P/E (vs Sector)']}이며, 수익성은 순이익률 {results['Profit Margin']}, 자기자본이익률 {results['Return on Equity (ROE)']}로 나타납니다.")

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
