# Import CSV to an existing database in the instance folder using sqlite3
from pathlib import Path
import sqlite3
import pandas as pd

if __name__ == '__main__':
    # 1. Create a SQLite database engine that connects to the database file
    db_file = Path(__file__).parent.parent.joinpath("instance", "paralympics.sqlite")
    connection = sqlite3.connect(db_file)

    # 2. Create a cursor object to execute SQL queries
    cursor = connection.cursor()

    # 3. Read the .csv or .xlsx files into pandas DataFrames

    # Read the noc_regions data to a pandas dataframe
    # Additional string to read "" as a null value
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html
    na_values = ["", ]
    noc_file = Path(__file__).parent.parent.joinpath("data", "noc_regions.csv")
    noc_regions = pd.read_csv(noc_file, keep_default_na=False, na_values=na_values)

    # Read the paralympics event data to a pandas dataframe
    event_file = Path(__file__).parent.parent.joinpath("data", "paralympic_events.csv")
    paralympics = pd.read_csv(event_file)

    # 4. Write the data from the pandas DataFrame to the database tables

    # if_exists="replace" If there is data in the table, replace it
    #  index=False Do not write the pandas index column to the database table
    noc_regions.to_sql("region", connection, if_exists="replace", index=False)
    paralympics.to_sql("event", connection, if_exists="replace", index=False)

    # 5. Close the database connection
    connection.close()
