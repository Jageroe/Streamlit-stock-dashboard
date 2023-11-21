import sys
import os
import pytest
import time 
import pandas as pd

# Add the 'src' folder to the Python path
src_dir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(src_dir)

from src.daily_price_api import PriceAPI



@pytest.fixture(scope='module')
def api():
    api = PriceAPI("GOOGL")
    api.get_history()
    api.get_earnings_dates()
    return api


def test_price_df_shape(api:PriceAPI) -> None:
    assert api.price_hist.shape[0] > 0
    assert api.price_hist.shape[1] == 5
  
def test_price_df_col_names(api:PriceAPI) -> None:
    assert (api.price_hist.columns == pd.Index(['Open','High','Low','Close','Volume'])).all()

def test_price_df_type(api:PriceAPI) -> None:
    assert isinstance(api.price_hist, pd.DataFrame)

def test_price_df_index_type(api:PriceAPI) -> None:
    assert isinstance(api.price_hist.index, pd.DatetimeIndex)

@pytest.mark.parametrize(
    "col_name, dtype",[
    ('Open','float64'),
    ('High','float64'),
    ('Low','float64'),
    ('Close','float64'),
    ('Volume','int64')]
)
def test_price_df_datatypes(api:PriceAPI, col_name, dtype) -> None:
    assert api.price_hist[col_name].dtype == dtype




def test_earning_dates_shape(api:PriceAPI) -> None:
    assert api.earning_dates.shape[0] > 0
    assert api.earning_dates.shape[1] == 3
  
def test_earning_dates_col_names(api:PriceAPI) -> None:
    assert (api.earning_dates.columns == pd.Index(['EPS Estimate', 'Reported EPS', 'Surprise(%)'])).all()

def test_earning_dates_type(api:PriceAPI) -> None:
    assert isinstance(api.earning_dates, pd.DataFrame)

def test_earning_dates_index_type(api:PriceAPI) -> None:
    assert isinstance(api.earning_dates.index, pd.DatetimeIndex)


@pytest.mark.parametrize(
    "col_name, dtype",[
    ('EPS Estimate','float64'),
    ('Reported EPS','float64'),
    ('Surprise(%)','float64')]
)
def test_earning_dates_datatypes(api:PriceAPI, col_name, dtype) -> None:
    assert api.earning_dates[col_name].dtype == dtype


