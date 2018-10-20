from hlt.positionals import Direction, Position
from hlt import constants

import random
import logging

# Import my stuff
import helpers


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
        safe_spaces = helpers.get_safe_cardinals(ship, game_map)
        if len(safe_spaces) == 0:
            return (0, 0)

        h_amount = [game_map[x].halite_amount for x in safe_spaces]
        h_amount, safe_spaces = list(zip(*sorted(zip(h_amount, safe_spaces), key=lambda x: x[0], reverse=True)))

        move = game_map.naive_navigate(ship, safe_spaces[0])
        new_pos = curr_pos+Position(move[0], move[1])

    game_map[new_pos].mark_unsafe(ship)
    return move
