import yfinance as yf # type: ignore
import pandas as pd
from typing import Optional


class PriceAPI():

    """
    A simple API wrapper for retrieving historical prices, dividends, 
    and earnings dates using yfinance library

    """

    def __init__(self,ticker:str) -> None:

        self.ticker: str = ticker
        self.data: yf.Ticker = yf.Ticker(self.ticker)
        self.price_hist: Optional[pd.DataFrame] = None
        self.dividend_hist: Optional[pd.DataFrame] = None
        self.earning_dates: Optional[pd.DataFrame] = None
        

    def get_history(self) -> None:
        """
        Retrieve historical price and dividend data for the specified stock for the last 5 years.
        The results are stored in the dividend_hist and the price_hist attributes
        """
        
        df = self.data.history(period='5y')
        df.index = pd.to_datetime(df.index, utc=True).tz_convert('America/New_York').tz_localize(None)
        self.price_hist = df[['Open','High','Low','Close','Volume']]
        self.dividend_hist = df[['Dividends']]

    def get_earnings_dates(self) -> None:

        """
        Retrieve earnings dates data for the specified stock.
        """

        df = self.data.get_earnings_dates()
        df.index = pd.to_datetime(df.index, utc=True).tz_convert('America/New_York').tz_localize(None)
        self.earning_dates = df


