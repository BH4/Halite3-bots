from hlt.positionals import Position

import numpy as np
import logging


def toroidal_value_sum(matrix, square_side_length):
    w = len(matrix)
    h = len(matrix[0])

    s = square_side_length//2
    """Convolution on a torus"""
    values = []
    for i in range(w):
        col = []
        row_sums = []
        for j in range(h):

            curr = 0
            if len(row_sums) == 0:
                for jj in range(-s, s+1):
                    rs = 0
                    for ii in range(-s, s+1):
                        rs += matrix[(i+ii) % w][(j+jj) % h]
                    curr += rs
                    row_sums.append(rs)
            else:
                v = row_sums.pop(0)
                curr = col[-1]-v
                jj = s
                rs = 0
                for ii in range(-s, s+1):
                    rs += matrix[(i+ii) % w][(j+jj) % h]
                curr += rs
                row_sums.append(rs)

            col.append(curr)
        values.append(col)

    return np.array(values)


stored_density = None
def halite_density(game_map, params):
    global stored_density

    if stored_density is not None:
        return stored_density

    all_halite = []
    for i in range(game_map.width):
        col = []
        for j in range(game_map.height):
            col.append(game_map[Position(i, j)].halite_amount)

        all_halite.append(col)

    stored_density = toroidal_value_sum(all_halite, params.density_kernal_side_length)
    return stored_density


def closest_most_dense_spot(ship, game_map, params, n=3):
    """From the n most dense regions choose closest"""
    density = halite_density(game_map, params)
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


def closest_dense_spot(ship, game_map, params, density_req=None):
    """Return the closest location which satisfies the
    explore_dense_requirement."""
    if density_req is None:
        density_req = params.explore_dense_requirement

    density = halite_density(game_map, params)
    ind = []

    for i in range(len(density)):
        for j in range(len(density[0])):
            if density[i][j] > density_req:
                ind.append((i, j))

    if len(ind) == 0:
        logging.info("wtf")
        return None, None

    pos = [Position(x[0], x[1]) for x in ind]
    dist = [game_map.calculate_distance(ship.position, x) for x in pos]
    dist, pos = list(zip(*sorted(zip(dist, pos), key=lambda x: x[0])))


    logging.info("params.minimum_useful_halite {}".format(params.minimum_useful_halite))
    logging.info("density_req {}".format(density_req))
    logging.info("Actual density of spot I am telling you to move {} at pos {}".format(density[pos[0].x][pos[0].y], pos[0]))

    for i in range(-1, 2):
        for j in range(-1, 2):
            h = game_map[pos[0]+Position(i, j)].halite_amount
            logging.info("actual halite at pos[0] + {}={}".format((i,j), h))

    return pos[0], dist[0]


def dense_spots(game_map, params):
    density = halite_density(game_map, params)
    ind = []
    dval = []
    for i in range(len(density)):
        for j in range(len(density[0])):
            ind.append((i, j))
            dval.append(density[i][j])

    dval, ind = list(zip(*sorted(zip(dval, ind), reverse=True)))
    pos = [Position(x[0], x[1]) for x in ind]

    return pos, dval


def closest_drop(position, me, game_map):
    closest = me.shipyard.position
    dist = game_map.calculate_distance(position, me.shipyard.position)
    for drop in me.get_dropoffs():
        dist_temp = game_map.calculate_distance(position, drop.position)
        if dist_temp < dist:
            dist = dist_temp
            closest = drop.position

    return closest, dist


# Return id of closest ship to this position
def closest_ship(position, me, game_map):
    closest = -1
    dist = 10**5
    for ship in me.get_ships():
        dist_temp = game_map.calculate_distance(position, ship.position)
        if dist_temp < dist:
            dist = dist_temp
            closest = ship.id

    return closest, dist


# Return ids of ships sorted from closest to farthest
def sort_ships_by_distance(position, me, game_map):
    id_list = [ship.id for ship in me.get_ships()]
    dist_list = [game_map.calculate_distance(ship.position, position)
                 for ship in me.get_ships()]

    dist_list, id_list = list(zip(*sorted(zip(dist_list, id_list))))

    return id_list, dist_list


def get_spaces_in_region(ship, search_region=1):
    curr_pos = ship.position

    spaces = []
    for i in range(-1*search_region, search_region+1):
        for j in range(-1*search_region, search_region+1):
            if not (i == 0 and j == 0):
                spaces.append(curr_pos + Position(i, j))

    return spaces
