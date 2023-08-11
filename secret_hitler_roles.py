import random
import sys
from enum import Enum

from role_server import RoleConfiguration, RoleServer


class PlayerRole(Enum):
    FASCIST = "Fascist"
    LIBERAL = "Liberal"
    HITLER = "Hitler"

    def get_team_name(self):
        if self == PlayerRole.LIBERAL:
            return "Liberal"
        else:
            return "Fascist"

    def get_role_name(self):
        return self.name


class SecretHitlerRoleConfiguration:
    def does_hitler_know_fascists(NUM_PLAYERS):
        return NUM_PLAYERS <= 6

    def get_num_players(self, is_pythonista: bool) -> int:
        if is_pythonista:
            import dialogs

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

    def get_role_ratios(self, num_players):
        num_liberals = num_players // 2 + 1
        num_fascists = num_players - num_liberals - 1
        return {
            PlayerRole.LIBERAL: num_liberals,
            PlayerRole.FASCIST: num_fascists,
            PlayerRole.HITLER: 1,
        }

    def get_visible_roles(self, player, role_mappings, num_players):
        if player.role == PlayerRole.LIBERAL:
            return []
        elif player.role == PlayerRole.FASCIST:
            hitler = ""
            if role_mappings[PlayerRole.HITLER]:
                hitler = role_mappings[PlayerRole.HITLER][0].name + " (Hitler)"
            else:
                hitler = "(hitler, not yet assigned)"
            return [hitler] + [
                fascist.name
                for fascist in role_mappings[PlayerRole.FASCIST]
                if fascist != player
            ]
        else:
            if self.does_hitler_know_fascists(num_players):
                return [fascist.name for fascist in role_mappings[PlayreRole.FASCIST]]
            else:
                return ["You are Hitler, you don't get to know anyone"]

    def show_game_specific_information(self, player):
        prefix = """
            <button onClick="showDiv('partyDiv')">
                Click to toggle party <span style="color: green">(show this if you're being investigated)</span>
                </button>
                <div id="partyDiv" style="display: none">
                """
        party_line = f"<p>Your party is {player.role.get_team_name()}</p>"
        postfix = "</div>"
        return prefix + party_line + postfix


def main():
    role_server = RoleServer(SecretHitlerRoleConfiguration())
    role_server.run_server()


if __name__ == "__main__":
    main()
