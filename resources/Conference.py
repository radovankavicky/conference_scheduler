import sqlite3
import datetime
import itertools
from typing import List, Tuple
import pandas as pd
from conference_scheduler.resources.Speaker import Speaker
from conference_scheduler.resources.Presentation import Presentation
from conference_scheduler.resources.Schedule import Schedule


class Conference:
    """
    super basic class, currently only:
     * setting time frame of core conference
     * create speaker objects
     * create presentation objects
    
    """

    def __init__(self,
                 starts_at: datetime.datetime,
                 ends_at: datetime.datetime,
                 dbpath: str = None,
                 conference_key: str = None
                 ):
        """
        
        :param starts_at: 
        :param ends_at: 
        :param dbpath: path to a local db if you want to read form the database
        :param conference_key: key used in db, e.g. 'ep2017'
        """
        self.starts_at = starts_at
        self.ends_at = ends_at

        self.dbpath = dbpath
        self.conference_key = conference_key

        self.accepted = pd.DataFrame()  # one row per speaker - talk. 1 talk with 2 speakers = 2 rows!
        self.presentations_to_schedule = {}  # all session objects to schedule
        self.presentations_scheduled = {}  # all session objects to schedule
        self.conference_speakers = {}  # all speaker_ids
        self.rooms = set([])  # all rooms, used for capacity management

        self.schedule = Schedule()

    def get_accepted_presentations(self):
        """
        Get all accepted sessions from database or other source
        The result is expected to be returned in a pandas dataframe with e.g. the follwoing columns:
            id
            title
            status
            duration
            presenter_id / names
        :returns pandas DataFrame
        """

        raise NotImplementedError

    def get_tags_from_db(self):
        """
        Optional helper function - not implemented
        Get a list of tags to match tag_id  to a tag text
        :return:
        """
        return []

    @classmethod
    def normalize_votes(cls, votes):
        """
        Optional helper function - not implemented
        :return:
        """
        return votes

    def get_interest_indication_via_voting(self):
        """
        Optional helper function - not implemented
        Extrapolate general interest from user voted for a session count
        :return: dict {talk_id: interest}
        """
        return {x: 100 for x in self.accepted['talk_id']}

    def create_presenters(self):
        """
        Create unique presenters from accepted submissions information
        :return:
        """
        for index, row in self.accepted.iterrows():
            speaker = Speaker(
                name="{} {}".format(row['first_name'], row['last_name']),
                speaker_id=row['speaker_id'],
                conference=self
            )
            if row['speaker_id'] in self.speaker_ids:
                continue
            self.conference_speakers[row['speaker_id']] = speaker

    @property
    def speaker_ids(self):
        return self.conference_speakers.keys()

    def create_presentationslist(self):
        # config
        tracks = ['Business Track', 'Developing with Python', 'Django Track', 'Educational Track',
                  'Hardware/IoT Track', 'Science Track', 'Web Track']
        # get all tags from db
        _tags = self.get_tags(tracks)
        _interest = self.get_interest_indication_via_voting()

        for index, row in self.accepted.iterrows():
            if row['id'] in self.presentation_ids:
                continue
            if row['type'] in ['p_180', 'h_180']:  # skip poster / helpdesks
                continue
            if row['admin_type'] == 'k':  # skip keynotes
                continue
            track = _tags.get(row['id'], {}).get('track', set([]))
            # add sub_community to track
            if row['sub_community']:
                track.add(row['sub_community'])
            presentation = Presentation(
                speaker_ids=self.accepted[self.accepted['id'] == row['id']]['speaker_id'].tolist(),
                presentation_id=row['id'],
                title=row['title'],
                interest=_interest.get(row['id'], 0),
                tags=_tags.get(row['id'], {}).get('name', []),
                category=_tags.get(row['id'], {}).get('category', []),
                duration=row['duration'],
                track=track,
                session_type=row['type'],
                admin_type=row['admin_type'],
                level=row['level'],
            )
            self.presentations_to_schedule[row['id']] = presentation

    def get_tags(self):
        """
        Optional helper function - not implemented
        Can be used for normalisation of user generated tags, i.e. Data Science -> Data-Science
        :return: dict {talk_id: interest}
        """
        tags = self.get_tags_from_db()  # note: returns a pandas DataFrame here
        # normalize here
        return {}

    @property
    def presentation_ids(self):
        return self.presentations_to_schedule.keys()

    @property
    def conference_days(self):
        return [self.starts_at.date() + datetime.timedelta(days=i) for i in
                range((self.ends_at - self.starts_at).days + 1)]

    def get_speaker(self, speaker_id):
        for speaker in self.conference_speakers:
            if speaker.speaker_id == speaker_id:
                return speaker

    def set_speaker_departure(self, speaker_id: int, date_time: datetime.datetime):
        if speaker_id in self.conference_speakers:
            self.conference_speakers[speaker_id].conference_departure_at(date_time)

    def set_speaker_arrival(self, speaker_id: int, date_time: datetime.datetime):
        if speaker_id in self.conference_speakers:
            self.conference_speakers[speaker_id].conference_arrival_at(date_time)

    def get_most_popular(self, n) -> List[int]:
        """ return n most popular by voting, used to init the schedule """
        mplist = [x[0] for x in sorted(
            list(self.presentations_to_schedule.items()), key=lambda x: x[1].interest, reverse=True)]
        return mplist[:n]

    def assign_presentation_to_session(self, talk_id: int,
                                       room_name: List = None,
                                       starts_at: datetime.datetime = None,
                                       ends_at: datetime.datetime = None,
                                       best_match: bool = True,
                                       min_similarity_value: int = 0,
                                       ):
        if talk_id not in self.presentations_to_schedule:
            return
        if not room_name:
            room_name = []
        presentation = self.presentations_to_schedule[talk_id]
        unavailable = list(itertools.chain.from_iterable(
            [self.conference_speakers[s].not_assignable for s in self.conference_speakers if
             s in presentation.speaker_id]))
        if best_match:
            # clustering preferrred
            pres_assigned, session = self.schedule.assign_to_best_session(presentation,
                                                                          unavailable=unavailable,
                                                                          room_name=room_name,
                                                                          starts_at=starts_at,
                                                                          ends_at=ends_at,
                                                                          min_similarity_value=min_similarity_value)
        else:
            # spreading, only random clustering
            pres_assigned, session = self.schedule.assign_to_session(presentation,
                                                                     room_name=room_name,
                                                                     starts_at=starts_at,
                                                                     ends_at=ends_at,
                                                                     unavailable=unavailable)
        if pres_assigned:
            self.presentations_scheduled[talk_id] = presentation
            for speaker_id in presentation.speaker_id:
                self.conference_speakers[speaker_id].speaker_is_occupied(session)
            del self.presentations_to_schedule[talk_id]
            return True
