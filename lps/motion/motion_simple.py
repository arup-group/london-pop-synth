import pandas as pd
from datetime import timedelta, datetime
import numpy as np
import geopandas as gp
import random
from halo import Halo

from lps.core import samplers, generators
from lps.core.population import Agent, Plan, Activity, Leg


class Demand:

    def __init__(self, config):
        print('\n--------- Initiating Motion Population Input ---------')
        self.config = config
        self.zones = self.load_zones()
        self.filter = self.add_filter()
        self.demand = self.load_demand()
        self.num_plans = None
        self.sampler = None
        print('Input Demand Loaded:')
        print("\t> outputs using epsg:{}".format(config.EPSG))
        print("\t> demand input from: {}".format(config.INPUTPATH))
        print("\t> zone inputs from: {}".format(config.ZONESPATH))
        print("\t> saving to: {}".format(config.OUTPATH))

    # load zones
    def load_zones(self):
        """
        Load zones
        :return: GeoPandas GeoDataFrame
        """
        with Halo(text='loading zone data...', spinner='dots') as spinner:
            gdf = gp.read_file(self.config.ZONESPATH)
            if not gdf.crs.get('init') == self.config.EPSG:
                spinner.text = 'converting zones to espg:{}'.format(self.config.EPSG)
                gdf = gdf.to_crs(epsg=self.config.EPSG)
            gdf = gdf.loc[:, ['Sequential_9_1', 'geometry']]
            gdf = gdf.set_index('Sequential_9_1')
            spinner.text = 'buffering zone data'
            gdf.geometry = gdf.buffer(0)
            spinner.succeed('{} zones loaded and buffered'.format(len(gdf)))
        return gdf

    def load_filter(self):
        """
        Load filter
        :return: geometry
        """
        with Halo(text='loading filter data...', spinner='dots') as spinner:
            gdf = gp.read_file(self.config.FILTERPATH)
            if not gdf.crs.get('init') == self.config.EPSG:
                spinner.text = 'converting filter to espg:{}'.format(self.config.EPSG)
                gdf = gdf.to_crs(epsg=self.config.EPSG)
            spinner.text = 'buffering geometries'
            geometry = gdf.geometry.buffer(0)
            spinner.text = 'preparing for dissolve'
            spinner.text = 'dissolving all geometries'
            geometry = geometry.unary_union
            spinner.succeed('filter loaded')
        return geometry

    def add_filter(self):
        """
        Build spatial filter
        :return:
        """
        geom = self.load_filter()
        with Halo(text='preparing filter...', spinner='dots') as spinner:
            self.zones['london'] = self.zones.intersects(geom)
            assert len(self.zones) > 0
            out_filter = pd.Series(self.zones.loc[self.zones.london == False, :].index)
            assert len(out_filter) > 0
            in_filter = pd.Series(self.zones.loc[self.zones.london == True, :].index)
            assert len(in_filter) > 0
            spinner.succeed('filter prepared')
        return {'out': out_filter, 'in': in_filter}

    def filterer(self, df):
        """
        Filters df for lines that originate outside london and dest inside london,
        ie commuters
        :param df:
        :return:
        """
        out_filter = self.filter['out']
        out_mask = df.o.isin(out_filter)
        assert sum(out_mask)
        in_filter = self.filter['in']
        in_mask = df.d.isin(in_filter)
        assert sum(in_mask)
        return df.loc[out_mask & in_mask, :]

    def load_demand(self):
        """
        Load Motion demand and build sampling distributions
        :return: bespoke demand dict
        """
        with Halo(text='loading demand inputs...', spinner='dots') as spinner:
            demand = pd.read_csv(self.config.INPUTPATH)
            if is_wide(demand):
                id_vars = demand.columns[0]
                value_vars = demand.columns[1:]
                demand = pd.melt(demand, id_vars=id_vars, value_vars=value_vars)
                demand.columns = ['o', 'd', 'freq']
                demand = demand.astype({'o': int, 'd': int, 'freq': float})
            else:
                raise ValueError('unknown input format, only wide is implemented')
            spinner.succeed('input demand loaded')

        with Halo(text='filtering demand for commuters...', spinner='dots') as spinner:
            demand = self.filterer(demand)
            demand_sum = sum(demand.freq)
            spinner.succeed('inputs filtered for origin outside and dest inside London')

        print("\t> demand is {} trips".format(int(demand_sum)))

        with Halo(text='modelled daily demand profile...', spinner='dots') as spinner:
            start_hour = generators.DayDistributionGen(low=7, mean=8, upp=10, sd=1)
            lunch_hour = generators.DayDistributionGen(low=12, mean=13, upp=14, sd=1)
            end_hour = generators.DayDistributionGen(low=16, mean=17, upp=21, sd=1.5)
            spinner.succeed('{} total trips loaded'.format(demand_sum))

        with Halo(text='modelled O-D demand profiles...', spinner='dots') as spinner:
            profile = np.array(demand.freq)
            od = tuple(zip(demand.o, demand.d))
            od_sampler = (od, profile)
            spinner.succeed('O-D demand profiles completed')
        return {'total': demand_sum,
                'starts': start_hour,
                'lunches': lunch_hour,
                'ends': end_hour,
                'od': od_sampler}

    def sample(self, sampler, population):
        with Halo(text='sampling from distributions...', spinner='dots') as spinner:

            n = self.demand['total']  # total daily demand
            n = sampler.get_sample_size(n)

            # TODO: HARDCODED ASSUMING DEMAND MATRIX IS PER HOUR FOR 3 HOURS OF AM DEMAND
            n *= 3

            start_hours = self.demand['starts'].sample(n + 1)
            lunch_hours = self.demand['lunches'].sample(n + 1)
            end_hours = self.demand['ends'].sample(n + 1)

            start_times = generators.gen_minutes(start_hours)
            lunch_times = generators.gen_minutes(lunch_hours)
            end_times = generators.gen_minutes(end_hours)

            ods = random.choices(self.demand['od'][0], weights=self.demand['od'][1], k=n + 1)

            spinner.succeed('sampling completed for {} trips'.format(n))

        with Halo(text="building trips...", spinner="dots") as spinner:
            for trip in range(n):
                spinner.text = "Built {} of {} trips...".format(trip, n)

                uid = self.config.PREFIX + str(trip)
                start_time = start_times[trip]  # Random sample minute to make time stamp
                lunch_time = lunch_times[trip]  # Random sample minute to make time stamp
                end_time = end_times[trip]  # Random sample minute to make time stamp
                o_id, d_id = ods[trip]

                # Sample O-D points
                o = samplers.sample_point(o_id, self.zones)
                d1 = samplers.sample_point(d_id, self.zones)
                d2 = generators.gen_location(d1)

                # Get distance between pairs (for approx. journey time)
                dist1 = samplers.get_manhattan_distance(o, d1)
                td1 = timedelta(seconds=dist1 / 13)  # Approx. 30 mph with manhattan distance
                dist2 = samplers.get_manhattan_distance(d1, d2)
                td2 = timedelta(seconds=dist2 / 1)  # Approx. walking with manhattan distance

                # Build up day times
                dt0 = datetime(2000, 1, 1, start_time.hour, start_time.minute)  # leave home
                dt1 = dt0 + td1  # approx. arrive at work
                dt2 = datetime(2000, 1, 1, lunch_time.hour, lunch_time.minute)  # leave for lunch
                dt3 = dt2 + td2  # arrive at lunch
                minutes_at_lunch = random.randint(20, 40)
                dt4 = dt3 + timedelta(seconds=(minutes_at_lunch * 60))  # leave lunch
                dt5 = dt4 + td2  # arrive back at work
                dt6 = datetime(2000, 1, 1, end_time.hour, end_time.minute)  # leave work
                if dt6 < dt5:
                    print('\nWARNING', uid, dt5, dt6)
                dt7 = dt6 + td1  # arrive home

                loc = o, d1, d2
                dts = dt0, dt1, dt2, dt3, dt4, dt5, dt6, dt7
                d = dist1, dist2

                population.people.append(self.build_plan(uid, loc, dts, d))

            spinner.succeed("Plan simulation completed")
        return population

    def build_plan(self, uid, loc, dts, d):

        t0 = dts[0].time().strftime("%H:%M:%S")  # Home departure
        t1 = dts[1].time().strftime("%H:%M:%S")  # Work arrival
        t2 = dts[2].time().strftime("%H:%M:%S")  # Work departure
        t3 = dts[3].time().strftime("%H:%M:%S")  # Lunch arrival
        t4 = dts[4].time().strftime("%H:%M:%S")  # Lunch departure
        t5 = dts[5].time().strftime("%H:%M:%S")  # Work arrival
        t6 = dts[6].time().strftime("%H:%M:%S")  # Work departure
        t7 = dts[7].time().strftime("%H:%M:%S")  # Home arrival

        activities = []
        legs = []

        activities.append(Activity(uid, 0, 'home', loc[0], t7, t0))
        legs.append(Leg(uid, 0, 'pt', loc[0], loc[1], t0, t1, d[0]))
        activities.append(Activity(uid, 1, 'work', loc[1], t1, t2))
        legs.append(Leg(uid, 1, 'walk', loc[1], loc[2], t2, t3, d[1]))
        activities.append(Activity(uid, 2, 'shop', loc[2], t3, t4))
        legs.append(Leg(uid, 2, 'walk', loc[2], loc[1], t4, t5, d[1]))
        activities.append(Activity(uid, 3, 'work', loc[1], t5, t6))
        legs.append(Leg(uid, 3, 'pt', loc[1], loc[0], t6, t7, d[0]))
        activities.append(Activity(uid, 4, 'home', loc[0], t7, t0))

        tag = self.config.SOURCE
        plan = [Plan(activities, legs, tag)]
        keys = (
            'source', 'hsize', 'car', 'inc', 'hstr', 'gender', 'age', 'race', 'license', 'job', 'occ')
        values = [tag] * len(keys)
        attribute_dic = dict(zip(keys, values))

        return Agent(uid, plan, attribute_dic)


def is_wide(df):
    if len(df.columns) > 3:
        return True
    else:
        return False
