import hlt
from hlt import constants

from hlt.positionals import Direction, Position

import numpy as np
import random
import logging


###############################################################################
# Helper functions
###############################################################################
def toroidal_value_sum(matrix, square_side_length):
    w = len(matrix)
    h = len(matrix[0])

    s = square_side_length//2
    """Convolution on a torus"""
    values = []
    for j in range(h):
        row = []
        col_sums = []
        for i in range(w):
            curr = 0
            if len(col_sums) == 0:
                for ii in range(-s, s+1):
                    cs = 0
                    for jj in range(-s, s+1):
                        cs += matrix[(i+ii) % w][(j+jj) % h]
                    curr += cs
                    col_sums.append(cs)
            else:
                v = col_sums.pop(0)
                curr = row[-1]-v
                ii = s
                cs = 0
                for jj in range(-s, s+1):
                    cs += matrix[(i+ii) % w][(j+jj) % h]
                curr += cs
                col_sums.append(cs)

            row.append(curr)
        values.append(row)
    return np.array(values)


stored_density = None
def halite_density(game_map):
    global stored_density

    if stored_density is not None:
        return stored_density

    all_halite = []
    for i in range(game_map.width):
        col = []
        for j in range(game_map.height):
            col.append(game_map[Position(i, j)].halite_amount)

        all_halite.append(col)

    stored_density = toroidal_value_sum(all_halite, density_kernal_side_length)
    return stored_density


def closest_dense_spot(ship, game_map, n=3):
    """From the n most dense regions choose closest"""
    density = halite_density(game_map)
    ind = []
    dval = []
    for i in range(len(density)):
        for j in range(len(density[0])):
            ind.append((i, j))
            dval.append(density[i][j])

    dval, ind = list(zip(*sorted(zip(dval, ind), reverse=True)))

    pos = [Position(x[0], x[1]) for x in ind[:n]]
    dist = [game_map.calculate_distance(ship.position, x) for x in pos]
    dist, pos = list(zip(*sorted(zip(dist, pos), key=lambda x: x[0])))

    return pos[0], dist[0]


def closest_drop(ship, me, game_map):
    closest = me.shipyard.position
    dist = game_map.calculate_distance(ship.position, me.shipyard.position)
    for drop in me.get_dropoffs():
        dist_temp = game_map.calculate_distance(ship.position, drop.position)
        if dist_temp < dist:
            dist = dist_temp
            closest = drop.position

    return closest, dist


def get_safe_spaces_in_region(ship, game_map, search_region=1):
    curr_pos = ship.position

    safe_spaces = []
    for i in range(-1*search_region, search_region+1):
        for j in range(-1*search_region, search_region+1):
            if not (i == 0 and j == 0):
                test = curr_pos + Position(i, j)
                if not game_map[test].is_occupied:
                    safe_spaces.append(test)

    return safe_spaces


def get_safe_cardinals(ship, game_map):
    curr_pos = ship.position

    safe_spaces = [x for x in curr_pos.get_surrounding_cardinals() if not game_map[x].is_occupied]

    return safe_spaces


###############################################################################
# Movement functions
###############################################################################
def random_move(ship, game_map):
    curr_pos = ship.position

    move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO

    move = Direction.Still
    new_pos = curr_pos
    if ship.halite_amount >= move_cost:
        allowed = Direction.get_all_cardinals()
        move = random.choice(allowed)
        new_pos = curr_pos+Position(move[0], move[1])

        while game_map[new_pos].is_occupied and len(allowed) > 0:
            allowed.remove(move)

            if len(allowed) > 0:
                move = random.choice(allowed)
                new_pos = curr_pos+Position(move[0], move[1])
            else:
                move = (0, 0)
                new_pos = curr_pos

    game_map[new_pos].mark_unsafe(ship)
    return move


def returning_move(ship, game_map, closest):
    curr_pos = ship.position

    move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO

    move = Direction.Still
    new_pos = curr_pos
    if ship.halite_amount >= move_cost:
        move = game_map.naive_navigate(ship, closest)
        new_pos = curr_pos+Position(move[0], move[1])

        """
        if game_map[new_pos].is_occupied:
            move = Direction.Still
            new_pos = curr_pos
        """

    game_map[new_pos].mark_unsafe(ship)
    return move


def smart_explore(ship, game_map, search_region=1):
    curr_pos = ship.position

    move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO

    move = Direction.Still
    new_pos = curr_pos
    if ship.halite_amount >= move_cost:
        # safe_spaces = get_safe_spaces_in_region(ship, game_map, search_region=search_region)
        safe_spaces = get_safe_cardinals(ship, game_map)
        if len(safe_spaces) == 0:
            return (0, 0)

        h_amount = [game_map[x].halite_amount for x in safe_spaces]
        h_amount, safe_spaces = list(zip(*sorted(zip(h_amount, safe_spaces), key=lambda x: x[0], reverse=True)))

        move = game_map.naive_navigate(ship, safe_spaces[0])
        new_pos = curr_pos+Position(move[0], move[1])

    game_map[new_pos].mark_unsafe(ship)
    return move


###############################################################################
# Decision functions
###############################################################################
def dropoff_checklist(dist, game, ship, ship_status):
    me = game.me
    game_map = game.game_map

    too_far = dist > large_distance_from_drop
    sufficent_num_ships = len(me.get_ships()) > 1

    real_dropoff_cost = (constants.DROPOFF_COST
                         - game_map[ship.position].halite_amount
                         - ship.halite_amount)
    sufficient_halite_to_build = (me.halite_amount > real_dropoff_cost)

    not_end_game = game.turn_number < turn_to_stop_spending
    only_one_dropoff_at_a_time = "dropoff" not in ship_status

    return (too_far and sufficent_num_ships and
            sufficient_halite_to_build and not_end_game
            and only_one_dropoff_at_a_time)


def ship_spawn_checklist(game):
    me = game.me
    game_map = game.game_map

    not_end_game = game.turn_number < turn_to_stop_spending

    if "dropoff" in ship_status:
        sufficient_halite_to_build = (me.halite_amount >=
                                      constants.SHIP_COST
                                      + constants.DROPOFF_COST)
    else:
        sufficient_halite_to_build = me.halite_amount >= constants.SHIP_COST

    not_busy = not game_map[me.shipyard].is_occupied
    need_ships = len(me.get_ships()) < max_ships
    lots_of_halite = (me.halite_amount >
                      constants.DROPOFF_COST+constants.SHIP_COST)

    return (not_end_game and sufficient_halite_to_build and not_busy and
            (need_ships or lots_of_halite))


###############################################################################
# Game
###############################################################################
game = hlt.Game()
# Pre-processing area
ship_status = {}

# Game parameters
max_ships = 10
turn_to_stop_spending = 300
large_distance_from_drop = 10
minimum_useful_halite = constants.MAX_HALITE/10
sufficient_halite_for_droping = constants.MAX_HALITE/4
density_kernal_side_length = 3

game.ready("BH4-test")

logging.info("Successfully created bot! Player ID is {}.".format(game.my_id))

# Game Loop
while True:
    game.update_frame()

    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn.
    command_queue = []
    for ship in me.get_ships():
        game_map[ship.position].mark_unsafe(ship)

    for ship in me.get_ships():
        # Mark status
        if ship.id not in ship_status:
            ship_status[ship.id] = "exploring"

        if ship_status[ship.id] == "returning":
            closest, dist = closest_drop(ship, me, game_map)
            if dist == 0:
                ship_status[ship.id] = "exploring"
        elif ship.halite_amount >= sufficient_halite_for_droping:
            ship_status[ship.id] = "returning"

        # Take action
        if ship_status[ship.id] == "returning":
            closest, dist = closest_drop(ship, me, game_map)

            if dropoff_checklist(dist, game, ship, ship_status):
                command_queue.append(ship.make_dropoff())
                ship_status[ship.id] = "dropoff"

                logging.info("Ship {} decided to make a dropoff.".format(ship.id))
            else:
                move = returning_move(ship, game_map, closest)
                command_queue.append(ship.move(move))

                logging.info("Ship {} is returning by moving {}.".format(ship.id, move))
        elif ship_status[ship.id] == "exploring":
            if game_map[ship.position].halite_amount < minimum_useful_halite:
                move = smart_explore(ship, game_map)
                command_queue.append(ship.move(move))

                logging.info("Ship {} is exploring by moving {}.".format(ship.id, move))
            else:
                command_queue.append(ship.stay_still())

                logging.info("Ship {} is collecting by staying still.".format(ship.id))

    # If you're on the first turn and have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though.
    if ship_spawn_checklist(game, ship_status):
        command_queue.append(game.me.shipyard.spawn())

    # Reset turn based variables
    stored_density = None

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
