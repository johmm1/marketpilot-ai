DEMO_QUOTES = [
 {"symbol":"EUR/USD","name":"Euro / US Dollar","asset_class":"forex","price":1.0842,"change_pct":0.18,"source":"DEMO","delayed":True},
 {"symbol":"GBP/USD","name":"British Pound / US Dollar","asset_class":"forex","price":1.2715,"change_pct":-0.12,"source":"DEMO","delayed":True},
 {"symbol":"XAU/USD","name":"Gold / US Dollar","asset_class":"forex","price":2378.4,"change_pct":0.42,"source":"DEMO","delayed":True},
 {"symbol":"BTC/USD","name":"Bitcoin","asset_class":"crypto","price":67420.0,"change_pct":1.86,"source":"DEMO","delayed":True},
 {"symbol":"ETH/USD","name":"Ethereum","asset_class":"crypto","price":3520.0,"change_pct":0.94,"source":"DEMO","delayed":True},
 {"symbol":"AAPL","name":"Apple Inc.","asset_class":"stocks","price":212.3,"change_pct":0.31,"source":"DEMO","delayed":True},
 {"symbol":"NVDA","name":"NVIDIA","asset_class":"stocks","price":124.8,"change_pct":2.14,"source":"DEMO","delayed":True},
 {"symbol":"SPX","name":"S&P 500","asset_class":"indices","price":5420.1,"change_pct":0.27,"source":"DEMO","delayed":True},
 {"symbol":"NAS100","name":"NASDAQ 100","asset_class":"indices","price":19040.2,"change_pct":0.55,"source":"DEMO","delayed":True}]
def list_quotes(asset_class=None):
 return [q for q in DEMO_QUOTES if asset_class is None or q["asset_class"] == asset_class]
def find_quote(symbol: str):
 return next((q for q in DEMO_QUOTES if q["symbol"].upper() == symbol.upper()), None)
