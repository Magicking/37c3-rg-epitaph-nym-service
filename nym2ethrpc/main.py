import utils
from serve import Serve
import time

if __name__ == '__main__':

    # wait for nym-cloent to start, init and start the backend server
    time.sleep(1)
    serveClient = Serve()
