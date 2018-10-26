from hlt.positionals import Position
from hlt import constants

import logging

# Import my stuff
import helpers
import checklists
import movement


num_dropoffs = 0


def expand(game, ship_status, ship_destination, params):
    global num_dropoffs

    game.update_frame()

    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn.
    command_queue = []

    if num_dropoffs < params.max_dropoffs:
        # returns none if dropoff is a bad idea right now.
        sorted_ship_ids, drop_location = checklists.group_dropoff_decision(game, ship_status, params)
        if sorted_ship_ids == "stop":
            logging.info("dropoff never")
            num_dropoffs = params.max_dropoffs
        elif sorted_ship_ids is not None:
            drop_ship_id = sorted_ship_ids[0]

            logging.info("dropoff: {}, {}.".format(drop_ship_id, drop_location))
            ship_status[drop_ship_id] = "dropoff"
            ship_destination[drop_ship_id] = drop_location

            for i in range(1, (len(sorted_ship_ids)+1)//2 + 1):
                ship_status[sorted_ship_ids[i]] = "traveling"
                ship_destination[sorted_ship_ids[i]] = drop_location

    # Purge ship dictionaries
    shipids = set(ship.id for ship in me.get_ships())
    extras = set(ship_status.keys())-shipids
    for e in extras:
        ship_status.pop(e)
    extras = set(ship_destination.keys())-shipids
    for e in extras:
        ship_destination.pop(e)

    # Ship loop
    for ship in me.get_ships():
        # Pre-computed values for this ship
        if ship.id in ship_destination:
            dist = game_map.calculate_distance(ship.position, ship_destination[ship.id])
        else:
            dist = 0

        #######################################################################
        # Mark status
        #######################################################################
        # Just make sure every ship has a status and a destination
        if ship.id not in ship_status:
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
                dist = 0
        elif ship_status[ship.id] == "traveling" and dist < params.density_kernal_side_length:
            ship_status[ship.id] = "exploring"
            dist = 0

        #######################################################################
        # Get new destination if reached last one (or haven't gotten one yet)
        #######################################################################
        if ship_status[ship.id] == "returning" and dist == 0:
            destination = movement.returning_move(ship, me, game_map)
            ship_destination[ship.id] = destination

            logging.info("Ship {} is returning by moving {}.".format(ship.id, destination))
        elif ship_status[ship.id] == "exploring":
            # Exploring moves should recalculate the destination every turn in
            # case the conditions change.
            destination = movement.smart_explore(ship, game_map, params)
            ship_destination[ship.id] = destination

            logging.info("Ship {} is exploring by moving {}.".format(ship.id, destination))

        # Destination for a traveling ship should never need to be changed

    #######################################################################
    # Make move
    #######################################################################
    move_dict = movement.group_navigate(game, ship_status, ship_destination)
    currently_occupied_positions = []
    for ship in me.get_ships():
        if ship_status[ship.id] == "dropoff" and ship_destination[ship.id] == ship.position:
            if checklists.dropoff_checklist(game, ship, ship_status, params):
                num_dropoffs += 1
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
