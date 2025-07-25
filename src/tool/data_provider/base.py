from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd


class DataProvider(ABC):
    """
    Abstract base class for data providers.
    Defines a common interface for accessing financial data from different sources.
    """

    @abstractmethod
    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetches basic information for a given stock code.

        Args:
            stock_code (str): The stock code.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing basic stock information,
                                     or None if the data cannot be fetched.
        """
        pass

    @abstractmethod
    def get_daily_market_data(
        self, stock_code: str, start_date: str, end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetches daily market data (OHLCV) for a given stock code and date range.

        Args:
            stock_code (str): The stock code.
            start_date (str): The start date of the period (YYYY-MM-DD).
            end_date (str): The end date of the period (YYYY-MM-DD).

        Returns:
            Optional[pd.DataFrame]: A DataFrame containing the daily market data,
                                    or None if the data cannot be fetched.
        """
        pass

    @abstractmethod
    def get_real_time_quotes(self, stock_codes: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Fetches real-time quotes for a list of stock codes.

        Args:
            stock_codes (List[str]): A list of stock codes.

        Returns:
            Optional[Dict[str, Dict[str, Any]]]: A dictionary where keys are stock codes
                                                  and values are dictionaries of quote data,
                                                  or None if the data cannot be fetched.
        """
        pass
