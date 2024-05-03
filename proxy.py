import signal
import socket
import threading
import fnmatch
from time import strftime, localtime
import sys
from fuzzywuzzy import process 
from config import config


class Server:
    def __init__(self, config):
        # Shutdown on Ctrl+C
        signal.signal(signal.SIGINT, self.shutdown)

        # Create a TCP socket
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Re-use the socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # bind the socket to a public host, and a port
        self.serverSocket.bind((config["HOST_NAME"], config["BIND_PORT"]))

        self.serverSocket.listen(10)  # become a server socket
        self.__clients = {}

    def listen(self):
        while True:
            # Establish the connection
            (clientSocket, client_address) = self.serverSocket.accept()

            d = threading.Thread(
                name=self._getClientName(client_address),
                target=self.proxy_thread,
                args=(clientSocket, client_address),
            )
            d.setDaemon(True)
            d.start()

    # Get the client name
    def _getClientName(self, client_address):
        return client_address

    # Proxy thread
    def proxy_thread(self, conn, client_addr):
        request = conn.recv(config["MAX_REQUEST_LEN"])
        first_line = request.decode().split("\n")[0]
        url = first_line.split(" ")[1]
        method = first_line.split(" ")[0]

        # Check if the host:port is blacklisted
        for i in range(0, len(config["BLACKLIST_DOMAINS"])):
            if config["BLACKLIST_DOMAINS"][i] in url:
                print("Blacklisted domain, Not allowed to access...", url)
                conn.close()
                return

        # Check if host is allowed to access the content
        if not self._ishostAllowed(url):
            print("Site access denied by proxy...", url)
            conn.close()
            return

        if self._isBlacklistedFuzzy(url):  # Check the URL
            print("Blacklisted content (fuzzy match), access denied ...", url)
            conn.close()
            return
        
        if method not in config["ALLOWED_METHODS"]:
            print(f"Method {method} not allowed...")
            conn.close()
            return
        print (f"Connecting to: {url} using {method} method")
        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3) :]

        port_pos = temp.find(":")
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)
        webserver = ""
        port = -1
        if port_pos == -1 or webserver_pos < port_pos:
            port = 80
            webserver = temp[:webserver_pos]
        else:
            port = int((temp[(port_pos + 1) :])[: webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((webserver, port))
            s.send(request)

            while 1:
                data = s.recv(config["MAX_REQUEST_LEN"])
                if len(data) > 0:
                    conn.send(data)
                else:
                    break
            s.close()
            conn.close()
        except socket.error as error_msg:
            print("ERROR: ", client_addr, error_msg)
            if s:
                s.close()
            if conn:
                conn.close()

        # TODO: Add the rest of the code from the tutorials here...

    def _ishostAllowed(self, host):
        """Check if host is allowed to access the content"""
        for wildcard in config["HOST_ALLOWED"]:
            if fnmatch.fnmatch(host, wildcard):
                return True
        return False

    def _isBlacklistedFuzzy(self, text):
        """Checks if 'text' contains fuzzy matches for blacklisted words"""
        for bad_word in config["BLACKLIST_WORDS"]:
            matches = process.extract(bad_word, text, limit=1, scorer=config['FUZZY_SCORER'])
            if matches and matches[0][1] >= config["FUZZY_THRESHOLD"]:
                return True
        return False
    
    def shutdown(self, signum, frame):
        """Handle the exiting server. Clean all traces"""
        main_thread = threading.currentThread()  # Wait for all clients to exit
        for t in threading.enumerate():
            if t is main_thread:
                continue
            t.join()
        try:
            if self.serverSocket:
                self.serverSocket.close()
        except socket.error as e:
            print(f"Error closing socket: {e}")
        sys.exit(0)


def main():
    print("Starting proxy server...")
    server = Server(config)
    print("Server started...")
    print(f"Listening on - {config['HOST_NAME']}:{config['BIND_PORT']}")
    server.listen()


if __name__ == "__main__":
    main()
