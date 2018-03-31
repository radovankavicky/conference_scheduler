import datetime
import os
import json
import random
from typing import List, Tuple
import pandas as pd
from conference_scheduler.resources.Presentation import Presentation
import itertools
import string


class Schedule:
    def __init__(self):
        self.sessions = []
        self.speakers = {}

    def create_session(self, add_session):
        """
        helper
        :return: 
        """
        # check if session in the same room overlap
        adding_this_session_is_ok = True
        for session in self.sessions:
            if session.room.name != add_session.room.name:
                continue
            if (session.starts_at <= add_session.starts_at < session.ends_at) or (
                            session.starts_at < add_session.ends_at <= session.ends_at):
                try:
                    raise AssertionError(
                        "session overlap with session {} {}-{}".format(
                            session.room.name, session.starts_at, session.ends_at))
                except AssertionError:
                    # ok just do not add this session
                    adding_this_session_is_ok = False
                    continue
        if adding_this_session_is_ok:
            self.sessions.append(add_session)

    # noinspection PyBroadException
    @classmethod
    def score(cls, presentation, session):
        if not [x for x in session.slots_assigned if x]:
            # no session assigned to make any comparison
            return 0
        v1, v2, v3, v4 = (0,) * 4
        try:
            v1 = len(
                set(itertools.chain.from_iterable([p.tags for p in session.slots_assigned if p])) & presentation.tags)
        except Exception as e:
            pass
        try:
            v2 = len(
                set(itertools.chain.from_iterable([p.track for p in session.slots_assigned if p])) & presentation.track)
        except Exception as e:
            pass
        try:
            v3 = len(set(itertools.chain.from_iterable(
                [p.category for p in session.slots_assigned if p])) & presentation.category)
        except Exception as e:
            pass
        try:
            session_levels = [p.level for p in session.slots_assigned if p]
            if presentation.level in session_levels:
                v4 = 25
            elif presentation.level == 'advanced' and 'intermediate' in session_levels:
                v4 = 10
            elif presentation.level == 'beginner' and 'intermediate' in session_levels:
                v4 = 10
            elif presentation.level == 'intermediate':
                v4 = 10
        except Exception as e:
            pass

        if v1 > 0:
            pass
        if v2 > 0:
            pass
        if v3 > 0:
            pass

        value = sum([v1 * 30, v2 * 30, v3 * 10, v4 * 3])
        # return random.randint(0, 100)
        return value

    @classmethod
    def presentation_assignable_to_session(cls,
                                           presentation,
                                           session,
                                           room_name: (str, List) = None,
                                           starts_at: datetime.datetime = None,
                                           ends_at: datetime.datetime = None,
                                           unavailable: List[Tuple[datetime.datetime, datetime.datetime]] = None
                                           ):
        if isinstance(room_name, str):
            room_name = [room_name]
        if not session.space_available:
            return "no space available"
        if room_name and session.room.name not in room_name:
            return "this not a room you are looking for "
        if ends_at and ends_at < session.starts_at:
            return "session starts after end of range requested"
        if starts_at and starts_at > session.ends_at:
            return "session ends before range requested"
        # if presentation.duration and session.max_slot_duration_available < presentation.duration:
        #     return "no slot left for this duration"
        # if presentation.duration and session.min_slot_duration_available > presentation.duration:
        #     return "no slot left for this duration"
        if presentation.duration not in set(itertools.chain.from_iterable(
                [session.ranges_preferred[x] for x in session.slots_available])):
            return "no slot left for this duration"
        if presentation.duration and session.minutes_available < presentation.duration:
            return "presenation is longer then time left in this session"

        if unavailable:
            # check list of unavailibilty for all speakers involved
            if any([unav[0] < session.starts_at < unav[1] for unav in unavailable]):
                return "unavailable"
            if any([unav[0] < session.ends_at < unav[1] for unav in unavailable]):
                return "unavailable"
        return True

    def assign_to_best_session(self,
                               presentation: Presentation,
                               room_name: (str, List) = None,
                               starts_at: datetime.datetime = None,
                               ends_at: datetime.datetime = None,
                               unavailable: List[Tuple[datetime.datetime, datetime.datetime]] = None,
                               dry_run: bool = False,
                               min_similarity_value: int = 30):
        random.shuffle(self.sessions)
        candidate_sessions = []
        for session in self.session_with_slots():
            available = self.presentation_assignable_to_session(
                presentation, session, room_name, starts_at, ends_at, unavailable)
            if available is not True:
                continue
            pres = self.assign_to_session_slot(
                session,
                presentation,
                dry_run=True,
            )
            if pres:
                score = self.score(presentation, session)
                if min_similarity_value <= score:
                    candidate_sessions.append((session, score))
            else:
                pass
        if candidate_sessions:
            ranked_sessions = sorted(candidate_sessions, key=lambda x: x[1], reverse=True)
            pres_assigned = self.assign_to_session_slot(
                ranked_sessions[0][0],
                presentation, dry_run=dry_run
            )
            if pres_assigned:
                return pres_assigned, ranked_sessions[0][0]
        else:
            pass
        return None, None

    def assign_to_session(self,
                          presentation: Presentation,
                          room_name: (str, List) = None,
                          starts_at: datetime.datetime = None,
                          ends_at: datetime.datetime = None,
                          unavailable: List[Tuple[datetime.datetime, datetime.datetime]] = None,
                          dry_run: bool = False
                          ):
        """
        Validated assignment to a session which is more or less definded
        unique session = room_name + starts_at + ends_at
        :param presentation:
        :param room_name: 
        :param starts_at: 
        :param ends_at: 
        :param unavailable: 
        :param dry_run:
        :return:
        """
        random.shuffle(self.sessions)
        if room_name:
            if isinstance(room_name, str):
                room_name = [room_name]
        for session in self.session_with_slots():
            assignable = self.presentation_assignable_to_session(
                presentation, session, room_name, starts_at, ends_at, unavailable)
            if assignable is not True:
                continue
            pres_assigned = self.assign_to_session_slot(session, presentation, dry_run=dry_run)
            if not pres_assigned:
                pass  # should never happen
            return pres_assigned, session
        return None, None

    @classmethod
    def assign_to_session_slot(cls, session, presentation, dry_run=False):
        for position in session.slots_available:
            min_range, max_range = session.ranges_preferred[position]
            if min_range <= presentation.duration <= max_range:
                if presentation.title in [x.title for x in session.slots_assigned if x]:
                    pass
                if dry_run:
                    return True
                presentation.starts_at = session.starts_at + datetime.timedelta(
                    minutes=sum([max(x) for x in session.ranges_preferred[:position]]))
                presentation.room = session.room
                session.add_presentation(presentation, position)
                return True
        return

    def sessions_by_day(self, day: datetime.datetime):
        return sorted(list({x.day for x in self.sessions if x.day == datetime.datetime(day.year, day.month, day.day)}),
                      key=lambda x: x.room.name)

    def session_with_slots(self):
        return [s for s in self.sessions if s.slots_available and s.name != 'BREAK']

    def export_json(self):
        presentations_list = self.presentations_list_for_export()
        with open('schedules/V{}.json'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")),
                  'w') as f:
            json.dump(presentations_list)


    def export_excel(self):
        """ create list with all sessions with room and time index """
        presentations_list = self.presentations_list_for_export()
        schedule_df = pd.DataFrame(presentations_list)
        re_arrange: List = []
        for room in sorted(schedule_df['room'].unique()):
            attrs = ['time', 'title', 'duration', 'category', 'level', 'speakernames']
            d = schedule_df[schedule_df['room'] == room][attrs]
            d.index = d['time']
            series = d[attrs].apply(
                lambda x: "{} {} {}{}{}".format(
                    x['title'],
                    '[{}]'.format(x['duration']) if '<<< BREAK >>>' not in x['title'] else "",
                    '({})'.format(x['category']) if '<<<' not in x['title'] else "",
                    '[{}]'.format(x['level'])[0].upper() if x['level'] else "",
                    '[{}]'.format(x['speakernames']) if x['speakernames'] else ""),
                axis=1)
            series.name = room
            re_arrange.append(pd.DataFrame(series))

        schedule_dfa: pd.DataFrame = pd.concat(re_arrange, axis=1, ignore_index=False, copy=True, join='outer')
        schedule_dfa.fillna("", inplace=True)
        schedule_dfa.sort_index(inplace=True)
        schedule_dfa['dow'] = schedule_dfa.index.dayofweek % 2

        os.makedirs('schedules', exist_ok=True)
        writer = pd.ExcelWriter('schedules/V{}.xlsx'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")),
                                engine='xlsxwriter',
                                datetime_format='dd mmm hh:mm',
                                date_format='dd mmm'
                                )
        schedule_dfa.to_excel(writer, 'Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        breakformat = workbook.add_format()
        breakformat.set_align('center')
        breakformat.set_align('vcenter')
        breakformat.set_text_wrap()
        breakformat.set_bg_color('#e0e5de')
        available = workbook.add_format()
        available.set_align('center')
        available.set_align('vcenter')
        available.set_text_wrap()
        available.set_bg_color('#a0fc2f')
        datascience = workbook.add_format()  # Data Science
        datascience.set_bg_color('#ffa159')
        devops = workbook.add_format()  # DevOps
        devops.set_bg_color('#d3f4ff')
        web = workbook.add_format()  # Web
        web.set_bg_color('#ddd0e0')
        testing = workbook.add_format()  # Testing
        testing.set_bg_color('#ead7e7')
        programming = workbook.add_format()  # Programming
        programming.set_bg_color('#ffced1')
        weekday = workbook.add_format()
        weekday.set_bg_color('#f2f1d2')
        worksheet.conditional_format('B2:I100',
                                     {'type': 'text', 'criteria': 'containing', 'value': 'Data Science',
                                      'format': datascience})
        worksheet.conditional_format('B2:I100',
                                     {'type': 'text', 'criteria': 'containing', 'value': 'DevOps',
                                      'format': devops})
        worksheet.conditional_format('B2:I100',
                                     {'type': 'text', 'criteria': 'containing', 'value': 'Web',
                                      'format': web})
        worksheet.conditional_format('B2:I100',
                                     {'type': 'text', 'criteria': 'containing', 'value': 'Testing',
                                      'format': web})
        worksheet.conditional_format('B2:I100',
                                     {'type': 'text', 'criteria': 'containing', 'value': 'Programming',
                                      'format': web})
        worksheet.conditional_format('A2:H100',
                                     {'type': 'text', 'criteria': 'containing', 'value': '<<< BREAK >>',
                                      'format': breakformat})
        worksheet.conditional_format('B2:H100',
                                     {'type': 'text', 'criteria': 'containing', 'value': '<<< available >>>',
                                      'format': available})


        last_column = string.ascii_uppercase[len(schedule_dfa.columns)]
        worksheet.conditional_format('A2:K100',
                                     {'type': 'formula', 'format': weekday, 'criteria': '=${}2>0'.format(last_column)})
        worksheet.set_column('{0}:{0}'.format(last_column), None, None, {'hidden': True})  # hide weekday side calculation

        style = workbook.add_format()
        style.set_align('center')
        style.set_align('vcenter')
        style.set_text_wrap()
        tstyle = workbook.add_format()
        tstyle.set_num_format('dd.mm hh:mm')
        for i in range(len(schedule_dfa.index)):
            worksheet.set_row(i, 60)
        worksheet.set_column('A:A', 25, tstyle)
        worksheet.set_column('B:H', 35, style)
        writer.save()

    def presentations_list_for_export(self):
        presentations_list = []
        debug_dupes = set([])  # just for debugging
        for session in self.sessions:

            for i, presentation in enumerate(session.slots_assigned):
                record = {
                    'room': session.room.name,
                }
                if presentation:
                    if presentation.title in debug_dupes:
                        pass
                    record['speakers'] = presentation.speaker_id
                    record['speakernames'] = ', '.join([self.speakers[s].name for s in presentation.speaker_id])
                    record['title'] = presentation.title
                    record['duration'] = presentation.duration
                    record['level'] = presentation.level
                    record['time'] = presentation.starts_at
                    record['category'] = '|'.join(list(presentation.category))
                    record['tags'] = '|'.join(list(presentation.tags))
                    debug_dupes.add(presentation.title)
                else:
                    record['speakers'] = ''
                    record['speakernames'] = ''
                    record['title'] = "<<< BREAK >>>" if session.name == 'BREAK' else "<<< available >>>"
                    record['duration'] = session.ranges_preferred[i]
                    record['level'] = ''
                    record['time'] = session.presentation_start_times[i]
                    record['category'] = ''
                    record['tags'] = ''
                presentations_list.append(record)
        # sorted([x for x in presentations_list if x['title']!='<available>'], key=lambda x: x['title'])
        return presentations_list
