#!/usr/bin/env python3

# Manage socket connections for telnet to use the memcached server
import asyncio

async def handleCommand(reader, writer):
    while True:
        try:
            data = await reader.readline()
            print("received: ", data)
            if b'quit' in data:
                break
            writer.write(data + b'\r\n')
            await writer.drain()
        except:
            print('Client closed connection without sending \'quit\' command')
            break


    writer.close()

async def main():
    server = await asyncio.start_server(
    handleCommand, '127.0.0.1', 11211)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
