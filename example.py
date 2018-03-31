import datetime
import os
import random
import json
from operator import itemgetter
from typing import List
from conference_scheduler.resources.Conference import Conference
from conference_scheduler.resources.Room import Room
from conference_scheduler.resources.Session import Session
from conference_scheduler.resources.Presentation import talk_schedule_types
from conference_scheduler.resources.Speaker import Speaker
import pickle
import itertools
import pandas as pd





class ConferenceKA(Conference):
    def get_accepted_presentations(self):
        data = pd.read_json(self.dbpath)
        data['conference'] = 'pyconDE2017'
        data['admin_type'] = ''

        def map_talks_to_duration(talk_format):
            d = {
                'Talk (45 minutes)': 45,
                'Talk (30 minutes)': 30,
                'Workshop (60-90 minutes)': 75,
                'Poster': 0,
                 }
            return d[talk_format]
        data['duration'] = data['talk_format'].map(lambda x: map_talks_to_duration(x))
        data['speaker_id'] = data['name'].map(lambda x: ''.join([y.lower() for y in x if y.isalpha()]))
        data['sub_community'] = ''
        data['slug'] = ''
        data['id'] = data['url'].map(lambda x: x.split('/')[-1])

        # t.id, t.title, t.conference, t.type, t.level, t.slug, t.status, t.admin_type, t.duration, s.speaker_id,
        # u.first_name, u.last_name, p.sub_community
        self.accepted = data[[
            'id', 'title', 'conference', 'talk_format', 'audience_level', 'slug', 'state', 'admin_type',
            'duration', 'speaker_id', 'name', 'sub_community', 'rating'
        ]]
        self.accepted.rename(columns={
            'talk_format': 'type',
            'audience_level': 'level',
            'state': 'status',
        }, inplace=True)

    def get_tags_from_db(self):
        # i.object_id, i.tag_id, c.name, c.category, t.conference, t.title
        mapping = {
            '3d cameras': 'Programming',
            'Debian': 'DevOps',
            'Linux': 'DevOps',
            'Networking': 'DevOps',
            'SDN': 'DevOps',
            'SaltStack': 'DevOps',
            'Start-up': 'Business Track',
            'ai': 'Data Science',
            'algorithm': 'Data Science',
            'algorithms': 'Data Science',
            'analysis': 'Data Science',
            'analytics': 'Data Science',
            'apache': '',
            'api': 'DevOps',
            'arrow': 'Data Science',
            'autonomous-driving': 'Data Science',
            'backup': 'DevOps',
            'bestpractices': '',
            'business': 'Business Track',
            'c': '',
            'chatbot': 'Data Science',
            'cli': '',
            'code smell': 'Programming',
            'code-introspection': 'Programming',
            'compilation': 'Programming',
            'complexity': 'Programming',
            'crypto': 'Programming',
            'cython': '',
            'data': 'Data Science',
            'data modelling': 'Data Science',
            'data pipeline': 'Data Science',
            'data science': 'Data Science',
            'data structures': 'Data Science',
            'data-extraction': 'Data Science',
            'data-science': 'Data Science',
            'data-wrangling': 'Data Science',
            'database': 'Data Science',
            'deep learning': 'Data Science',
            'deeplearning': 'Data Science',
            'DevOps': 'DevOps',
            'django': 'Web',
            'e-commerce': 'Web',
            'editor': '',
            'etl': 'Programming',
            'facebook': 'Web',
            'fasttext': '',
            'finance': 'Business Track',
            'gesture control': '',
            'gis': '',
            'hadoop': 'Data Science',
            'hardware': '',
            'ide': 'Programming',
            'infrasturcture': 'DevOps',
            'iot': 'Programming',
            'jupyter': 'Data Science',
            'jupyterhub': 'Data Science',
            'knowledge-management': '',
            'machine learning': 'Data Science',
            'machine-learning': 'Data Science',
            'machinelearning': 'Data Science',
            'mathematics': '',
            'micropython': 'Programming',
            'natural language': 'Data Science',
            'naturallanguageprocessing': 'Data Science',
            'neovim': 'Programming',
            'netdevops': 'DevOps',
            'netops': 'DevOps',
            'networkx': 'Data Science',
            'neural networks': 'Data Science',
            'nlp': 'Data Science',
            'numpy': 'Data Science',
            'open source': 'Programming',
            'optimisation': 'Programming',
            'out-of-core analytics': 'Data Science',
            'pandas': 'Data Science',
            'parquet': 'Data Science',
            'parser': 'Programming',
            'performance': '',
            'physics': '',
            'pipeline': '',
            'Data Science': 'Data Science',
            'python': 'Programming',
            'python3': 'Programming',
            'pytorch': 'Data Science',
            'railsgirls': '',
            'refactoring': 'Programming',
            'robotics': 'Programming',
            'science': 'Data Science',
            'scikit-learn': 'Data Science',
            'search': '',
            'skipgram': '',
            'solr': '',
            'solrcloud': '',
            'space': '',
            'sympy': '',
            'system design': 'DevOps',
            'telepresence': '',
            'tensorflow': 'Data Science',
            'time series': 'Data Science',
            'tokenizer': '',
            'torch': '',
            'use-case': '',
            'vim': '',
            'visualization': 'Data Science',
            'vr': 'Programming',
            'web': 'Web',
            'wordvector': 'Data Science',
            'workflow': '',

        }
        df = pd.read_json(self.dbpath)
        tags = df[['tags', 'url']]
        tags.index = df['url'].map(lambda x: x.split('/')[-1])
        tagseries = tags.apply(lambda x: pd.Series(x['tags']), axis=1).stack().reset_index(level=1, drop=True)
        tags = pd.DataFrame({'name': tagseries, 'object_id': tagseries.index})
        tags.colums = ['name', 'object_id']
        tags.reindex()
        tags['tag_id'] = ''
        tags['category'] = tags['name'].map(lambda x: mapping.get(x, 'Other'))
        tags['conference'] = 'pyconDE2017'
        tags['title'] = ''
        return tags

    def get_interest_indication_via_voting(self):
        pass

    def create_presenters(self):
        for index, row in self.accepted.iterrows():
            speaker = Speaker(
                name=row['name'],
                speaker_id=row['speaker_id'],
                conference=self
            )
            if row['speaker_id'] in self.speaker_ids:
                continue
            self.conference_speakers[row['speaker_id']] = speaker

    def get_interest_indication_via_voting(self):
        return {x[0]: x[1] for x in self.accepted[['id', 'rating']].to_records(index=False)}

    def set_speaker_departure(self, speaker_id: str, date_time: datetime.datetime):
        super(ConferenceKA, self).set_speaker_departure(speaker_id, date_time)



pycon = ConferenceKA(
    starts_at=datetime.datetime(2017, 10, 25, 10, 0),
    ends_at=datetime.datetime(2017, 10, 27, 16, 1),
    dbpath='/Users/hendorf/Desktop/pyconDE/pycon/talks/speakers_accepted.json',
    conference_key=''  # key used in database to indentify conference's submissions
)

pycon.get_accepted_presentations()
pycon.create_presenters()
pycon.create_presentationslist()

# rooms and capacities
# set this for the current conference
rooms = {
    'Medientheater': 280,
    'Vortragsaal': 90,
    'Media-Lounge': 30,
    'Trainings': 30,
}

for r in rooms:
    pycon.rooms.add(
        Room(r, rooms[r])
    )


# create schedule


def training_rooms() -> List:
    return [rm for rm in pycon.rooms if rm.name in {'Trainings'}]


def training_room_names(random_order: bool = True) -> List:
    """ return training room names in (random) order """
    names = ['Trainings']
    if random_order:
        random.shuffle(names)
    return names


def talk_rooms() -> List:
    return [rm for rm in pycon.rooms if rm.name not in {'Trainings'}]


def talk_room_names(random_order: bool = True) -> List:
    """ return talk room names in (random) order """
    names = [rm.name for rm in pycon.rooms if rm.name not in training_room_names(random_order=False)]
    if random_order:
        random.shuffle(names)
    return names


# hardcode sessions: create a very specific session where standart rules do not apply:
# eg.: patterns does not fit slot (e.g. 90 minutes)
# eg.: create a session with pattern in a room and assign a spectifc session to it below as for EPS general assembly
# nothing to do here

def create_session(conf, _name, _room, _day, _start, _end, ranges_preferred):
    """ helper func """
    conf.schedule.create_session(
        Session(
            name=_name,
            room=_room,
            starts_at=datetime.datetime(_day.year, _day.month, _day.day) + _start,
            ends_at=datetime.datetime(_day.year, _day.month, _day.day) + _end,
            ranges_preferred=ranges_preferred,
        ))


# morning patterns: 30/45 and 45/30/30 minute slots
# morning sessions Wednesday
name = "morning"
start = datetime.timedelta(hours=11, minutes=30)
end = datetime.timedelta(hours=12, minutes=35)
ranges = [[(45, 45), (30, 30)]] * 3

for day in pycon.conference_days[:1]:
    _rooms = talk_rooms()
    random.shuffle(list(_rooms))
    for i, room in enumerate(_rooms):
        create_session(pycon, name, room, day, start, end, ranges[i])

# morning sessions Thursday+Friday
start = datetime.timedelta(hours=10, minutes=30)
end = datetime.timedelta(hours=12, minutes=10)
ranges = [[(45, 45), (30, 30), (30, 30)]] * 3

for day in pycon.conference_days[1:]:
    _rooms = talk_rooms()
    random.shuffle(list(_rooms))
    for i, room in enumerate(_rooms):
        create_session(pycon, name, room, day, start, end, ranges[i])

# after lunch sessions
# patterns: 45/30
name = "after lunch"
start = datetime.timedelta(hours=14, minutes=0)
end = datetime.timedelta(hours=15, minutes=30)
ranges = [[(45, 45), (30, 30)]] * 3

for day in pycon.conference_days:
    _rooms = talk_rooms()
    random.shuffle(list(_rooms))
    for i, room in enumerate(_rooms):
        create_session(pycon, name, room, day, start, end, ranges[i])

# afternoon sessions
# patterns: 30/30
name = "afternoon"
start = datetime.timedelta(hours=16, minutes=00)
end = datetime.timedelta(hours=16, minutes=50)
ranges = [[(30, 30), (30, 30)]] * 3

# only on Wed + Thu
for day in pycon.conference_days[:2]:
    _rooms = talk_rooms()
    random.shuffle(list(_rooms))
    for i, room in enumerate(_rooms):
        create_session(pycon, name, room, day, start, end, ranges[i])

# trainings
name = "training"
fixedrange = [(75, 90)]
for day in pycon.conference_days[:1]:
    _rooms = training_rooms()
    for room in _rooms:
        for start, end in [
            (datetime.timedelta(hours=11, minutes=30), datetime.timedelta(hours=12, minutes=45)),
            (datetime.timedelta(hours=14, minutes=0), datetime.timedelta(hours=15, minutes=15)),
            (datetime.timedelta(hours=16, minutes=0), datetime.timedelta(hours=17, minutes=15))
        ]:
            create_session(pycon, name, room, day, start, end, fixedrange)

for day in pycon.conference_days[1:2]:
    _rooms = training_rooms()
    for room in _rooms:
        for start, end in [
            (datetime.timedelta(hours=10, minutes=30), datetime.timedelta(hours=12, minutes=45)),
            (datetime.timedelta(hours=14, minutes=0), datetime.timedelta(hours=15, minutes=15)),
            (datetime.timedelta(hours=16, minutes=0), datetime.timedelta(hours=17, minutes=15))
        ]:
            create_session(pycon, name, room, day, start, end, fixedrange)

for day in pycon.conference_days[2:]:
    _rooms = training_rooms()
    for room in _rooms:
        for start, end in [
            (datetime.timedelta(hours=10, minutes=30), datetime.timedelta(hours=12, minutes=45)),
            (datetime.timedelta(hours=14, minutes=0), datetime.timedelta(hours=15, minutes=15)),
        ]:
            create_session(pycon, name, room, day, start, end, fixedrange)

# add breaks - only for one room is enough for triggering outputline, 5 min so not presenattion can fit
_rooms = talk_rooms()
name = "BREAK"
for day in pycon.conference_days[:1]:
    for room in _rooms:
        for start, end in [
            (datetime.timedelta(hours=12, minutes=50), datetime.timedelta(hours=14, minutes=0)),
            (datetime.timedelta(hours=15, minutes=30), datetime.timedelta(hours=16, minutes=0)),
        ]:
            create_session(pycon, name, room, day, start, end, [(5, 5)])

for day in pycon.conference_days[1:]:
    for room in _rooms:
        for start, end in [
            (datetime.timedelta(hours=10, minutes=0), datetime.timedelta(hours=10, minutes=30)),
            (datetime.timedelta(hours=12, minutes=30), datetime.timedelta(hours=14, minutes=0)),
            (datetime.timedelta(hours=15, minutes=30), datetime.timedelta(hours=16, minutes=0)),
        ]:
            create_session(pycon, name, room, day, start, end, [(5, 5)])

for y in ['morning', 'after lunch', 'afternoon']:
    print("sessions", y, len([x for x in pycon.schedule.sessions if x.name == y]))
    print("slots", y, sum([len(x.ranges_preferred) for x in pycon.schedule.sessions if x.name == y]))

# speaker availibilty
for speaker in sorted(pycon.conference_speakers.values()):
    print(speaker.speaker_id, speaker.name)
for talk in sorted(pycon.presentations_to_schedule.values()):
    print(talk.presentation_id, talk.title)

# Anand Chitipothu, Wed,Thu
pycon.set_speaker_departure('anandchitipothu', datetime.datetime(2017, 10, 27))  # set to Fri 0:00
# Samuel Muñoz Hidalgo
pycon.set_speaker_departure('samuelmuñozhidalgobeeva', datetime.datetime(2017, 10, 27))  # set to Fri 0:00

#

# Trainings due to speaker availibilty
# How to Fund Your Company WS
talk_id = '23546'
pycon.assign_presentation_to_session(talk_id,
                                     room_name=training_room_names(),
                                     starts_at=datetime.datetime(2017, 10, 26, 14),
                                     ends_at=datetime.datetime(2017, 10, 26, 15, 59),
                                     best_match=False)
# editorial decision
talk_id = '23555'
pycon.assign_presentation_to_session(talk_id,
                                     room_name=training_room_names(),
                                     starts_at=datetime.datetime(2017, 10, 26, 10),
                                     ends_at=datetime.datetime(2017, 10, 26, 12),
                                     best_match=False)


# ################ TALKS #################

# Miro --> Wednesday afternoon
talk_id = '22469'
pres = pycon.presentations_to_schedule[talk_id]
print("assigning {}".format(pres))
assigned = pycon.assign_presentation_to_session(talk_id,
                                                room_name=['Vortragsaal'],
                                                starts_at=datetime.datetime(2017, 10, 25, 16),
                                                ends_at=datetime.datetime(2017, 10, 25, 18),
                                                best_match=False)
if not assigned:
    print("-----> not assigned: {}".format(assigned, pres))

# editorial - Why Python… Finance
talk_id = '20712'
pres = pycon.presentations_to_schedule[talk_id]
print("assigning {}".format(pres))
assigned = pycon.assign_presentation_to_session(talk_id,
                                                room_name=['Medientheater'],
                                                starts_at=datetime.datetime(2017, 10, 26, 11),
                                                ends_at=datetime.datetime(2017, 10, 26, 13),
                                                best_match=False)
if not assigned:
    print("-----> not assigned: {}".format(assigned, pres))

# Alexander Hendorf - orga
# todo - talk fehlt noch
# talk_id = ''
# pycon.assign_presentation_to_session(talk_id,
#                                      # room preference can be set by order
#                                      room_name=['Medientheater],
#                                      starts_at=datetime.datetime(2017, 10, 26, 13),
#                                      ends_at=datetime.datetime(2017, 10, 26, 16),
#                                      best_match=False)

# schedule all unscheduled trainings first: they block a lot of speaker availibilty
trainings = [t for t in pycon.presentations_to_schedule if pycon.presentations_to_schedule[t].session_type == 'Workshop (60-90 minutes)']
for talk_id in trainings:
    pycon.assign_presentation_to_session(talk_id,
                                         room_name=training_room_names(),
                                         best_match=False)

# improve building by pre-select pres. (e.g. Data Science, tag: Data Science) + set range start_at/ends_at (e.g. 2 days)
categories = [
    {'cat': {'Data Science'},
     'room_preference': ['Vortragssaal', 'Medientheater', 'Media-Lounge'],
     'starts_at': datetime.datetime(2017, 10, 25)},
    {'cat': {'DevOps'}},
    {'cat': {'Web'}},
    {'cat': {'Programming'}},
]
for category in categories:
    for talk_id in [p for p in pycon.presentations_to_schedule
                    if (set(pycon.presentations_to_schedule[p].category) & category.get('cat'))
                    or 'Data Science' in pycon.presentations_to_schedule[p].track]:
        pres = pycon.presentations_to_schedule[talk_id]
        print("assigning {}".format(pres))
        # min similarity required, if none if found open new session
        for min_similarity_value in range(100, -1, -10):
            assigned = pycon.assign_presentation_to_session(talk_id,
                                                            room_name=category.get('room_preference',
                                                                                    talk_room_names()),
                                                            starts_at=category.get('starts_at'),
                                                            ends_at=category.get('ends_at'),
                                                            best_match=True,
                                                            min_similarity_value=min_similarity_value)
        if not assigned:
            print("--> not assigned {}".format(pres))
        else:
            print("assigend {} {}".format(pycon.presentations_scheduled[talk_id].starts_at, pres))

# get most popular talks, spread them all over the week randomly, and assign them to the bigger rooms
# check already for speaker availibilty
for talk_id in pycon.get_most_popular(15):
    pycon.assign_presentation_to_session(talk_id,
                                         room_name=['Medientheater'])

# first: speakers with constraints
speakers_with_contraints = {pycon.conference_speakers[speaker].speaker_id for speaker in pycon.conference_speakers
                            if pycon.conference_speakers[speaker].unavailable}
for talk_id in [p for p in pycon.presentations_to_schedule
                if (set(pycon.presentations_to_schedule[p].speaker_id) & speakers_with_contraints)]:
    pres = pycon.presentations_to_schedule[talk_id]
    print("assigning {}".format(pres))
    assigned = pycon.assign_presentation_to_session(talk_id,
                                                    room_name=talk_room_names())
    if not assigned:
        print("--> not assigned {}".format(pres))

# all others
the_talks = pycon.get_most_popular(len(pycon.presentations_to_schedule))
# random.shuffle(the_talks)
for talk_id in the_talks:
    pres = pycon.presentations_to_schedule[talk_id]
    for min_similarity_value in range(100, -1, -10):
        print("assigning {}".format(pres))
        assigned = pycon.assign_presentation_to_session(talk_id,
                                                        room_name=talk_room_names(),
                                                        min_similarity_value=min_similarity_value)
    if not assigned:
        print("--> not assigned {}".format(pres))

# finally sometimes some talks remain, add randomly
the_talks = pycon.get_most_popular(len(pycon.presentations_to_schedule))
for talk_id in the_talks:
    pres = pycon.presentations_to_schedule[talk_id]
    print("assigning {}".format(pres))
    assigned = pycon.assign_presentation_to_session(talk_id,
                                                    room_name=talk_room_names(),
                                                    best_match=False)
    if not assigned:
        print("--> not assigned {}".format(pres))

print("== ERRORS ==")

print("== UNSCHEDULED ==")
for i, x in enumerate(pycon.presentations_to_schedule.values(), 1):
    print(i, x.title, x.duration, x.session_type)

print("== SESSIONS WITH OPEN SLOTS ==")
for s in pycon.schedule.session_with_slots():
    if s.name == 'BREAK':
        continue
    print(s.minutes_available, s.max_slot_duration_available, s.room.name, s.starts_at)

# pass over Speakers for schedul print outs
pycon.schedule.speakers = pycon.conference_speakers

os.makedirs('schedules', exist_ok=True)
pycon.schedule.export_excel()
# save unscheduled to disk
with open('schedules/V{}_unscheduled.json'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")), 'w') as f:
    json.dump(list([{
        'id': x.presentation_id,
        'title': x.title,
        'track': list(x.track),
        'tags': list(x.tags), 'category': list(x.category),
        'duration': x.duration,
        'session_type': x.session_type,
        'admin_type': x.admin_type,
    } for x in pycon.presentations_to_schedule.values()]), f)

with open('schedules/V{}.pickle'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")), 'wb') as f:
    pickle.dump(pycon, f)
