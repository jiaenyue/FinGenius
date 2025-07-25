from typing import Any, Dict, List, Optional

import akshare as ak
import pandas as pd

from src.tool.data_provider.base import DataProvider


class AkshareProvider(DataProvider):
    """
    Data provider for akshare.
    """

    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetches basic information for a given stock code using akshare.
        """
        try:
            stock_info_df = ak.stock_individual_info_em(symbol=stock_code)
            if stock_info_df.empty:
                return None

            # The result from akshare is a DataFrame with two columns: 'item' and 'value'
            # We convert it to a dictionary for easier access.
            stock_info = dict(zip(stock_info_df['item'], stock_info_df['value']))
            return stock_info
        except Exception as e:
            print(f"Error fetching stock basic info from akshare for {stock_code}: {e}")
            return None

    def get_daily_market_data(
        self, stock_code: str, start_date: str, end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetches daily market data (OHLCV) for a given stock code and date range using akshare.
        """
        try:
            # akshare requires the stock code to be prefixed with the market code (e.g., 'sh' or 'sz')
            # However, for A-shares, it can often infer this.
            # We'll try without a prefix first.
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq",  # qfq: 前复权
            )
            return df
        except Exception as e:
            print(f"Error fetching daily market data from akshare for {stock_code}: {e}")
            return None

    def get_real_time_quotes(self, stock_codes: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Fetches real-time quotes for a list of stock codes using akshare.
        """
        if not isinstance(stock_codes, list):
            stock_codes = [stock_codes]

        try:
            # akshare's real-time quote function takes a comma-separated string of stock codes
            stock_codes_str = ",".join(stock_codes)
            df = ak.stock_zh_a_spot_em(symbol=stock_codes_str)
            if df.empty:
                return None

            # The result is a DataFrame, we need to convert it to a dictionary
            # indexed by stock code for consistency with the interface.
            quotes = {}
            for _, row in df.iterrows():
                quotes[row['代码']] = row.to_dict()
            return quotes
        except Exception as e:
            print(f"Error fetching real-time quotes from akshare: {e}")
            return None
