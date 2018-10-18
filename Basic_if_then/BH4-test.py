import hlt
from hlt import constants

from hlt.positionals import Direction, Position

import random
import logging

move_cost_fraction = .1


def random_move(ship, game_map, occupied):
    curr_pos = ship.position

    move_cost = move_cost_fraction*game_map[curr_pos].halite_amount

    move = Direction.Still
    new_pos = curr_pos
    if ship.halite_amount >= move_cost:
        allowed = Direction.get_all_cardinals()
        move = random.choice(allowed)
        new_pos = curr_pos+Position(move[0], move[1])

        while new_pos in occupied and len(allowed) > 0:
            allowed.remove(move)

            if len(allowed) > 0:
                move = random.choice(allowed)
                new_pos = curr_pos+Position(move[0], move[1])
            else:
                move = (0, 0)
                new_pos = curr_pos

    occupied.append(new_pos)
    return move, occupied


def returning_move(ship, game_map, occupied):
    curr_pos = ship.position

    move_cost = move_cost_fraction*game_map[curr_pos].halite_amount

    move = Direction.Still
    new_pos = curr_pos
    if ship.halite_amount >= move_cost:
        move = game_map.naive_navigate(ship, closest)
        new_pos = curr_pos+Position(move[0], move[1])

        if new_pos in occupied:
            move = Direction.Still
            new_pos = curr_pos

    occupied.append(new_pos)
    return move, occupied


def closest_drop(ship, me, game_map):
    closest = me.shipyard.position
    dist = game_map.calculate_distance(ship.position, me.shipyard.position)
    for drop in me.get_dropoffs():
        dist_temp = game_map.calculate_distance(ship.position, drop.position)
        if dist_temp < dist:
            dist = dist_temp
            closest = drop.position

    return closest, dist


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
    occupied = [x.position for x in me.get_ships()]

    for ship in me.get_ships():
        # Mark status
        if ship.id not in ship_status:
            ship_status[ship.id] = "exploring"

        if ship_status[ship.id] == "returning" and ship.position == me.shipyard.position:
            ship_status[ship.id] = "exploring"
        elif ship.halite_amount >= constants.MAX_HALITE/4:
            ship_status[ship.id] = "returning"

        # Take action
        if ship_status[ship.id] == "returning":
            closest, dist = closest_drop(ship, me, game_map)

            if dist > 7 and len(me.get_ships()) > 1 and me.halite_amount > constants.DROPOFF_COST:
                command_queue.append(ship.make_dropoff())

                logging.info("Ship {} decided to make a dropoff.".format(ship.id))
            else:
                move, occupied = returning_move(ship, game_map, occupied)
                command_queue.append(ship.move(move))

                logging.info("Ship {} is returning by moving {}.".format(ship.id, move))
        elif ship_status[ship.id] == "exploring":
            if game_map[ship.position].halite_amount < constants.MAX_HALITE/10:
                move, occupied = random_move(ship, game_map, occupied)
                command_queue.append(ship.move(move))

                logging.info("Ship {} is exploring by moving {}.".format(ship.id, move))
            else:
                occupied.append(ship.position)
                command_queue.append(ship.stay_still())

                logging.info("Ship {} is collecting by staying still.".format(ship.id))

    # If you're on the first turn and have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though.
    if ((game.turn_number <= 300 and me.halite_amount >= constants.SHIP_COST
         and me.shipyard.position not in occupied and
         (len(me.get_ships()) < 4 or
          me.halite_amount > constants.DROPOFF_COST+constants.SHIP_COST))):

        command_queue.append(game.me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
