import requests
from typing import Optional
from os import getenv
from dotenv import load_dotenv 


# Loading the .env file and the api key from it
load_dotenv()
API_KEY: str  = getenv("API_KEY") # type: ignore
BASE_URL_POLYGON: str = getenv("BASE_URL_POLYGON") # type: ignore
HEADER: dict = {'Authorization': f'Bearer {API_KEY}'}


class LimitReachedError(Exception):
    def __init__(self, message="You have reached the API limit"):
        self.message = message
        super().__init__(self.message)


class TickerNotFoundError(Exception):
    def __init__(self, message="TickerNotFoundError"):
        self.message = message
        super().__init__(self.message)


def check_ticker_validity(ticker:str) -> bool:
    """ 
    A simple method to check if the given ticker is available in Polygon's database.
    
    """

    ticker = ticker.upper()
    url = f'{BASE_URL_POLYGON}v3/reference/tickers?ticker={ticker}&market=stocks&active=true&limit=1'

    response = requests.get(url, headers=HEADER)

    if response.status_code == 429:
            raise LimitReachedError(response.json()['error'])
    print(response.json())
    if len(response.json()['results']) == 1:
        # if the given ticker is available
        return True
    else:
        # If the given ticker is not available
        return False



class PolygonAPI():

    """Class for interacting with the Polygon API."""

    def __init__(self, ticker:str) -> None:

        self.base_url: Optional[str] = BASE_URL_POLYGON
        self.ticker: str = ticker.upper()
        self.financials: Optional[list[dict]] = None
        self.details: Optional[dict] = None
        self.news: Optional[list[dict]] = None


    def _request_data(self, url:str) -> dict:

        """ 
        MMake a request and handling common errors.
        """

        response = requests.get(url, headers=HEADER)

        if response.status_code == 429:
            raise LimitReachedError(response.json()['error'])
        
        # Unfortunately the polygons API doesn't provide a consistent
        # behaviour when a non existing ticker is called during a request.
        # That's why I check multiple conditions
        if (
            response.json()['status'] == 'NOT_FOUND'
            or response.json().get('results') is None
            or response.json().get('results') == []
        ):
            raise TickerNotFoundError()

        return response.json()


    def get_financials(self) -> None:

        """Get financial data for the specified ticker."""

        url = f"{self.base_url}vX/reference/financials?ticker={self.ticker}&filing_date.gte=2010-10-01&limit=100"
        self.financials = self._request_data(url)['results']


    def get_ticker_details(self) -> None:

        """Get details for the specified ticker."""

        url = f"{self.base_url}v3/reference/tickers/{self.ticker}"
        self.details = self._request_data(url)['results']


    def get_news(self) -> None:

        """Get news for the specified ticker."""

        url = f"{self.base_url}v2/reference/news?ticker={self.ticker}&limit=10&sort=published_utc"
        self.news = self._request_data(url)['results']

    


    


    





