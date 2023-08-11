import os
import random
import sys
from enum import Enum
from dataclasses import dataclass
from typing import Optional

from simple_http_server import BaseRequestHandler, start_server, urlparse, parse_qs


IS_PYTHONISTA = "Pythonista3" in os.getenv("HOME", "")

if IS_PYTHONISTA:
    import dialogs

NUM_PLAYERS = 0
REMAINING_ROLES = []
IP_ROLES = {}
KNOWN_FASCISTS = []


class Role(Enum):
    FASCIST = "Fascist"
    LIBERAL = "Liberal"
    HITLER = "Hitler"


@dataclass
class UserRoleMapping:
    ROLE_PARTY = {
        Role.LIBERAL: Role.LIBERAL,
        Role.FASCIST: Role.FASCIST,
        Role.HITLER: Role.FASCIST,
    }
    role: Role
    party: Role
    name: Optional[str]

    def __init__(self, role):
        self.role = role
        self.party = self.ROLE_PARTY[role]
        self.name = None

    def get_player_name(self, is_current_player):
        if self.name is None:
            return "Unknown (refresh later to see this change)"
        elif is_current_player:
            return f"{self.name} (you)"
        else:
            return self.name


def get_role_counts(num_players):
    num_liberals = num_players // 2 + 1
    num_fascists = num_players - num_liberals - 1
    return {
        Role.LIBERAL: num_liberals,
        Role.FASCIST: num_fascists,
        Role.HITLER: 1,
    }


def does_hitler_know_fascists(NUM_PLAYERS):
    return NUM_PLAYERS <= 6


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
    def create_role_card(player):
        role_div = '''
                <button onClick="showDiv('roleDiv')">
                    Click to toggle role <span style="color: red">(do not show anyone else this)</span>
                </button>
                <div id="roleDiv" style="display: none">
        '''
        role_line = f"<p>Your role is {player.role.name}</p>"
        if player.party == Role.FASCIST and (does_hitler_know_fascists(NUM_PLAYERS) or player.role != Role.HITLER):
            fascists = [
                fascist.get_player_name(fascist == player)
                for fascist in KNOWN_FASCISTS
            ]
            print(fascists)
            fascist_players = f"<p>The other fascists are: {', '.join(fascists)}</p>"
        else:
            fascist_players = ""
        role_div_close = "</div>"
        return role_div + role_line + fascist_players + role_div_close

    @staticmethod
    def create_envelope_response(player, insert_post_request):
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
                    p, label, h1 {
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
        '''
        player_name = f"<h1>Hello! {player.name}, we're still waiting on {len(REMAINING_ROLES)} players</h1>"
        post_request = '''
                <form method="GET" action="/?sendName">
                    <label for="nameInput">What's your name? (make it identifiable)</label>
                    <input id="nameInput" name="playerName" placeholder="..." />
                    <button type="submit">Send</button>
                </form>
        '''
        role_card = RequestHandler.create_role_card(player)
        infix = '''
            <button onClick="showDiv('partyDiv')">
                Click to toggle party <span style="color: green">(show this if you're being investigated)</span>
                </button>
                <div id="partyDiv" style="display: none">
                '''
        party_line = f"<p>Your party is {player.party.name}</p>"
        postfix = '''
                </div>
            </body>
        </html>
        '''
        response = prefix
        if player.name is not None:
            response += player_name
        if insert_post_request:
            response += post_request
        response += role_card + infix + party_line + postfix
        return response

    def get_message(self, body):
        url = urlparse(self.path)
        query = parse_qs(url.query) if url.query is not None else {}
        player_name = query.get("playerName")
        client_address = self.client_address[0]
        if client_address in IP_ROLES:
            print("Found existing IP")
            player = IP_ROLES[client_address]
            if player.name is None and player_name:
                player.name = player_name[0]
            needs_to_get_name = player.name is None
        else:
            print("Found new IP")
            player = UserRoleMapping(REMAINING_ROLES.pop())
            IP_ROLES[client_address] = player
            if player.party == Role.FASCIST:
                KNOWN_FASCISTS.append(player)
            if player_name:
                player.name = player_name[0]

            needs_to_get_name = player.name is None

        response = self.create_envelope_response(
            player, needs_to_get_name
        )
        return response


def main():
    global NUM_PLAYERS
    NUM_PLAYERS = get_num_players()
    create_roles()
    start_server(RequestHandler)

    print(IP_ROLES)


if __name__ == "__main__":
    main()
