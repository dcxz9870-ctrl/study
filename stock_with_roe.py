from pykrx import stock
import pandas as pd
import datetime
import numpy as np

# 1. 최근 2년치 분기 마지막 영업일 및 현재 일자 계산
end = datetime.datetime.today()
start = end - datetime.timedelta(days=365 * 2)

# 분기 말일 생성 (3월, 6월, 9월, 12월)
quarter_ends = pd.date_range(start, end, freq="Q")

# 최근 영업일로 변환
biz_days = [stock.get_nearest_business_day_in_a_week(d.strftime("%Y%m%d")) for d in quarter_ends]

# 현재 일자의 최근 영업일을 추가
today_biz_day = stock.get_nearest_business_day_in_a_week(end.strftime("%Y%m%d"))
if today_biz_day not in biz_days:
    biz_days.append(today_biz_day)
    
# 날짜 순으로 정렬
biz_days.sort()

# 2. 코스피 + 코스닥 데이터 수집
markets = {"KOSPI": "코스피", "KOSDAQ": "코스닥"}
df_list = []

for day in biz_days:
    for market_code, market_name in markets.items():
        # 펀더멘털 데이터
        fundamental = stock.get_market_fundamental_by_ticker(day, market=market_code)

        # 시세 데이터 (OHLCV) - 종가, 거래량, 시가총액 포함
        ohlcv = stock.get_market_ohlcv_by_ticker(day, market=market_code)

        # 두 데이터 합치기 (티커 기준)
        tmp = fundamental.merge(
            ohlcv[["종가", "거래량", "시가총액"]],
            left_index=True, right_index=True, how="left"
        )

        # ROE 계산 (%), BPS가 0이면 NaN 처리
        tmp["ROE"] = np.where(tmp["BPS"] != 0, tmp["EPS"] / tmp["BPS"] * 100, np.nan)

        # 종목명 추가
        tickers = stock.get_market_ticker_list(day, market=market_code)
        ticker_name_map = {tic: stock.get_market_ticker_name(tic) for tic in tickers}
        tmp["종목명"] = tmp.index.map(ticker_name_map)
        
        tmp["시장구분"] = market_name
        tmp["날짜"] = day
        tmp.reset_index(inplace=True)
        tmp.rename(columns={"티커": "종목코드"}, inplace=True)

        # 필요한 컬럼만 추출
        tmp = tmp[[
            "날짜", "시장구분", "종목코드", "종목명",
            "종가", "시가총액", "거래량",
            "PER", "PBR", "EPS", "BPS", "DIV", "ROE"
        ]]
        
        df_list.append(tmp)

# 3. 하나의 데이터프레임으로 합치기
final_df = pd.concat(df_list, ignore_index=True)

# 4. 엑셀로 저장
output_file = "KRX_analysis_quarterly_with_ROE.xlsx"
final_df.to_excel(output_file, index=False)

print(f"✅ 저장 완료: {output_file}")