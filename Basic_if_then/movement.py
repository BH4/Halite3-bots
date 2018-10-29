from hlt.positionals import Position, Direction
from hlt import constants

import random
import logging

# Import my stuff
import helpers


def navigate_old(ship, destination, game_map):
    curr_pos = ship.position

    move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO
    if ship.halite_amount >= move_cost:
        move = game_map.naive_navigate(ship, destination)
        new_pos = curr_pos+Position(move[0], move[1])

        game_map[curr_pos].ship = None
        game_map[new_pos].mark_unsafe(ship)
        return move
    return (0, 0)


def navigate(game_map, ship, destination):
    destination = game_map.normalize(destination)

    logging.info("destination normalized")

    w = game_map.width
    h = game_map.height
    curr_pos = ship.position

    move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO
    if ship.halite_amount < move_cost:
        # If the ship doesn't have enough halite on board to move
        # Then it MUST stay still. No other action is possible.
        logging.info("navigate: Ship {} decided there isn't enough halite to move.".format(ship.id))
        return [(0, 0)]

    logging.info("navigate: Ship {} decided there is enough halite to move.".format(ship.id))
    possible_moves = []
    dy = destination.y - curr_pos.y
    if dy > w//2:
        dy -= w
    elif dy < -w//2:
        dy += w

    dx = destination.x - curr_pos.x
    if dx > w//2:
        dx -= w
    elif dx < -w//2:
        dx += w

    logging.info("navigate: Ship {} says dx={} and dy={}.".format(ship.id, dx, dy))

    h_amount = {x: game_map[curr_pos+Position(*x)].halite_amount
                for x in Direction.get_all_cardinals()}

    logging.info("navigate: Ship {} got halite amount at adjacent positions.".format(ship.id))

    # Possible moves sorted by preference only taking into account distance
    if abs(dy) > abs(dx):
        logging.info("navigate: Ship {} wants vertical move.".format(ship.id))
        y_sign = dy//abs(dy)

        possible_moves.append((0, y_sign))  # dy>0
        if dx == 0:
            logging.info("test1")
            possible_moves.append((0, 0))
            if h_amount[(1, 0)] <= h_amount[(-1, 0)]:
                logging.info("test2")
                possible_moves.append((1, 0))
                possible_moves.append((-1, 0))
            else:
                logging.info("test3")
                possible_moves.append((-1, 0))
                possible_moves.append((1, 0))
            possible_moves.append((0, -1*y_sign))
        else:
            logging.info("test4")
            x_sign = dx//abs(dx)

            possible_moves.append((x_sign, 0))
            possible_moves.append((0, 0))
            possible_moves.append((-1*x_sign, 0))
            possible_moves.append((0, -1*y_sign))

            # Take halite amount into consideration for preference
            # (weather or not to flip the first two and same but independent of the last two)
            # currently ignored
    elif abs(dy) < abs(dx) or (abs(dy) == abs(dx) and dy != 0):
        logging.info("navigate: Ship {} wants horizontal move.".format(ship.id))
        x_sign = dx//abs(dx)

        possible_moves.append((x_sign, 0))  # dx>0
        if dy == 0:
            logging.info("test1")
            possible_moves.append((0, 0))
            if h_amount[(0, 1)] <= h_amount[(0, -1)]:
                logging.info("test2")
                possible_moves.append((0, 1))
                possible_moves.append((0, -1))
            else:
                logging.info("test3")
                possible_moves.append((0, -1))
                possible_moves.append((0, 1))
            possible_moves.append((-1*x_sign, 0))
        else:
            logging.info("test4")
            y_sign = dy//abs(dy)

            possible_moves.append((0, y_sign))
            possible_moves.append((0, 0))
            possible_moves.append((0, -1*y_sign))
            possible_moves.append((-1*x_sign, 0))

            # Take halite amount into consideration for preference
            # (weather or not to flip the first two and same but independent of the last two)
            # currently ignored
    else:
        # This ship doesn't want to move
        logging.info("navigate: Ship {} doesn't want to move.".format(ship.id))
        a = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        random.shuffle(a)
        possible_moves = [(0, 0)] + a

    logging.info("navigate: Ship {} got possible_moves.".format(ship.id))
    return possible_moves


def group_navigate(game, ship_status, ship_destination):
    me = game.me
    game_map = game.game_map

    # Can't navigate with no ships.
    if len(me.get_ships()) == 0:
        return {}

    logging.info("group_navigate: There is more than zero ships.")

    # List all moves for each ship
    move_list = {ship.id: navigate(game_map, ship, ship_destination[ship.id]) for ship in me.get_ships()}

    logging.info("group_navigate: Got moves.")
    priority_list = {}

    # Ship priorities will follow distances from current destination.
    # Ships making a dropoff have highest priority.
    sorted_ship_list = []
    dist_list = []
    for ship in me.get_ships():
        sorted_ship_list.append(ship)
        if ship.id in ship_destination and ship_status[ship.id] != "returning":
            dist_list.append(game_map.calculate_distance(ship.position, ship_destination[ship.id]))
        elif ship_status[ship.id] == "dropoff":
            dist_list.append(-1)
        else:
            dist_list.append(0)

    z = zip(dist_list, sorted_ship_list)
    sz = sorted(z, key=lambda x: x[0])
    dist_list, sorted_ship_list = list(zip(*sz))

    for i in range(len(sorted_ship_list)):
        priority_list[sorted_ship_list[i].id] = i

    logging.info("group_navigate: Made priority_list.")

    solution = group_navigate_main(me.get_ships(), game_map, priority_list, move_list)
    if solution is None:
        logging.info("group_navigate: No solution")
    return solution


def group_navigate_main(ship_list, game_map, priority_list, move_list):
    logging.info("group_navigate_main: "+str(move_list))
    conflicting_positions = set()

    move_test = {x: move_list[x][0] for x in move_list.keys()}
    position_test = {}
    for ship in ship_list:
        s = str(game_map.normalize(ship.position + Position(*move_test[ship.id])))
        if s in position_test:
            conflicting_positions.add(s)
            position_test[s].append(ship.id)
        else:
            position_test[s] = [ship.id]

    # Solution is acceptable
    if len(conflicting_positions) == 0:
        return move_test

    # Conflict resolution
    # Attempt resolution to one conflict at a time when all are solved a
    # solution will be returned.
    logging.info("group_navigate_main: "+str(conflicting_positions))

    for s in conflicting_positions:
        logging.info("group_navigate_main: "+s)
        crashing_ships = position_test[s]
        logging.info("group_navigate_main: "+str(crashing_ships))
        priorities = [priority_list[x] for x in crashing_ships]
        logging.info("group_navigate_main: "+str(priorities))

        # Allow one ship to move to this position but no more.
        # If there are any that don't have the ability to move at all
        # (not enough halite) then they must be the one to remain in
        # this position and all other ships that want to move here will
        # have to go somewhere else. If there is more than one that can't
        # move then there is no solution.
        only_one_move = [i for i, x in enumerate(crashing_ships) if len(move_list[x]) == 1]
        logging.info("group_navigate_main: "+str(only_one_move))
        if len(only_one_move) == 1:
            sorted_inds = [only_one_move[0]]
        elif len(only_one_move) > 1:
            return None  # There are no solutions
        else:
            _, sorted_inds = list(zip(*sorted(zip(priorities, range(len(priorities))))))

        logging.info("group_navigate_main: "+str(sorted_inds))
        for ind in sorted_inds:
            new_move_list = {x: [y for y in move_list[x]] for x in move_list}

            # Keep the other crashing ships from moving here.
            # Keep ship at ind the same.
            for i in range(len(crashing_ships)):
                if i != ind:
                    shipid = crashing_ships[i]
                    new_move_list[shipid] = new_move_list[shipid][1:]

            solution = group_navigate_main(ship_list, game_map, priority_list, new_move_list)
            if solution is not None:
                return solution

    return None  # failed to find any solutions


def random_move(ship, game_map, params):
    curr_pos = ship.position

    # Don't move if there is enough halite here
    if game_map[curr_pos].halite_amount < params.minimum_useful_halite:
        move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO

        # Don't move if I can't pay for it
        if ship.halite_amount >= move_cost:
            spaces = curr_pos.get_surrounding_cardinals()

            # Don't move if nowhere else is safe
            if len(spaces) > 0:
                new_pos = random.choice(spaces)
                return new_pos

    return curr_pos


def returning_move(ship, me, game_map):
    closest, dist = helpers.closest_drop(ship.position, me, game_map)

    curr_pos = ship.position

    move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO

    if ship.halite_amount >= move_cost:
        return closest

    return curr_pos


def smart_explore(ship, game_map, params):
    #if random.random() < .5:
    #    logging.info("Randomly chose to vacuum.")
    #    return vacuum_explore(ship, game_map, params)

    curr_pos = ship.position

    # Don't move if there is enough halite here
    if game_map[curr_pos].halite_amount < params.minimum_useful_halite:
        logging.info("Ship {} decided there isn't enough halite here.".format(ship.id))

        move_cost = game_map[curr_pos].halite_amount/constants.MOVE_COST_RATIO

        # Don't move if I can't pay for it
        if ship.halite_amount >= move_cost:
            logging.info("Ship {} is able to pay for movement.".format(ship.id))

            spaces = helpers.get_spaces_in_region(ship, search_region=params.search_region)
            # spaces = curr_pos.get_surrounding_cardinals()

            # Don't set destination to be on top of another ship
            # unless it is necessary.
            new_spaces = []
            for p in spaces:
                if not game_map[p].is_occupied:
                    new_spaces.append(p)

            if len(new_spaces) > 0:
                spaces = new_spaces

            # Don't move if nowhere else is safe
            if len(spaces) > 0:
                h_amount = [game_map[x].halite_amount for x in spaces]
                # If none of the spaces have enough halite then move to a
                # better area
                if max(h_amount) < params.minimum_useful_halite:
                    logging.info("Moving to better area")
                    pos, dist = helpers.closest_dense_spot(ship, game_map, params)
                    if dist == 0:
                        logging.info("Moving to same location :/")

                    if pos is None:  # default to other method if none found over threshold
                        # pos, dist = helpers.closest_most_dense_spot(ship, game_map, params, n=params.number_of_dense_spots_to_check)
                        pos = vacuum_explore(ship, game_map, params)
                    return pos

                h_amount, spaces = list(zip(*sorted(zip(h_amount, spaces), key=lambda x: x[0], reverse=True)))
                destination = spaces[0]
                return destination
        else:
            logging.info("Ship {} is NOT able to pay for movement.".format(ship.id))
    else:
        logging.info("Ship {} decided there is plenty of halite here.".format(ship.id))

    return curr_pos


def vacuum_explore(ship, game_map, params):
    curr_pos = ship.position

    minimum_useful_halite = constants.EXTRACT_RATIO*2
    explore_density = minimum_useful_halite*params.density_kernal_side_length**2

    # Don't move if there is enough halite here
    if game_map[curr_pos].halite_amount < minimum_useful_halite:
        logging.info("Ship {} decided there isn't enough halite here.".format(ship.id))

        # Movement cost should always be zero.
        logging.info("Ship {} is able to pay for movement.".format(ship.id))

        spaces = helpers.get_spaces_in_region(ship, search_region=params.search_region)
        # spaces = curr_pos.get_surrounding_cardinals()

        # Don't set destination to be on top of another ship
        # unless it is necessary.
        new_spaces = []
        for p in spaces:
            if not game_map[p].is_occupied:
                new_spaces.append(p)

        if len(new_spaces) > 0:
            spaces = new_spaces

        # Don't move if nowhere else is safe
        if len(spaces) > 0:
            h_amount = [game_map[x].halite_amount for x in spaces]
            # If none of the spaces have enough halite then move to a
            # better area
            if max(h_amount) < minimum_useful_halite:
                logging.info("Moving to better area")
                pos, dist = helpers.closest_dense_spot(ship, game_map, params, density_req=explore_density)
                if dist == 0:
                    logging.info("Moving to same location :/")

                if pos is None:  # default to other method if none found over threshold
                    pos, dist = helpers.closest_most_dense_spot(ship, game_map, params, n=params.number_of_dense_spots_to_check)
                return pos

            h_amount, spaces = list(zip(*sorted(zip(h_amount, spaces), key=lambda x: x[0], reverse=True)))
            destination = spaces[0]
            return destination
    else:
        logging.info("Ship {} decided there is plenty of halite here.".format(ship.id))

    return curr_pos
