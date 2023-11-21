import os
import sys
from datetime import datetime
import logging
import pytest
import pandas as pd
from io import StringIO
import json
import time 

# Add the 'src' folder to the Python path
src_dir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(src_dir)

from src.data_processor import fiscal_to_calender_converter, DataProcessor, IncorrectDataError, MissingAttributeError 
from src.polygon_api import PolygonAPI
from src.daily_price_api import PriceAPI



def test_fiscal_to_calender_converter():

    assert fiscal_to_calender_converter('2022-12-15') == '2022-12-31'
    assert fiscal_to_calender_converter('2023-01-05') == '2022-12-31'
    assert fiscal_to_calender_converter('2023-02-05') == '2022-12-31'
    assert fiscal_to_calender_converter('2023-03-05') == '2023-03-31'
    assert fiscal_to_calender_converter('2023-05-05') == '2023-03-31'
    assert fiscal_to_calender_converter('2023-07-05') == '2023-06-30'
    assert fiscal_to_calender_converter('2023-06-05') == '2023-06-30'
    assert fiscal_to_calender_converter('2023-10-05') == '2023-09-30'
    assert fiscal_to_calender_converter('2023-09-05') == '2023-09-30'


def init_data_local(ticker):

    """ 
    Initialize a test DataProcessor object with attributes loaded from locally saved JSON files.
    It contains 2 submethods:
        - read_json: Its for PolygonAPI's attributes
        - read_json_to_df: It's for the PriceAPI's attributes. It returns DataFrame since the yfinance library (which is wrapped in the PriceAPI) returns dataframes

    
    """

    TEST_RESOURCES_PATH = "src/tests/test_resources"

    def read_json(file_name):
        """
        Read and parse a JSON file.
        """
        with open(os.path.join(TEST_RESOURCES_PATH,ticker,file_name), 'r') as json_file:
            return json.load(json_file)
        

    def read_json_to_df(file_name):
        """ 
        Read and parse a JSON file into a DataFrame.
        """
        with open(os.path.join(TEST_RESOURCES_PATH,ticker,file_name), 'r') as json_file:
            data = json.load(json_file)
            data = pd.read_json(StringIO(data))
            if 'Earnings Date' in data.columns:
                data['Earnings Date'] = pd.to_datetime(data['Earnings Date'], unit='ms')
                data.index = pd.Index(data['Earnings Date'])
                data.drop(columns=['Earnings Date'], inplace=True)

            else:
                data.index = pd.Index(data['Date'])
                data.drop(columns=['Date'], inplace=True)

            
            return data


    details = read_json('details.json')
    financials = read_json('financials.json')
    news = read_json('news.json')
    price_hist = read_json_to_df('price_hist.json')
    dividend_hist = read_json_to_df('dividend_hist.json')
    earning_dates = read_json_to_df('earning_dates.json')


    fin_api = PolygonAPI(ticker)
    fin_api.details = details
    fin_api.financials = financials
    fin_api.news = news

    price_api = PriceAPI(ticker)
    price_api.price_hist = price_hist
    price_api.dividend_hist = dividend_hist
    price_api.earning_dates = earning_dates

    return DataProcessor(
        fin_api=fin_api,
        price_api=price_api
    )


def init_data_online(ticker):
    """
    Initialize a test DataProcessor object with attributes fetched online.
    """

    fin_api = PolygonAPI(ticker)
    
    fin_api.get_ticker_details()
    fin_api.get_financials()
    fin_api.get_news()

    price_api = PriceAPI(ticker)
    price_api.get_history()
    price_api.get_earnings_dates()
    time.sleep(60)   

    return DataProcessor(
        fin_api=fin_api,
        price_api=price_api
    )

# creating fixtures for the testcases
@pytest.fixture(scope='module')
def data_online_google():
    return init_data_online('GOOGL')
    
@pytest.fixture(scope='module')
def data_local_google():
    return init_data_local('GOOGL')

@pytest.fixture(scope='module')
def data_local_msft():
    return init_data_local('MSFT')

@pytest.fixture(scope='module')
def data_local_jnj():
    return init_data_local('JNJ')
    


# Test cases:

def test_fin_content_online(data_online_google):

    fin_content = data_online_google._fin_content()
    assert isinstance(fin_content, dict)
    assert len(fin_content) > 0


def test_fin_content_local(data_local_msft):

    fin_content = data_local_msft._fin_content()
    assert isinstance(fin_content, dict)
    assert len(fin_content) > 0
    assert list(fin_content.keys()) == ['comprehensive_income', 'cash_flow_statement', 'balance_sheet', 'income_statement']



def test_extract_from_fin_online(data_online_google):

    dict_data = data_online_google._extract_from_fin('income_statement','net_income_loss_attributable_to_parent')

    for i, item in enumerate(dict_data.items()):
        if i == 0:
            items_num = len(item)
        assert len(item) == items_num


def test_extract_from_fin_local(data_local_msft):

    dict_data = data_local_msft._extract_from_fin('income_statement','net_income_loss_attributable_to_parent')

    for i, item in enumerate(dict_data.items()):
        if i == 0:
            items_num = len(item)
        assert len(item) == items_num



def test_calculate_quarterly_data_missing_data_error_case1(data_local_jnj):
    """ 
    JNJ has incomplete data
    """
    with pytest.raises(IncorrectDataError):
        data_local_jnj.calculate_quarterly_data('income_statement','revenues')

def test_calculate_quarterly_data_missing_data_error_case3(data_local_jnj):
    """ 
    For some periods, the financials data  miss the cash_flow_statements
    """
    with pytest.raises(KeyError):
        data_local_jnj.calculate_quarterly_data('cash_flow_statement','net_cash_flow')

def test_calculate_quarterly_data_missing_data_error_case4(data_local_jnj):
    with pytest.raises(IncorrectDataError):
        data_local_jnj.calculate_quarterly_data('balance_sheet','liabilities_and_equity')



def test_calculate_quarterly_data_online_income_statement(data_online_google):

    result = data_online_google.calculate_quarterly_data('income_statement','revenues')
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] > 0
    assert result.shape[1] > 0


def test_calculate_quarterly_data_online_balance_sheet(data_online_google):

    result = data_online_google.calculate_quarterly_data('balance_sheet','liabilities_and_equity')
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] > 0
    assert result.shape[1] > 0

def test_calculate_quarterly_data_online_cash_flow_statement(data_online_google):

    result = data_online_google.calculate_quarterly_data('cash_flow_statement','net_cash_flow')
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] > 0
    assert result.shape[1] > 0



def test_calculate_quarterly_data_local_income_statement(data_local_google):

    result = data_local_google.calculate_quarterly_data('income_statement','revenues')
    assert (result.loc[result['end_date'] == '2023-09-30'].value == 7.669300e+10).values
    assert (result.loc[result['end_date'] == '2023-06-30'].value == 7.460400e+10).values
    assert (result.loc[result['end_date'] == '2023-03-31'].value == 6.978700e+10).values
    assert (result.loc[result['end_date'] == '2022-12-31'].value == 7.604800e+10).values
    assert (result.loc[result['end_date'] == '2021-12-31'].value == 7.532500e+10).values
    assert (result.loc[result['end_date'] == '2020-06-30'].value == 3.829700e+10).values


def test_calculate_quarterly_data_local_balance_sheet(data_local_google):

    result = data_local_google.calculate_quarterly_data('balance_sheet','liabilities_and_equity')
    assert (result.loc[result['end_date'] == '2023-09-30'].value == 3.967110e+11).values
    assert (result.loc[result['end_date'] == '2023-06-30'].value == 3.830440e+11).values
    assert (result.loc[result['end_date'] == '2023-03-31'].value == 3.694910e+11).values
    assert (result.loc[result['end_date'] == '2022-12-31'].value == 3.652640e+11).values
    assert (result.loc[result['end_date'] == '2021-12-31'].value == 3.592680e+11).values
    assert (result.loc[result['end_date'] == '2020-06-30'].value == 2.784920e+11).values

def test_calculate_quarterly_data_local_cash_flow_statement(data_local_google):

    result = data_local_google.calculate_quarterly_data('cash_flow_statement','net_cash_flow')
    assert (result.loc[result['end_date'] == '2023-09-30'].value == 4.773000e+09).values
    assert (result.loc[result['end_date'] == '2023-06-30'].value == 5.000000e+06).values
    assert (result.loc[result['end_date'] == '2023-03-31'].value == 4.045000e+09).values
    assert (result.loc[result['end_date'] == '2022-12-31'].value == -1.050000e+08).values
    assert (result.loc[result['end_date'] == '2021-12-31'].value == -2.774000e+09).values
    assert (result.loc[result['end_date'] == '2020-06-30'].value == -1.902000e+09).values




def test_get_ttm_data_online_income_statement(data_online_google):

    result = data_online_google.get_ttm_data('income_statement','revenues')
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] > 0
    assert result.shape[1] > 0


def get_ttm_data_online_balance_sheet(data_online_google):

    result = data_online_google.get_ttm_data('balance_sheet','liabilities_and_equity')
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] > 0
    assert result.shape[1] > 0

def get_ttm_data_online_cash_flow_statement(data_online_google):

    result = data_online_google.get_ttm_data('cash_flow_statement','net_cash_flow')
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] > 0
    assert result.shape[1] > 0


def test_get_ttm_data_local_income_statement(data_local_google):

    result = data_local_google.get_ttm_data('income_statement','revenues')
    assert (result.loc[result['end_date'] == '2023-09-30'].value == 2.971320e+11).values
    assert (result.loc[result['end_date'] == '2023-06-30'].value == 2.895310e+11).values
    assert (result.loc[result['end_date'] == '2023-03-31'].value == 2.846120e+11).values
    assert (result.loc[result['end_date'] == '2022-12-31'].value == 2.828360e+11).values
    assert (result.loc[result['end_date'] == '2021-12-31'].value == 2.576370e+11).values
    assert (result.loc[result['end_date'] == '2020-06-30'].value == 1.660300e+11).values


def test_get_ttm_data_local_cash_flow_statement(data_local_google):

    result = data_local_google.get_ttm_data('cash_flow_statement','net_cash_flow')
    assert (result.loc[result['end_date'] == '2023-09-30'].value == 8.718000e+09).values
    assert (result.loc[result['end_date'] == '2023-06-30'].value == 7.993000e+09).values
    assert (result.loc[result['end_date'] == '2023-03-31'].value == 5.038000e+09).values
    assert (result.loc[result['end_date'] == '2022-12-31'].value == 9.340000e+08).values
    assert (result.loc[result['end_date'] == '2021-12-31'].value == -5.520000e+09).values
    assert (result.loc[result['end_date'] == '2020-06-30'].value == 1.155000e+09).values




def test_get_yearly_avg_data_online_balance_sheet(data_online_google):

    result = data_online_google.get_yearly_avg_data('balance_sheet','liabilities_and_equity')
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] > 0
    assert result.shape[1] > 0


def test_get_yearly_avg_data_local_balance_sheet(data_local_google):

    result = data_local_google.get_yearly_avg_data('balance_sheet','liabilities_and_equity')
    assert (result.loc[result['end_date'] == '2023-09-30'].value == 378627500000.0).values
    assert (result.loc[result['end_date'] == '2023-06-30'].value == 369013500000.0).values
    assert (result.loc[result['end_date'] == '2023-03-31'].value == 362048750000.0).values
    assert (result.loc[result['end_date'] == '2022-12-31'].value == 358950000000.0).values
    assert (result.loc[result['end_date'] == '2021-12-31'].value == 342288250000.0).values
    assert (result.loc[result['end_date'] == '2020-06-30'].value == 272712000000.0).values



def test_get_name_online(data_online_google):
    name = data_online_google.get_name()
    assert isinstance(name,str)
    assert len(name) > 0


def test_get_name_local(data_local_msft):
    name = data_local_msft.get_name()
    assert isinstance(name,str)
    assert len(name) > 0
    assert name == 'Microsoft Corp'



def test_get_market_cap_online(data_online_google):

    market_cap = data_online_google.get_market_cap()
    assert isinstance(market_cap,float)
    assert market_cap > 0

def test_get_market_cap_local_case1(data_local_msft):

    market_cap = data_local_msft.get_market_cap()
    assert market_cap == 2680742699447.01

def test_get_market_cap_local_case2(data_local_google):

    market_cap = data_local_google.get_market_cap()
    assert market_cap == 1630083840000.0


def test_get_sic_online(data_online_google):
    sic_desc = data_online_google.get_sic_desc()
    assert isinstance(sic_desc,str)
    assert len(sic_desc) > 0

def test_get_sic_local(data_local_msft):
    sic_desc = data_local_msft.get_sic_desc()
    sic_desc == 'SERVICES-PREPACKAGED SOFTWARE'


def test_get_curr_prev_price_online(data_online_google):
    data = data_online_google.get_curr_prev_price()
    for i in data.values():
        assert isinstance(i,float)

    assert list(data.keys()) == ['current', 'previous']

def test_get_curr_prev_price_local(data_local_msft):
    assert data_local_msft.get_curr_prev_price() == {'current': 369.2300109863, 'previous': 360.6900024414}



def test_get_eps_online(data_online_google):
    eps = data_online_google.get_market_cap()
    assert isinstance(eps,float)

def test_get_eps_local_case1(data_local_msft):
    eps = data_local_msft.get_eps()
    assert round(eps,2) == 10.37

def test_get_eps_online_local_case2(data_local_google):
    eps = data_local_google.get_eps()
    assert round(eps,2) == 5.33



def test_get_pe_online(data_online_google):
    eps = data_online_google.get_pe()
    assert isinstance(eps,float)

def test_get_pe_local_case1(data_local_msft):
    eps = data_local_msft.get_pe()
    assert round(eps,2) == 35.59

def test_get_pe_local_case2(data_local_google):
    eps = data_local_google.get_pe()
    assert round(eps,2) == 24.61



def test_gget_52week_low_online(data_online_google):
    low = data_online_google.get_52week_low()
    assert isinstance(low,float)
    assert low > 0

def test_get_52week_low_local_case1(data_local_msft):
    low = data_local_msft.get_52week_low()
    assert round(low,2) == 217.86

def test_get_52week_low_local_case2(data_local_google):
    low = data_local_google.get_52week_low()
    assert round(low,2) == 84.86



def test_get_52week_high_online(data_online_google):
    high = data_online_google.get_52week_high()
    assert isinstance(high,float)
    assert high > 0

def test_get_52week_high_local_case1(data_local_msft):
    high = data_local_msft.get_52week_high()
    assert round(high,2) == 369.53

def test_get_52week_high_local_case2(data_local_google):
    high = data_local_google.get_52week_high()
    assert round(high,2) == 141.22




def test_get_next_report_date_online(data_online_google):

    rep_date = data_online_google.get_next_report_date()
    date_in_date_format = datetime.strptime(rep_date, '%Y-%m-%d')
    assert isinstance(rep_date,str)
    assert isinstance(date_in_date_format, datetime)

def test_get_next_report_date_local_case1(data_local_msft):

    rep_date = data_local_msft.get_next_report_date()
    assert rep_date == "2024-01-22"

def test_get_next_report_date_local_case2(data_local_google):

    rep_date = data_local_google.get_next_report_date()
    assert rep_date == "2024-01-31"



def test_get_earnings_dates_online(data_online_google):
    earning_dates = data_online_google.get_earnings_dates()
    assert isinstance(earning_dates,pd.DataFrame)
    assert earning_dates.shape[0] > 0
    assert earning_dates.shape[1] > 0

def test_get_earnings_dates_local(data_local_msft):
    earning_dates = data_local_msft.get_earnings_dates()
    assert earning_dates.shape == (12,4)
    assert earning_dates.iloc[8]['Earnings Date'] == "2023-01-24"
    assert earning_dates.iloc[8]['EPS Estimate'] == 2.29
    assert earning_dates.iloc[8]['Reported EPS'] == 2.32
    assert earning_dates.iloc[8]['Surprise(%)'] == 0.0109


def test_get_ttm_profit_margin_online_(data_online_google):

    result = data_online_google.get_ttm_profit_margin()
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] > 0
    assert result.shape[1] > 0


def test_get_ttm_profit_margin_local(data_local_google):

    result = data_local_google.get_ttm_profit_margin()
    assert (result.loc[result['end_date'] == '2023-09-30'].value == 0.2246).values
    assert (result.loc[result['end_date'] == '2023-06-30'].value == 0.2105).values
    assert (result.loc[result['end_date'] == '2023-03-31'].value == 0.2058).values
    assert (result.loc[result['end_date'] == '2022-12-31'].value == 0.2120).values
    assert (result.loc[result['end_date'] == '2021-12-31'].value == 0.2951).values
    assert (result.loc[result['end_date'] == '2020-06-30'].value == 0.1899).values

def test_get_yearly_price_online(data_online_google):
    result = data_online_google.get_yearly_price_change()
    assert isinstance(result,float)

def test_get_yearly_price_local_msft(data_local_msft):
    result = data_local_msft.get_yearly_price_change()
    assert round(result,2) == 0.53

def test_get_yearly_price_local_google(data_local_google):
    result = data_local_google.get_yearly_price_change()
    assert round(result,2) == 0.4



def test_get_div_yield_online(data_online_google):

    div_yield = data_online_google.get_div_yield()
    assert isinstance(div_yield,float)
    assert div_yield >= 0

def test_get_div_yield_local_case1(data_local_msft):

    div_yield = data_local_msft.get_div_yield()
    assert round(div_yield,4)  == 0.0074

def test_get_div_yield_local_case2(data_local_google):

    div_yield = data_local_google.get_div_yield()
    assert round(div_yield,4)  == 0.0


def test_get_roe_online(data_online_google):
    roe = data_online_google.get_roe()
    assert isinstance(roe,float)

def test_get_roe_local_case1(data_local_msft):
    roe = data_local_msft.get_roe()
    assert round(roe,4) == 0.3832

def test_get_roe_local_case2(data_local_google):
    roe = data_local_google.get_roe()
    assert round(roe,4) == 0.2524



def test_get_news_df_online(data_online_google):
    news_df = data_online_google.get_news_df()
    assert isinstance(news_df,pd.DataFrame)
    assert news_df.shape[0] > 0
    assert news_df.shape[1] > 0


def test_get_news_df_local(data_local_msft):
    news_df = data_local_msft.get_news_df()
    assert isinstance(news_df,pd.DataFrame)
    assert news_df.iloc[0]['Title'] == 'Adobe Positioned For Success With AI Integration And Expanding Partnerships, Says Analyst'
    assert news_df.iloc[0]['URL'] == 'https://www.benzinga.com/analyst-ratings/analyst-color/23/11/35730042/adobe-positioned-for-success-with-ai-integration-and-expanding-partnerships-says-an'
    assert news_df.iloc[-1]['Title'] == "Prediction: Microsoft Will Overtake Apple as the World's Largest Company By 2025"
    assert news_df.iloc[-1]['URL'] == 'https://www.fool.com/investing/2023/11/10/prediction-microsoft-will-overtake-apple-as-the-wo/'

        

def test_get_news_html_online(data_online_google):
    news_html = data_online_google.get_news_html()
    assert isinstance(news_html,str)
    assert len(news_html) > 0

def test_get_news_html_local(data_local_msft):
    news_html = data_local_msft.get_news_html()
    assert isinstance(news_html,str)
    assert len(news_html) > 0





