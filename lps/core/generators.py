from scipy.stats import truncnorm
import numpy as np
import random
from datetime import time
from shapely.geometry import Point


class UniformDistributionGen:
    """
    Object for initiating and sampling from a uniform distribution
    """
    def __init__(self, range_in=None, low=None, upp=None):
        if range_in:
            self.hours = range_in
        elif low and upp:
            self.hours = range(low, upp)
        else:
            raise NotImplemented('Unknown inputs')

    def sample(self, n=1):
        return random.choices(self.hours, k=n)


class NormDayDistributionGen:
    """
    Object for initiating and sampling a daytime distribution
    """
    def __init__(self, low=7, mean=8, upp=10, sd=1):
        self.hours = range(low, upp+1)
        self.dist = truncnorm((low - mean) / sd, (upp + 1 - mean) / sd, loc=mean, scale=sd)

    def sample(self, n=None):
        """
        Sample hour
        :param n: number of samples to be returned
        :return: single integer or list of integers sampled from distribution
        """
        if n:
            return [int(i) for i in self.dist.rvs(n)]
        else:
            return int(self.dist.rvs())


class FrequencyDistribution:
    """
    Object for initiating and sampling from frequency weighted distributing
    """
    def __init__(self, dist, freq):
        self.distribution = tuple(dist)
        self.frequency = np.array(freq)

    def sample(self, n=1):
        """
        :param n: number of samples to be returned
        :return: single object or list of objects sampled from distribution
        """
        return random.choices(self.distribution, weights=self.frequency, k=n)

    def sample_exclude(self, exclude, patience=10):
        for attempt in range(patience):
            provisional = self.sample()
            if exclude not in provisional:
                return provisional
        raise StopIteration('failed to find valid sample after {} attempts'.format(patience))


def gen_minute(hour, steps=1):
    """
    Return random time in given hour, based on minutes with given number of intervals
    :param hour: hour int
    :param steps: minute precision int (default: 5)
    :return: time object (hh:mm:00)
    """
    minutes = np.arange(0, 60, steps)
    minute = int(random.choice(minutes))
    t = time(hour, minute, 0)
    return t


def gen_minutes(hours, steps=1):
    """
    Return random times in given hour, based on minutes with given number of intervals
    :param hours: hour integers in list for
    :param steps: minute precision int m(default: 5)
    :param k: number of times to return
    :return: time object (hh:mm:00)
    """
    k = len(hours)
    minutes = np.arange(0, 60, steps)
    minutes = random.choices(minutes, k=k)
    times = [None] * k
    for t, (hour, minute) in enumerate(zip(hours, minutes)):
        times[t] = time(hour, minute, 0)
    return times


def gen_location(o, low=0, upp=500):
    """
    Generated a Point based on an input point and a given distance range. Distance
    is sampled from uniform distribution between lower and upper bounds. Direction
    is sampled randomly. Note that input bounds should be in appropriate units (m).
    :param o: Point
    :param low: int
    :param upp: int
    :return: Point
    """
    distance = np.arange(low, upp, 1)
    distance = int(random.choice(distance))
    angle = np.pi * np.random.uniform(0, 2)
    x = distance * np.cos(angle)
    y = distance * np.sin(angle)
    return Point(o.x + x, o.y + y)


