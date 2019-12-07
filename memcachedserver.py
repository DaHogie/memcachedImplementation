#!/usr/bin/env python3

# Manage socket connections for telnet to use the memcached server
import socketserver

class MyTCPHandler(socketserver.StreamRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        close = False
        while not close:
            self.data = self.rfile.readline().strip()
            if not self.data:
                # EOF, client closed, just return
                return
            print("{} wrote:".format(self.client_address[0]))
            print(self.data)
            # Likewise, self.wfile is a file-like object used to write back
            # to the client
            self.data += b'\n'
            self.wfile.write(self.data.upper())
            if b'quit' in self.data:
                close = True

if __name__ == "__main__":
    HOST, PORT = "localhost", 11211
    # Create the server, binding to localhost on port 11211
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()
