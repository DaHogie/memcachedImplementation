#!/usr/bin/env python3

# Running both servers in the same process
import subprocess

# Handle the task of getting the absolute path for the current working directory
import os.path

# Handle command line arguments
import argparse

# Sqlite
import sqlite3
from sqlite3 import Error

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

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def main():
    parser = argparse.ArgumentParser(description='Start the memcached and front end servers')
    parser.add_argument('databaseFile', metavar='databaseFile', type=str,
                        help='the database file for the memcached server')

    args = parser.parse_args()

    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    databaseFile = cwd+'/'+args.databaseFile

    sql_create_keys_table = """ CREATE TABLE IF NOT EXISTS keysTable (
                                    key text PRIMARY KEY,
                                    flags integer NOT NULL,
                                    bytes integer,
                                    dataBlock text
                                ); """

    # create a database connection
    conn = create_connection(databaseFile)

    # create tables
    if conn is not None:
        # create keys table
        create_table(conn, sql_create_keys_table)
    else:
        print("Error! cannot create the database connection.")


    try:
        subprocess.Popen(('python3',
            'frontendserver.py', args.databaseFile), cwd=cwd)
    except IndexError:
        print('Cannot find frontendserver.py')
        sys.exit(1)

    try:
        subprocess.Popen(('python3',
            'memcachedserver.py', args.databaseFile), cwd=cwd)
    except IndexError:
        print('Cannot find memcachedserver.py')
        sys.exit(1)


    try:
        while True:
            pass
    except KeyboardInterrupt:
        print('All servers terminated')

if __name__ == '__main__':
    main()
