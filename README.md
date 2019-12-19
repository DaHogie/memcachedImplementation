# Memcached Protocol Implementation

This is a simple implementation of the [memcached protocol](https://github.com/memcached/memcached/blob/master/doc/protocol.txt).
The `main.py` file takes in a required argument that is the name of a sqlite file in the same directory.
It will then start two subprocesses that run the memcached server on port 11211 and the monitoring UI server on port 8000.
The memcached server was implemented with the asyncio library; specifically with a child object of the asyncio.Protocol object.
The front end server was implemented with Flask, HTML5, CSS (Grid and Flexbox), and React.

## Dependencies Required

1. Python3 will need to be installed on your machine.
2. Flask will need to be installed with pip3 to run the front end server.
3. CSS Grid is used on the UI so if you're viewing the site with Chrome you'll need to enable the `Experimental Web Platform Features` flag. See [Browser Support](https://www.lambdatest.com/css-grid-layout) for more info.

## Start Command

Navigate to the root of the repository and run `python main.py database.sqlite`.
There are python3 shebang lines in all of the `.py` scripts to ensure the
python3 interpreter is chosen if possible.

## Commands Implemented

Implemented `set`, `get`, and `delete` from the Memcached Protocol.
View the [Memcached Protocol Reference](https://github.com/memcached/memcached/blob/master/doc/protocol.txt) for more info.

### Special Notes

The `<exptime>` flag on the set command is a mandatory argument to the command,
but it is ignored on the server side. None of the stored values will expire.

There were some ambiguous areas in the protocol reference for the `set` command.
In this implementation the data block cannot contain a `\r` and `\n` together.
If `\r\n` is found in the data block the memcached server treats it as the end of the entry
and will throw a *CLIENT_ERROR* if the number of bytes not including the `\r\n` differs
from the value found in the `<bytes>` flag of the set command prior.

Additionally the values for the `<flags> <exptime> <bytes>` must only be digits.
Otherwise the memcached protocol will throw a *CLIENT_ERROR*.

### Memcached Server Testing

You can test the memcached server by connecting to it with telnet.
If no commands are received within the first minute of the initial connection the server will
timeout the client and disconnect.
