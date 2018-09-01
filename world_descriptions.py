class Package:
    def __init__(self, package_id, orig_place_id, dest_place_id):
        self.id = package_id

        self.origin_place_id = orig_place_id
        self.destination_place_id = dest_place_id

        self.destination_place_phase1 = None  # airport in the city if out
        self.destination_place_phase2 = None  # airport in dest city

        self.destination_place_phase3 = self.destination_place_id

    def get_destination(self, phase: int) -> int:
        if phase is 1:
            return self.destination_place_phase1
        if phase is 2:
            return self.destination_place_phase2
        if phase is 3:
            return self.destination_place_phase3
        raise AttributeError(f"Invalid phase:'{phase}', only 1-3 supported")

    def __repr__(self):
        return f"Package, id: {self.id}, FromPlaceId: {self.origin_place_id}, ToPlaceId: {self.destination_place_id}"

    def __str__(self):
        return self.__repr__()


class City:
    def __init__(self, obj_id: int):
        self.id = obj_id

        self.places_ids = []
        self.trucks_ids = []

        self.airport_place_id = None

    def __repr__(self):
        return "City, id: {self.id}, #places: '{", ".join(self.places_ids)}', #trucks: {", ".join(self.trucks_ids)}"

    def __str__(self):
        return self.__repr__()

class World:
    def __init__(self):
        self.packages = []
        self.num_planes = 0
        self.planes_starting_places_ids = {}
        self.trucks_starting_places_ids = {}
        self.cities = []

        self.places_to_city_ids = {}

    # def load(self, file_path: str):
    #     WorldLoader(self).load_world(file_path)

    def __repr__(self):
        return f"World, #cities: {len(self.cities)}, #planes: {self.num_planes}, #packages: {len(self.packages)}"

    def __str__(self):
        return self.__repr__()

    def get_starting_solver_state_phase1(self):
        pass

class WorldActionsPrices:
    def __init__(self, phase: int):
        self.phase = phase

    def get_unload_price(self):
        if(self.phase is 2):
            return 11
        return 2

    def get_load_price(self):
        if(self.phase is 2):
            return 14
        return 2

    def get_move_price(self):
        if(self.phase is 2):
            return 1000
        return 17