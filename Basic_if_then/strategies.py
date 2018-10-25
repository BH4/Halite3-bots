from hlt.positionals import Position
from hlt import constants

import logging

# Import my stuff
import helpers
import checklists
import movement

try_to_make_dropoff = True


def expand(game, ship_status, ship_destination, params):
    global try_to_make_dropoff

    game.update_frame()

    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn.
    command_queue = []

    if try_to_make_dropoff:
        # returns none if dropoff is a bad idea right now.
        drop_ship_id, drop_location = checklists.group_dropoff_decision(game, ship_status, params)
        if drop_ship_id == "stop":
            try_to_make_dropoff = False
        elif drop_ship_id is not None:
            logging.info("dropoff: {}, {}.".format(drop_ship_id, drop_location))
            ship_status[drop_ship_id] = "dropoff"
            ship_destination[drop_ship_id] = drop_location

    for ship in me.get_ships():
        # Pre-computed values for this ship
        closest, dist = helpers.closest_drop(ship.position, me, game_map)

        #######################################################################
        # Mark status
        #######################################################################
        if ship.id not in ship_status:
            # Just make sure every ship has a status and a destination
            ship_status[ship.id] = "exploring"
            ship_destination[ship.id] = ship.position

        # Status changes
        if ship_status[ship.id] == "returning" and dist == 0:
            ship_status[ship.id] = "exploring"
        elif ship_status[ship.id] == "exploring":
            if((ship.halite_amount >= params.sufficient_halite_for_droping and
               ship.halite_amount > game_map[ship.position].halite_amount) or
               constants.MAX_HALITE-ship.halite_amount < game_map[ship.position].halite_amount/constants.EXTRACT_RATIO):
                ship_status[ship.id] = "returning"

        #######################################################################
        # Get new destination if reached last one (or haven't gotten one yet)
        #######################################################################
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
    move_dict = movement.group_navigate(game, ship_status, ship_destination)
    currently_occupied_positions = []
    for ship in me.get_ships():
        if ship_status[ship.id] == "dropoff" and ship_destination[ship.id] == ship.position:
            if checklists.dropoff_checklist(game, ship, ship_status, params):
                command_queue.append(ship.make_dropoff())

                logging.info("Ship {} made a dropoff.".format(ship.id))
            else:
                logging.info("Ship {} couldn't make a dropoff!!!!!!!!!!!!!!!!.".format(ship.id))
                currently_occupied_positions.append(ship.position)
        else:
            move = move_dict[ship.id]
            currently_occupied_positions.append(ship.position+Position(*move))
            command_queue.append(ship.move(move))

    #######################################################################
    # Ship spawn
    #######################################################################
    if checklists.ship_spawn_checklist(game, ship_status, currently_occupied_positions, params):
        command_queue.append(game.me.shipyard.spawn())

    #######################################################################
    # Reset turn based variables
    #######################################################################
    helpers.stored_density = None

    #######################################################################
    # Send your moves back to the game environment, ending this turn.
    #######################################################################
    game.end_turn(command_queue)
