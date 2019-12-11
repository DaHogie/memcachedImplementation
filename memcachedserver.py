#!/usr/bin/env python3

# Manage socket connections for telnet to use the memcached server
import asyncio

class MemcachedServer(asyncio.Protocol):
    """Implementation of the Memcached Protocol with Asyncio
    Static variables are for constants
    """
    TIMEOUT = 10 # Seconds
    CLIENT_ERROR_FORMATTING_SET = b'CLIENT_ERROR incorrect # of arguments for set command\r\n'
    CLIENT_ERROR_FORMATTING_GET = b'CLIENT_ERROR incorrect # of arguments for get command\r\n'
    CLIENT_ERROR_FORMATTING_DELETE = b'CLIENT_ERROR incorrect # of arguments for delete command\r\n'

    def __init__(self):
        """Timeout implementation to limit client connections that are not going to provide input
        Also sets a flag that will be usec to receive data blocks on set commands
        """
        self.expectingDataBlock = False
        try:
            loop = asyncio.get_running_loop()
            self.timeout_handle = loop.call_later(self.TIMEOUT, self._timeout)
        except RuntimeError:
            print(self.__class__.__name__, ' is being instantiated without a running event loop')

    def connection_made(self, transport):
        """Method called when a client connection is made
        Arg(s): transport -> transport object representing the connection to the client
        """
        self.transport = transport

    def connection_lost(self, exc):
        """Method called when connection with client is closed
        Arg(s): exc -> Python exception or None if connection closed by server
        """
        if exc is not None:
            self.transport.close()

    def data_received(self, data):
        """Method called when data received from client
        Arg(s): data -> bytestring from client
        No Return
        """
        self.timeout_handle.cancel()
        self.handleReceivedData(data)

    def handleReceivedData(self, data):
        """Decisioning method for deciphering commands and client errors
        Arg(s): data -> bytestring of input
        No return
        """
        print(b'received: ' + data)
        commandParams = data.split()
        print(commandParams)

        if len(commandParams) == 0:
            return

        if commandParams[0] == b'quit':
            self.transport.close()
        elif commandParams[0] == b'set':
            if len(commandParams) < 5 or len(commandParams) > 6:
                # TODO: write to client instead of returning
                return self.CLIENT_ERROR_FORMATTING_SET
            self.expectingDataBlock = True
        elif commandParams[0] == b'get':
            if len(commandParams) < 2:
                # TODO: write to client instead of returning
                return self.CLIENT_ERROR_FORMATTING_GET
        elif commandParams[0] == b'delete':
            if len(commandParams) < 2 or len(commandParams) > 3:
                # TODO: write to client instead of returning
                return self.CLIENT_ERROR_FORMATTING_DELETE
        else:
            # TODO: write to client instead of returning
            return b'ERROR\r\n'

    def _timeout(self):
        """Method to close transport connection if timeout condition is met
        """
        self.transport.close()

async def main(host, port):
    """Main method to bind Memcached asyncio.Protocol implementation to asyncio event loop
    """
    loop = asyncio.get_running_loop()
    server = await loop.create_server(MemcachedServer, host, port)
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main('127.0.0.1', 11211))
