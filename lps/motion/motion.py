import pandas as pd
import numpy as np
import geopandas as gp
from halo import Halo
import os
from utils import persistence

from lps.core import samplers, generators
from lps.core.population import Population, Agent, Plan, Activity, Leg


class Demand:
    """
    Container for Motion Demand
    """

    def __init__(self, config):
        print('\n--------- Initiating Motion Population Inputs ---------')
        self.config = config

        self.attributes = self.load_xlsx(self.config.SEGMENTSPATH)
        self.outbound_factors = PeriodFactors(self.config, self.config.OUTBOUNDFACTORPATH)
        # self.return_factors = PeriodFactors(self.config, self.config.RETURNFACTORPATH)

        self.zones, self.regions_map = self.load_zones()
        self.filter = self.add_filter()

        print('Input Demand Loaded:')
        print("\t> outputs using epsg:{}".format(config.EPSG))
        print("\t> demand input from: {}".format(config.TOURS))
        print("\t> zone inputs from: {}".format(config.ZONESPATH))
        print("\t> saving to: {}".format(config.OUTPATH))

    def sample(self, sampler, population=None):
        """
        Adds a sample of the demand to the input Population Object, using the input Sampler Object
        :param sampler:
        :param population:
        :return: Population Object
        """
        if not population:
            print('Creating new population object')
            population = Population()

        total_count = 0

        for tour in self.config.TOURS:

            activity = self.config.TOURSACTIVITYMAP[tour]

            for mode_key in self.config.MODES:

                print('> segmentation for {} {}'.format(tour, mode_key))

                tour_segment_key = self.config.TOURSSEGMENTMAP.get(tour)
                tour_factor_key = self.config.TOURSFACTORSMAP.get(tour)
                mode = self.config.MODESMAP[mode_key]

                # Find base demand matrices
                demand_path = os.path.join(self.config.DEMANDPATH, tour, mode_key)
                demand_segments = sorted([path for path in persistence.list_dir(demand_path) if path.endswith('.CSV')])

                # Find base attribute segmentation
                attributes = self.attributes[tour_segment_key]
                # num_segments = len(attributes.Seg_No)
                #
                # assert num_segments == len(demand_segments)  # check that number of matrices == number of segments

                # Build demand object for each segment

                with Halo(text='building demand segments and sampling...', spinner='dots') as spinner:
                    for n, (demand_segment, (seg_no, attribute_series)) in enumerate(zip(demand_segments, attributes.iterrows())):

                        assert n == seg_no

                        # get income
                        car = attribute_series.car
                        gender = attribute_series.gender
                        job = attribute_series.job
                        occ = attribute_series.occ
                        income = attribute_series.inc
                        income_mapped = self.config.INCOMEMAP.get(income, 'All')

                        spinner.text = 'building demand for segment {}: car:{} gender:{} job:{} occ:{} inc:{}'.format(n, car, gender, job, occ, income)

                        # Build period factors
                        outbound_factors = self.outbound_factors.get_factor_map(tour_factor_key, mode_key, income_mapped)
                        # return_factors = self.return_factors.get_factor_map(tour_factor_key, mode_key, income)

                        # Build path for segment demand
                        full_path = os.path.join(demand_path, demand_segment)
                        outbound_demand = DayDemand(self, full_path)
                        sample_demand = sampler.get_sample_size(outbound_demand.total_demand)

                        if not sample_demand:  # skip if no demand sampled
                            spinner.text = 'skipping'
                            continue

                        outbound_demand.build_periods(outbound_factors)

                        for trip in range(sample_demand):

                            total_count += 1

                            spinner.text = "sampling gender:car:{} gender:{} job:{} occ:{} inc:{}: {}/{}".format(car, gender, job, occ, income, trip + 1, sample_demand)

                            # Sample Outbound
                            [out_period] = outbound_demand.period_sampler.sample(n=1)
                            [out_hour] = outbound_demand.period_demands[out_period].hour_sampler.sample()
                            out_time = generators.gen_minute(out_hour)

                            [(origin_zone, destination_zone)] = outbound_demand.period_demands[out_period].od_sampler.sample()
                            # origin_zone, destination_zone = zones

                            # Sample Inbound Time (from oposite period, ie am to pm return)
                            # return_period = return_demand.sampler.sample_exclude(out_period)
                            index = self.config.ALLPERIODS.index(out_period) - 2
                            return_period = list(self.config.PERIODTIMES.keys())[index]
                            [return_hour] = outbound_demand.period_demands[return_period].hour_sampler.sample()
                            return_time = generators.gen_minute(return_hour)

                            # Sample O-D points
                            origin = samplers.sample_point(origin_zone, self.zones)
                            destination = samplers.sample_point(destination_zone, self.zones)

                            # Get distance between pairs (for approx. journey time)
                            distance = samplers.get_approx_distance(origin, destination)
                            journey_time = samplers.build_journey_time(distance, mode=mode)

                            # Build up leg datetimes (method prevents leg wrapping)
                            out_depart_dt, out_arrive_dt = samplers.build_trip_times(out_time, journey_time, 'forward')
                            return_depart_dt, return_arrive_dt = samplers.build_trip_times(return_time, journey_time, 'back')

                            # Build Plan
                            uid = '{}_{}_{}_{}'.format(self.config.PREFIX, total_count, tour, mode)

                            t0 = out_depart_dt.time().strftime("%H:%M:%S")  # Home departure
                            t1 = out_arrive_dt.time().strftime("%H:%M:%S")  # Activity arrival
                            t2 = return_depart_dt.time().strftime("%H:%M:%S")  # Activity departure
                            t3 = return_arrive_dt.time().strftime("%H:%M:%S")  # Home arrival

                            activities = []
                            legs = []

                            if return_time > out_time:  # therefore no wrapping

                                activities.append(Activity(uid, 0, 'home', origin, t3, t0))
                                legs.append(Leg(uid, 0, mode, origin, destination, t0, t1, distance))
                                activities.append(Activity(uid, 1, activity, destination, t1, t2))
                                legs.append(Leg(uid, 1, mode, destination, origin, t2, t3, distance))
                                activities.append(Activity(uid, 2, 'home', origin, t3, t0))

                            else:  # eg a night shift - start with destination activity
                                activities.append(Activity(uid, 0, activity, destination, t1, t2))
                                legs.append(Leg(uid, 0, mode, destination, origin, t2, t3, distance))
                                activities.append(Activity(uid, 1, 'home', origin, t3, t0))
                                legs.append(Leg(uid, 1, mode, origin, destination, t0, t1, distance))
                                activities.append(Activity(uid, 2, activity, destination, t1, t2))

                            tag = '{}_{}'.format(self.config.SOURCE, tour)
                            plan = [Plan(activities, legs, tag)]

                            # keys = (
                            #     'source', 'hsize', 'car', 'inc', 'hstr', 'gender', 'age', 'race', 'license', 'job',
                            #     'occ')

                            default = 'unknown'
                            subpopulation = self.config.INCOMECONVERT.get(income, 'inc56')
                            if car == 'car0':
                                subpopulation += '_nocar'
                            attribute_dic = {'source': tag,
                                             'subpopulation': subpopulation,
                                             'hsize': default,
                                             'car': car,
                                             'inc': income,
                                             'hstr': default,
                                             'gender': gender,
                                             'age': default,
                                             'race': default,
                                             'license': default,
                                             'job': job,
                                             'occ': occ
                                             }

                            population.agents.append(Agent(uid, plan, attribute_dic))

                    spinner.succeed("{} samples taken".format(total_count))
        return population

    def load_xlsx(self, path):
        """
        :return: dictionary of Pandas DataFrames
        """
        # xl_file = pd.ExcelFile(self.config.SEGMENTSPATH)
        dfs = pd.read_excel(path, sheet_name=None)  # load xlsx data
        return dfs

    def load_zones(self):
        """
        Load demand zones and build PCIO region map
        :return: GeoPandas GeoDataFrame, dictionary
        """
        with Halo(text='loading zone data...', spinner='dots') as spinner:
            gdf = gp.read_file(self.config.ZONESPATH)
            if not gdf.crs.get('init') == self.config.EPSG:
                spinner.text = 'converting zones to espg:{}'.format(self.config.EPSG)
                gdf = gdf.to_crs(epsg=self.config.EPSG)

            # Build zones-regions dict
            zone_ids = gdf.loc[:, 'Sequential_9_1']
            region_ids = gdf.loc[:, 'PCIO']
            regions_map = dict(zip(zone_ids, region_ids))

            gdf = gdf.loc[:, ['Sequential_9_1', 'geometry']]
            gdf = gdf.set_index('Sequential_9_1')

            spinner.text = 'buffering zone data'
            gdf.geometry = gdf.buffer(0)

            spinner.succeed('{} zones loaded and buffered'.format(len(gdf)))
        return gdf, regions_map

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


class TourDemand:
    """
    Demand container for given tour type
    """
    def __init__(self):
        raise NotImplementedError


class ModeDemand:
    """
    Demand container for given tour and mode
    """
    def __init__(self):
        raise NotImplementedError


class SegmentDemand:
    """
    Demand container for given tour, mode and segment
    """
    def __init__(self):
        raise NotImplementedError


class DayDemand:
    """
    Daily Demand for a Motion Tour-Mode-Income combination.
    Contains demand for indfividual periods, total demand and a sampler for sampling the period
    from the all-day demand profile
    """

    def __init__(self, master, path):
        self.master = master
        self.config = master.config
        self.zones = master.zones
        self.filter = master.filter
        self.period_demands = {}
        self.period_sampler = None
        self.demand = self.load_demand_df(path)

        self.total_demand = samplers.probability_rounder(sum(self.demand.freq))

    def build_periods(self, period_factors):

        for period, factor_map in period_factors.items():
            self.period_demands[period] = PeriodDemand(self, period, factor_map)

        totals = [d.total_demand for d in self.period_demands.values()]
        self.period_sampler = generators.FrequencyDistribution(list(self.period_demands.keys()), totals)

    def load_demand_df(self, path):
        demand = pd.read_csv(path)

        if is_wide(demand):
            id_vars = demand.columns[0]
            value_vars = demand.columns[1:]
            demand = pd.melt(demand, id_vars=id_vars, value_vars=value_vars)
            demand.columns = ['o', 'd', 'freq']
            demand = demand.astype({'o': int, 'd': int, 'freq': float})
        else:
            raise ValueError('unknown input format, only wide (ie matrix) is implemented')

        demand = self.master.filterer(demand)
        demand['od_zones'] = tuple(zip(demand.o, demand.d))
        origin_regions = demand.o.map(self.master.regions_map)
        destination_regions = demand.d.map(self.master.regions_map)
        demand['od_regions'] = tuple(zip(origin_regions, destination_regions))

        return demand


class PeriodDemand:
    """
    Period Demand.
    Includes total period demand and a sampler for sampling origin-destinations
    """

    def __init__(self, day_demand, period, factor_map):
        self.config = day_demand.config
        demand = day_demand.demand.copy()
        demand['factors'] = demand.od_regions.map(factor_map)
        demand.freq *= demand.factors
        self.od_sampler = generators.FrequencyDistribution(demand.od_zones, demand.freq)
        self.total_demand = sum(demand.freq)
        self.hour_sampler = generators.UniformDistributionGen(range_in=self.config.PERIODTIMES[period])


class PeriodFactors:
    """
    Object for handling input demand factors
    """

    period_col_map = {'AM': 1,
                      'IP': 10,
                      'PM': 19}

    def __init__(self, config, xlsx_path):
        self.config = config
        self.xlsx = pd.read_excel(xlsx_path, sheet_name=None)  # load xlsx data

    def get_factor_map(self, tour, mode, income):
        """
        Builds a dictionary of dictionaries for period factors
        :param tour:
        :param mode:
        :param income:
        :return:
        """
        period_factors = {}
        df = self.xlsx[tour]
        remainder = 1
        for period in self.config.PERIODS:
            mode_index = self.find_mode_index(df, 0, mode)
            row = self.find_income_index(df, 0, mode_index, income)
            col = self.period_col_map.get(period)
            selected_df = df.iloc[row + 2:row + 8, col + 1:col + 7]
            selected_df.index = range(1, 7)
            selected_df.columns = range(1, 7)

            selected_df.loc[7] = selected_df.loc[6]
            selected_df = selected_df.append(selected_df.loc[6, :], ignore_index=True)
            selected_df.loc[7, 7] = selected_df.loc[6, 6]

            selected_df = melt_demand_matrix(selected_df)
            freq = np.array(selected_df.freq)
            remainder -= freq
            od = tuple(zip(selected_df.o, selected_df.d))
            period_factors[period] = dict(zip(od, freq))

        period_factors['night'] = dict(zip(od, remainder))  # add remainder to 'night'

        return period_factors

    def find_mode_index(self, df, col, mode):
        search = self.config.MODESFACTORSMAP.get(mode, 'All modes')
        for index, key in enumerate(df.iloc[:, col]):
            if key == search:
                return index
        raise LookupError('cannot find {} in this table'.format(search))

    def find_income_index(self, df, col, start, income):
        search = self.config.INCOMEMAP.get(income, 'All')
        for index in range(start + 1, start + 32):
            key = df.iloc[index, col]
            if key in list(self.config.MODESMAP.values()):
                return self.find_income_index(df, col, start, 'unknown')
            if key == search:
                return index
        raise LookupError('cannot find {} in this table'.format(search))


def is_wide(df):
    if len(df.columns) > 3:
        return True
    else:
        return False


def melt_demand_matrix(df):
    """
    Transform wide format demand matrix to narrow format [origins, destination, weight]
    :param df:
    :return:
    """
    df = df.reset_index()
    id_vars = df.columns[0]
    value_vars = df.columns[1:]

    df = pd.melt(df, id_vars=id_vars, value_vars=value_vars)
    df.columns = ['o', 'd', 'freq']
    return df.astype({'o': int, 'd': int, 'freq': float})

