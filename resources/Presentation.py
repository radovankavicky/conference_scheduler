import json
import datetime as datetime
from typing import List, Set


# optional norlize talk types
types = {
    'h_180': 'help desk',
    'h': 'help desk', # 2015
    'r_180': 'training',
    't': 'training', # 2015
    't_30': 'talk 30 Min',
    't_45': 'talk 45 Min',
    't_60': 'talk 60 Min',
    's': 'talk 30+45 Min', # 2015
    'i_60': 'interactive',
    'p_180': 'poster',
    'p': 'poster'}

talk_schedule_types = ['t_30', 't_45', 't_60',
                       'i_60',
                       'n_60', 'n_90',
                       'r_180']


class Presentation:
    def __init__(self,
                 speaker_ids: List[int],
                 presentation_id: int,
                 title: str,
                 interest: int,
                 tags: Set[str],
                 category: Set[str],
                 duration: int,
                 frozen: bool=False,
                 track: str=None,
                 session_type: str=None,
                 admin_type: str=None,
                 level: str=None,
                 ):

        self.speaker_id = speaker_ids
        self.presentation_id = presentation_id
        self.title = title
        self.interest = interest
        self.tags = tags
        self.category = category
        self.track = track      # pydata etc
        self.duration = duration
        self.frozen = frozen
        self.session_type = session_type
        self.admin_type = admin_type
        self.level = level

        self._starts_at = None
        self._ends_at = None

        self.idx = 0

    def __gt__(self, other):
        return self.title > other

    def __lt__(self, other):
        return self.title < other

    def __eq__(self, other):
        return self.title == other

    def __iter__(self):
        return self

    def __next__(self):
        if self.idx:
            self.idx = 0
            raise StopIteration
        self.idx += 1
        return self.presentation_id, self.title

    def __repr__(self):
        return "{}: {} [{}][{}]".format(self.presentation_id, self.title, self.duration, ', '.join(list(self.track)))

    @property
    def starts_at(self):
        return self._starts_at

    @property
    def ends_at(self):
        return self._ends_at

    @starts_at.setter
    def starts_at(self, starts_at: datetime.datetime):
        if self.frozen:
            raise AssertionError("This presentation is frozen, unfreeze to set a new start time")
        self._starts_at = starts_at
        self._ends_at = starts_at + datetime.timedelta(minutes=self.duration)
