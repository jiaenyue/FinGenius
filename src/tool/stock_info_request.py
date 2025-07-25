import asyncio
from typing import Any, Dict

import pandas as pd
from pydantic import Field

from src.tool.base import BaseTool, ToolResult, get_recent_trading_day
from src.tool.data_provider import get_data_provider


class StockInfoResponse(ToolResult):
    """Response model for stock information, extending ToolResult."""

    output: Dict[str, Any] = Field(default_factory=dict)

    @property
    def current_trading_day(self) -> str:
        """Get the current trading day from the output."""
        return self.output.get("current_trading_day", "")

    @property
    def basic_info(self) -> Dict[str, Any]:
        """Get the basic stock information from the output."""
        return self.output.get("basic_info", {})


class StockInfoRequest(BaseTool):
    """Tool to fetch basic information about a stock with the current trading date."""

    name: str = "stock_info_request"
    description: str = "获取股票基础信息和当前交易日，返回JSON格式的结果。"
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {"stock_code": {"type": "string", "description": "股票代码"}},
        "required": ["stock_code"],
    }

    async def execute(self, stock_code: str, **kwargs) -> StockInfoResponse | None:
        """
        Execute the tool to fetch stock information.

        Args:
            stock_code: The stock code to query

        Returns:
            StockInfoResponse containing stock information and current trading date
        """
        try:
            # Get current trading day
            trading_day = get_recent_trading_day()

            # Get data provider
            data_provider = get_data_provider()

            if data_provider is None:
                return StockInfoResponse(error="Could not get a valid data provider.")

            # Fetch stock information
            basic_info = data_provider.get_stock_basic_info(stock_code)

            if basic_info is None:
                return StockInfoResponse(error="Failed to fetch stock basic info from any provider.")

            # Create and return the response
            return StockInfoResponse(
                output={
                    "current_trading_day": trading_day,
                    "basic_info": basic_info,
                }
            )

        except (ValueError, RuntimeError) as e:
            return StockInfoResponse(
                error=f"Data provider configuration error: {str(e)}"
            )
        except Exception as e:
            return StockInfoResponse(
                error=f"获取股票信息失败: {str(e)}"
            )


if __name__ == "__main__":
    import json
    import sys

    # Use default stock code "600519" (Maotai) if not provided
    code = sys.argv[1] if len(sys.argv) > 1 else "600519"

    # Create and run the tool
    tool = StockInfoRequest()
    result = asyncio.run(tool.execute(code))

    # Print the result
    if result.error:
        print(f"Error: {result.error}")
    else:
        print(json.dumps(result.output, ensure_ascii=False, indent=2))
