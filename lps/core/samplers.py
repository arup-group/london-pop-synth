from shapely.geometry import Point
import random
from datetime import timedelta, datetime
from lps.core.population import Population


class NotRequired:
    """
    Object for not sampling (ie for MOMO tests)
    """
    def __init__(self, config):
        pass

    def sample(self):
        raise NotImplementedError


class ObjectSampler:
    """
    Object for sampling from input data parsers
    """
    def __init__(self, config):
        self.config = config
        print('Sampler initialised:')
        print("\t> sampling will be @ {}%".format(config.SAMPLE))
        if config.NOFREQ:
            print("\t> input plans frequency removed (sampled once only)")
        if config.LIMIT:
            print("\t> results limited to {} plans".format(config.LIMIT))
        if not config.DUMMIES:
            print("\t> dummy trips to be removed automatically")

        random.seed = config.SEED
        self.samples = random.sample(range(10000), int(self.config.SAMPLE * 100))  # sample % from range 10000
        self.count = 0
        self.sample_count = 0

    def sample(self):
        if self.count % 10000 not in self.samples:
            self.count += 1
            return False
        self.count += 1
        self.sample_count += 1
        return True


class DemandSampler:
    """
    Object for sampling from input demand data
    """
    def __init__(self, config):
        self.config = config
        self.adjustment = config.SAMPLE / 100
        print('Sampler initialised:')
        print("\t> sampling will be @ {}%".format(config.SAMPLE))
        if config.NORM:
            print("\t> input demand normalised to {} trips".format(config.NORM))
        if config.LIMIT:
            print("\t> results limited to {} plans".format(config.LIMIT))

        self.counter = 0
        self.hit_limit = False

    def get_sample_size(self, n):
        """
        Method for returning sample size. Uses Config to consider sampling, limit or normalisation.
        :param n:
        :return:
        """
        # if self.config.NORM:
        #     return int(self.config.NORM)
        n = n * self.adjustment
        count = probability_rounder(n)
        provisional_counter = self.counter + count

        if self.config.LIMIT and self.config.LIMIT < provisional_counter:  # check if limit reached
            self.counter = self.config.LIMIT
            self.hit_limit = True
            return self.config.LIMIT - self.counter

        self.counter = provisional_counter
        return count


def probability_rounder(n):
    """
    function for probabilistic rounding of integers
    :param n:
    :return:
    """
    remainder = n - int(n)
    remainder = int(random.random() < remainder)
    return int(n) + remainder


def sample_point(geo_id, geo_df):
    """
    Returns randomly placed point within given geometry, using the lsoa_df. Note that it uses
    random sampling within the shape's bounding box then checks if point is within given geometry.
    If the method cannot return a valid point within 50 attempts then a RunTimeWarning is raised.
    :param geo_id: sting for LSOA identification
    :param geo_df: GeoPandas df object with required boundaries
    :return: Point object
    """
    # TODO can speed this up by returning n points for geo where n is the sample frequency
    try:
        geom = geo_df.geometry.loc[geo_id]
    except LookupError:
        print('Unknown geo_id: {}'.format(geo_id))
        return Point(530000, 180000)  # default to central london if not found (specifically Horseguard's Parade)
    min_x, min_y, max_x, max_y = geom.bounds
    patience = 1000
    for attempt in range(patience):
        random_point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
        if geom.is_valid:
            if random_point.within(geom):
                return random_point
        else:
            if random_point.within(geom.buffer(0)):
                return random_point

    raise RuntimeWarning(f'unable to sample point from geometry:{geo_id} with {patience} attempts')


mode_speeds = {'Car_driver': 40,  # in miles per hour
               'Car_passenger': 40,
               'Rail': 40,
               'Bus': 20,
               'Cycle': 15,
               'Walk': 4,
               'Taxi': 30
               }


def build_journey_time(distance, default_speed=30, limit=5400, mode='unknown', factor=1.5):
    """
    Build journey time/duration from origin and destination
    :param distance:
    :param default_speed:
    :param limit:
    :param mode:
    :param factor:
    :return: datetime timedelta
    """
    speed = mode_speeds.get(mode, default_speed)
    speed = speed * 1600 / 3600  # metres per second
    journey_time = timedelta(seconds=distance * factor / speed)
    if journey_time > timedelta(seconds=limit):
        return timedelta(seconds=limit)
    else:
        return journey_time


def build_trip_times(time, journey_time, push='forward'):
    """
    Build trip departure and arrival times around given time and journey time.
    If leg overlaps 'midnight' then times will be either pushed 'forward' or
    'back' to ensure activity is available at start of day.
    :param time:
    :param journey_time:
    :param push: 'forward' or 'back'
    :return:
    """
    assert push in ['forward', 'back']
    dt = datetime(2000, 1, 1, time.hour, time.minute)
    depart_dt = dt - journey_time / 2.
    arrive_dt = dt + journey_time / 2.
    if depart_dt.day != arrive_dt.day:
        if push == 'forward':
            depart_dt = datetime(2000, 1, 1, 0, 0)
            arrive_dt = depart_dt + journey_time
        if push == 'back':
            arrive_dt = datetime(2000, 1, 1, 23, 59)
            depart_dt = depart_dt - journey_time
    return depart_dt, arrive_dt


def get_manhattan_distance(a, b, factor=1):
    x_diff = abs(a.x - b.x)
    y_diff = abs(a.y - b.y)
    return (x_diff + y_diff) * factor


def get_approx_distance(a, b, factor=1):
    x_diff = abs(a.x - b.x)
    y_diff = abs(a.y - b.y)
    dist = (x_diff ** 2 + y_diff ** 2) ** 0.5
    return dist * factor


def get_timestamp(integer):
    """
    Parses integer timestamp from csv into correctly formatted string for xml
    :param integer: input integer formatted hhmm
    :return: output string formatted to hh:mm:ss
    """
    string = str(integer)
    if len(string) == 1:
        return '00:0{}:00'.format(string)
    elif len(string) == 2:
        return '00:{}:00'.format(string)
    else:
        minutes = string[-2:]
        hours = string[:-2]
        if len(hours) == 1:
            hours = '0' + hours
        return '{}:{}:00'.format(hours, minutes)
