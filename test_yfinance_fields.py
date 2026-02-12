import yfinance as yf
ticker = yf.Ticker('600519.SS')
info = ticker.info
print('All keys:')
for k in sorted(info.keys()):
    print(f'  {k}: {info[k]}')