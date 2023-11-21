import os
import sys
from datetime import datetime
import pytest
import time

# Add the 'src' folder to the Python path
src_dir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(src_dir)

from src.polygon_api import PolygonAPI, TickerNotFoundError


tickers_to_test = ['GOOGL']

@pytest.fixture(scope='module',params=tickers_to_test)
def api_init(request):
    ticker = request.param
    api = PolygonAPI(ticker)
    api.get_news()
    api.get_financials()    
    api.get_ticker_details()
    time.sleep(60)        
    return api


def test_fin_type(api_init) -> None:
    fin = api_init.financials
    assert isinstance(fin, list)


def test_fin_content(api_init) -> None:
    fin = api_init.financials
    assert len(fin) > 0
    assert len(fin[0]['financials']) > 0
    assert len(fin[0]['financials']['income_statement']) > 0
    assert len(fin[0]['financials']['balance_sheet']) > 0
    assert len(fin[0]['financials']['cash_flow_statement']) > 0



def test_details_type(api_init) -> None:
    details = api_init.details
    assert isinstance(details, dict)


def test_details_content(api_init) -> None:
    details = api_init.details
    assert details['ticker'] != None
    assert details['name'] != None
    assert details['sic_description'] != None
    assert details['weighted_shares_outstanding'] != None
    assert details['share_class_shares_outstanding'] != None


def test_news_type(api_init) -> None:
    news = api_init.news
    assert isinstance(news, list)


def test_news_content(api_init) -> None:
    news = api_init.news
    assert len(news) > 0
    assert len(news[0]['article_url']) > 0
    assert len(news[0]['title']) > 0


def test_notvalid_ticker() -> None:

    ticker = 'NOTVALIDTICKER'
    api = PolygonAPI(ticker)
    with pytest.raises(TickerNotFoundError):
        api.get_financials()

    
def test_notvalid_ticker2() -> None:

    ticker = 'NOTVALIDTICKER'
    api = PolygonAPI(ticker)
    with pytest.raises(TickerNotFoundError):
        api.get_ticker_details()


def test_notvalid_ticker3() -> None:

    ticker = 'NOTVALIDTICKER'
    api = PolygonAPI(ticker)
    with pytest.raises(TickerNotFoundError):
        api.get_news()


    
