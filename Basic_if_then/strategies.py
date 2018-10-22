import logging

# Import my stuff
import helpers
import checklists
import movement


def expand(game, ship_status, ship_destination, params):
    game.update_frame()

    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn.
    command_queue = []

    # Mark current positions unsafe and
    # sort ships by closest to previous destination.
    sorted_ship_list = []
    prev_dist_list = []
    for ship in me.get_ships():
        game_map[ship.position].mark_unsafe(ship)

        sorted_ship_list.append(ship)
        if ship.id in ship_destination:
            prev_dist_list.append(game_map.calculate_distance(ship.position, ship_destination[ship.id]))
        else:
            prev_dist_list.append(0)

    if len(sorted_ship_list) > 0:
        z = zip(prev_dist_list, sorted_ship_list)
        sz = sorted(z, key=lambda x: x[0])
        prev_dist_list, sorted_ship_list = list(zip(*sz))

        # Purge ship dictionaries
        shipids = set(ship.id for ship in me.get_ships())
        extras = set(ship_status.keys())-shipids
        for e in extras:
            ship_status.pop(e)
        extras = set(ship_destination.keys())-shipids
        for e in extras:
            ship_destination.pop(e)

    for ship, prev_dist in zip(sorted_ship_list, prev_dist_list):
        # Pre-computed values for this ship
        closest, dist = helpers.closest_drop(ship, me, game_map)

        #######################################################################
        # Mark status
        #######################################################################
        if ship.id not in ship_status:
            ship_status[ship.id] = "exploring"

        # Status changes
        if ship_status[ship.id] == "returning" and dist == 0:
            ship_status[ship.id] = "exploring"
        elif ship.halite_amount >= params.sufficient_halite_for_droping:
            ship_status[ship.id] = "returning"

        if checklists.dropoff_checklist(dist, game, ship, ship_status, params):
            ship_status[ship.id] = "dropoff"

        #######################################################################
        # Get new destination if reached last one (or haven't gotten one yet)
        #######################################################################
        if prev_dist == 0:
            if ship_status[ship.id] == "returning":
                destination = movement.returning_move(ship, game_map, closest)
                ship_destination[ship.id] = destination

                logging.info("Ship {} is returning by moving {}.".format(ship.id, destination))
            elif ship_status[ship.id] == "exploring":
                destination = movement.smart_explore(ship, game_map, params)
                ship_destination[ship.id] = destination

                logging.info("Ship {} is exploring by moving {}.".format(ship.id, destination))

        #######################################################################
        # Make move
        #######################################################################
        if ship_status[ship.id] == "dropoff":
            command_queue.append(ship.make_dropoff())

            logging.info("Ship {} decided to make a dropoff.".format(ship.id))
        else:
            move = movement.navigate(ship, ship_destination[ship.id], game_map)
            command_queue.append(ship.move(move))

    #######################################################################
    # Ship spawn
    #######################################################################
    if checklists.ship_spawn_checklist(game, ship_status, params):
        command_queue.append(game.me.shipyard.spawn())

    #######################################################################
    # Reset turn based variables
    #######################################################################
    helpers.stored_density = None

    #######################################################################
    # Send your moves back to the game environment, ending this turn.
    #######################################################################
    game.end_turn(command_queue)
