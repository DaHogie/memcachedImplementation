#!/usr/bin/env python3

# Manage socket connections for telnet to use the memcached server
import asyncio

class MemcachedServer(asyncio.Protocol):

    TIMEOUT = 10 # Seconds

    def __init__(self):
        loop = asyncio.get_running_loop()
        self.timeout_handle = loop.call_later(self.TIMEOUT, self._timeout)

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self.timeout_handle.cancel()
        self.data = data
        self.parseReceivedData()
        self.transport.write(data)

    def parseReceivedData(self):
        print(b'received: ' + self.data)

    def _timeout(self):
        self.transport.close()

async def main(host, port):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(MemcachedServer, host, port)
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main('127.0.0.1', 11211))
