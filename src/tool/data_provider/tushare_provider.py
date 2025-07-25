from typing import Any, Dict, List, Optional

import pandas as pd
import tushare as ts

from src.tool.data_provider.base import DataProvider


class TushareProvider(DataProvider):
    """
    Data provider for tushare.
    """

    def __init__(self, token: str):
        self.pro = ts.pro_api(token)

    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetches basic information for a given stock code using tushare.
        Tushare's basic info is spread across multiple API calls.
        We will fetch from 'stock_basic' and 'daily_basic'.
        """
        try:
            # Tushare needs the format to be like '600519.SH'
            ts_code = self._convert_to_ts_code(stock_code)

            # Fetch from stock_basic
            stock_basic_df = self.pro.stock_basic(ts_code=ts_code, fields='ts_code,symbol,name,area,industry,fullname,enname,market,exchange,curr_type,list_status,list_date,delist_date,is_hs')
            if stock_basic_df.empty:
                return None

            stock_info = stock_basic_df.iloc[0].to_dict()

            # Fetch from daily_basic to get more info like PE ratio, etc.
            # Tushare requires a trade_date for this. We'll use the latest.
            daily_basic_df = self.pro.daily_basic(ts_code=ts_code)
            if not daily_basic_df.empty:
                stock_info.update(daily_basic_df.iloc[0].to_dict())

            return stock_info
        except Exception as e:
            print(f"Error fetching stock basic info from tushare for {stock_code}: {e}")
            return None

    def get_daily_market_data(
        self, stock_code: str, start_date: str, end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetches daily market data (OHLCV) for a given stock code and date range using tushare.
        """
        try:
            ts_code = self._convert_to_ts_code(stock_code)
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
            )
            return df
        except Exception as e:
            print(f"Error fetching daily market data from tushare for {stock_code}: {e}")
            return None

    def get_real_time_quotes(self, stock_codes: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Fetches real-time quotes for a list of stock codes using tushare.
        Tushare's free tier has limitations on real-time data.
        We will use the 'daily_basic' endpoint for the latest day's data as a substitute.
        """
        if not isinstance(stock_codes, list):
            stock_codes = [stock_codes]

        try:
            ts_codes = [self._convert_to_ts_code(code) for code in stock_codes]
            ts_codes_str = ",".join(ts_codes)

            df = self.pro.daily_basic(ts_code=ts_codes_str)
            if df.empty:
                return None

            quotes = {}
            for _, row in df.iterrows():
                # Convert the tushare code back to the original format
                original_code = row['ts_code'].split('.')[0]
                quotes[original_code] = row.to_dict()
            return quotes
        except Exception as e:
            print(f"Error fetching real-time quotes from tushare: {e}")
            return None

    @staticmethod
    def _convert_to_ts_code(stock_code: str) -> str:
        """
        Converts a standard stock code (e.g., '600519') to tushare's format (e.g., '600519.SH').
        """
        if stock_code.startswith('6'):
            return f"{stock_code}.SH"
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            return f"{stock_code}.SZ"
        # Add other market prefixes if necessary (e.g., for Beijing stock exchange)
        elif stock_code.startswith('8') or stock_code.startswith('4'):
            return f"{stock_code}.BJ"
        else:
            # Fallback for other cases, though may not be correct
            return f"{stock_code}.SH"
