import datetime as datetime
from typing import List, Tuple
from conference_scheduler.resources.Room import Room
from conference_scheduler.resources.Presentation import Presentation


class Session:
    """
    A session is a set of slots
    """

    def __init__(self,
                 room: Room,
                 name: str,
                 starts_at: datetime.datetime,
                 ends_at: datetime.datetime,
                 ranges_preferred: List[Tuple[int, int]],
                 # list of durations in minutes (min, max), e.g. [(45, 45), (45, 45),(30, 45)]
                 ):
        """

        :param room: Room object
        :param starts_at: start time
        :param ends_at: end of availibilty, not neccessarily the end of the last slot
        :param ranges_preferred: list of tuples of (min, max) durations the session should be filled with
        """
        self.name = name
        self.room = room
        self.starts_at = starts_at
        self.day = datetime.datetime(self.starts_at.year, self.starts_at.month, self.starts_at.day)

        self.ends_at = ends_at
        self.capacity = room.capacity

        self._ranges_preferred = None
        self.slots_assigned = None  # slots in the session, ordered
        self.ranges_preferred = ranges_preferred

    def __repr__(self):
        return "{} {}-{} [{}]".format(self.room,
                                      self.starts_at.strftime('%a %d.%m %H:%M'),
                                      self.ends_at.strftime('%H:%M'),
                                      self.space_available)

    @property
    def duration(self):
        """
        :return: duration in minutes
        """
        return int((self.ends_at - self.starts_at).total_seconds() / 60)

    @property
    def minutes_available(self):
        """
        :return: minutes still available in this session
        """
        if not self.slots_available:
            return 0  # all slots are taken
        return sum([max(self.ranges_preferred[x]) for x in self.slots_available])

    @property
    def max_slot_duration_available(self):
        if not self.slots_available:
            return 0  # all slots are taken
        return max([max(self.ranges_preferred[x]) for x in self.slots_available])

    @property
    def min_slot_duration_available(self):
        if not self.slots_available:
            return 0  # all slots are taken
        return min([min(self.ranges_preferred[x]) for x in self.slots_available])

    @property
    def space_available(self):
        return len(self.ranges_preferred) > len([x for x in self.slots_assigned if x])

    @property
    def ranges_preferred(self):
        return self._ranges_preferred

    @ranges_preferred.setter
    def ranges_preferred(self, ranges_preferred):
        self._ranges_preferred = ranges_preferred
        self.slots_assigned = [None for x in self._ranges_preferred]

    @property
    def slots_available(self) -> List:
        """ returns list of free slot positions """
        if not self.space_available:
            return False
        return [i for i in range(len(self.slots_assigned)) if not self.slots_assigned[i]]

    @property
    def last_slot_ends_at(self):
        if not [x for x in self.slots_assigned if x]:
            return self.starts_at
        return max([slot.ends_at for slot in self.slots_assigned if slot])

    def add_presentation(self, presentation: Presentation, position: int):
        # print("slots =", [x.title for x in self.slots_assigned if x])
        # print("slots +", presentation.title)
        # print('-'*72)
        self.slots_assigned[position] = presentation
        return

    @property
    def presentation_start_times(self):
        start_times = []
        presentation_start_time = self.starts_at  # for handling slots without presentation assigned
        for i, presentation in enumerate(self.slots_assigned):
            if presentation:
                start_times.append(presentation.starts_at)
                presentation_start_time = presentation.ends_at  # next presenatations start time
            else:
                start_times.append(presentation_start_time)
                minutes = self.ranges_preferred[i - 1][1] if i > 0 else self.ranges_preferred[0][1]
                presentation_start_time = presentation_start_time + datetime.timedelta(
                    minutes=minutes)
        return start_times
