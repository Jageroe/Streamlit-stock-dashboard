"""
This module containing components and tools for our Streamlit page 
It will be initialized from the main.py file.
"""

from datetime import datetime
from typing import List, Optional
import os 
from os import getenv # type: ignore
import pandas as pd
import plotly.graph_objects as go # type: ignore
from plotly.graph_objs._figure import Figure  # type: ignore
import streamlit as st # type: ignore

from src.polygon_api import check_ticker_validity
from src.json_io import check_ticker_on_list, delete_ticker, add_ticker, read_ticker_list

import time 
from dotenv import load_dotenv
from streamlit.delta_generator import DeltaGenerator

# Loading the .env file and the api key from it
load_dotenv()
TICKER_FILE: str = getenv("TICKER_FILE") # type: ignore


def _set_page_width() -> DeltaGenerator:
    """
    Workaround the set the streamlit page wider, because using streamlit wide mode doesn't result the desired page structure.
    """

    css="""
    <style>
        section.main > div {max-width:60rem}
    </style>
    """
    return st.markdown(css, unsafe_allow_html=True)


def basic_page_setup() -> None:

    # Basic page setups
    st.set_page_config(page_title="Stonks$$",page_icon="📉",)
    _set_page_width()



def add_sidebar_ticker_form() -> Optional[str]:
    """ 
    Method to setup the streamlit sidebar part of the page.
    Including:
        - A selection box to choose from saved tickers.
        - A ticker form to add new tickers and delete them from the saved tickers list

    """

    ticker_options = read_ticker_list(TICKER_FILE)

    option = st.sidebar.selectbox(
        "Choose ticker",
        ticker_options,
        index=None,
        placeholder="Select ticker...",
    )

    # Sidebar: add/delete ticker part

    # Streamlit has a unique control flow. It runs the entire script from top to bottom
    # every time there is interaction with a button. Due to this, I need to implement a workaround:
    # I save the state of those buttons and store it in the session_state. When the script reruns,
    # the button's state is retrieved from the session_state, preventing it from being forgotten.

    def get_add_ticker_form_state() -> bool:
        if 'add_ticker_form_state' not in st.session_state:
            st.session_state['add_ticker_form_state'] = None
        return st.session_state['add_ticker_form_state']

    def get_delete_ticker_form_state() -> bool:
        if 'delete_ticker_form_state' not in st.session_state:
            st.session_state['delete_ticker_form_state'] = None
        return st.session_state['delete_ticker_form_state']

    # If the add_ticker button is active this method returns True
    if get_add_ticker_form_state():
        with st.sidebar.form('form'):
            temp_add_input = st.text_input('Add new ticker')
            cols = st.columns(2)
            if cols[0].form_submit_button('submit'):
                ticker_to_add = temp_add_input.upper()

                # Checking if the given ticker is valid
                if check_ticker_validity(ticker_to_add):

                    # Checking if the given ticker is already in the ticker list
                    if check_ticker_on_list(TICKER_FILE, ticker_to_add):

                        st.warning('The ticker is already on the list!')
                        # Keep the warning lane visibile for a while
                        time.sleep(0.7)
                    else:
                        add_ticker(TICKER_FILE,ticker_to_add)
                        st.success(f'{ticker_to_add} successfully saved!')
                        # Keep the success lane visibile for a while
                        time.sleep(0.7)

                else:
                    st.error(f'{ticker_to_add} is not a valid ticker or its not available!')
                    # Keep the error lane visibile for a while
                    time.sleep(1)
                    st.rerun()
                st.session_state['add_ticker_form_state']=False
                st.rerun()

            if cols[1].form_submit_button('cancel'):
                st.session_state['add_ticker_form_state']=False
                st.rerun()

    # If the delete ticker button is active this method returns True
    elif get_delete_ticker_form_state():
        with st.sidebar.form('form'):
            pass
            temp_del_input = st.selectbox(
                "Choose ticker to delete",
                ticker_options,
                index=None
            )

            cols = st.columns(2)
            if cols[0].form_submit_button('delete'):
                ticker_to_del = temp_del_input

                if ticker_to_del is None:
                    st.warning("Choose a ticker first!")
        
                else: 
                    if delete_ticker(TICKER_FILE,ticker_to_del):
                        st.success(f'{ticker_to_del} successfully deleted!')
                        time.sleep(0.5)
                    else:
                        st.warning(f'The deletion was unsuccessful!')
                        time.sleep(0.5)

                st.session_state['delete_ticker_form_state']=False
                st.rerun()

            if cols[1].form_submit_button('cancel'):
                st.session_state['delete_ticker_form_state']=False
                st.rerun()

    else:
        button_cols = st.sidebar.columns(2)
        if button_cols[0].button('Add new ticker'):
            st.session_state['add_ticker_form_state'] = True
            st.rerun()

        if button_cols[1].button('Delete ticker'):
            st.session_state['delete_ticker_form_state'] = True
            st.rerun()


    return option


def _configure_layout(fig: Figure) -> None:
    """
    Configure layout settings for the given Plotly Figure object.

    """
    fig.update_layout(margin=dict(l=20, r=20, t=5, b=40), height=300)



def _quartely_barplot(data:pd.DataFrame) -> Figure:
    """
    Generate a quarterly bar plot using the given DataFrame.

    Args:
        data: output df of the src.data_processor's calculate_quarterly_data method

    """

    # Convert data to a DataFrame and perform data type conversion
 
    df_pivot = pd.pivot_table(
        data=data, 
        values='value', 
        index=['quarter'],
        columns='year', 
        aggfunc="sum"
    )

    # ploty
    fig = go.Figure()
    for col in df_pivot.columns:
        fig.add_trace(
            go.Bar(
                x=df_pivot.index, 
                y=df_pivot[col],
                name = col,
            )
        )

    _configure_layout(fig)
    return fig






def _yearly_lineplot(data:pd.DataFrame) -> Figure:
    """
    Generate a yearly line plot using the given DataFrame.

    Args:
        data: output df of the src.data_processor's calculate_quarterly_data method

    """


    df_pivot = pd.pivot_table(
        data=data,
        values='value',
        index=['year'],
        aggfunc= ['sum','count']
    )

    df_pivot.columns = df_pivot.columns.droplevel(level=1)
    df_pivot = df_pivot.loc[df_pivot['count'] == 4]
    df_pivot.drop(columns='count', inplace=True)

    fig = go.Figure(data=go.Scatter(x=df_pivot.index, y=df_pivot['sum']))
    _configure_layout(fig)
    return fig


def _quarterly_lineplot(data:pd.DataFrame) -> Figure:
    """
    Generate a quarterly line plot using the given DataFrame.

    Args:
        data: output df of the src.data_processor's calculate_quarterly_data method

    """


    # Convert data to a DataFrame and perform data type conversion
    df = pd.DataFrame(data)
    
    # fig = px.line(x=df_pivot.index, y=df_pivot['sum'])
    fig = go.Figure(data=go.Scatter(x=df['end_date'], y=df['value']))
    _configure_layout(fig)
    return fig


def _candlestick_chart(hist: pd.DataFrame, start_date: datetime, end_date: datetime) -> Figure:
    
    """
    Generate a candlestick chart using the given DataFrame and date range.

    Args:
        hist (pd.DataFrame): Input DataFrame with 'Open', 'High', 'Low', 'Close' columns.
        start_date (datetime): Start date for filtering the data.
        end_date (datetime): End date for filtering the data.

    """
    
    hist = hist.loc[
        (hist.index >= pd.to_datetime(start_date)) & 
        (hist.index <= pd.to_datetime(end_date))
    ]
    
    fig = go.Figure(
        data=[go.Candlestick(
            x=hist.index,
            open=hist['Open'], high=hist['High'],
            low=hist['Low'], close=hist['Close'])
        ]
    )

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=5, b=40)
    )

    return fig


def add_center_panel(data, candlestick_chart_status) -> None:
    """ 
    Method to setup the center part of the streamlit page. It containts
    every information of the choosen ticker.
    
    """
    name = data.get_name()
    sic_desc = data.get_sic_desc()

    # Header
    st.markdown(
        f""" 
        # {name} - {data.ticker}
        Industries: {sic_desc.lower()}
    
        ---
        """
    )

    # Main metrics under the header
    current_price = data.get_curr_prev_price()['current']
    last_price = data.get_curr_prev_price()['previous']
    price_delta = ((current_price / last_price) -1) * 100
    yearly_change = round(data.get_yearly_price_change()*100,2)
    yearly_change_prefix = "+" if yearly_change > 0 else ""
    market_cap = round(data.get_market_cap() / 1000000000,2)

    cols = st.columns(6)
    cols[0].metric(
        'Current price',
        round(current_price,2),
        f'{price_delta:.2f} %'
    )
    cols[1].metric("Yearly change", f'{yearly_change_prefix}{yearly_change}%')
    cols[2].metric('52 Week High', round(data.get_52week_high(),2))
    cols[3].metric('52 Week Low', round(data.get_52week_low(),2))
    cols[4].metric('Market cap (B)',market_cap)

    cols = st.columns(6)
    cols[0].metric('EPS', round(data.get_eps(),2))
    cols[1].metric('P/E', round(data.get_pe(),2))
    cols[2].metric('ROE', round(data.get_roe() * 100,2))
    cols[3].metric('ProfitMargin', f'{data.get_profit_margin()* 100:.2f}%')
    cols[4].metric('DividendYield', f'{data.get_div_yield() * 100:.2f}%')

    # I use markdown here, becasue the streamlit's internal tool makes to large margins. 
    st.markdown(
        f""" 
        Next report's date: {data.get_next_report_date()}

        ---
        """
    )

    if candlestick_chart_status:

        # Candlestick chart
        start_time, end_time = st.slider(
            "Select period:",
            value=(datetime(2020, 1, 1, 9, 30),datetime(2023, 10, 15, 9, 30)),
            format="YYYY/MM/DD"
        )
        st.plotly_chart(
            _candlestick_chart(data.price_hist, start_time, end_time),
            use_container_width=True
        )

    # Net income part
    st.subheader("Net Income")
    col_ni = st.columns(2)
    df = data.calculate_quarterly_data('income_statement','net_income_loss_attributable_to_parent')
    col_ni[0].caption("Quarterly")
    col_ni[0].plotly_chart(_quartely_barplot(df),use_container_width=True)
    col_ni[1].caption("Yearly")
    col_ni[1].plotly_chart(_yearly_lineplot(df),use_container_width=True)

    # Revenue part
    st.subheader("Revenue")
    col_charts = st.columns(2)
    df = data.calculate_quarterly_data('income_statement','revenues')
    col_charts[0].caption("Quarterly")
    col_charts[0].plotly_chart(_quartely_barplot(df),use_container_width=True)
    col_charts[1].caption("Yearly")
    col_charts[1].plotly_chart(_yearly_lineplot(df),use_container_width=True)

    # TTM profit line plot
    df_profit_margin = data.get_ttm_profit_margin()
    cols = st.columns(2)
    cols[0].subheader("Profit margin %")
    cols[0].plotly_chart(_quarterly_lineplot(df_profit_margin),use_container_width=True)

    # EPS report table
    cols[1].subheader("EPS reports %")
    cols[1].dataframe(data.get_earnings_dates().iloc[:7],use_container_width=True)

    # TTM Cashflow lineplot
    df = data.get_ttm_data('cash_flow_statement','net_cash_flow')
    st.subheader("Free cashflow - TTM")
    st.plotly_chart(_quarterly_lineplot(df),use_container_width=True)

    # News table with clickable links
    news_html = data.get_news_html()
    st.subheader("Relevant news")
    st.markdown(news_html,unsafe_allow_html=True)