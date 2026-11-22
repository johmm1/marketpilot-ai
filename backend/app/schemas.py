from pydantic import BaseModel, Field
from typing import Literal
AssetClass = Literal["forex", "crypto", "stocks", "indices"]
class SignalRequest(BaseModel):
 symbol: str = Field(min_length=2, max_length=30)
 asset_class: AssetClass
 timeframe: Literal["5m", "15m", "1h", "4h", "1d"] = "1h"
class Signal(BaseModel):
 symbol: str
 action: Literal["BUY", "SELL", "HOLD"]
 confidence: int = Field(ge=0, le=100)
 rationale: str
 entry_reference: float | None = None
 stop_loss_reference: float | None = None
 take_profit_reference: float | None = None
 model: str
 disclaimer: str = "Illustrative only; not financial advice. Validate market data and risk."
class PaperOrderRequest(BaseModel):
 symbol: str
 side: Literal["BUY", "SELL"]
 quantity: float = Field(gt=0, le=1000000)
 reference_price: float = Field(gt=0)
class PaperOrder(BaseModel):
 id: str
 symbol: str
 side: str
 quantity: float
 reference_price: float
 status: str = "PAPER_FILLED"
 live_execution: bool = False
