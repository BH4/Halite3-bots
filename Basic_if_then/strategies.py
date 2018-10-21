import logging

# Import my stuff
import helpers
import checklists
import movement


def expand(game, ship_status, params):
    game.update_frame()

    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn.
    command_queue = []
    for ship in me.get_ships():
        game_map[ship.position].mark_unsafe(ship)

    for ship in me.get_ships():
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
        elif (ship_status[ship.id] == "exploring" and
              ship.halite_amount >= params.sufficient_halite_for_droping):
            ship_status[ship.id] = "returning"

        if checklists.dropoff_checklist(dist, game, ship, ship_status, params):
            ship_status[ship.id] = "dropoff"

            logging.info("Ship {} decided to make a dropoff.".format(ship.id))

        #######################################################################
        # Take action
        #######################################################################
        if ship_status[ship.id] == "returning":
            move = movement.returning_move(ship, game_map, closest)
            command_queue.append(ship.move(move))

            logging.info("Ship {} is returning by moving {}.".format(ship.id, move))
        elif ship_status[ship.id] == "exploring":
            if game_map[ship.position].halite_amount < params.minimum_useful_halite:
                move = movement.smart_explore(ship, game_map)
                command_queue.append(ship.move(move))

                logging.info("Ship {} is exploring by moving {}.".format(ship.id, move))
            else:
                command_queue.append(ship.stay_still())

                logging.info("Ship {} is collecting by staying still.".format(ship.id))
        elif ship_status[ship.id] == "dropoff":
            command_queue.append(ship.make_dropoff())

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
