from world_descriptions import World
from world_loader import WorldLoader
from world_solver import WorldSolver

new_world = World()
WorldLoader(new_world).load_world("/home/alby/pythonai1/test_input.txt")
print("Loading done!")

solver = WorldSolver(new_world)
init_state_0 = solver.init_city_phase1(0)
states0 = init_state_0.generate_all_neighbours()


init_state_1 = solver.init_city_phase1(1)
states1 = init_state_1.generate_all_neighbours()

print("States initialized")