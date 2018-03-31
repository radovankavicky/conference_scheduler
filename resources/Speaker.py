import datetime as datetime
from typing import List, Tuple

try:
    from conference_scheduler.resources.Session import Session
except ImportError:
    # noinspection PyUnresolvedReferences
    from resources.Resources import Session


class Speaker:

    def __init__(self,
                 name: str,
                 speaker_id: int,
                 conference: object,  # Conference, cannot be used here yet
                 unavailable: List[Tuple[datetime.datetime, datetime.datetime]]=None):
        """
        Manage speaker availibity and check for overlaps
        :param name: 
        :param speaker_id: 
        :param conference: 
        :param unavailable: use only for times the speaker is not present at the confernce, 
        for session assignments use occupied
        """
        self.name = name
        self.speaker_id = speaker_id
        self.conference = conference
        if not unavailable:
            unavailable = []
        self.unavailable = unavailable

        self.occupied = []

        self.idx = 0

    def __repr__(self):
        return self.name

    def __gt__(self, other):
        return self.name > other

    def __lt__(self, other):
        return self.name < other

    def __eq__(self, other):
        return self.name == other

    def __iter__(self):
        return self

    def __next__(self):
        if self.idx:
            self.idx = 0
            raise StopIteration
        self.idx += 1
        return self.speaker_id, self.name

    def add_not_available(self, start: datetime.datetime=None, end: datetime.datetime=None):
        """
        Person is not avaialable with this timeframe
        :param start: 
        :param end: 
        :return: 
        """
        if not start and not end:
            return
        elif start and not end:
            end = self.conference.ends_at
        elif end and not start:
            start = self.conference.starts_at
        self.unavailable.append((start, end))

    def conference_departure_at(self, date_time: datetime.datetime):
        """ wrapper for readbility / convenience """
        self.add_not_available(start=date_time)

    def conference_arrival_at(self, date_time: datetime.datetime):
        """ wrapper for readbility / convenience """
        self.add_not_available(end=date_time)

    def check_availibity(self, starts_at: datetime.datetime, ends_at: datetime.datetime):
        """ return if person is available in the timeframe """
        for unavailable in self.unavailable:
            if unavailable[0] <= starts_at <= unavailable[1]:
                return False
            if unavailable[0] <= ends_at <= unavailable[1]:
                return False
        return True

    @property
    def not_assignable(self):
        """ return list of unavailable and occupied with other sessions """
        return self.unavailable + self.occupied

    def speaker_is_occupied(self, session):
        """
        block a whole Session rather than just a slot in a session
        Unlikely (+genarally unwanted) the same speaker is giving two talks in a row or closeby each other
        might conflict
        :return:
        """
        self.occupied.append((session.starts_at, session.ends_at))
