import streamlit as st
from src.polygon_api import PolygonAPI
from src.daily_price_api import PriceAPI
from src.data_processor import DataProcessor
from src.components import add_sidebar_ticker_form, basic_page_setup, add_center_panel


@st.cache_data
def init_load_data(ticker):
    """ 
    Initialize a dataprocessor object and calling the neccessarry requests. 
    """

    fin_api = PolygonAPI(ticker)
    fin_api.get_ticker_details()
    fin_api.get_financials()
    fin_api.get_news()

    price_api = PriceAPI(ticker)
    price_api.get_history()
    price_api.get_earnings_dates()


    return DataProcessor(
        fin_api=fin_api,
        price_api=price_api
    )

def main():     


    basic_page_setup()

    # Creating the ticker handling component to the sidebar
    option = add_sidebar_ticker_form()

    # Settings part on the sidebar
    st.sidebar.divider()
    st.sidebar.caption("Settings:")
    candlestick_chart_status = st.sidebar.toggle('Show candlestick chart')

    # If there's a choosen ticker
    if option:
        data = init_load_data(option)
        # The main panel, where everything is shown
        add_center_panel(data, candlestick_chart_status)

        
if __name__ == "__main__":
    main()