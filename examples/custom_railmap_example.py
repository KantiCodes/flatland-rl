import random
from typing import Any

import numpy as np

from flatland.core.grid.rail_env_grid import RailEnvTransitions
from flatland.core.transition_map import GridTransitionMap
from flatland.envs.rail_env import RailEnv
from flatland.envs.rail_generators import RailGenerator, RailGeneratorProduct
from flatland.envs.schedule_generators import ScheduleGenerator, ScheduleGeneratorProduct
from flatland.utils.rendertools import RenderTool

random.seed(100)
np.random.seed(100)


def custom_rail_generator() -> RailGenerator:
    def generator(width: int, height: int, num_agents: int = 0, num_resets: int = 0) -> RailGeneratorProduct:
        rail_trans = RailEnvTransitions()
        grid_map = GridTransitionMap(width=width, height=height, transitions=rail_trans)
        rail_array = grid_map.grid
        rail_array.fill(0)
        new_tran = rail_trans.set_transition(1, 1, 1, 1)
        print(new_tran)
        rail_array[0, 0] = new_tran
        rail_array[0, 1] = new_tran
        return grid_map, None

    return generator


def custom_schedule_generator() -> ScheduleGenerator:
    def generator(rail: GridTransitionMap, num_agents: int, hints: Any = None) -> ScheduleGeneratorProduct:
        agents_positions = []
        agents_direction = []
        agents_target = []
        speeds = []
        return agents_positions, agents_direction, agents_target, speeds

    return generator


env = RailEnv(width=6,
              height=4,
              rail_generator=custom_rail_generator(),
              number_of_agents=1)

env.reset()

env_renderer = RenderTool(env)
env_renderer.render_env(show=True)

input("Press Enter to continue...")
