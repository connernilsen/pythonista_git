import os
import random
import sys
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List
from collections import defaultdict

from simple_http_server import BaseRequestHandler, start_server, urlparse, parse_qs


class Role(ABC):
    @abstractmethod
    def get_role_name(self) -> str:
        ...


@dataclass
class PlayerRoleMapping:
    role: Role
    name: Optional[str]

    def __init__(self, role):
        self.role = role
        self.name = None

    def get_player_name(self, is_current_player):
        if self.name is None:
            return "Unknown (refresh later to see this change)"
        elif is_current_player:
            return f"{self.name} (you)"
        else:
            return self.name


class RequestHandler(BaseRequestHandler):
    role_server = None

    def create_role_card(self, player):
        role_div = """
                <button onClick="showDiv('roleDiv')">
                    Click to toggle role <span style="color: red">(do not show anyone else this)</span>
                </button>
                <div id="roleDiv" style="display: none">
        """
        role_line = f"<p>Your role is {player.role.get_role_name()}</p>"
        visible_roles = self.role_server.get_visible_roles(player)
        visible_players = f"<p>The other players you're allowed to see are: {', '.join(visible_roles)}</p>"
        role_div_close = "</div>"
        return role_div + role_line + visible_players + role_div_close

    def create_envelope_response(self, player, insert_post_request):
        prefix = """
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
        """
        player_name = f"<h1>Hello! {player.name}, we're still waiting on {len(self.role_server.remaining_roles)} players</h1>"
        post_request = """
                <form method="GET" action="/?sendName">
                    <label for="nameInput">What's your name? (make it identifiable)</label>
                    <input id="nameInput" name="playerName" placeholder="..." />
                    <button type="submit">Send</button>
                </form>
        """
        role_card = self.create_role_card(player)
        game_specific_information = (
            self.role_server.role_configuration.show_game_specific_information(player)
        )
        postfix = """
            </body>
        </html>
        """
        response = prefix
        if player.name is not None:
            response += player_name
        if insert_post_request:
            response += post_request
        response += role_card + game_specific_information + postfix
        return response

    def get_message(self, body):
        url = urlparse(self.path)
        query = parse_qs(url.query) if url.query is not None else {}
        player_name = query.get("playerName")
        client_address = self.client_address[0]

        if client_address in self.role_server.ip_roles:
            print("Found existing IP")
            player = self.role_server.ip_roles[client_address]
            if player.name is None and player_name:
                player.name = player_name[0]
            needs_to_get_name = player.name is None
        else:
            print("Found new IP")
            player = PlayerRoleMapping(self.role_server.remaining_roles.pop())
            self.role_server.ip_roles[client_address] = player
            self.role_server.role_mappings[player.role].append(player)
            if player_name:
                player.name = player_name[0]

            needs_to_get_name = player.name is None

        response = self.create_envelope_response(player, needs_to_get_name)
        return response


class RoleConfiguration(ABC):
    @abstractmethod
    def get_num_players(self, is_pythonista: bool) -> int:
        ...

    @abstractmethod
    def get_role_ratios(self, num_players) -> Dict[Role, int]:
        ...

    @abstractmethod
    def get_visible_roles(
        self, player: PlayerRoleMapping, role_mappings: Dict[PlayerRoleMapping, Role]
    ) -> List[str]:
        ...

    @abstractmethod
    def show_game_specific_information(self, player: PlayerRoleMapping) -> str:
        ...


class RoleServer:
    role_server = None
    role_configuration = None
    num_players = 0
    remaining_roles = []
    ip_roles = {}
    role_mappings = defaultdict(list)

    def __new__(cls, *args, **kwargs):
        if cls.role_server is not None:
            raise Exception("Server already exists")
        return super(RoleServer, cls).__new__(cls)

    def __init__(self, role_configuration: RoleConfiguration):
        self.role_configuration = role_configuration
        is_pythonista = "Pythonista3" in os.getenv("HOME", "")
        self.num_players = role_configuration.get_num_players(is_pythonista)

    def create_roles(self):
        role_ratios = self.role_configuration.get_role_ratios(self.num_players)
        self.remaining_roles = [
            key for key, value in role_ratios.items() for _ in range(value)
        ]
        random.shuffle(self.remaining_roles)

    def get_visible_roles(self, player):
        return self.role_configuration.get_visible_roles(
            player, self.role_mappings, self.num_players
        )

    def run_server(self, port=80):
        self.create_roles()
        RequestHandler.role_server = self
        start_server(RequestHandler)
        print(ip_roles)
        self.__class__.role_server = None
