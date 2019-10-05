"""
Definition of the RailEnv environment and related level-generation functions.

Generator functions are functions that take width, height and num_resets as arguments and return
a GridTransitionMap object.
"""

import numpy as np

from flatland.core.grid.grid4 import Grid4TransitionsEnum
from flatland.core.grid.grid4_astar import a_star
from flatland.core.grid.grid4_utils import get_direction, mirror, direction_to_point
from flatland.core.grid.grid_utils import IntVector2D, IntVector2DDistance, IntVector2DArray
from flatland.core.grid.grid_utils import Vec2dOperations as Vec2d
from flatland.core.transition_map import GridTransitionMap, RailEnvTransitions


def connect_rail_in_grid_map(grid_map: GridTransitionMap, start: IntVector2D, end: IntVector2D,
                             rail_trans: RailEnvTransitions,
                             a_star_distance_function: IntVector2DDistance = Vec2d.get_manhattan_distance,
                             flip_start_node_trans: bool = False, flip_end_node_trans: bool = False,
                             respect_transition_validity: bool = True,
                             forbidden_cells: IntVector2DArray = None) -> IntVector2DArray:
    """
        Creates a new path [start,end] in `grid_map.grid`, based on rail_trans, and
    returns the path created as a list of positions.
    :param rail_trans: basic rail transition object
    :param grid_map: grid map
    :param start: start position of rail
    :param end: end position of rail
    :param flip_start_node_trans: make valid start position by adding dead-end, empty start if False
    :param flip_end_node_trans: make valid end position by adding dead-end, empty end if False
    :param respect_transition_validity: Only draw rail maps if legal rail elements can be use, False, draw line without respecting rail transitions.
    :param a_star_distance_function: Define what distance function a-star should use
    :param forbidden_cells: cells to avoid when drawing rail. Rail cannot go through this list of cells
    :return: List of cells in the path
    """

    path: IntVector2DArray = a_star(grid_map, start, end, a_star_distance_function, respect_transition_validity,
                                    forbidden_cells)
    if len(path) < 2:
        return []

    current_dir = get_direction(path[0], path[1])
    end_pos = path[-1]
    for index in range(len(path) - 1):
        current_pos = path[index]
        new_pos = path[index + 1]
        new_dir = get_direction(current_pos, new_pos)

        new_trans = grid_map.grid[current_pos]
        if index == 0:
            if new_trans == 0:
                # end-point
                if flip_start_node_trans:
                    # need to flip direction because of how end points are defined
                    new_trans = rail_trans.set_transition(new_trans, mirror(current_dir), new_dir, 1)
                else:
                    new_trans = 0
            else:
                # into existing rail
                new_trans = rail_trans.set_transition(new_trans, current_dir, new_dir, 1)
        else:
            # set the forward path
            new_trans = rail_trans.set_transition(new_trans, current_dir, new_dir, 1)
            # set the backwards path
            new_trans = rail_trans.set_transition(new_trans, mirror(new_dir), mirror(current_dir), 1)
        grid_map.grid[current_pos] = new_trans

        if new_pos == end_pos:
            # setup end pos setup
            new_trans_e = grid_map.grid[end_pos]
            if new_trans_e == 0:
                # end-point
                if flip_end_node_trans:
                    new_trans_e = rail_trans.set_transition(new_trans_e, new_dir, mirror(new_dir), 1)
                else:
                    new_trans_e = 0
            else:
                # into existing rail
                new_trans_e = rail_trans.set_transition(new_trans_e, new_dir, new_dir, 1)
            grid_map.grid[end_pos] = new_trans_e

        current_dir = new_dir
    return path


def connect_straight_line_in_grid_map(grid_map: GridTransitionMap, start: IntVector2D,
                                      end: IntVector2D, rail_trans: RailEnvTransitions) -> IntVector2DArray:
    """
    Generates a straight rail line from start cell to end cell.
    Diagonal lines are not allowed
    :param rail_trans:
    :param grid_map:
    :param start: Cell coordinates for start of line
    :param end: Cell coordinates for end of line
    :return: A list of all cells in the path
    """

    if not (start[0] == end[0] or start[1] == end[1]):
        print("No straight line possible!")
        return []

    direction = direction_to_point(start, end)

    if direction is Grid4TransitionsEnum.NORTH or direction is Grid4TransitionsEnum.SOUTH:
        start_row = min(start[0], end[0])
        end_row = max(start[0], end[0]) + 1
        rows = np.arange(start_row, end_row)
        length = np.abs(end[0] - start[0]) + 1
        cols = np.repeat(start[1], length)

    else:  # Grid4TransitionsEnum.EAST or Grid4TransitionsEnum.WEST
        start_col = min(start[1], end[1])
        end_col = max(start[1], end[1]) + 1
        cols = np.arange(start_col, end_col)
        length = np.abs(end[1] - start[1]) + 1
        rows = np.repeat(start[0], length)

    path = list(zip(rows, cols))

    for cell in path:
        transition = grid_map.grid[cell]
        transition = rail_trans.set_transition(transition, direction, direction, 1)
        transition = rail_trans.set_transition(transition, mirror(direction), mirror(direction), 1)
        grid_map.grid[cell] = transition

    return path
