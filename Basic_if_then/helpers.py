from hlt.positionals import Position

import numpy as np
import logging


def toroidal_value_sum(matrix, square_side_length):
    w = len(matrix)
    h = len(matrix[0])

    s = square_side_length//2
    """Convolution on a torus"""
    values = []
    for j in range(h):
        row = []
        col_sums = []
        for i in range(w):
            curr = 0
            if len(col_sums) == 0:
                for ii in range(-s, s+1):
                    cs = 0
                    for jj in range(-s, s+1):
                        cs += matrix[(i+ii) % w][(j+jj) % h]
                    curr += cs
                    col_sums.append(cs)
            else:
                v = col_sums.pop(0)
                curr = row[-1]-v
                ii = s
                cs = 0
                for jj in range(-s, s+1):
                    cs += matrix[(i+ii) % w][(j+jj) % h]
                curr += cs
                col_sums.append(cs)

            row.append(curr)
        values.append(row)
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


def closest_dense_spot(ship, game_map, params, n=3):
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


def closest_drop(ship, me, game_map):
    closest = me.shipyard.position
    dist = game_map.calculate_distance(ship.position, me.shipyard.position)
    for drop in me.get_dropoffs():
        dist_temp = game_map.calculate_distance(ship.position, drop.position)
        if dist_temp < dist:
            dist = dist_temp
            closest = drop.position

    return closest, dist


def get_safe_spaces_in_region(ship, game_map, search_region=1):
    curr_pos = ship.position

    safe_spaces = []
    for i in range(-1*search_region, search_region+1):
        for j in range(-1*search_region, search_region+1):
            if not (i == 0 and j == 0):
                test = curr_pos + Position(i, j)
                if not game_map[test].is_occupied:
                    safe_spaces.append(test)

    return safe_spaces


def get_safe_cardinals(ship, game_map):
    curr_pos = ship.position

    safe_spaces = [x for x in curr_pos.get_surrounding_cardinals() if not game_map[x].is_occupied]

    return safe_spaces
