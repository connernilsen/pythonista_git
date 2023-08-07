import os
import random
import sys
from enum import Enum

from simple_http_server import BaseRequestHandler, start_server


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

class RequestHandler(BaseRequestHandler):
    @staticmethod
    def create_envelope_response(role, party):
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

    def get_message(self):
        client_address = self.client_address[0]
        if client_address in IP_ROLES:
            print("Found existing IP")
            role = IP_ROLES[client_address]
        else:
            print("Found new IP")
            role = REMAINING_ROLES.pop()
            IP_ROLES[client_address] = role

        return self.create_envelope_response(role, ROLE_PARTY[role])


def main():
    global NUM_PLAYERS
    NUM_PLAYERS = get_num_players()
    create_roles()
    start_server(RequestHandler)

    print(IP_ROLES)

if __name__ == '__main__':
    main()
