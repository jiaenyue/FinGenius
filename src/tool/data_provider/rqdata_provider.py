from typing import Any, Dict, List, Optional

import pandas as pd
import rqdatac

from src.tool.data_provider.base import DataProvider


class RQDataProvider(DataProvider):
    """
    Data provider for RQData.
    """

    def __init__(self, username, password):
        rqdatac.init(username, password)

    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetches basic information for a given stock code using RQData.
        """
        try:
            # RQData's stock code format is usually like '600519.XSHG'
            rq_code = self._convert_to_rq_code(stock_code)

            # Fetch basic info
            instrument = rqdatac.instruments(rq_code)
            if not instrument:
                return None

            stock_info = vars(instrument)


            return stock_info
        except Exception as e:
            print(f"Error fetching stock basic info from RQData for {stock_code}: {e}")
            return None

    def get_daily_market_data(
        self, stock_code: str, start_date: str, end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetches daily market data (OHLCV) for a given stock code and date range using RQData.
        """
        try:
            rq_code = self._convert_to_rq_code(stock_code)
            df = rqdatac.get_price(
                rq_code,
                start_date=start_date,
                end_date=end_date,
                frequency='1d',
                fields=['open', 'high', 'low', 'close', 'volume']
            )
            return df
        except Exception as e:
            print(f"Error fetching daily market data from RQData for {stock_code}: {e}")
            return None

    def get_real_time_quotes(self, stock_codes: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Fetches real-time quotes for a list of stock codes using RQData.
        """
        if not isinstance(stock_codes, list):
            stock_codes = [stock_codes]

        try:
            rq_codes = [self._convert_to_rq_code(code) for code in stock_codes]

            # RQData's current_snapshot is good for real-time quotes
            snapshot_df = rqdatac.current_snapshot(rq_codes)
            if snapshot_df.empty:
                return None

            quotes = {}
            for rq_code, row in snapshot_df.iterrows():
                original_code = rq_code.split('.')[0]
                quotes[original_code] = row.to_dict()
            return quotes
        except Exception as e:
            print(f"Error fetching real-time quotes from RQData: {e}")
            return None

    @staticmethod
    def _convert_to_rq_code(stock_code: str) -> str:
        """
        Converts a standard stock code (e.g., '600519') to RQData's format (e.g., '600519.XSHG').
        """
        if stock_code.startswith('6'):
            return f"{stock_code}.XSHG"  # Shanghai Stock Exchange
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            return f"{stock_code}.XSHE"  # Shenzhen Stock Exchange
        elif stock_code.startswith('8') or stock_code.startswith('4'):
            return f"{stock_code}.XSES"  # Beijing Stock Exchange
        else:
            # Fallback for other cases, though may not be correct
            return f"{stock_code}.XSHG"
