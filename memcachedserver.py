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

    def __init__(self):
        """Timeout implementation to limit client connections that are not going to provide input
        Also sets a flag that will be usec to receive data blocks on set commands
        """
        self.expectingDataBlock = None
        try:
            loop = asyncio.get_running_loop()
            self.timeout_handle = loop.call_later(self.TIMEOUT, self._timeout)
        except RuntimeError:
            print(self.__class__.__name__, ' is being instantiated without a running event loop')

    def connection_made(self, transport):
        """Method called when a client connection is made
        :param transport: object representing the connection to the client
        :no return:
        """
        self.transport = transport

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
            # print(commandParams)
            if len(commandParams) == 0:
                self.transport.write(b'ERROR\r\n')

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
        pass

    def getKeyData(self, commandParams):
        pass

    def deleteKeyData(self, commandParams):
        pass

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
