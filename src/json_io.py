""" 
Simple module to handle JSON i/o operation to store the tickers which 
have been added

"""

import json
import os


def _create_file_if_not_exists(ticker_file:str):
    """
    Create the JSON file if it doesn't exist at the given location
    """
        
    if not os.path.exists(ticker_file):
        with open(ticker_file, "w") as file:
                json.dump([], file)  # Create an empty JSON array
      

def read_ticker_list(ticker_file:str) -> list:
    """
    Opens the JSON file containing tickers and returns its content as a list.
    """

    
    _create_file_if_not_exists(ticker_file)

    with open(ticker_file, "r+") as file:
        tickers = json.load(file)
        return tickers


# Function to add ticker to the list
def add_ticker(ticker_file:str, ticker_to_add:str) -> None:
    """
    Add the given ticker to the specified JSON file.
    """
    with open(ticker_file, "r+") as file:
        tickers = json.load(file)
        if ticker_to_add.upper() not in tickers:
            tickers.append(ticker_to_add.upper())
            file.seek(0)
            json.dump(tickers, file, indent=2)


# Function to delete ticker from the list
def delete_ticker(ticker_file:str, ticker_to_delete:str) -> bool:
    """ 
    Delete the given ticker 
    """

    try:
        with open(ticker_file, 'r+') as file:
            data = json.load(file)

        # Check if the entry exists in the data
        if ticker_to_delete not in data:
            #I.e. not a succesfully delete
            return False
        
        # Remove the entry
        data.remove(ticker_to_delete)

        # Write the updated data back to the file
        with open(ticker_file, 'w') as file:
            json.dump(data, file, indent=2)

        return True

    except:
        return False

        


def check_ticker_on_list(ticker_file:str, ticker:str) -> bool:
    """
    Check if the given ticker is in the list stored in the JSON file.
    """
    with open(ticker_file, "r+") as file:
        tickers = json.load(file)

    if ticker in tickers:
        return True
    else:
        return False
     

