from world_descriptions import Package, City, World, WorldActionsPrices
from world_loader import WorldLoader
from world_states import SolverState, TransporterState, PlaceState
from priority_queue import PriorityQueue

# import queue
import heapq

# World solver uses simple search algorithms to try and find sequence of steps which will lead to good solution
# The algorithm has three phases (to split the computing requirement at bigger instances)
# 1. solve each city using only trucks, if the package's destination within the city then deliver it, else deliver it to the airport
# 2. deliver packages from airports to the destination cities using only planes
# 3. solve each city again using only trucks, all packages which needs to be delivered will be at the airport
# We can see that this aproach is pottentialy suboptimal, but it should not matter too much
# possitive thing is that we wont be needing the trucks in the second thing - therefore they will stay at the airports ready to be delivering
# and phases 1 and 3 are easily parrallelizable

class WorldSolverStatesSearch:
    def __init__(self):
        self.priority_queue = PriorityQueue()
        self.closed_set = set()
        self.debuging_list = []

    def search(self, start_state):
        self.priority_queue.add(start_state, start_state.price + start_state.get_heuristic_estimate())
        while not self.priority_queue.is_empty():
            current = self.priority_queue.pop()
            # print(f"retrieving: {current.price + current.heuristic_estimate}")
            # print(f"adding - g:{int(current.price)} - h:{int(current.heuristic_estimate)} - f: {int(current.price + current.heuristic_estimate)}")
            if current.is_final():
                return current

            self.closed_set.add(current)

            for neighbour in current.generate_all_neighbours():
                if neighbour in self.closed_set:
                    continue
                self.debuging_list.append(neighbour)
                heuristics = neighbour.get_heuristic_estimate()
                # if(heuristics + neighbour.price) < (current.heuristic_estimate + current.price):
                #     print("wtf")

                # print(f"adding - g:{neighbour.price} - h:{heuristics} - f: {neighbour.price + heuristics}")
                self.priority_queue.add(neighbour, neighbour.price + heuristics)

    def get_path(self, final_state):
        id_to_states = { state.unique_solver_state_id:state for state in list(self.closed_set) }
        states = [final_state]

        previous_id = states[-1].previous_unique_solver_state_id
        while previous_id is not None:
            state = id_to_states[previous_id]
            states.append(state)
            previous_id = states[-1].previous_unique_solver_state_id
        
        states.reverse()
        return states


class WorldSolver:
    def __init__(self, world: World):
        self.output = []
        self.world = world
        self.current_packages_places = {
            package.id: package.origin_place_id for package in self.world.packages }

        self.current_places_states = {}
        self.current_trucks_states = {}
        self.current_planes_states = {}

    def init_city_phase1(self, city_id):
        first_solver_state = SolverState(
            self.world, WorldActionsPrices(1), 1, city_id)
        city = self.world.cities[city_id]
        for truck_id in city.trucks_ids:
            new_transporter_state = TransporterState(
                truck_id, self.world.trucks_starting_places_ids[truck_id], [])
            first_solver_state.transports_states[new_transporter_state.id] = new_transporter_state

        for place_id in city.places_ids:
            packages_at_place = [
                package.id for package in self.world.packages if package.origin_place_id is place_id]
            new_place_state = PlaceState(
                place_id, self.world, packages_at_place)
            first_solver_state.places_states[new_place_state.id] = new_place_state

        first_solver_state.get_unique_id()

        return first_solver_state

    def init_world_phase2(self):
        first_solver_state = SolverState(
            self.world, WorldActionsPrices(2), 2, None)

        for plane_id in range(self.world.num_planes):

            new_transporter_state = TransporterState(
                plane_id, self.world.planes_starting_places_ids[plane_id], [])
            first_solver_state.transports_states[new_transporter_state.id] = new_transporter_state

        for place_id in [city.airport_place_id for city in self.world.cities]:
            place_state_from_phase1 = self.current_places_states[place_id]
            first_solver_state.places_states[place_state_from_phase1.id] = place_state_from_phase1

        first_solver_state.get_unique_id()

        return first_solver_state

    def init_city_phase3(self, city_id):
        first_solver_state = SolverState(
            self.world, WorldActionsPrices(3), 3, city_id)
        city = self.world.cities[city_id]
        for truck_id in city.trucks_ids:
            truck_state_from_phase1 = self.current_trucks_states[truck_id]
            first_solver_state.transports_states[truck_state_from_phase1.id] = truck_state_from_phase1

        for place_id in city.places_ids:
            place_state_from_phase2 = self.current_places_states[place_id]
            first_solver_state.places_states[place_state_from_phase2.id] = place_state_from_phase2

        first_solver_state.get_unique_id()

        return first_solver_state

    def solve_phase1(self):
        for city in self.world.cities:
            first_state = self.init_city_phase1(city.id)
            self.solve_phase(1, first_state)
        print("% phase1 done")

    def solve_phase2(self):
        first_state = self.init_world_phase2()
        self.solve_phase(2, first_state)
        print("% phase2 done")

    def solve_phase3(self):
        for city in self.world.cities:
            first_state = self.init_city_phase3(city.id)
            self.solve_phase(3, first_state)
        print("% phase3 done")
    

    def solve_phase(self, phase_number, first_state):
        searcher = WorldSolverStatesSearch()

        final_state = searcher.search(first_state)
        if final_state is None:
            print("%No solution found")
            return

        self.update_states(final_state)
        
        if final_state == first_state:
            print("%No search needed")
            return

        path = searcher.get_path(final_state)
        self.get_output(path)


    def update_states(self, state):
        for transport_state in state.transports_states.values():
            if state.phase_number is 2:
                self.current_planes_states[transport_state.id] = transport_state
            else:
                self.current_trucks_states[transport_state.id] = transport_state
        
        for place_state in state.places_states.values():
            self.current_places_states[place_state.id] = place_state


    def get_output(self, path):
        [print(state.action_from_previous) for state in path if state.action_from_previous is not None]