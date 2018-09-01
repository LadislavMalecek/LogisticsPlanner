from world_descriptions import Package, City, World

class WorldLoader:
    def __init__(self, world):
        self.world = world

    def read_next_valid(self, file):
        line = None
        while line is None:
            line = file.readline()
            if str.startswith(line, '%'):
                line = None
        return line

    def load_world(self, file_path: str) -> None:
        file = open(file_path, "r")

        # loading cities
        num_of_cities = int(self.read_next_valid(file))
        self.create_cities(num_of_cities)

        # loading places
        num_of_places = int(self.read_next_valid(file))
        for place_id in range(num_of_places):
            city_id_in = int(self.read_next_valid(file))
            self.create_place(place_id, city_id_in)

        # loading airports
        for __ in range(num_of_cities):
            place_id_to_set_airport = int(self.read_next_valid(file))
            self.set_as_airport(place_id_to_set_airport)

        # loading trucks
        num_of_trucks = int(self.read_next_valid(file))
        for truck_id in range(num_of_trucks):
            trucks_place = int(self.read_next_valid(file))
            self.create_truck(trucks_place, truck_id)

        # loading airplanes
        num_of_planes = int(self.read_next_valid(file))
        for plane_id in range(num_of_planes):
            planes_place = int(self.read_next_valid(file))
            self.world.num_planes = planes_place
            self.create_plane(planes_place, plane_id)

        # loading packages
        num_of_packages = int(self.read_next_valid(file))
        for package_id in range(num_of_packages):
            line = self.read_next_valid(file).split()
            self.create_package(package_id, int(line[0]), int(line[1]))

        return self.world

    def create_cities(self, num_of_cities):
        self.world.cities = [City(i) for i in range(num_of_cities)]

    def create_place(self, place_id, city_id):
        self.world.cities[city_id].places_ids.append(place_id)
        self.world.places_to_city_ids[place_id] = city_id

    def set_as_airport(self, place_id):
        city_in = self.world.places_to_city_ids[place_id]
        self.world.cities[city_in].airport_place_id = place_id

    def create_truck(self, place_id, truck_id):
        city_in = self.world.places_to_city_ids[place_id]
        self.world.cities[city_in].trucks_ids.append(truck_id)
        self.world.trucks_starting_places_ids[truck_id] = place_id

    def create_plane(self, place_id, plane_id):
        self.world.planes_starting_places_ids[plane_id] = place_id

    def create_package(self, package_id, origin_place_id, destination_place_id):
        new_package = Package(package_id, origin_place_id,
                              destination_place_id)

        origin_city_id = self.world.places_to_city_ids[origin_place_id]
        destination_city_id = self.world.places_to_city_ids[destination_place_id]

        if origin_city_id is not destination_city_id:
            new_package.destination_place_phase1 = self.world.cities[origin_city_id].airport_place_id
            new_package.destination_place_phase2 = self.world.cities[
                destination_city_id].airport_place_id

        self.world.packages.append(new_package)
