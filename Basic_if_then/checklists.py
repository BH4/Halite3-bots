from hlt import constants

import logging


def dropoff_checklist(dist, game, ship, ship_status, params):
    me = game.me
    game_map = game.game_map

    too_far = dist > params.large_distance_from_drop
    sufficent_num_ships = len(me.get_ships()) > 1

    real_dropoff_cost = (constants.DROPOFF_COST
                         - game_map[ship.position].halite_amount
                         - ship.halite_amount)
    sufficient_halite_to_build = (me.halite_amount > real_dropoff_cost)

    not_end_game = game.turn_number < params.turn_to_stop_spending
    only_one_dropoff_at_a_time = "dropoff" not in ship_status

    return (too_far and sufficent_num_ships and
            sufficient_halite_to_build and not_end_game
            and only_one_dropoff_at_a_time)


def ship_spawn_checklist(game, ship_status, params):
    me = game.me
    game_map = game.game_map

    not_end_game = game.turn_number < params.turn_to_stop_spending

    if "dropoff" in ship_status:
        sufficient_halite_to_build = (me.halite_amount >=
                                      constants.SHIP_COST
                                      + constants.DROPOFF_COST)
    else:
        sufficient_halite_to_build = me.halite_amount >= constants.SHIP_COST

    not_busy = not game_map[me.shipyard].is_occupied
    need_ships = len(me.get_ships()) < params.max_ships
    lots_of_halite = (me.halite_amount >
                      constants.DROPOFF_COST+constants.SHIP_COST)

    return (not_end_game and sufficient_halite_to_build and not_busy and
            (need_ships or lots_of_halite))