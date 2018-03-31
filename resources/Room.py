class Room:
    """

    """

    def __init__(self,
                 name: str,
                 capacity: int):
        self.name = name
        self._capacity = capacity

    @property
    def capacity(self):
        return self._capacity

    @capacity.setter
    def capacity(self, capacity):
        self._capacity = capacity
