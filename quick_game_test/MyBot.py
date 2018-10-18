import hlt
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction

import random
import logging

game = hlt.Game()

# Pre-processing area
ship_status = {}


game.ready("BH4-test")

logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

# Game Loop
while True:
    game.update_frame()

    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn.
    command_queue = []

    for ship in me.get_ships():
        logging.info("Ship {} has {} halite.".format(ship.id, ship.halite_amount))

        if ship.id not in ship_status:
            ship_status[ship.id] = "exploring"

        if ship_status[ship.id] == "returning":
            if ship.position == me.shipyard.position:
                ship_status[ship.id] = "exploring"
            else:
                closest = me.shipyard.position
                dist = game_map.calculate_distance(ship.position, me.shipyard.position)
                for drop in me.get_dropoffs():
                    dist_temp = game_map.calculate_distance(ship.position, drop.position)
                    if dist_temp < dist:
                        dist = dist_temp
                        closest = drop.position

                if dist > 7 and len(me.get_ships()) > 1 and me.halite_amount > 4000:
                    command_queue.append(ship.make_dropoff())
                else:
                    move = game_map.naive_navigate(ship, closest)
                    command_queue.append(ship.move(move))
                continue
        elif ship.halite_amount >= constants.MAX_HALITE / 4:
            ship_status[ship.id] = "returning"


        if game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 or ship.is_full:
            command_queue.append(
                ship.move(random.choice([Direction.North, Direction.South, Direction.East, Direction.West])))
        else:
            command_queue.append(ship.stay_still())

    # If you're on the first turn and have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though.
    if game.turn_number <= 300 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(game.me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
