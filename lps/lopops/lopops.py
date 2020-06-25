from lps.core import samplers
from lps.core.population import Population, Agent, Plan, Activity, Leg
from halo import Halo
import pandas as pd
import geopandas as gp


class Data:
    """
    Container for TFL synthesised plans
    """

    def __init__(self, config):
        print('\n--------- Initiating LoPopS Population Input ---------')
        self.config = config
        self.zones = self.load_zones()
        self.attributes = self.load_attributes()
        self.df = self.prepare()
        self.num_plans = None
        self.sampler = None
        print('Input Synthesis Loaded:')
        print("\t> pop inputs from: {}".format(config.INPUTPATH))
        print("\t> area inputs from: {}".format(config.ZONESPATH))
        print("\t> outputs using epsg:{}".format(config.EPSG))

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
            gdf = gdf.set_index('ZoneID')
            spinner.succeed('{} zones loaded'.format(len(gdf)))
        return gdf

    def load(self):
        """
        :return: Pandas DataFrame
        """
        with Halo(text='Loading data...', spinner='dots') as spinner:
            df = pd.read_csv(self.config.INPUTPATH)  # load csv data
            spinner.succeed('{} trips loaded'.format(len(df)))
        return df

    def load_attributes(self):
        """
        :return: Pandas DataFrame
        """
        with Halo(text='Loading attributes data...', spinner='dots') as spinner:
            df = pd.read_csv(self.config.ATTRIBPATH, index_col='recID')  # load csv data
            spinner.succeed('{} attributes loaded'.format(len(df)))
        return df

    def prepare(self):
        """
        Method for returning parsed trip
        :return: list of Plan Objects
        """
        df = self.load()

        with Halo(text='Preparing data...', spinner='dots') as spinner:
            df = df.sort_values(['tpid', 'tseqno'])
            spinner.text = 'population data sorted'
            df = df.groupby('tpid')
            self.num_plans = len(df)
            spinner.succeed('raw trip data sorted and grouped into {} plans'.format(self.num_plans))

        return df

    def sample(self, sampler, population=None):
        """
        Sample from the input plans data:
        1) Initiate Sampler to keep track of sampling
        2) Loop through all plans
        3) Get attributes for person
        4) Initiate a Parser with plan
        5) Sample from the Parser
        6) Add returned People to the Population

        :param sampler: Sampler object
        :param population: Population object
        :return: Population object
        """
        if not population:
            print('Creating new population object')
            population = Population()

        self.sampler = sampler

        with Halo(text='Sampling...', spinner='dots') as spinner:
            for index, (tpid, day_plan) in enumerate(self.df):
                spinner.text = '{} plans sampled'.format(sampler.sample_count)

                # Get attributes for tpid
                pid_attributes = dict(self.attributes.loc[tpid][2:])

                # Initiate the parser for the tpid
                parser = Parser(self.config, tpid, day_plan, self.zones, pid_attributes)

                # Sample for the parser using the sampler, not that may return no people
                # The sampler keeps track of sampling for all instances of the parser
                people = parser.sample(self.sampler)

                # add sampled people (with plan) to the population
                if people:
                    population.agents.extend(people)
                if self.config.LIMIT and (sampler.sample_count >= self.config.LIMIT):  # break if limit exceeded
                    spinner.succeed('limit reached: {} plans sampled'.format(sampler.sample_count))
                    break
        spinner.succeed('{} plans sampled'.format(sampler.sample_count))
        return population


class Parser:
    """
    Intermediate object for holding trip info that can then be sampled
    """

    def __init__(self, config, tpid, df, zones, attributes):
        self.config = config
        self.tpid = tpid
        self.df = df
        self.zones = zones
        self.dummy = None
        self.first = df.iloc[0]
        self.freq = self.first.Freq16
        self.attributes = attributes
        if self.config.NOFREQ:
            self.freq = 1

        self.num_trips = len(df.Freq16)

    def sample(self, sampler):
        """

        :param sampler:
        :param count:
        :param sample_count:
        :return:
        """
        people = []
        for person in range(self.freq):  # generate person and plan using frequency weighting

            if sampler.sample():  # Checks for sample and updates sampler counts
                people.append(self.parse(person))

            if self.config.LIMIT and (sampler.sample_count >= self.config.LIMIT):
                break

        return people  # can sample be safely removed from this loop?

    def parse(self, person):
        """
        Method to initiate parse
        :param person: integer
        :return: Person Object for population
        """
        uid = self.config.PREFIX + str(self.tpid) + '_' + str(person)
        return self.infer_plan(uid)

    def infer_plan(self, uid):
        """
        Method for inferring plans from synthesised trips
        :param uid:
        :return: Person Object for population
        """

        if self.config.VERBOSE:
            print(self.tpid)
            print(uid)
            print(self.freq)
            print(self.num_trips)
            print(self.df.loc[:, ['tpid', 'tseqno', 'mdname', 'dpurp', 'tstime', 'tetime']])

        ozone = list(self.df.ozone)
        dzone = list(self.df.dzone)
        dpurp = list(self.df.dpurp)
        mdname = list(self.df.mdname)
        tstime = list(self.df.tstime)
        tetime = list(self.df.tetime)

        last_purpose = None
        new_pair = False

        act_locations = [None] * (self.num_trips + 1)
        act_start_times = [None] * (self.num_trips + 1)
        act_end_times = [None] * (self.num_trips + 1)
        act_types = ['Home'] * (self.num_trips + 1)  # assumes home if no inference made

        for t in range(self.num_trips):  # loop through trips
            trip_purpose = dpurp[t]
            act_locations[t] = ozone[t]  # get trip origin
            act_start_times[t] = samplers.get_timestamp(tetime[t - 1])  # activity start time = prev trip end
            act_end_times[t] = samplers.get_timestamp(tstime[t])

            # TODO check/improve activity inference
            # currently defaults to home. If new trip purpose is found then sets next activity to that purpose.
            # If repeated trip purpose then assumes this is a return trip and defaults to home activity.
            # Note that first activity will always be home in this case but that plan does not need to return home.
            if trip_purpose != last_purpose or new_pair:
                act_types[t + 1] = trip_purpose
                new_pair = False
            else:
                new_pair = True

            last_purpose = trip_purpose  # reset lookback

        act_locations[-1] = dzone[-1]
        act_start_times[-1] = samplers.get_timestamp(tetime[-1])
        act_end_times[-1] = samplers.get_timestamp(tstime[0])

        # ----------- Force home -----------
        if self.config.FORCEHOME:
            act_types[-1] = 'Home'

        # ----------- Deal with dummy legs -----------
        num_trips = self.num_trips
        if not self.config.DUMMIES:
            if self.first.dpurp == 'dummy':
                del act_types[1]
                del act_locations[1]
                del act_start_times[1]
                del act_end_times[1]
                num_trips = num_trips - 1

        # ----------- Build unique location coordinates -----------

        # Build unique locations for each unique activity (so that 'home' is always same coords for example)
        # Note that any repeat of same activity in same zone should repeat coordinates
        act_pairs = list(zip(act_types, act_locations))
        act_uniques = list(set(act_pairs))
        act_points = [samplers.sample_point(loc, self.zones) for (act, loc) in act_uniques]
        act_loc_dict = dict(zip(act_uniques, act_points))
        act_points = [act_loc_dict.get(p) for p in act_pairs]

        # ----------- Convert to MATSIM -----------
        mode_dict = self.config.MODEMAP
        if self.config.ALLCARS:
            mode_dict = {}
        t_modes = [mode_dict.get(m, 'car') for m in mdname]  # default to car

        act_dict = self.config.ACTIVITYMAP
        act_types = [act_dict.get(a, 'other') for a in act_types]

        # ----------- Build plan objects -----------
        activities = []
        legs = []
        for t in range(num_trips):
            activities.append(Activity(uid,
                                       t,
                                       act_types[t],
                                       act_points[t],
                                       act_start_times[t],
                                       act_end_times[t]))
            legs.append(Leg(uid,
                            t,
                            t_modes[t],
                            act_points[t],
                            act_points[t + 1],
                            act_end_times[t],
                            act_start_times[t + 1],
                            samplers.get_approx_distance(act_points[t], act_points[t + 1])
                            )
                        )

            if self.config.VERBOSE:
                print(activities[t].report())
                print(legs[t].report())

        # Get final activity
        activities.append(Activity(uid,
                                   self.num_trips,
                                   act_types[-1],
                                   act_points[-1],
                                   act_start_times[-1],
                                   act_end_times[-1]))
        if self.config.VERBOSE:
            print(activities[-1].report())

        tag = self.config.SOURCE
        plan = [Plan(activities, legs, tag)]
        self.attributes['source'] = self.config.SOURCE
        subpopulation = self.attributes['inc']
        if self.attributes['car'] == 'car0':
            subpopulation += '_nocar'
        self.attributes['subpopulation'] = subpopulation

        return Agent(uid, plan, self.attributes)
