import pandas as pd
import yfinance as yf
import pandas_ta as ta
import urllib.request

def get_index_tickers(index_name="SP500"):
    """
    Wikipedia에서 지정된 지수(SP500 또는 NASDAQ100)의 종목 티커 리스트를 가져옵니다.
    403 Forbidden 오류를 피하기 위해 User-Agent 헤더를 추가합니다.
    
    Args:
        index_name (str): 가져올 지수의 이름 ("SP500" 또는 "NASDAQ100").

    Returns:
        list: 지정된 지수의 종목 티커 리스트.
    """
    try:
        if index_name == "SP500":
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            symbol_col = 'Symbol'
        elif index_name == "NASDAQ100":
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            symbol_col = 'Ticker' # NASDAQ 100 페이지에서는 'Ticker' 컬럼 사용
        else:
            print(f"지원하지 않는 지수 이름입니다: {index_name}")
            return []

        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read()
        
        tables = pd.read_html(html)
        tickers = []
        for table in tables:
            if symbol_col in table.columns:
                tickers = table[symbol_col].tolist()
                break
        
        if not tickers:
            print(f"{index_name} 페이지에서 '{symbol_col}' 컬럼을 찾을 수 없습니다.")
            return []

        tickers = [s.replace('.', '-') for s in tickers]
        print(f"{index_name} 종목 리스트를 성공적으로 가져왔습니다. (총 {len(tickers)}개)")
        return tickers
    except Exception as e:
        print(f"{index_name} 리스트를 가져오는 중 오류 발생: {e}")
        return []

def find_undervalued_stocks(rsi_threshold=50, peg_threshold=1.0, use_peg_filter=True, rsi_period=14, index_name="SP500"):
    """
    지정된 지수 종목 중 저평가 후보 종목들을 찾아 리스트업합니다.

    Args:
        rsi_threshold (int): RSI 기준값. 이 값 미만인 종목을 찾습니다.
        peg_threshold (float): PEG Ratio 기준값. use_peg_filter가 True일 때 사용됩니다.
        use_peg_filter (bool): PEG Ratio 필터를 사용할지 여부.
        rsi_period (int): RSI 계산 기간. 기본값은 14입니다.
        index_name (str): 분석할 지수의 이름 ("SP500" 또는 "NASDAQ100").

    Returns:
        list: 저평가 후보 종목들의 티커, RSI, PEG 값을 담은 딕셔너리 리스트.
    """
    tickers = get_index_tickers(index_name) # 변경된 함수 호출
    if not tickers:
        return []

    undervalued_stocks = []
    total_tickers = len(tickers)

    print(f"\n총 {total_tickers}개의 {index_name} 종목에 대한 분석을 시작합니다...")

    for i, ticker in enumerate(tickers):
        progress_msg = f"  - 진행: [{i + 1}/{total_tickers}] {ticker}"
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            peg_ratio = None

            # 1. PEG Ratio 필터링
            if use_peg_filter:
                peg_ratio = info.get('pegRatio')
                peg_ok = peg_ratio is not None and 0 < peg_ratio < peg_threshold
                if not peg_ok:
                    print(f"{progress_msg} (PEG: {peg_ratio if peg_ratio is not None else 'N/A'} -> SKIP)          ", end='\r')
                    continue

            # 2. RSI 계산
            df = stock.history(period="1mo", timeout=10)
            if df.empty:
                print(f"{progress_msg} (데이터 없음 -> SKIP)          ", end='\r')
                continue
            
            df.ta.rsi(length=rsi_period, append=True)
            rsi_col = f'RSI_{rsi_period}'
            latest_rsi = df.iloc[-1][rsi_col]

            # 3. RSI 필터링 및 결과 저장
            if pd.notna(latest_rsi):
                print(f"{progress_msg} (RSI: {latest_rsi:.2f})          ", end='\r')
                if latest_rsi < rsi_threshold:
                    undervalued_stocks.append({
                        'ticker': ticker,
                        'rsi': latest_rsi,
                        'peg': peg_ratio if use_peg_filter else 'N/A'
                    })
            else:
                print(f"{progress_msg} (RSI: N/A -> SKIP)          ", end='\r')

        except Exception as e:
            error_msg = repr(e).strip()
            print(f"{progress_msg} (오류: {error_msg} -> SKIP)          ", end='\r')
            continue
    
    print("\n분석 완료!                                  ")
    return undervalued_stocks

if __name__ == '__main__':
    # 예시: NASDAQ 100 종목 중 저평가 후보 찾기
    low_value_list = find_undervalued_stocks(rsi_threshold=50, peg_threshold=2.0, use_peg_filter=True, rsi_period=14, index_name="NASDAQ100")

    if low_value_list:
        print(f"\n--- 저평가 후보 종목 ({len(low_value_list)}개) ---")
        results_df = pd.DataFrame(low_value_list)
        print(results_df.to_string(index=False))
    else:
        print("\n조건에 맞는 종목을 찾지 못했습니다.")