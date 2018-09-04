import heapq

class PriorityQueue:
    class PQPriority:
            # used to add to the real price to make it unique as a key to the priority queue
            # - then I dont have to implement comparation btw SolverStates when the prices are the same
            _seq_num = 0
            def __init__(self, priority):
                self.priority = priority
                self.seq_num = type(self)._seq_num
                type(self)._seq_num += 1

            def __lt__(self, other):
                if self.priority is not other.priority:
                    return self.priority < other.priority
                else:
                    return self.seq_num < other.seq_num

    class PQItem:
        def __init__(self, value, priority):
            self.value = value
            self.priority = priority
            self.is_mark_as_deleted = False

        def mark_deleted(self):
            self.is_mark_as_deleted = True
        
        def is_valid(self):
            return not self.is_mark_as_deleted

    def __init__(self):
        self.PQstore = []
        self.item_set = {}
        self.valid_count = 0

    def add(self, item, priority):
        item_already_in = self.item_set.get(item)
        if item_already_in is not None:
            if item_already_in.priority <= priority:
                # print("q: item adding with higher f - ignore")
                # do nothing, same value with smaller priority is already in PQ
                return
            else:
                # print("q: item adding with lower f - replace")
                item_already_in.mark_deleted()
                self.valid_count -= 1
        
        key = self.PQPriority(priority)
        value = self.PQItem(item, priority)
        heapq.heappush(self.PQstore, (key, value))
        self.item_set[item] = value
        self.valid_count += 1
    
    def pop(self):
        while self.PQstore:
            item = heapq.heappop(self.PQstore)[1]
            if item.is_valid():
                self.valid_count -= 1
                self.item_set.pop(item.value)
                return item.value
        return None

    def is_empty(self):
        return self.valid_count <= 0