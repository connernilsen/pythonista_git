import os
import random
import socket
import sys
from http import server
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, TimeoutError

IS_PYTHONISTA = "Pythonista3" in os.getenv("HOME", "")

if IS_PYTHONISTA:
    import dialogs

NUM_PLAYERS = 0
REMAINING_ROLES = []
IP_ROLES = {}

class Role(Enum):
    FASCIST = 'Fascist'
    LIBERAL = 'Liberal'
    HITLER = 'Hitler'


ROLE_PARTY = {
    Role.LIBERAL: Role.LIBERAL,
    Role.FASCIST: Role.FASCIST,
    Role.HITLER: Role.FASCIST,
}


def get_role_counts(num_players):
    num_liberals = num_players // 2 + 1
    num_fascists = num_players - num_liberals - 1
    return {
        Role.LIBERAL: num_liberals,
        Role.FASCIST: num_fascists,
        Role.HITLER: 1,
    }

def get_num_players():
    if IS_PYTHONISTA:
        return dialogs.list_dialog("Number of Players", range(5, 11))
    else:
        args = sys.argv
        if len(args) != 2:
            raise ValueError("Expected number of players as argument to script")
        if not args[1].isnumeric():
            raise ValueError("Expected number of players to be a number")
        num_players = int(args[1])
        if not (5 <= num_players <= 10):
            raise ValueError("Number of players must be between 5 and 10")
        return num_players

def create_roles():
    global REMAINING_ROLES, NUM_PLAYERS
    roles = get_role_counts(NUM_PLAYERS)
    REMAINING_ROLES += [Role.LIBERAL] * roles[Role.LIBERAL]
    REMAINING_ROLES += [Role.FASCIST] * roles[Role.FASCIST]
    REMAINING_ROLES += [Role.HITLER]

    random.shuffle(REMAINING_ROLES)

class RequestHandler(server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    @staticmethod
    def _create_response(role, party):
        prefix = '''
        <html>
            <head>
                <style>
                    body {
                        background-color: black
                    }
                    div {
                        padding: 20px;
                        display: none;
                    }
                    button {
                        margin: 50px;
                    }
                    p {
                        padding: 50px;
                        color: white;
                    }
                </style>
                <script>
                function showDiv(divName) {
                  var x = document.getElementById(divName);
                  if (x.style.display === "none") {
                    x.style.display = "block";
                  } else {
                    x.style.display = "none";
                  }
                }
                </script>
            </head>
            <body>
                <button onClick="showDiv('roleDiv')">
                    Click to toggle role <span style="color: red">(do not show anyone else this)</span>
                </button>
                <div id="roleDiv">
        '''
        role_line = f"<p>Your role is {role.name}</p>"
        infix = '''
                </div>
                <button onClick="showDiv('partyDiv')">
                Click to toggle party <span style="color: green">(show this if you're being investigated)</span>
                </button>
                <div id="partyDiv">
                '''
        party_line = f"<p>Your party is {party.name}</p>"
        postfix = '''
                </div>
            </body>
        </html>
        '''
        return prefix + role_line + infix + party_line + postfix

    def _send_response(self, role, party):
        response = self._create_response(role, party)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(bytes(response, "utf-8"))

    def do_GET(self):
        client_address = self.client_address[0]
        if client_address in IP_ROLES:
            print("Found existing IP")
            role = IP_ROLES[client_address]
            party = ROLE_PARTY[role]
            self._send_response(role, party)
            return

        print("Found new IP")
        role = REMAINING_ROLES.pop()
        party = ROLE_PARTY[role]
        IP_ROLES[client_address] = role
        print(self.client_address)
        self._send_response(role, party)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def start_server(http_server, ip):
    RequestHandler.server_version = "HTTP/1.1"
    RequestHandler.close_connection = True
    print(f'Server started @ {ip}')
    try:
        http_server.serve_forever()
    except:
        http_server.server_close()
        print("shut down server")

def main():
    global NUM_PLAYERS
    NUM_PLAYERS = get_num_players()
    create_roles()
    ip = get_local_ip()
    port = 80
    
    with server.HTTPServer(('', port), RequestHandler) as http_server:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(start_server, http_server, ip)
            try:
                future.result(timeout=60 * 3) # run for 3 min max
            except TimeoutError:
                print("Stopping server from timeout")
                http_server.shutdown()

    print(IP_ROLES)

if __name__ == '__main__':
    main()
