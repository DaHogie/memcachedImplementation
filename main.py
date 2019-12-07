#!/usr/bin/env python3

# Running both servers in the same process
import subprocess

# Handle the task of getting the absolute path for the subprocesses
import glob
import os.path


if __name__ == '__main__':
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__)))

    try:
        subprocess.Popen(('python3',
            'frontendserver.py'), cwd=cwd)
    except IndexError:
        print('Cannot find frontendserver.py')
        sys.exit(1)

    try:
        subprocess.Popen(('python3',
            'memcachedserver.py'), cwd=cwd)
    except IndexError:
        print('Cannot find memcachedserver.py')
        sys.exit(1)


    try:
        while True:
            pass
    except KeyboardInterrupt:
        print('All servers terminated')
