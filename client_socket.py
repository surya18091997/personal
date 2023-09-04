import sys
from socket import *

import httplib2

try:
    sock = socket(AF_INET, SOCK_STREAM)
    print(sock)
    print("created")
except error as err:
    print(err)
    sys.exit()

try:
    sock.connect(("url", 80))
    print("connected")

    sock.shutdown(2)
except error as err:
    print(err)
    sock.close()
