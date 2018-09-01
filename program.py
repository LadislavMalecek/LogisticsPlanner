from world_descriptions import World
from world_loader import WorldLoader
from world_solver import WorldSolver

new_world = World()
WorldLoader(new_world).load_world("/home/alby/pythonai1/test_input.txt")
print("% Loading done!")

solver = WorldSolver(new_world)
solver.solve_phase1()
solver.solve_phase2()
solver.solve_phase3()

