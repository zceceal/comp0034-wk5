# Different options for creating the database and adding data to the database
import csv
import sqlite3
import pandas as pd
from pathlib import Path

from paralympics import Region, Event

# File locations
db_file = Path(__file__).parent.joinpath("paralympics.sqlite")
region_file = Path(__file__).parent.parent.joinpath("data", "noc_regions.csv")
event_file = Path(__file__).parent.parent.joinpath("data", "paralympic_events.csv")


def create_db_if_not_exist(db_file):
    """
    For the coursework the Flask-SQLAlchemy db.create_all() will do this for you. You do not need this for the
    coursework. This is just an example of how you could use sqlite3 instead.

    sqlite3 creates the file in the specified path if the file does not already exist. Tables are only added if they
    don't exist.
    :param db_file: Path to the file location
    :return:
    """
    # 1. Create a SQLite database engine that connects to the database file
    connection = sqlite3.connect(db_file)

    # 2. Create a cursor object to execute SQL queries
    cursor = connection.cursor()

    # 2. Define the tables in SQL
    # 'region' table definition in SQL
    create_region_table = """CREATE TABLE if not exists region(
                        NOC TEXT PRIMARY KEY,
                        region TEXT NOT NULL,
                        notes TEXT);
                        """

    # 'event' table definition in SQL
    # Columns in the csv file: type, year, country, host, NOC, start, end, duration, disabilities_included,
    # countries, events, sports, participants_m, participants_f, participants, highlights
    create_event_table = """CREATE TABLE if not exists event(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            year INTEGER,
            country TEXT,
            host TEXT,
            NOC TEXT,
            start TEXT,
            end TEXT,
            duration INTEGER,
            disabilities_included TEXT,
            events INTEGER,
            sports INTEGER,
            countries INTEGER,
            participants_m INTEGER,
            participants_f INTEGER,
            participants INTEGER,
            highlights TEXT,
            FOREIGN KEY(NOC) REFERENCES region(NOC));"""

    # 4. Execute SQL to create the tables in the database
    cursor.execute(create_region_table)
    cursor.execute(create_event_table)

    # 5. Commit the changes to the database (this saves the tables created in the previous step)
    connection.commit()


def add_data_pandas(region_file, event_file):
    """
    Version that adds data to the database using pandas DataFrame methods.

    pandas.to_csv() can also create the database tables, however this will use the columns as defined in the
    DataFrame which may not match what you want for the database.
    :param event_file: csv file with teh event data
    :param region_file: csv file with the region data
    """
    # 1. Create a SQLite database engine that connects to the database file
    connection = sqlite3.connect(db_file)

    # 2. Import data from CSV to database table using pandas read_csv
    # First count the existing rows in the region, only add data if there are 0 rows
    num = connection.cursor().execute("SELECT COUNT(*) FROM region")
    count = num.fetchone()[0]
    if count == 0:
        # Read the noc_regions data to a pandas dataframe
        na_values = [""]
        regions_df = pd.read_csv(region_file, keep_default_na=False, na_values=na_values)

        # 3. Write the pandas DataFrame contents to the database tables
        # For the region table we do not want the pandas DataFrame index column
        regions_df.to_sql("region", connection, if_exists="append", index=False)

    # Count the existing rows in event table, only add data if there are 0 rows
        num = connection.cursor().execute("SELECT COUNT(*) FROM event")
        count = num.fetchone()[0]
        if count == 0:
            # Read the paralympics event data to a pandas dataframe
            events_df = pd.read_csv(event_file)

            # 3. Write the pandas DataFrame contents to the database tables
            # For the event table we want the pandas index, but it needs to start from 1 and not 0
            events_df.index += 1
            events_df.to_sql("event", connection, if_exists="append", index_label='id')

    # 4. Close the database connection
    connection.close()


def add_data_csv(db_file, region_file, event_file):
    """Add data using sqlite3 to make the connection and csv to read the data

    Only add the data if it doesn't exist.
    :param db_file: database file
    :param region_file: csv file with the region data
    :param event_file: csv file with the event data
    """
    # 1. Create a SQLite database engine that connects to the database file
    connection = sqlite3.connect(db_file)

    # 2. Create a cursor object to execute SQL queries
    cursor = connection.cursor()

    # 3. Import data from CSV and write to database table
    # First count the existing rows, only add data if there are 0 rows
    num = cursor.execute("SELECT COUNT(*) FROM region")
    count = num.fetchone()[0]
    if count == 0:
        # open the csv file using csv.reader and execute the sql using sqlite3 cursor
        with open(region_file, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header row
            sql = "INSERT INTO region values(?, ?, ?)"
            for row in csv_reader:
                for i in range(len(row)):
                    if row[i] == '':
                        row[i] = None
                cursor.execute(sql, row)
            connection.commit()

    # First check if there are any existing rows, only add data if there are 0 rows
    num = cursor.execute("SELECT count(*) FROM event")
    count = num.fetchone()[0]
    if count == 0:
        with (open(event_file, 'r') as file):
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header row
            sql = ("INSERT INTO event (type, year, country, host, NOC, start, end, duration, disabilities_included, "
                   "events, sports, countries, participants_m, participants_f, participants, highlights) VALUES (?, ?, ?, "
                   "?, ?, ?, ?, ?, ?, ? ,?, ?, ?, ?, ?, ?)")
            for row in csv_reader:
                for i in range(len(row)):
                    if row[i] == '':
                        row[i] = None
                cursor.execute(sql, row)
            connection.commit()

    # 8. Close the database connection
    connection.close()

def add_data(db):
    """Adds data to the database if it does not already exist.

    This method uses db which is the FlaskSQLALchemy instance for the app

    :param db: SQLAlchemy database for the app
    """

    # If there are no regions in the database, then add them
    first_region = db.session.execute(db.select(Region)).first()
    if not first_region:
        print("Start adding region data to the database")
        noc_file = Path(__file__).parent.parent.joinpath("data", "noc_regions.csv")
        with open(noc_file, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header row
            for row in csv_reader:
                # row[0] is the first column, row[1] is the second column
                r = Region(NOC=row[0], region=row[1], notes=row[2])
                db.session.add(r)
            db.session.commit()

    # If there are no Events, then add them
    first_event = db.session.execute(db.select(Event)).first()
    if not first_event:
        print("Start adding event data to the database")
        event_file = Path(__file__).parent.parent.joinpath("data", "paralympic_events.csv")
        with open(event_file, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header row
            for row in csv_reader:
                # row[0] is the first column, row[1] is the second column etc
                e = Event(type=row[0],
                          year=row[1],
                          country=row[2],
                          host=row[3],
                          NOC=row[4],
                          start=row[5],
                          end=row[6],
                          duration=row[7] or None,
                          disabilities_included=row[8],
                          countries=row[9] or None,
                          events=row[10] or None,
                          sports=row[11] or None,
                          participants_m=row[12] or None,
                          participants_f=row[13] or None,
                          participants=row[14] or None,
                          highlights=row[15])
                db.session.add(e)
            db.session.commit()


# if __name__ == '__main__':
    # Add code here if you want to run it as a one off
    # create_db_if_not_exist(db_file)
    # add_data_csv(region_file=region_file, event_file=event_file, db_file=db_file)
    # add_data_pandas(region_file=region_file, event_file=event_file)
