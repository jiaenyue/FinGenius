from src.config import config
from src.tool.data_provider.akshare_provider import AkshareProvider
from src.tool.data_provider.base import DataProvider
from src.tool.data_provider.rqdata_provider import RQDataProvider
from src.tool.data_provider.tushare_provider import TushareProvider


_provider_instance = None

def get_data_provider() -> DataProvider:
    """
    Factory function to get the data provider based on the configuration.
    It supports both explicit provider selection and an automatic fallback mechanism.
    On the first call, it determines the best available provider and caches it.
    """
    global _provider_instance
    if _provider_instance:
        return _provider_instance

    provider_name = config.get("data_provider_config").provider

    def try_tushare():
        tushare_token = config.get("data_provider_config").tushare_token
        if tushare_token and tushare_token != "invalid_token":
            print("Attempting to use Tushare...")
            try:
                provider = TushareProvider(token=tushare_token)
                provider.pro.trade_cal(exchange='', start_date='20250101', end_date='20250101')
                print("Tushare is available.")
                return provider
            except Exception as e:
                print(f"Tushare is not available: {e}")
        return None

    def try_rqdata():
        rqdata_username = config.get("data_provider_config").rqdata_username
        rqdata_password = config.get("data_provider_config").rqdata_password
        if rqdata_username and rqdata_password:
            print("Attempting to use RQData...")
            try:
                provider = RQDataProvider(username=rqdata_username, password=rqdata_password)
                print("RQData is available.")
                return provider
            except Exception as e:
                print(f"RQData is not available: {e}")
        return None

    def try_akshare():
        print("Falling back to Akshare.")
        return AkshareProvider()

    if provider_name == "auto":
        _provider_instance = try_tushare() or try_rqdata() or try_akshare()
    elif provider_name == "tushare":
        _provider_instance = try_tushare()
    elif provider_name == "rqdata":
        _provider_instance = try_rqdata()
    elif provider_name == "akshare":
        _provider_instance = try_akshare()
    else:
        raise ValueError(f"Unknown data provider: {provider_name}")

    if not _provider_instance:
        raise RuntimeError(f"Could not initialize data provider: {provider_name}")

    return _provider_instance
