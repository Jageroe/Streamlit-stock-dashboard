import os
import sys

# Add the 'src' folder to the Python path
src_dir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(src_dir)

from src.json_io import read_ticker_list, add_ticker, delete_ticker, check_ticker_on_list
TEST_JSON_PATH = 'src/tests/test_tickers.json'


def test_read_ticker_list_when_doesnt_exist():
    """ 
    Try to read the JSON file. Because it doesnt exist, 
    it should create one. 
    """
    read_ticker_list(TEST_JSON_PATH)

def test_add_ticker1():

    add_ticker(TEST_JSON_PATH,'GOOGL')
    assert len(read_ticker_list(TEST_JSON_PATH)) == 1

def test_add_ticker2():

    # I intentionally typed that in lowercase."
    add_ticker(TEST_JSON_PATH,'pypl')
    assert len(read_ticker_list(TEST_JSON_PATH)) == 2

def test_add_ticker3():

    add_ticker(TEST_JSON_PATH,'MSFT')
    assert len(read_ticker_list(TEST_JSON_PATH)) == 3


def test_check_ticker_on_list_existing():
    assert check_ticker_on_list(TEST_JSON_PATH,'MSFT') == True


def test_check_ticker_on_list_non_existing():
    assert check_ticker_on_list(TEST_JSON_PATH,'TESTCOMPANY') == False


def test_delete_ticker_case1():

    delete_ticker(TEST_JSON_PATH, 'PYPL')
    assert len(read_ticker_list(TEST_JSON_PATH)) == 2


def test_delete_ticker_case2():

    delete_ticker(TEST_JSON_PATH, 'MSFT')
    assert len(read_ticker_list(TEST_JSON_PATH)) == 1


def test_delete_json():
    """ 
    This is not an actual test function. 
    It just to set everything to default (delete the test JSON file.)
    """

    os.remove(TEST_JSON_PATH)
