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

# a route where we will display a welcome message via an HTML template
@app.route("/")
def hello():
    message = "Hello, World"
    return render_template('monitoring_page.html', message=message)


def main():
    parser = argparse.ArgumentParser(description='Start the memcached and front end servers')
    parser.add_argument('databaseFile', metavar='databaseFile', type=str,
                        help='the database for the memcached server')

    args = parser.parse_args()

    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    databaseFile = cwd+'/'+args.databaseFile

    print('frontEndServer: ', databaseFile)

    app.run(debug=True, host='0.0.0.0', port=8000)

if __name__ == "__main__":
    main()
