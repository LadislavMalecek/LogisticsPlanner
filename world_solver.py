from world_descriptions import Package, City, World, WorldActionsPrices
from world_loader import WorldLoader
from world_states import SolverState, TransporterState, PlaceState

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


class WorldSolverStatesMem:
    class PricePriority:
        def __init__(self, price, seq_num):
            self.price = price
            self.seq_num = seq_num

        def __lt__(self, other):
            if self.price is not other.price:
                return self.price < other.price
            else:
                return self.seq_num < other.seq_num

    def __init__(self):
        self.solver_states_by_id = {}
        # no need for priority heap with decrease key, bcs all hops between places are in constant cost -> triangle inequality holds
        # self.solver_states_by_price_queue = queue.PriorityQueue()
        self.solver_states_by_price_queue = []

        # used to add to the real price to make it unique as a key to the priority queue
        # - then I dont have to implement comparation btw SolverStates when the prices are the same
        self.seq_num = 0

    def get_next_unique(self):
        self.seq_num += 1
        return self.seq_num

    def add(self, solver_state):
        state_id = solver_state.unique_solver_state_id
        already_seen: SolverState = self.solver_states_by_id.get(state_id)
        if already_seen is None:
            self.solver_states_by_id[solver_state.unique_solver_state_id] = solver_state

            queue_key = self.PricePriority(solver_state.price, self.get_next_unique())

            # self.solver_states_by_price_queue.put((solver_state.price, solver_state))
            heapq.heappush(self.solver_states_by_price_queue, (queue_key, solver_state))
            return True
        elif already_seen.price > solver_state.price:
            raise AssertionError(
                "This should have not happend! Need to use decreasable PQ, premise not valid.")
        else:
            # Item already added, and the already added items price is less as predicted
            return False

    def pop_min_by_price(self):
        # if self.solver_states_by_price_queue.empty():
        #     return None
        # return self.solver_states_by_price_queue.get()[1]

        if self.is_empty():
            return None
        return heapq.heappop(self.solver_states_by_price_queue)[1]

    def is_empty(self):
        return not self.solver_states_by_price_queue

    def get_all_states_by_id_dic(self):
        return self.solver_states_by_id


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
        mem = WorldSolverStatesMem()

        if first_state.is_final_for_phase(phase_number):
            self.update_states(first_state)
            print("% No search needed - all done")
            return
        mem.add(first_state)

        while not mem.is_empty():
            lowest_price_state = mem.pop_min_by_price()
            newStates = lowest_price_state.generate_all_neighbours()
            for state in newStates:
                if state.is_final_for_phase(phase_number):
                    print("% Found with price: " + str(state.price))
                    self.get_output(state, mem.get_all_states_by_id_dic())
                    self.update_states(state)
                    return
                mem.add(state)
        print("% Solution not found")

    def update_states(self, state):
        for transport_state in state.transports_states.values():
            if state.phase_number is 2:
                self.current_planes_states[transport_state.id] = transport_state
            else:
                self.current_trucks_states[transport_state.id] = transport_state
        
        for place_state in state.places_states.values():
            self.current_places_states[place_state.id] = place_state


    def get_output(self, last_state, unique_state_id_to_state):
        actions = []
        current_state = last_state
        while current_state is not None and current_state.action_from_previous is not None:
            actions.append(current_state.action_from_previous)
            current_state = unique_state_id_to_state.get(current_state.previous_unique_solver_state_id)
        actions.reverse()
        [print(action) for action in actions]