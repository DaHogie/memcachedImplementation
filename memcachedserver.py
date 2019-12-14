#!/usr/bin/env python3

# Manage socket connections for telnet to use the memcached server
import asyncio

# Handle the task of getting the absolute path for the current working directory
import os.path

# Handle command line arguments
import argparse

# Sqlite
import sqlite3
from sqlite3 import Error

class MemcachedServer(asyncio.Protocol):
    """Implementation of the Memcached Protocol with Asyncio
    Static variables are for constants
    """
    TIMEOUT = 10 # Seconds
    CLIENT_ERROR_FORMATTING_SET = b'CLIENT_ERROR incorrect # of arguments for set command\r\n'
    CLIENT_ERROR_FORMATTING_SET_NOREPLY = b'CLIENT_ERROR incorrect 6th argument to set command. Expected \'noreply\'\r\n'
    CLIENT_ERROR_FORMATTING_SET_KEY_LENGTH_TOO_LONG = b'CLIENT_ERROR key length of set command exceeds 250 characters'
    CLIENT_ERROR_FORMATTING_GET = b'CLIENT_ERROR incorrect # of arguments for get command\r\n'
    CLIENT_ERROR_FORMATTING_DELETE = b'CLIENT_ERROR incorrect # of arguments for delete command\r\n'
    CLIENT_ERROR_FORMATTING_DELETE_NOREPLY = b'CLIENT_ERROR incorrect 3rd argument to set command. Expected \'noreply\'\r\n'

    SERVER_ERROR_SET_FAILURE = b'SERVER_ERROR error storing data\r\n'
    SERVER_ERROR_GET_FAILURE = b'SERVER_ERROR error retrieving stored data\r\n'
    SERVER_ERROR_DELETE_FAILURE = b'SERVER_ERROR error deleting stored data\r\n'

    SET_SUCCESS = b'STORED\r\n'
    DELETE_SUCCESS = b'DELETED\r\n'

    END = b'END\r\n'

    def __init__(self, databaseFile):
        """Timeout implementation to limit client connections that are not going to provide input
        Also sets a flag that will be usec to receive data blocks on set commands
        :param databaseFile: full path to a sqlite database file
        :no return:
        """
        self.databaseFile = databaseFile
        self.expectingDataBlock = None
        try:
            loop = asyncio.get_running_loop()
            self.timeout_handle = loop.call_later(self.TIMEOUT, self._timeout)
        except RuntimeError:
            print(self.__class__.__name__, ' is being instantiated without a running event loop')

    def create_sqlite_connection(self):
        """ create a database connection to the SQLite database
            specified by the class's self.databaseFile variable
        :return: Connection object or None
        """
        connection = None
        try:
            connection = sqlite3.connect(self.databaseFile)
        except Error as error:
            print(error)

        return connection

    def connection_made(self, transport):
        """Method called when a client connection is made
        :param transport: object representing the connection to the client
        :no return:
        """
        self.transport = transport
        self.sqliteConnection = self.create_sqlite_connection()

    def connection_lost(self, exc):
        """Method called when connection with client is closed
        :param exc: Python exception or None if connection closed by server
        :no return:
        """
        if exc is not None:
            self.transport.close()

    def data_received(self, data):
        """Method called when data received from client
        :param data: bytestring from client
        :no return:
        """
        self.timeout_handle.cancel()
        self.handleReceivedData(data)

    def handleReceivedData(self, data):
        """Decisioning method for deciphering commands and client errors
        :param data: bytestring of input
        :no return:
        """
        # print(b'received: ' + data)

        if self.expectingDataBlock:
            self.setKeyData(data)
        else:
            commandParams = data.split()
            print(commandParams)
            if len(commandParams) == 0:
                self.transport.write(b'ERROR\r\n')
                return

            if commandParams[0] == b'quit':
                self.transport.close()
            elif commandParams[0] == b'set':
                if len(commandParams) < 5 or len(commandParams) > 6:
                    self.transport.write(self.CLIENT_ERROR_FORMATTING_SET)
                elif len(commandParams) == 6 and commandParams[5] != b'noreply':
                    self.transport.write(self.CLIENT_ERROR_FORMATTING_SET_NOREPLY)
                elif len(commandParams[1]) > 250:
                    self.transport.write(self.CLIENT_ERROR_FORMATTING_SET_KEY_LENGTH_TOO_LONG)
                else:
                    self.expectingDataBlock = commandParams
            elif commandParams[0] == b'get':
                if len(commandParams) < 2:
                    self.transport.write(self.CLIENT_ERROR_FORMATTING_GET)
                else:
                    self.getKeyData(commandParams)
            elif commandParams[0] == b'delete':
                if len(commandParams) < 2 or len(commandParams) > 3:
                    self.transport.write(self.CLIENT_ERROR_FORMATTING_DELETE)
                elif len(commandParams) == 3 and commandParams[2] != b'noreply':
                    self.transport.write(self.CLIENT_ERROR_FORMATTING_DELETE_NOREPLY)
                else:
                    self.deleteKeyData(commandParams)
            else:
                self.transport.write(b'ERROR\r\n')

    def setKeyData(self, dataBlock):
        values = (
                    self.expectingDataBlock[1].decode(),
                    self.expectingDataBlock[2].decode(),
                    self.expectingDataBlock[4].decode(),
                    dataBlock.strip()[:int(self.expectingDataBlock[4].decode())].decode()
                )
        insertOrReplace = """ INSERT OR REPLACE INTO keysTable(key, flags, bytes, dataBlock) VALUES (?, ?, ?, ?) """
        try:
            sqliteCursor = self.sqliteConnection.cursor()
            sqliteCursor.execute(insertOrReplace, values)
            self.sqliteConnection.commit()
            self.transport.write(self.SET_SUCCESS)
        except Exception as error:
            print(error)
            self.transport.write(self.SERVER_ERROR_SET_FAILURE)

        self.expectingDataBlock = None

    def getKeyData(self, commandParams):
        interpolationCount = len(commandParams) - 1
        interpolationString = "?," * (len(commandParams) - 2) + "?"
        selectQuery = """ SELECT * FROM keysTable WHERE key IN ({}) """.format(interpolationString)

        keys = tuple(commandParams[i].decode() for i in range(1, len(commandParams)))
        try:
            sqliteCursor = self.sqliteConnection.cursor()
            sqliteCursor.execute(selectQuery, keys)

            rows = sqliteCursor.fetchall()
            for row in rows:
                self.transport.write(b'VALUE ' + row[0].encode('utf-8') + b' ' + str(row[1]).encode('utf-8') + b' ' + str(row[2]).encode('utf-8') + b'\r\n')
                self.transport.write(row[3].encode('utf-8') + b'\r\n')

            self.transport.write(self.END)
        except Exception as error:
            print(error)
            self.transport.write(self.SERVER_ERROR_GET_FAILURE)


    def deleteKeyData(self, commandParams):
        deleteQuery = """ DELETE FROM keysTable WHERE key=? """

        key = (commandParams[1].decode(),)
        try:
            sqliteCursor = self.sqliteConnection.cursor()
            sqliteCursor.execute(deleteQuery, key)
            self.sqliteConnection.commit()
            print(sqliteCursor.lastrowid)

            self.transport.write(self.DELETE_SUCCESS)
        except Exception as error:
            print(error)
            self.transport.write(self.SERVER_ERROR_DELETE_FAILURE)

    def _timeout(self):
        """Method to close transport connection if timeout condition is met
        """
        self.transport.close()

async def main(host, port):
    """Main method to bind Memcached asyncio.Protocol implementation to asyncio event loop
    """

    parser = argparse.ArgumentParser(description='Start the memcached server')
    parser.add_argument('databaseFile', metavar='databaseFile', type=str,
                        help='the database file for the memcached server')

    args = parser.parse_args()

    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    databaseFile = cwd+'/'+args.databaseFile
    print('memcached: ', databaseFile)

    loop = asyncio.get_running_loop()
    server = await loop.create_server(lambda: MemcachedServer(databaseFile), host, port)
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main('127.0.0.1', 11211))
