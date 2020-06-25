
from datetime import datetime as dt
from lps.core import output

"""
Classes for holding Plan Information:
- Population
    - Person * n
        - Plan * n
            - Activity * n
            - Leg * n
"""


class Population:
    def __init__(self):

        self.agents = []

        self.num_people = None
        self.acts = None
        self.legs = None

        self.records = {}

    def build_sub_categories(self):
        for person in self.agents:
            person.build_sub_categories()

    def add_agents(self, other):
        self.agents.extend(other.agents)
        self.records.update(other.records)

    def get_size(self):
        num_people = 0
        acts = 0
        legs = 0
        for person in self.agents:
            num_people += 1
            for plan in person.plans:
                acts += len(plan.activities)
                legs += len(plan.legs)
        self.num_people = num_people
        self.acts = acts
        self.legs = legs
        return num_people, acts, legs

    def make_records(self, config):
        self.get_size()
        record = {
            'time': dt.now(),
            'plans': self.num_people,
            'acts': self.acts,
            'legs': self.legs
        }
        record.update(config.RECORDS)
        records = {config.SOURCE: record}
        self.records = records
        return records

    def add_records(self, config):
        self.get_size()
        record = {
            'time': dt.now(),
            'plans': self.num_people,
            'acts': self.acts,
            'legs': self.legs
        }
        record.update(config.RECORDS)
        records = {config.SOURCE: record}
        self.records.update(records)
        return records

    def xml(self, path):
        output.write_xml(self, path)


class Agent:
    def __init__(self, uid, plans, attributes=None):
        self.uid = uid
        self.plans = plans
        self.attributes = attributes

    def build_sub_categories(self):
        for plan in self.plans:
            plan.build_sub_categories()


class Plan:
    def __init__(self, activities, legs, source):
        self.activities = activities
        self.legs = legs
        self.num_activities = len(activities)
        self.num_legs = len(legs)
        self.wrapped_activities = activities[0].act == activities[-1].act
        self.wrapped_locations = activities[0].point == activities[-1].point
        self.wrapped = self.wrapped_activities and self.wrapped_locations
        self.source = source

    def build_sub_categories(self):
        self.build_sub_work_categories()
        self.build_sub_home_categories()

    def build_sub_work_categories(self):
        total_work_duration = 0
        work_activities = []
        for act in self.activities:
            if act.act == 'work':
                total_work_duration += act.duration
                work_activities.append(act)
        if not work_activities:
            return None
        if total_work_duration > (7 * 60):
            if (6.5 * 60) < work_activities[0].start_time_minutes < (11.5 * 60):
                if len(work_activities) == 1:
                    work_activities[0].act = 'work_9to5'
                    return None
                if len(work_activities) == 2 and work_activities[1].end_time_minutes < (20 * 60):
                    work_activities[0].act = 'work_9to5am'
                    work_activities[1].act = 'work_9to5pm'
                    return None
        for act in work_activities:
            if act.duration > (7 * 60):
                act.act = 'work_7_p'
            elif act.duration > (3 * 60):
                act.act = 'work_3_7'
            else:
                act.act = 'work_0_3'

    def build_sub_home_categories(self):
        for act in self.activities:
            if act.act == 'home':
                if act.duration > (8 * 60):
                    act.act = 'home_8_p'
                else:
                    act.act = 'home_0_8'

    def activity_report(self):
        report = []
        if self.wrapped:  # if wrapped (ie same start and end activities) then don't duplicate in report
            for act in self.activities[:-1]:
                report.append([self.source] + act.report())
        else:
            for act in self.activities:
                report.append([self.source] + act.report())
        return report

    def leg_report(self):
        report = []
        for leg in self.legs:
            report.append([self.source] + leg.report())
        return report


class Activity:
    def __init__(self, uid, seq, act, point, start_time=None, end_time=None):
        self.uid = uid
        self.sequence = seq
        self.act = act
        self.point = point
        self.start_time = start_time
        self.end_time = end_time
        self.start_time_dt = dt.strptime(self.start_time, '%H:%M:%S')
        self.end_time_dt = dt.strptime(self.end_time, '%H:%M:%S')
        self.start_time_minutes = self.start_time_dt.hour * 60 + self.start_time_dt.minute
        self.end_time_minutes = self.end_time_dt.hour * 60 + self.end_time_dt.minute
        self.duration = self.end_time_minutes - self.start_time_minutes
        if self.duration < 0:
            self.duration = (24 * 60) + self.duration

    def report(self):
        return [self.uid,
                self.sequence,
                self.act,
                self.point.x,
                self.point.y,
                self.start_time,
                self.end_time,
                self.start_time_minutes,
                self.end_time_minutes,
                self.duration
                ]

    def report_dict(self):
        return {'uid': self.uid,
                'sequence': self.sequence,
                'activity': self.act,
                'x': int(self.point.x),
                'y': int(self.point.y),
                'start_time': self.start_time,
                'end_time': self.end_time,
                'start_time_mins': self.start_time_minutes,
                'end_time_mins': self.end_time_minutes,
                'duration_mins': self.duration
                }


class Leg:
    def __init__(self, uid, seq, mode,
                 start_loc=None, end_loc=None,
                 start_time=None, end_time=None,
                 dist=None):
        self.uid = uid
        self.sequence = seq
        self.mode = mode
        self.start_loc = start_loc
        self.end_loc = end_loc
        self.start_time = start_time
        self.end_time = end_time
        self.start_time_dt = dt.strptime(start_time, '%H:%M:%S')
        self.end_time_dt = dt.strptime(end_time, '%H:%M:%S')
        self.start_time_minutes = self.start_time_dt.hour * 60 + self.start_time_dt.minute
        self.end_time_minutes = self.end_time_dt.hour * 60 + self.end_time_dt.minute
        self.duration = self.end_time_minutes - self.start_time_minutes
        self.dist = dist
        if self.duration < 0:
            self.duration = (24 * 60) + self.duration

    def report(self):
        return [self.uid,
                self.sequence,
                self.mode,
                self.start_loc.x,
                self.start_loc.y,
                self.end_loc.x,
                self.end_loc.y,
                self.start_time,
                self.end_time,
                self.start_time_minutes,
                self.end_time_minutes,
                self.duration,
                self.dist
                ]

    def report_dict(self):
        return {'uid': self.uid,
                'sequence': self.sequence,
                'mode': self.mode,
                'ox': int(self.start_loc.x),
                'oy': int(self.start_loc.y),
                'dx': int(self.end_loc.x),
                'dy': int(self.end_loc.y),
                'start_time': self.start_time,
                'end_time': self.end_time,
                'start_time_mins': self.start_time_minutes,
                'end_time_mins': self.end_time_minutes,
                'duration_mins': self.duration,
                'distance': self.dist
                }
