#!/usr/bin/env python3

# Handle the task of getting the absolute path for the current working directory
import os.path

# Handle command line arguments
import argparse

# Sqlite
import sqlite3
from sqlite3 import Error

# Use flask to serve the static html file instead of using the python simple server.
# Gives control of what is actually served from the server, and allows us to do some
# preprocessing to the html file if we chose choose before it's delivered.
from flask import Flask
from flask import render_template

# creates a Flask application, named app
app = Flask(__name__)
app.config['ENV'] = 'development'

# Route to serve the HTML file with inserted keyValue pairs to be used by the React Javascript
@app.route("/")
def hello():
    databaseRows = getAllKeys(app.config['DATABASE_FILE'])
    keys = [{ 'keyName': row[0], 'value': row[3]} for row in databaseRows]
    return render_template('monitoring_page.html', keys=keys)


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def getAllKeys(db_file):
    """ get all rows from the keysTable in the SQLite database
        specified by db_file
    :param db_file: database file
    """
    connection = create_connection(db_file)
    with connection:
        selectAllQuery = """ SELECT * FROM keysTable """

        cursor = connection.cursor()
        try:
            cursor.execute(selectAllQuery)
        except Exception as error:
            print(error)

        rows = cursor.fetchall()

        return rows


def main():
    parser = argparse.ArgumentParser(description='Start the memcached and front end servers')
    parser.add_argument('databaseFile', metavar='databaseFile', type=str,
                        help='the database for the memcached server')

    args = parser.parse_args()

    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    databaseFile = cwd+'/'+args.databaseFile

    app.config['DATABASE_FILE'] = databaseFile
    app.run(debug=False, host='0.0.0.0', port=8000)

if __name__ == "__main__":
    main()
