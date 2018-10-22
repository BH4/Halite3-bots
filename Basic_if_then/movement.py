from hlt.positionals import Position
from hlt import constants

import random
import logging

# Import my stuff
import helpers


def navigate(ship, destination, game_map):
    curr_pos = ship.position

    move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO
    if ship.halite_amount >= move_cost:
        move = game_map.naive_navigate(ship, destination)
        new_pos = curr_pos+Position(move[0], move[1])

        game_map[curr_pos].ship = None
        game_map[new_pos].mark_unsafe(ship)
        return move
    return (0, 0)


def random_move(ship, game_map, params):
    curr_pos = ship.position

    # Don't move if there is enough halite here
    if game_map[curr_pos].halite_amount < params.minimum_useful_halite:
        move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO

        # Don't move if I can't pay for it
        if ship.halite_amount >= move_cost:
            allowed = helpers.get_safe_cardinals(curr_pos, game_map)

            # Don't move if nowhere else is safe
            if len(allowed) > 0:
                new_pos = random.choice(allowed)
                return new_pos

    return curr_pos


def returning_move(ship, game_map, closest):
    curr_pos = ship.position

    move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO

    if ship.halite_amount >= move_cost:
        return closest

    return curr_pos


def smart_explore(ship, game_map, params, search_region=1):
    curr_pos = ship.position

    # Don't move if there is enough halite here
    if game_map[curr_pos].halite_amount < params.minimum_useful_halite:
        move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO

        # Don't move if I can't pay for it
        if ship.halite_amount >= move_cost:
            # safe_spaces = get_safe_spaces_in_region(ship, game_map, search_region=search_region)
            safe_spaces = helpers.get_safe_cardinals(curr_pos, game_map)

            # Don't move if nowhere else is safe
            if len(safe_spaces) > 0:
                h_amount = [game_map[x].halite_amount for x in safe_spaces]
                h_amount, safe_spaces = list(zip(*sorted(zip(h_amount, safe_spaces), key=lambda x: x[0], reverse=True)))
                destination = safe_spaces[0]
                return destination

    return curr_pos
