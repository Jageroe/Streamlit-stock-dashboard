import pandas as pd 
import numpy as np
import re
from datetime import datetime, timedelta
from src.polygon_api import PolygonAPI
from src.daily_price_api import PriceAPI
from typing import Optional, Any



class IncorrectDataError(Exception):
    def __init__(self, message="IncompleteDataError"):
        self.message = message
        super().__init__(self.message)


class MissingAttributeError(Exception):
    def __init__(self, message="Missing a required class attributes"):
        self.message = message
        super().__init__(self.message)


def fiscal_to_calender_converter(date: str) -> str:

    """ 
    Find the closest calendar quarter closing date, to the given input date.

    Args:
        date (str): The input date in the format YYYY-MM-DD.

    Returns:
        str: The closest calendar quarter closing date in the format YYYY-MM-DD.
    """

    # Convert date string to datetime object
    date_format = '%Y-%m-%d'
    date_obj = datetime.strptime(date, date_format)


    obj_year = date_obj.year
    last_obj_year = obj_year - 1

    # Defining the quarter ending dates
    cal_end_date_list = [
        datetime(obj_year,9,30),
        datetime(obj_year,6,30),
        datetime(obj_year,3,31),
        datetime(obj_year,12,31),
        datetime(last_obj_year,12,31),
    ]

    cal_close_date = min(cal_end_date_list, key=lambda date: abs(date_obj - date))

    return cal_close_date.strftime('%Y-%m-%d')



class DataProcessor:

    """
    A class for handling the data from the PolygonAPI and the PriceAPI.

    This class includes necessary transformation steps to retrieve different metrics and dataframes.
    The methods assume that you have already called the necessary API requests; otherwise, it raises a MissingAttributeError.

    An example of usage of this class:   

    fin_api = PolygonAPI(ticker)
    fin_api.get_ticker_details()
    fin_api.get_financials()
    fin_api.get_news()

    price_api = PriceAPI(ticker)
    price_api.get_history()
    price_api.get_earnings_dates()
    
    data_processor = DataProcessor(
        fin_api=fin_api,
        price_api=price_api
    )
    
    """


    def __init__(self, fin_api: PolygonAPI, price_api:PriceAPI) -> None:

        self.ticker: Optional[str] = fin_api.ticker
        self.financials: Optional[list[dict]] = fin_api.financials
        self.details: Optional[dict] = fin_api.details
        self.price_hist: Optional[pd.DataFrame] = price_api.price_hist
        self.dividend_hist: Optional[pd.DataFrame] = price_api.dividend_hist
        self.earning_dates: Optional[pd.DataFrame] = price_api.earning_dates
        self.news: Optional[list[dict]] = fin_api.news



    def _fin_content(self) -> dict[str,list]:
        """
        Returns the different financials and its possible values 
        """

        if self.financials is None:
            raise MissingAttributeError("Missing the the required attributes: financials")
        
        return { i[0]:list(i[1].keys()) for i in self.financials[0]['financials'].items()}
    

    def _extract_from_fin(self, financial: str, metric: str) -> dict:

        """
        Extracts financial data for a given metric.
        """

        if self.financials is None:
            raise MissingAttributeError("Missing the the required attributes: financials")
        
        result: dict = {
            'start_date': [],
            'end_date': [],
            'timeframe':[],
            'fiscal_period':[],
            'fiscal_year':[],
            'value': []
        }

        for i in self.financials:
            value = i['financials'][financial].get(metric)
            if value is not None:
                result['start_date'].append(i['start_date'])
                result['end_date'].append(i['end_date'])
                result['timeframe'].append(i['timeframe'])
                result['fiscal_period'].append(i['fiscal_period'])
                result['fiscal_year'].append(i['fiscal_year'])
                result['value'].append(value['value'])
            else:
                raise IncorrectDataError

        return result

    
    def calculate_quarterly_data(self, financial: str, metric: str, year_from:int =2018) -> pd.DataFrame:

        """ 
        Create a quarterly dataframe containing the desired metric.

        The function calculates quarterly data, taking into consideration that the value for Q4 contains the
        entire year in the raw data. Some calculations are performed to extract the quarterly data for the
        last quarters. If the required data is not available, an exception is raised.
        """

        data = self._extract_from_fin(financial, metric)
        df = pd.DataFrame(data)

        quarterly_df = df[df['timeframe'] == 'quarterly']

        # Get a pd.Series containing which year has all of the 3 other quarters
        enough_q_years = (quarterly_df.groupby('fiscal_year')['fiscal_period'].count()) == 3
        enough_q_years.sort_index(ascending=False, inplace=True)


        countable_years = []
        for i, item in enumerate(enough_q_years.to_dict().items()):


            #I need the latest quarters also when we dont have full year
            if i == 0 and item[1] == False:
                countable_years.append(item[0])

            elif item[1] == True:
                countable_years.append(item[0])

            # Break at the first occurence when we dont have a full year.
            else:
                break

        
        # In these two case the data are aggregated for the q4 period, otherwise
        # we shouldn't make the subtraction

        if financial in ['income_statement','cash_flow_statement']:
            quarters_to_subtract = quarterly_df.loc[
                quarterly_df['fiscal_year'].isin(countable_years)
            ].groupby(['fiscal_year'])[['value']].agg('sum')

            quarters_to_subtract.rename(columns={'value': 'q_sum'}, inplace=True)

            df = df.merge( 
                quarters_to_subtract, 
                left_on='fiscal_year',
                right_on='fiscal_year'
            )
            df.loc[df['timeframe'] == 'quarterly']


            df['value'] = df['value'].where(
                cond=(df['timeframe'] == 'quarterly'),
                other=(df['value'] - df['q_sum'])
            )
            
        else:
            df = df[df['fiscal_year'].isin(countable_years)]


        df.rename(columns={'end_date':'fiscal_end_date'}, inplace=True)

        df['end_date'] = df['fiscal_end_date'].apply(lambda x : fiscal_to_calender_converter(x))
        df['end_date'] = pd.to_datetime(df['end_date'])
        df['quarter'] = df['end_date'].dt.quarter
        df['year'] = df['end_date'].dt.year
        df = df[['fiscal_end_date','end_date','year','quarter', 'value']]

        # Filtering the df based on the input parameter
        result = df.loc[df.year >= year_from]


        # Because I experienced some incorrect data from the API
        # I doublechek its correctness. This time I check if every calendar year
        # has its 4 month beside the starting and the ending year.
        # For example the data for JNJ are incorrect. 

        max_year = result['year'].max()
        min_year = result['year'].min()
        years_to_examine = result.loc[~result['year'].isin([max_year,min_year])]

        if (years_to_examine.groupby('year')['value'].count() != 4).any():
            raise IncorrectDataError()
        else:
            return result



    def get_ttm_data(self,financial: str, metric: str, year_from:int =2018) -> pd.DataFrame:
        """
        Retrieves trailing twelve months (TTM) data for the given metric.
        """

        df = self.calculate_quarterly_data(financial, metric, year_from)
        df.sort_values(by='end_date', ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)
        df['value']= df['value'].rolling(4, min_periods=4).sum()
        df = df.loc[df['value'].notnull()]

        return df
    
    
    def get_yearly_avg_data(self,financial: str, metric: str, year_from:int =2018) -> pd.DataFrame:
        """ 
        
        """
        df = self.calculate_quarterly_data(financial, metric, year_from)
        df.sort_values(by='end_date', ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)
        df['value']= df['value'].rolling(4, min_periods=4).mean()
        df = df.loc[df['value'].notnull()]

        return df

    def get_name(self) -> str:
        """
        Get the name of the company
        """

        if self.details is None:
            raise MissingAttributeError("Missing the the required attributes: details")
        
        return self.details['name']
    

    def get_market_cap(self) -> float:
        """
        Get the market capitalization.
        """

        if self.details is None:
            raise MissingAttributeError("Missing the the required attributes: details")
        
        return self.details['market_cap']
    

    def get_sic_desc(self) -> str:
        """
        Get the SIC (Standard Industrial Classification) description.
        """

        if self.details is None:
            raise MissingAttributeError("Missing the the required attributes: details")
        
        return self.details['sic_description']
    

    def get_curr_prev_price(self) -> dict[str,float]:
        """
        Get the current and previous (daily) closing prices.
        """

        if self.price_hist is None:
            raise MissingAttributeError("Missing the the required attributes: price_hist")
        
        return {
            'current':self.price_hist.iloc[-1]['Close'],
            'previous':self.price_hist.iloc[-2]['Close']
        }
    

    def get_eps(self) -> float:
        """
        Get the earnings per share (EPS)
        """

        if self.details is None:
            raise MissingAttributeError("Missing the the required attributes: details")
        
        ttm_incomes = self.calculate_quarterly_data(
            'income_statement','net_income_loss_attributable_to_parent'
        )['value'][:4].sum()

        return ttm_incomes / self.details['weighted_shares_outstanding']
    
    
    def get_pe(self) -> float:
        """
        Get the price-to-earnings (P/E) ratio.
        """
        return self.get_curr_prev_price()['current']  / self.get_eps()
    

    def get_52week_low(self) -> float:
        """
        Get the 52-week low price.
        """

        if self.price_hist is None:
            raise MissingAttributeError("Missing the the required attributes: price_hist")

        date = datetime.now() - timedelta(weeks=52)
        df = self.price_hist.drop(columns='Volume')
        return df[df.index >= date]['Low'].min()
    

    def get_52week_high(self) -> float:
        """ 
        Get the 52-week high price.
        """

        if self.price_hist is None:
            raise MissingAttributeError("Missing the the required attributes: price_hist")

        date = datetime.now() - timedelta(weeks=52)
        df = self.price_hist.drop(columns='Volume')
        return df[df.index >= date]['High'].max()
    

    def get_next_report_date(self) -> str:
        """
        Get the date of the next earnings report.
        """

        if self.earning_dates is None:
            raise MissingAttributeError("Missing the the required attributes: earning_dates")

        df = self.earning_dates['Reported EPS']
        df = df.loc[df.isnull()]
        return df.index[-1].date().strftime('%Y-%m-%d')
    

    def get_earnings_dates(self) -> pd.DataFrame:
        """
        Get a DataFrame of earnings dates containing historically the reported and the estimated EPS
        """

        if self.earning_dates is None:
            raise MissingAttributeError("Missing the the required attributes: earning_dates")

        df = self.earning_dates.reset_index(drop=False)
        df['Earnings Date'] = df['Earnings Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        return df


    def get_ttm_profit_margin(self) -> pd.DataFrame:
        """
        Get the trailing twelve months (TTM) profit margin.
        """

        df_ttm_income = self.get_ttm_data('income_statement','net_income_loss_attributable_to_parent')
        df_ttm_revenue = self.get_ttm_data('income_statement','revenues')
        
        df_ttm_income.rename(columns={'value':'income'}, inplace=True)
        df_ttm_revenue.rename(columns={'value':'revenue'}, inplace=True)

        df = df_ttm_income.merge(
            df_ttm_revenue[['end_date','revenue']],
            left_on='end_date',
            right_on='end_date'
        )

        df['value'] = np.round(df['income'] / df['revenue'],4)
        df = df.loc[df['value'].notnull()]
        return df[['end_date','year','quarter','value']]
        
    
    def get_profit_margin(self) -> float:
        """
        Get the current profit margin.
        """
        return self.get_ttm_profit_margin().iloc[-1]['value']
    

    def get_yearly_price_change(self) -> float:
        """ 
        Get the percentage change in price over the last year.

        """

        if self.price_hist is None:
            raise MissingAttributeError("Missing the the required attributes: price_hist")

        df = self.price_hist
        
        curr_date = (df.iloc[-1]).name 
        curr_price = df['Close'].loc[curr_date] # type: ignore
        ly_price_date = curr_date - timedelta(weeks=52) # type: ignore

        ly_price = df[df.index < ly_price_date]['Close'].iloc[-1]

        return (curr_price/ly_price -1)
    
    
    def get_div_yield(self) -> float:
        """
        Get the current dividend yield.

        """

        if self.dividend_hist is None:
            raise MissingAttributeError("Missing the the required attributes: dividend_hist")

        df = self.dividend_hist
        df = df.loc[df['Dividends'] > 0]
        div_ttm = df.loc[df.index >df.index.max() - timedelta(weeks=50)].sum().iloc[0]

        return (div_ttm / self.get_curr_prev_price()['current'])


    def get_roe(self) -> float:
        """
        Get the return on equity (ROE).
        """

        last_ttm_net_income = self.get_ttm_data('income_statement','net_income_loss_attributable_to_parent')['value'].iloc[-1]

        avg_equity_sh = self.get_yearly_avg_data('balance_sheet','equity_attributable_to_parent')['value'].iloc[-1]

        return (last_ttm_net_income / avg_equity_sh)
    

    def get_news_df(self) -> pd.DataFrame:
        """
        Get a DataFrame of news articles and its urls regarding the relevant company
        """


        if self.news is None:
            raise MissingAttributeError("Missing the the required attributes: news")
        
        # empty list to pupulate
        title = []
        url = []

        for new in self.news:
            title.append(new['title'])
            url.append(new['article_url'])


        return pd.DataFrame({
            'Title':title,
            'URL':url
        })


    def get_news_html(self) -> str:
        """
        Get an HTML representation of news articles with clickable links.
        """

        df = self.get_news_df()
        
        # Extract the domain name (page name) from the URL using regex
        def extract_domain(url_col):
            match = re.search(r'://(www\.)?(.*?)\/', url_col)
            if match:
                return match.group(2)
            else:
                return ''

        df['Page'] = df['URL'].apply(extract_domain)

        # Create a new column for clickable links
        df['Link'] = df['URL'].apply(lambda x: f'<a href="{x}" target="_blank">Link</a>')        
        df.drop(columns=['URL'], inplace=True)

        # Convert the DataFrame to HTML
        html_code =  df.to_html(escape=False, index=False)
        html_code = html_code.replace(
            '<tr style="text-align: right;">',
            '<tr style="text-align: left;">'
        )
        return html_code