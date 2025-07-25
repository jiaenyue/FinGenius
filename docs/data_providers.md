# 数据提供者 API 文档

本文档概述了数据提供者框架，并为每个组件提供了 API 文档。

## 数据源总结

系统支持以下三种数据源：

1.  **Tushare**：一个专业的金融数据接口，提供高质量的数据。需要 token 认证。
2.  **RQData**：另一个专业的金融数据接口，提供全面的数据。需要用户名和密码认证。
3.  **Akshare**：一个免费、开源的金融数据接口，无需认证即可使用。

系统提供两种数据源选择模式：

*   **自动模式 (`"auto"`)**：这是默认模式。系统会按照 `Tushare` -> `RQData` -> `Akshare` 的顺序，尝试初始化每个数据源。它将使用第一个成功初始化的数据源。
*   **手动模式**：用户可以在 `config.toml` 文件中，将 `provider` 设置为 `"tushare"`、`"rqdata"` 或 `"akshare"`，以强制使用特定的数据源。

---

## `src/tool/data_provider/base.py`

### DataProvider (抽象基类)

#### `DataProvider(ABC)`

##### 描述

这是一个抽象基类，为所有数据提供者定义了一个通用的接口。它确保了无论使用哪个数据源，系统的其余部分都可以以相同的方式与之交互。

##### 方法

###### `get_stock_basic_info(self, stock_code: str) -> Optional[Dict[str, Any]]`

-   **描述**: 获取给定股票代码的基本信息。
-   **参数**:
    -   `stock_code (str)`: 股票代码。
-   **返回**: `Optional[Dict[str, Any]]` - 包含股票基本信息的字典，如果无法获取数据，则返回 `None`。

###### `get_daily_market_data(self, stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]`

-   **描述**: 获取给定股票代码和日期范围的每日市场数据 (OHLCV)。
-   **参数**:
    -   `stock_code (str)`: 股票代码。
    -   `start_date (str)`: 时期开始日期 (YYYY-MM-DD)。
    -   `end_date (str)`: 时期结束日期 (YYYY-MM-DD)。
-   **返回**: `Optional[pd.DataFrame]` - 包含每日市场数据的 DataFrame，如果无法获取数据，则返回 `None`。

###### `get_real_time_quotes(self, stock_codes: List[str]) -> Optional[Dict[str, Dict[str, Any]]]`

-   **描述**: 获取给定股票代码列表的实时报价。
-   **参数**:
    -   `stock_codes (List[str])`: 股票代码列表。
-   **返回**: `Optional[Dict[str, Dict[str, Any]]]` - 一个字典，其中键是股票代码，值是包含报价数据的字典；如果无法获取数据，则返回 `None`。

---

## `src/tool/data_provider/akshare_provider.py`

### AkshareProvider

#### `AkshareProvider(DataProvider)`

##### 描述

`akshare` 的数据提供者实现。

##### 方法

(方法遵循 `DataProvider` 接口。)

---

## `src/tool/data_provider/tushare_provider.py`

### TushareProvider

#### `TushareProvider(DataProvider)`

##### 描述

`tushare` 的数据提供者实现。

##### `__init__(self, token: str)`

-   **描述**: 初始化 `TushareProvider`。
-   **参数**:
    -   `token (str)`: 您的 Tushare API token。

##### 方法

(方法遵循 `DataProvider` 接口。)

---

## `src/tool/data_provider/rqdata_provider.py`

### RQDataProvider

#### `RQDataProvider(DataProvider)`

##### 描述

`RQData` 的数据提供者实现。

##### `__init__(self, username, password)`

-   **描述**: 初始化 `RQDataProvider`。
-   **参数**:
    -   `username (str)`: 您的 RQData 用户名。
    -   `password (str)`: 您的 RQData 密码。

##### 方法

(方法遵循 `DataProvider` 接口。)

---

## `src/tool/data_provider/__init__.py`

### 数据提供者工厂

#### `get_data_provider() -> DataProvider`

##### 描述

这是一个工厂函数，根据配置获取数据提供者。它支持显式提供者选择和自动回退机制。在第一次调用时，它会确定最佳的可用提供者并将其缓存。

##### 返回

`DataProvider` - 一个具体的数据提供者实例 (`AkshareProvider`, `TushareProvider`, or `RQDataProvider`)。

##### 抛出

-   `ValueError`: 如果在 `config.toml` 中指定了未知的数据提供者。
-   `RuntimeError`: 如果无法初始化任何数据提供者。
