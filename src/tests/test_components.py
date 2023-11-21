import pandas as pd
import pytest
import plotly.graph_objects as go
from datetime import datetime
import os, sys

# Add the 'src' folder to the Python path
src_dir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(src_dir)

import src.components as components  # Replace 'your_module' with the actual module name containing your functions

# Test data for your functions
test_data = pd.DataFrame(

{
    'fiscal_end_date': [
        '2023-09-30','2023-06-30','2023-03-31','2022-12-31',
        '2022-09-30','2022-06-30','2022-03-31','2021-12-31',
        '2021-09-30','2021-06-30','2021-03-31'
    ],
    'end_date': [
        '2023-09-30','2023-06-30','2023-03-31','2022-12-31',
        '2022-09-30','2022-06-30','2022-03-31','2021-12-31',
        '2021-09-30','2021-06-30','2021-03-31'
    ],
    'year': [
        2023,2023,2023,2022,
        2022,2022,2022,2021,
        2021,2021,2021
    ],
    'quarter': [
        3,2,1,4,
        3,2,1,4,
        3,2,1
    ],
    'value': [
        19689000000.0,18368000000.0,15051000000.0,13624000000.0,
        13910000000.0,16002000000.0,16436000000.0,20642000000.0,
        18936000000.0,18525000000.0,17930000000.0
    ]
})

def test_quartely_barplot():
    fig = components._quartely_barplot(test_data)
    assert isinstance(fig, go.Figure)

def test_yearly_lineplot():
    fig = components._yearly_lineplot(test_data)
    assert isinstance(fig, go.Figure)

def test_quarterly_lineplot():
    fig = components._quarterly_lineplot(test_data)
    assert isinstance(fig, go.Figure)

def test_candlestick_chart():
    hist_data = pd.DataFrame({
        'Open': [100, 150, 180, 220],
        'High': [120, 170, 190, 230],
        'Low': [80, 140, 170, 210],
        'Close': [110, 160, 200, 215]
    }, index=pd.date_range(start='2022-01-01', periods=4))
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 1, 4)
    fig = components._candlestick_chart(hist_data, start_date, end_date)
    assert isinstance(fig, go.Figure)
