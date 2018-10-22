import hlt
from hlt import constants

import logging

# Import my stuff
import strategies


game = hlt.Game()
# Pre-processing area
ship_status = {}
ship_destination = {}


class parameters():
    def __init__(self):
        self.max_ships = 10
        self.large_distance_from_drop = 10
        self.minimum_useful_halite = constants.MAX_HALITE/10
        self.sufficient_halite_for_droping = constants.MAX_HALITE/4
        self.density_kernal_side_length = 3

        self.turn_to_stop_spending = 10000
        self.max_dropoffs = 1


params = parameters()

# Start
game.ready("BH4-test")

logging.info("Successfully created bot! Player ID is {}.".format(game.my_id))

# Game Loop
while True:
    strategies.expand(game, ship_status, ship_destination, params)
