from world_descriptions import Package, City, World, WorldActionsPrices
from world_loader import WorldLoader

# World solver uses simple search algorithms to try and find sequence of steps which will lead to good solution
# The algorithm has three phases (to split the computing requirement at bigger instances)
# 1. solve each city using only trucks, if the package's destination within the city then deliver it, else deliver it to the airport
# 2. deliver packages from airports to the destination cities using only planes
# 3. solve each city again using only trucks, all packages which needs to be delivered will be at the airport
# We can see that this aproach is pottentialy suboptimal, but it should not matter too much
# possitive thing is that we wont be needing the trucks in the second thing - therefore they will stay at the airports ready to be delivering
# and phases 1 and 3 are easily parrallelizable


class WorldSolver:
    def __init__(self, world: World):
        self.world = world
        self.current_packages_places = {
            package.id: package.origin_place_id for package in self.world.packages}

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

    # This phase will
    def solve_city_phase1(self, city_id):
        action_prices = WorldActionsPrices(1)
        pass


class TransporterState:
    def __init__(self, id, current_place_id, current_packages_ids):
        self.id = id
        self.current_place_id = current_place_id
        self.current_packages_ids = set(current_packages_ids)

    def get_id_string(self):
        packages_ids = '-'.join(sorted([str(i) for i in self.current_packages_ids]))
        return f"(t{self.id},{self.current_place_id}:{packages_ids})"

    def get_copy(self):
        new_transport_state = TransporterState(
            self.id, self.current_place_id, list(self.current_packages_ids))
        return new_transport_state

    def is_empty(self):
        return len(self.current_packages_ids)


class PlaceState:
    def __init__(self, id: int, world: World, current_packages_ids):
        self.id = id
        self.world = world
        self.current_packages_ids = set(current_packages_ids)

    def get_id_string(self):
        packages_ids = '-'.join(sorted([str(i) for i in self.current_packages_ids]))
        return f"(p{self.id}:{packages_ids})"

    def get_copy(self):
        new_place_state = PlaceState(
            self.id, self.world, list(self.current_packages_ids))
        return new_place_state

    def no_package_misplaced(self, phase: int):
        no_package_missplaced = all([self.world.packages[package_id].get_destination(
            phase) is self.id for package_id in self.current_packages_ids])
        return no_package_missplaced


class SolverState:
    def __init__(self, world: World, action_prices: WorldActionsPrices, phase_num: int, city_id: int):
        # used tp quickly search through already visited states
        self.unique_solver_state_id = None
        self.previous_unique_solver_state_id = None

        self.price = 0

        self.transports_states = {}
        self.places_states = {}

        self.phase_number = phase_num
        self.city_id = city_id

        self.world = world
        self.action_prices = action_prices

    def get_unique_id(self):
        transports_id = ','.join([state.get_id_string()
                                  for state in self.transports_states.values()])
        places_id = ','.join([state.get_id_string()
                              for state in self.places_states.values()])
        self.unique_solver_state_id = f"t:{transports_id} || p:{places_id}"
        return self.unique_solver_state_id

    def __repr__(self):
        return self.unique_solver_state_id

    def __str__(self):
        return self.__repr__()

    def get_copy(self):
        new_copy = SolverState(
            self.world, self.action_prices, self.phase_number, self.city_id)
        new_copy.price = self.price
        new_copy.transports_states = {
            state.id: state.get_copy() for state in self.transports_states.values()}
        new_copy.places_states = {state.id: state.get_copy()
                                  for state in self.places_states.values()}
        new_copy.unique_solver_state_id = self.unique_solver_state_id
        new_copy.previous_unique_solver_state_id = self.unique_solver_state_id
        return new_copy

    def is_final_for_phase(self, phase_number: int):
        # possible optimalization would be to generate the final state once and check againts the its unique_state_id
        all_transports_empty = all([transport.is_empty()
                                    for transport in self.transports_states.values()])
        if not all_transports_empty:
            return False

        all_packages_in_destination = all([place.no_package_misplaced(
            phase_number) for place in self.places_states.values()])
        # no need to check all_transports_empty it is true at this point
        return all_packages_in_destination

    def generate_all_neighbours(self):
        neighbours = []
        neighbours.extend(self.get_unload_neigbours())
        neighbours.extend(self.get_load_neigbours())
        neighbours.extend(self.get_move_neighbours())
        return neighbours

    def get_move_neighbours(self):
        neighbours = []
        for transport_id, transport in self.transports_states.items():
            for place in self.places_states.values():
                if place.id == transport.current_place_id:
                    continue
                neighbours.append(self.get_neighbour_move(transport_id, place.id))
        return neighbours

    def get_neighbour_move(self, transport_id, destination_place_id):
        new: SolverState = self.get_copy()
        new.transports_states[transport_id].current_place_id = destination_place_id
        new.price += self.action_prices.get_move_price()
        new.get_unique_id()
        return new

    def get_unload_neigbours(self):
        neighbours = []
        for transport_id, transport in self.transports_states.items():
            for package_id in transport.current_packages_ids:
                neighbours.append(self.get_neighbour_unload(
                    transport_id, package_id, transport.current_place_id))
        return neighbours

    def get_neighbour_unload(self, transport_id, package_id, place_id):
        new: SolverState = self.get_copy()
        new.transports_states[transport_id].current_packages_ids.pop(
            package_id)
        new.places_states[place_id].current_packages_ids.add(package_id)
        new.price += self.action_prices.get_unload_price
        new.get_unique_id()
        return new

    def get_load_neigbours(self):
        neighbours = []
        for transport_id, transport in self.transports_states.items():
            place = self.places_states[transport.current_place_id]
            for package_id in place.current_packages_ids:

                packages_destination = self.world.packages[package_id].get_destination(
                    self.phase_number)
                if packages_destination is place.id:
                    # already at place
                    continue

                neighbours.append(self.get_neighbour_load(
                    transport_id, package_id, transport.current_place_id))
        return neighbours

    def get_neighbour_load(self, transport_id, package_id, place_id):
        new: SolverState = self.get_copy()
        new.transports_states[transport_id].current_packages_ids.add(
            package_id)
        new.places_states[place_id].current_packages_ids.pop(package_id)
        new.price += self.action_prices.get_load_price
        new.get_unique_id()
        return new
