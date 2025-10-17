import yfinance as yf
import pandas_ta as ta
import pandas as pd
import sys
import os
import configparser
from fundamental_analyzer import get_fundamental_analysis

def get_combined_analysis(ticker, short_ma=20, mid_ma=50, long_ma=200, rsi_period=14):
    """
    특정 티커에 대한 기술적 분석과 펀더멘탈 분석을 모두 수행하고 출력합니다.
    """
    # --- 설정 로드 ---
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    config.read(config_path)
    use_strict_filter = config.getboolean('Analyzer', 'use_strict_filter', fallback=False)

    print(f"\n--- {ticker} 종합 분석 시작 ---")
    print(f"[분석 조건] 추세 필터: {'엄격 모드' if use_strict_filter else '완화 모드'}")
    
    # --- 1. 기술적 분석 ---
    print(f"\n--- 1. 기술적 분석 (Technical Analysis) ---")
    try:
        df = yf.download(ticker, period="250d", auto_adjust=True, progress=False, timeout=10)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        if df.empty:
            print(f"'{ticker}'에 대한 주가 데이터를 가져올 수 없습니다.")
        else:
            # 지표 계산
            df[f'SMA_{short_ma}'] = df.ta.sma(length=short_ma)
            df[f'SMA_{mid_ma}'] = df.ta.sma(length=mid_ma)
            df[f'SMA_{long_ma}'] = df.ta.sma(length=long_ma)
            df[f'RSI_{rsi_period}'] = df.ta.rsi(length=rsi_period)
            bbands = df.ta.bbands(length=20, std=2.0)
            if bbands is not None and not bbands.empty:
                df['BBL_20_2.0'] = bbands.iloc[:, 0]
                df['BBM_20_2.0'] = bbands.iloc[:, 1]
                df['BBU_20_2.0'] = bbands.iloc[:, 2]

            if len(df) < long_ma:
                print(f"'{ticker}'에 대한 데이터 기간이 부족하여 일부 기술적 분석이 제한될 수 있습니다.")

            last_row = df.iloc[-1]
            
            # 결과 출력
            print("\n[최신 기술적 지표]")
            print(f"  - 날짜: {last_row.name.strftime('%Y-%m-%d')}")
            print(f"  - 종가: {last_row['Close']:.2f}")
            print(f"  - 이동평균 (단기 {short_ma}일): {last_row.get(f'SMA_{short_ma}', float('nan')):.2f}")
            print(f"  - 이동평균 (중기 {mid_ma}일): {last_row.get(f'SMA_{mid_ma}', float('nan')):.2f}")
            print(f"  - 이동평균 (장기 {long_ma}일): {last_row.get(f'SMA_{long_ma}', float('nan')):.2f}")
            print(f"  - RSI ({rsi_period}일): {last_row.get(f'RSI_{rsi_period}', float('nan')):.2f}")

            # 해석 생성 및 출력
            interpretation = []
            position_guidance = {'buy': 0, 'sell': 0, 'neutral': 0}

            current_price = last_row['Close']
            current_rsi = last_row.get(f'RSI_{rsi_period}')
            sma_short = last_row.get(f'SMA_{short_ma}')
            sma_mid = last_row.get(f'SMA_{mid_ma}')
            sma_long = last_row.get(f'SMA_{long_ma}')
            bb_lower = last_row.get('BBL_20_2.0')
            bb_upper = last_row.get('BBU_20_2.0')

            # 추세 해석 (config.ini 설정에 따라 분기)
            trend_status = ""
            if pd.notna(sma_short) and pd.notna(sma_mid) and pd.notna(sma_long):
                is_strong_uptrend = sma_short > sma_mid and sma_mid > sma_long and current_price > sma_short
                is_uptrend = current_price > sma_long and sma_mid > sma_long
                is_strong_downtrend = sma_short < sma_mid and sma_mid < sma_long and current_price < sma_short
                is_downtrend = current_price < sma_long and sma_mid < sma_long

                if use_strict_filter:
                    if is_strong_uptrend:
                        trend_status = "강력한 상승 추세 (정배열)"
                        position_guidance['buy'] += 2
                    elif is_strong_downtrend:
                        trend_status = "강력한 하락 추세 (역배열)"
                        position_guidance['sell'] += 2
                    else:
                        trend_status = "혼조세 또는 횡보 추세 (엄격 모드 기준)"
                        position_guidance['neutral'] += 1
                else: # 완화 모드
                    if is_strong_uptrend:
                        trend_status = "강력한 상승 추세 (정배열)"
                        position_guidance['buy'] += 2
                    elif is_uptrend:
                        trend_status = "상승 추세 (완화된 조건)"
                        position_guidance['buy'] += 1
                    elif is_strong_downtrend:
                        trend_status = "강력한 하락 추세 (역배열)"
                        position_guidance['sell'] += 2
                    elif is_downtrend:
                        trend_status = "하락 추세 (완화된 조건)"
                        position_guidance['sell'] += 1
                    else:
                        trend_status = "혼조세 또는 횡보 추세"
                        position_guidance['neutral'] += 1
            else:
                trend_status = "이동평균선 데이터 부족으로 추세 판단 불가"
            interpretation.append(trend_status)

            # RSI 해석
            if pd.notna(current_rsi):
                if current_rsi > 70:
                    interpretation.append(f"RSI ({current_rsi:.2f}): 과매수 구간 (매도 또는 조정 가능성)")
                    position_guidance['sell'] += 1
                elif current_rsi < 30:
                    interpretation.append(f"RSI ({current_rsi:.2f}): 과매도 구간 (매수 또는 반등 가능성)")
                    position_guidance['buy'] += 1
                else:
                    interpretation.append(f"RSI ({current_rsi:.2f}): 중립 구간")
                    position_guidance['neutral'] += 1
            else:
                interpretation.append("RSI 데이터 부족")

            # 볼린저 밴드 해석
            if pd.notna(bb_lower) and pd.notna(bb_upper):
                if current_price > bb_upper:
                    interpretation.append(f"볼린저 밴드: 상단 돌파 (과열 신호, 단기 매도 고려)")
                    position_guidance['sell'] += 1
                elif current_price < bb_lower:
                    interpretation.append(f"볼린저 밴드: 하단 이탈 (과매도 신호, 단기 매수 고려)")
                    position_guidance['buy'] += 1
                else:
                    interpretation.append(f"볼린저 밴드: 밴드 내 움직임 (중립)")
                    position_guidance['neutral'] += 1
            else:
                interpretation.append("볼린저 밴드 데이터 부족")

            print("\n[간단 해석]")
            for item in interpretation:
                print(f"- {item}")

            # 최종 포지션 가이드
            final_position = ""
            if position_guidance['buy'] > position_guidance['sell']:
                final_position = "종합: 매수(Long) 관점 우세"
            elif position_guidance['sell'] > position_guidance['buy']:
                final_position = "종합: 매도(Short) 또는 관망 관점 우세"
            else:
                final_position = "종합: 중립 또는 혼조세로 판단"
            
            print("\n[포지션 가이드 (참고용)]")
            print(f"- {final_position}")

    except Exception as e:
        print(f"기술적 분석 중 오류 발생: {e}")

    # --- 2. 펀더멘탈 분석 ---
    print(f"\n--- 2. 펀더멘탈 분석 (Fundamental Analysis) ---")
    try:
        get_fundamental_analysis(ticker)
    except Exception as e:
        print(f"펀더멘탈 분석 중 오류 발생: {e}")
        
if __name__ == '__main__':
    if len(sys.argv) > 1:
        ticker_to_analyze = sys.argv[1].upper()
    else:
        ticker_to_analyze = input("분석할 티커를 입력하세요 (예: AAPL): ").upper()

    if ticker_to_analyze:
        get_combined_analysis(ticker_to_analyze)
    else:
        print("티커가 입력되지 않아 분석을 시작할 수 없습니다.")