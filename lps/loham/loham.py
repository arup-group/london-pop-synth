import pandas as pd
from datetime import time, timedelta, datetime
import numpy as np
import geopandas as gp
import random
from halo import Halo

from lps.core import samplers, generators
from lps.core.population import Population, Agent, Plan, Activity, Leg

times = {
    (7, 10): 0,
    (10, 16): 1,
    (16, 19): 2
}


class Demand:

    def __init__(self, config):
        print('\n--------- Initiating LoHAM (freight) Population Input ---------')
        self.config = config
        self.zones = self.load_zones()
        self.london = self.load_filter()
        self.demand = self.load_demand()
        self.num_plans = None
        self.sampler = None
        print('Input Demand Loaded:')
        print("\t> daily demand distribution: {}".format(config.WEIGHTS))
        print("\t> outputs using epsg:{}".format(config.EPSG))
        print("\t> AM demand inputs from: {}".format(config.AMPATH))
        print("\t> Inter-peak demand inputs from: {}".format(config.INTERPATH))
        print("\t> PM demand inputs from: {}".format(config.PMPATH))
        print("\t> zone inputs from: {}".format(config.ZONESPATH))
        print("\t> saving to: {}".format(config.OUTPATH))

    # load zones
    def load_zones(self):
        """
        Load zones
        :return: GeoPandas GeoDataFrame
        """
        with Halo(text='Loading zone data...', spinner='dots') as spinner:
            gdf = gp.read_file(self.config.ZONESPATH)
            if not gdf.crs.get('init') == self.config.EPSG:
                spinner.text = 'converting zones to espg:{}'.format(self.config.EPSG)
                gdf = gdf.to_crs(epsg=self.config.EPSG)
            gdf = gdf.loc[:, ['renumber_I', 'london', 'geometry']]
            gdf = gdf.set_index('renumber_I')
            spinner.succeed('{} zones loaded'.format(len(gdf)))
        return gdf

    def load_filter(self):
        return pd.Series(self.zones.loc[self.zones.london == 1, :].index)

    def filter(self, df):
        return df.loc[df.o.isin(self.london) | df.d.isin(self.london), :]

    # load OD pairs
    def load_demand(self):
        with Halo(text='loading demand inputs...', spinner='dots') as spinner:
            am = pd.read_csv(self.config.AMPATH, header=None, names=['o', 'd', 'freq'])
            inter = pd.read_csv(self.config.INTERPATH, header=None, names=['o', 'd', 'freq'])
            pm = pd.read_csv(self.config.PMPATH, header=None, names=['o', 'd', 'freq'])
            spinner.succeed('input demand loaded')

            # TODO SENSE CHECK - halve demand so that return trip does not cause double counting
            am.freq = am.freq / 2
            inter.freq = inter.freq / 2
            pm.freq = pm.freq / 2

        with Halo(text='filtering am demand (1/3) for london...', spinner='dots') as spinner:
            am = self.filter(am)
            spinner.text = 'filtering inter demand (2/3) for london...'
            inter = self.filter(inter)
            spinner.text = 'filtering pm demand (3/3) for london...'
            pm = self.filter(pm)

            am_hour = sum(am.freq)
            inter_hour = sum(inter.freq)
            pm_hour = sum(pm.freq)
            spinner.succeed('inputs filtered for London')

        print("\t> AM-peak hourly demand is {} trips".format(int(am_hour)))
        print("\t> Inter-peak hourly demand is {} trips".format(int(inter_hour)))
        print("\t> PM-peak hourly demand is {} trips".format(int(pm_hour)))
        print("\t> Overnight hourly demand approximated as {} trips".format(int(self.config.WEIGHTS[3] * inter_hour)))

        with Halo(text='Modelled daily demand profile...', spinner='dots') as spinner:
            trips = 0
            daily_hours = np.arange(24)
            daily_profile = []
            for hour in daily_hours:  # Build profile
                demand = self.config.WEIGHTS[3] * inter_hour
                for (start, end), period in times.items():
                    if end > hour >= start:
                        weight = self.config.WEIGHTS[period]
                        if period == 0:  # AM
                            demand = am_hour * weight
                        elif period in [1, 3]:  # Inter peak or night
                            demand = inter_hour * weight
                        elif period == 2:  # PM
                            demand = pm_hour * weight
                        # break
                daily_profile.append(demand)
                trips += demand
            spinner.succeed('Daily demand model complete')

        if self.config.VERBOSE:
            for hour in daily_hours:
                hour_str = time(hour).strftime("%H:%M")
                norm = int(20 * daily_profile[hour] / max(am_hour, inter_hour, pm_hour))
                print(hour_str + ': ' + ('/' * norm))

        daily_profile = np.array(daily_profile)
        daily_sampler = (daily_hours, daily_profile)

        if self.config.NORM:  # Normalise
            print("Normalising")
            daily_profile = self.config.NORM * daily_profile / trips

        print("{} total trips loaded".format(int(sum(daily_profile))))

        with Halo(text='Modelled O-D demand profiles...', spinner='dots') as spinner:
            am_profile = np.array(am.freq)
            am_od = tuple(zip(am.o, am.d))
            am_sampler = (am_od, am_profile)
            inter_profile = np.array(inter.freq)
            inter_od = tuple(zip(inter.o, inter.d))
            inter_sampler = (inter_od, inter_profile)
            pm_profile = np.array(pm.freq)
            pm_od = tuple(zip(pm.o, pm.d))
            pm_sampler = (pm_od, pm_profile)
            spinner.succeed('O-D demand profiles completed')

        return {'daily': daily_sampler, 'am': am_sampler, 'inter': inter_sampler, 'pm': pm_sampler}

    def sample(self, sampler, population=None):

        if not population:
            print('Creating new population object')
            population = Population()

        with Halo(text='Sampling from distributions', spinner='dots') as spinner:

            n = sum(self.demand['daily'][1])  # total daily demand
            n = sampler.get_sample_size(n)

            # Sample n times (over samples but no significant slow down)
            hours = random.choices(self.demand['daily'][0], weights=self.demand['daily'][1], k=n + 1)
            start_times = generators.gen_minutes(hours)
            am_od_ids = random.choices(self.demand['am'][0], weights=self.demand['am'][1], k=n + 1)
            inter_od_ids = random.choices(self.demand['inter'][0], weights=self.demand['inter'][1], k=n + 1)
            pm_od_ids = random.choices(self.demand['pm'][0], weights=self.demand['pm'][1], k=n + 1)
            spinner.succeed('Sampling completed for {} plans'.format(n))

        with Halo(text="Building trips...", spinner="dots") as spinner:
            for trip in range(n):
                spinner.text = "Built {} of {} trips...".format(trip, n)

                # Make unique ID
                uid = self.config.PREFIX + str(trip)

                # Random sample hour from daily profile distribution
                hour = hours[trip]

                # Random sample minute to make time stamp
                start_time = start_times[trip]

                # Select Peak or Inter-Peal O-D pairs and weights
                period = 3
                for (start, end), p in times.items():
                    if end > hour >= start:
                        period = p
                        break
                if period == 0:  # Use am matrix
                    o_id, d_id = am_od_ids[trip]
                elif period == 2:  # Use pm matrix
                    o_id, d_id = pm_od_ids[trip]
                else:  # Use inter-peak matrix
                    o_id, d_id = inter_od_ids[trip]

                # Sample O-D points
                o = samplers.sample_point(o_id, self.zones)
                d = samplers.sample_point(d_id, self.zones)

                # Get distance between pair (for approx. journey time)
                dist = samplers.get_approx_distance(o, d)
                journey_time = samplers.build_journey_time(dist, mode=self.config.MODE, limit=72000)  # limited at 20 hours

                # Build up day times
                dt = datetime(2000, 1, 1, start_time.hour, start_time.minute)
                dt0, dt1 = samplers.build_trip_times(dt, journey_time, push='forward')  # function prevents leg straddling day
                minutes = random.randint(1, 6) * 5
                dt2 = dt1 + timedelta(seconds=(minutes * 60))  # Assume 5 to 30 minutes at destination
                dt3 = dt2 + journey_time

                population.agents.append(self.build_plan(uid, o, d, dt0, dt1, dt2, dt3, dist))

            spinner.succeed("Plan simulation completed for {} plans".format(n))
        return population

    def build_plan(self, uid, o, d, dt0, dt1, dt2, dt3, dist=None):

        t0 = dt0.time().strftime("%H:%M:%S")  # Home departure
        t1 = dt1.time().strftime("%H:%M:%S")  # Delivery arrival
        t2 = dt2.time().strftime("%H:%M:%S")  # Delivery departure
        t3 = dt3.time().strftime("%H:%M:%S")  # Home arrival

        activities = []
        legs = []

        if (dt1 - dt0).days or (dt1 - dt0).seconds > (12 * 60 * 60):  # long journey - don't try to return
            activities.append(Activity(uid, 0, 'depot', o, t1, t0))
            legs.append(Leg(uid, 0, self.config.MODE, o, d, t0, t1, dist))
            activities.append(Activity(uid, 1, 'delivery', d, t1, t0))
        else:
            if dt0.time() < dt2.time():  # Regular sequence with delivery end time after depo departure
                activities.append(Activity(uid, 0, 'depot', o, t3, t0))
                legs.append(Leg(uid, 0, self.config.MODE, o, d, t0, t1, dist))
                activities.append(Activity(uid, 1, 'delivery', d, t1, t2))
                legs.append(Leg(uid, 1, self.config.MODE, d, o, t2, t3, dist))
                activities.append(Activity(uid, 2, 'depot', o, t3, t0))
            else:  # sequence starting at delivery
                activities.append(Activity(uid, 0, 'delivery', d, t1, t2))
                legs.append(Leg(uid, 0, self.config.MODE, d, o, t2, t3, dist))
                activities.append(Activity(uid, 1, 'depot', o, t3, t0))
                legs.append(Leg(uid, 1, self.config.MODE, o, d, t0, t1, dist))
                activities.append(Activity(uid, 2, 'delivery', o, t1, t2))

        tag = self.config.SOURCE
        plan = [Plan(activities, legs, tag)]
        keys = (
            'source', 'subpopulation', 'hsize', 'car', 'inc', 'hstr', 'gender', 'age', 'race', 'license', 'job', 'occ')
        values = [tag] * len(keys)
        attribute_dic = dict(zip(keys, values))

        return Agent(uid, plan, attribute_dic)
