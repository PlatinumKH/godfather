import typing
import re
from .player import Player
from godfather.factions import factions
from godfather.roles import all_roles
from godfather.utils import get_random_sequence

class Setup:
    # Regex patterns are static members because
    # they're the same for all instances.

    # pattern to find out setup metadata (name and total players)
    meta_pattern = re.compile(r'^([a-zA-z]+?)\s*:\s*(\d+?)\s*\.\s*')
    # pattern to find data about each role
    role_pattern = re.compile(r'\(\s*([\S][^,]+?)\s*,\s*([\S][^,]+?)\s*,\s*(\d+?)\s*\)\s*(?:,\s*|$)')

    @staticmethod
    def read_setups(setupfile_path: str):
        """Static method to read a list of setups from a file"""
        with open(setupfile_path) as setupfile:
            return {setup.name: setup for setup in
                    map(Setup, [line.strip() for line in setupfile])}

    def __init__(self, setup_str: str):
        # Example setup:
        # dethysucks: 5. (town, vanilla, 3), (town, doctor, 1), (mafia, goon, 1)

        self.name: str
        self.total_players: int
        self.roles: typing.List[typing.Tuple[str, str]] = []

        # Get setup metadata
        setup_meta = Setup.meta_pattern.match(setup_str)

        if not setup_meta:
            raise ValueError("Invalid setup string!")

        self.name = setup_meta.group(1)
        self.total_players = int(setup_meta.group(2))

        # Get setup roles
        setup_roles = Setup.role_pattern.findall(setup_str)

        if not setup_roles:
            raise ValueError("Invalid setup string!")

        for role_match in setup_roles:
            role_faction = role_match[0]
            role_name = role_match[1]
            role_num = int(role_match[2])

            self.roles.extend([(role_faction, role_name)] * role_num)

        # Remove all matches from the string and check if
        # the resulting string is empty or not. If not,
        # it means there are extraneous unmatched characters which indicate
        # a possible setup syntax error

        # First filter out the metadata, then the roles, using a nested regex substitution
        unmatched_str = Setup.role_pattern.sub('', Setup.meta_pattern.sub('', setup_str))

        # If resulting string is not empty, raise an error
        if unmatched_str != "":
            raise ValueError(f"Unmatched characters: '{unmatched_str}' while "
                             "trying to parse the setup")

        if len(self.roles) != self.total_players:
            raise ValueError("Supplied and actual number of players do not match!")

    def assign_roles(self, players: typing.List[Player]):
        """Take a list of player objects and assign roles to them"""

        # order is the numbered order of the current loop
        # index is the current random index from the random sequence
        for order, index in enumerate(get_random_sequence(0, len(self.roles)-1)):
            players[order].faction = factions.get(self.roles[index][0])
            players[order].role = all_roles.get(self.roles[index][1])
