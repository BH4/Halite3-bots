from hlt import constants

import logging

# Import my stuff
import helpers


def dropoff_checklist(game, ship, ship_status, params):
    me = game.me
    game_map = game.game_map

    sufficent_num_ships = len(me.get_ships()) > 1

    real_dropoff_cost = (constants.DROPOFF_COST
                         - game_map[ship.position].halite_amount
                         - ship.halite_amount)
    sufficient_halite_to_build = (me.halite_amount > real_dropoff_cost)

    not_end_game = game.turn_number < params.turn_to_stop_spending

    not_enough_dropoffs = len(me.get_dropoffs()) < params.max_dropoffs

    logging.info("dropoff_checklist: sufficent_num_ships {}".format(sufficent_num_ships))
    logging.info("dropoff_checklist: real_dropoff_cost {}".format(real_dropoff_cost))
    logging.info("dropoff_checklist: constants.DROPOFF_COST {}".format(constants.DROPOFF_COST))
    logging.info("dropoff_checklist: game_map[ship.position].halite_amount {}".format(game_map[ship.position].halite_amount))
    logging.info("dropoff_checklist: ship.halite_amount {}".format(ship.halite_amount))
    logging.info("dropoff_checklist: sufficient_halite_to_build {}".format(sufficient_halite_to_build))
    logging.info("dropoff_checklist: me.halite_amount {}".format(me.halite_amount))
    logging.info("dropoff_checklist: not_end_game {}".format(not_end_game))
    logging.info("dropoff_checklist: not_enough_dropoffs {}".format(not_enough_dropoffs))

    return (sufficent_num_ships and sufficient_halite_to_build
            and not_end_game and not_enough_dropoffs)


# Special "checklist" since it returns non-boolean values
def group_dropoff_decision(game, ship_status, params):
    me = game.me
    game_map = game.game_map

    sufficent_num_ships = len(me.get_ships()) > 1

    sufficient_halite_to_build = (me.halite_amount > constants.DROPOFF_COST)

    not_end_game = game.turn_number < params.turn_to_stop_spending
    only_one_dropoff_at_a_time = "dropoff" not in ship_status.values()

    not_enough_dropoffs = len(me.get_dropoffs()) < params.max_dropoffs

    if not (sufficent_num_ships and not_end_game and only_one_dropoff_at_a_time
            and not_enough_dropoffs and sufficient_halite_to_build):
        # Not a good time
        return (None, None)

    pos, dvals = helpers.dense_spots(game_map, params)

    if max(dvals) < params.dropoff_dense_requirement:
        logging.info("not dense enough")
        # Nowhere is dense enough
        return ("stop", None)

    logging.info(pos)
    logging.info(dvals)

    i = 0
    dist_shipyard = game_map.calculate_distance(me.shipyard.position, pos[i])
    _, dist_drop = helpers.closest_drop(pos[i], me, game_map)
    while i < len(pos) and (dist_shipyard > params.farthest_allowed_dropoff or
                            dist_drop < params.large_distance_from_drop):
        logging.info("{} is not suitable for dropoff: dist_shipyard {}, dist_drop {}, dval {}.".format(pos[i], dist_shipyard, dist_drop, dvals[i]))

        i += 1
        dist_shipyard = game_map.calculate_distance(me.shipyard.position, pos[i])
        _, dist_drop = helpers.closest_drop(pos[i], me, game_map)

    if i == len(pos):
        # No suitable spots found and none ever will be.
        return ("stop", None)

    drop_location = pos[i]
    ship_ids, travel_dist = helpers.sort_ships_by_distance(drop_location, me, game_map)

    return ship_ids, drop_location


def ship_spawn_checklist(game, ship_status, currently_occupied_positions, params):
    me = game.me
    game_map = game.game_map

    num_ships = len(me.get_ships())

    end_game = game.turn_number > params.turn_to_stop_spending
    low_ship_num = num_ships < params.min_ships

    if "dropoff" in ship_status.values():
        sufficient_halite_to_build = (me.halite_amount >=
                                      constants.SHIP_COST
                                      + constants.DROPOFF_COST)
    else:
        sufficient_halite_to_build = me.halite_amount >= constants.SHIP_COST

    need_ships = num_ships < params.max_ships
    lots_of_halite = (me.halite_amount >
                      constants.DROPOFF_COST+constants.SHIP_COST)

    not_busy = me.shipyard.position not in currently_occupied_positions

    logging.info("ship_spawn_checklist: num ships {}".format(num_ships))
    logging.info("ship_spawn_checklist: end_game {}".format(end_game))
    logging.info("ship_spawn_checklist: low_ship_num {}".format(low_ship_num))
    logging.info("ship_spawn_checklist: sufficient_halite_to_build {}".format(sufficient_halite_to_build))
    logging.info("ship_spawn_checklist: me.halite_amount {}".format(me.halite_amount))
    logging.info("ship_spawn_checklist: constants.SHIP_COST {}".format(constants.SHIP_COST))
    logging.info("ship_spawn_checklist: constants.DROPOFF_COST {}".format(constants.DROPOFF_COST))
    logging.info("ship_spawn_checklist: need_ships {}".format(need_ships))
    logging.info("ship_spawn_checklist: not_busy {}".format(not_busy))

    return (sufficient_halite_to_build and not_busy and
            ((end_game and low_ship_num) or (not end_game and (need_ships))))  # or lots_of_halite))))
