import hlt
from hlt import constants

import logging

# Import my stuff
import strategies
import helpers


game = hlt.Game()
# Pre-processing area
ship_status = {}
ship_destination = {}


class parameters():
    def __init__(self):
        # Ship numbers
        self.max_ships = 30
        self.min_ships = 2

        # dropoff parameters
        self.large_distance_from_drop = 10
        self.farthest_allowed_dropoff = game.game_map.width/2
        self.dropoff_dense_requirement = constants.DROPOFF_COST

        self.minimum_useful_halite = constants.MAX_HALITE/10
        self.sufficient_halite_for_droping = constants.MAX_HALITE
        self.density_kernal_side_length = 3
        self.search_region = 1
        self.number_of_dense_spots_to_check = 10

        self.explore_dense_requirement = self.minimum_useful_halite*self.density_kernal_side_length**2

        self.turn_to_stop_spending = 300
        self.max_dropoffs = 1


params = parameters()

# Start
game.ready("BH4-test")

logging.info("Successfully created bot! Player ID is {}.".format(game.my_id))

# Game Loop
while True:
    hd = helpers.halite_density(game.game_map, params)

    m = max([max(x) for x in hd])
    # m <= constants.MAX_HALITE*params.density_kernal_side_length**2

    if m > 0*params.explore_dense_requirement:
        strategies.expand(game, ship_status, ship_destination, params)
    else:
        logging.info("Started vacuum")
        strategies.vacuum(game, ship_status, ship_destination, params)
