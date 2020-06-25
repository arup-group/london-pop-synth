from shapely.geometry import Point
from pyproj import Proj, transform
import pandas as pd
from halo import Halo
import s2sphere as s2

# custom
from utils import s2_geo_toolkit_ftns as s2_tools, aws_cognito_ftns, persistence, osm_ftns
from lps.core.population import Plan, Leg, Activity, Population, Agent


# these are the s2 cells as ripped from Region Coverer, which cover London
london_hex = ['47d897', '47d89c', '47d8b', '47df4b54', '47df4d', '47df54', '4875dc', '4875e4', '4875fc',
              '48761', '487624', '48763c', '487641', '48766c', '487674']


class Data:
    """
    Container for MoMo
    """
    def __init__(self, config):
        print('\n--------- Initiating MoMo Population Input ---------')
        self.config = config
        # momo data
        self.df_trips = self.load_and_prep_trips()
        # self.cognito_data = self.load_cognito()
        # lopops data - might be used for inferring activity or beefing out personal attributes
        # self.lopops_attributes = self.load_lopops_attributes()
        # self.lopops_trips = self.load_lopops_trips()
        print('Input Synthesis Loaded:')
        print("\t> MoMo inputs from: {}".format(config.MOMOTRIPSPATH))
        print("\t> outputs using epsg:{}".format(config.EPSG))

    def load_and_prep_trips(self):
        """
        Load trips
        :return: Pandas.DataFrame of momo inferred trips
        """
        with Halo(text='Loading and preparing MoMo trips data...', spinner='dots') as spinner:
            # csv that was a result of 'SELECT * FROM trip WHERE user_id IN (...)' query on the momo inferred data
            # database, trip table
            self.df_trips = persistence.read_content(self.config.MOMOTRIPSPATH)

            self.df_trips['origin_timestamp'] = pd.to_datetime(self.df_trips['origin_timestamp'])
            self.df_trips['destination_timestamp'] = pd.to_datetime(self.df_trips['destination_timestamp'])
            self.df_trips['date'] = pd.to_datetime(self.df_trips['origin_timestamp'].dt.date)

            self.df_trips = s2_tools.parse_spatial_data_df_trips(self.df_trips)
            self.df_trips = s2_tools.get_trips_to_from_s2_cells(self.df_trips, london_hex)
            self.df_trips = Data.naming_convention_df_trips(self)

            spinner.succeed('{} trips loaded'.format(len(self.df_trips)))
        return self.df_trips

    def load_cognito(self):
        """
        :return: Pandas DataFrame with cognito data
        """
        with Halo(text='Loading cognito data...', spinner='dots') as spinner:
            # extract user info from cognito
            users = list(self.df_trips['user_id'].unique())

            user_list = aws_cognito_ftns.get_cognito_user_list(self.config.cognito_region_name,
                                                               self.config.cognito_user_pool)
            _df = aws_cognito_ftns.get_cognito_users_dataframe(user_list,
                                                               requested_users_list=users)

            # TODO follow naming conventions

            spinner.succeed('{} users data loaded'.format(len(_df)))
        return _df

    def load_lopops_attributes(self):
        with Halo(text='Loading and renaming categorical values in lopops attributes data...', spinner='dots') as spinner:
            _df = persistence.read_content(self.config.ATTRIBPATH)
            # TODO follow naming conventions

        spinner.succeed('{} users data loaded'.format(len(_df)))
        return _df

    def load_lopops_trips(self):
        with Halo(text='Loading and renaming categorical values in lopops trips data...', spinner='dots') as spinner:
            _df = persistence.read_content(self.config.INPUTPATH)
            # follow naming conventions
            _df['dpurp'] = _df['dpurp'].map(self.config.ACTIVITYMAP)
            _df['mdname'] = _df['mdname'].map(self.config.MODEMAP)
        spinner.succeed('{} users data loaded'.format(len(_df)))
        return _df

    def naming_convention_df_trips(self):
        mode_encoding = {
            'walk': ['walk', 'walking', 'feet', 'on_foot', 'running', 'run'],
            'bike': ['cycling', 'bicycling', 'bicycle', 'cycle', 'bike'],
            'car': ['drive', 'driving', 'car', 'taxi', 'auto', 'motorbike', 'rideshare', 'car driver', 'motorcycle',
                    'private car', 'uber'],
            'pt': ['bus', 'train', 'lightrail', 'tram', 'commuter train', 'tube', 'metro rail', 'subway', 'muni',
                   'metro', 'underground', 'dlr', 'airplane', 'fly', 'aeroplane', 'transit', 'pt']
        }
        # flatten the dict above
        new_keys = []
        new_values = []
        for key, value in mode_encoding.items():
            for item in value:
                new_keys.append(item)
                new_values.append(key)
        flat_mode_dict = dict(zip(new_keys, new_values))

        series = self.df_trips['dominant_mode'].str.lower()

        modes_not_encoded = set(series) - set(new_keys)
        if len(modes_not_encoded) != 0:
            print('The following modes do not have encoding!')
            print(modes_not_encoded)

        self.df_trips['dominant_mode'] = series.map(flat_mode_dict)
        return self.df_trips

    def make_pop(self):
        """

        :return: mimi.population.Population object from MoMo data
        """
        population = Population()

        # for each uuid in the trips data, make a person and then extend the population. Return a population object.
        momo_users = list(self.df_trips['user_id'].unique())

        for user in momo_users:
            # TODO get cognito data for that user
            # _df_cog = self.cognito_data[self.cognito_data['user_id'] == user]
            attributes = make_attributes()

            _df_trips = self.df_trips[self.df_trips['user_id'] == user].copy()
            # make this into a person with plans, for one day
            plans, person_uid = make_plans(_df_trips, user)

            if plans is not None:
                momo_person = Agent(uid=person_uid, plans=plans, attributes=attributes)
                population.agents.append(momo_person)

        return population

    def sample(self, sampler, population=None):
        return self.make_pop()


def make_legs(df, person_uid):
    legs = []
    for idx in df.index:
        leg = df.loc[idx, :]
        legs.append(
            Leg(
                uid=person_uid,
                seq=idx,
                mode=leg['dominant_mode'],
                start_loc=Point(project_lat_lon_to_27700(leg['origin_lon'], leg['origin_lat'])),
                end_loc=Point(project_lat_lon_to_27700(leg['destination_lon'], leg['destination_lat'])),
                start_time=str(leg['origin_timestamp'].time()),
                end_time=str(leg['destination_timestamp'].time()),
                dist=leg['total_distance']))
    return legs


def infer_activity(lon, lat):
    # get osm data around the point in space
    osm_data = osm_ftns.download_osm(lon, lat, radius=300)
    # parse it for buildings
    buildings_data = osm_ftns.parse_osm_to_building_types(osm_data)
    # look at land use and number of buildings matching that land use
    return osm_ftns.infer_activity_from_osm_buildings_count(buildings_data)


def make_activities(df, person_uid):
    activities = []
    # activities are the life type things that happen between trips
    # let's assume the activity of being at home ends with the first trip of the day

    # let's assume the activity that is longest apart from being at home is work or education
    # based on age of the Person
    index = list(df.index)
    home_s2_cell = s2.Cell()
    for i in range(len(index)):
        # activity is sandwiched between the two trips=legs
        previous_leg = df.loc[index[i - 1], :]
        next_leg = df.loc[index[i], :]
        if i == 0:
            # assume a person's first trip is leaving 'home'
            home_s2_cell = next_leg['origin_s2']
            act = 'home'
        else:
            if home_s2_cell.intersects(next_leg['origin_s2']):
                # check that they aren't going home in between trips - compare cells on the highest level 30,
                # alternative implementation to consider neighbourhood via s2_geo_toolkit_ftns.neighbourhood_of_point
                # method
                act = 'home'
            else:
                # decide on activity type
                act = infer_activity(next_leg['origin_lon'], next_leg['origin_lat'])

        # the point in space of activity is the origin of the leg that takes person away from it
        point = Point(project_lat_lon_to_27700(next_leg['origin_lon'], next_leg['origin_lat']))
        start_time = str(previous_leg['destination_timestamp'].time())
        end_time = str(next_leg['origin_timestamp'].time())

        activities.append(
            Activity(
                uid=person_uid,
                seq=i,
                act=act,
                point=point,
                start_time=start_time,
                end_time=end_time))

        # if it was the last leg, append the final activity of staying in your house overnight
        if i == (len(index) - 1):
            activities.append(
                Activity(
                    uid=person_uid,
                    seq=i+1,
                    act='home',
                    point=Point(project_lat_lon_to_27700(df.loc[index[0], 'origin_lon'], df.loc[index[0], 'origin_lat'])),
                    start_time=str(next_leg['destination_timestamp'].time()),
                    end_time=str(df.loc[index[0], 'destination_timestamp'].time())))

    return activities


def make_plans(df, user):
    _df = df.copy()
    _df['date'] = _df['origin_timestamp'].dt.date

    for date in _df['date'].unique():
        single_day_df = _df[_df['date'] == date]
        if len(single_day_df) > 1:
            __df = single_day_df.sort_values('origin_timestamp').reset_index(drop=True)

            first_trip_idx = __df.index[0]
            last_trip_idx = __df.index[-1]

            if s2_tools.s2_intersection(
                    s2_cell_1=__df.loc[first_trip_idx, 'origin_s2'],
                    s2_cell_2=__df.loc[last_trip_idx, 'destination_s2'],
                    parent_level=14) and s2_tools.origins_destinations_intersect(
                    __df['origin_s2'],
                    __df['destination_s2'],
                    parent_level=14):
                # this day is a closed loop and the origin of the next trip is close enough to the destination
                # to make plans out of it
                # we assume people start at home
                person_uid = 'momo_{}_{}'.format(user, date)

                activities = make_activities(__df, person_uid)
                legs = make_legs(__df, person_uid)

                daily_plan = Plan(
                    activities=activities,
                    legs=legs,
                    source='momo'
                )
                # return the first feasible daily plan
                # TODO try finding a more interesting or average day
                return [daily_plan], person_uid
    return None, None


def make_attributes():
    # TODO user cognito and other data to estimate
    hsize = 'hsize_Arup'
    car_no = 'car_no_Arup'
    inc = 'inc_Arup'
    hstr = 'hstr_Arup'
    gender = 'gender_Arup'
    age = 'age_Arup'
    race = 'race_Arup'
    licence = 'licence_Arup'
    job = 'job_Arup'
    occ = 'occ_Arup'
    source = 'source_Arup'
    subpopulation = 'default'

    return {'hsize': hsize,
            'car': car_no,
            'inc': inc,
            'hstr': hstr,
            'gender': gender,
            'age': age,
            'race': race,
            'license': licence,
            'job': job,
            'occ': occ,
            'source': source,
            'subpopulation': subpopulation}


def project_lat_lon_to_27700(lon,lat):
    outProj = Proj(init='epsg:27700')
    inProj = Proj(init='epsg:4326')
    return transform(inProj,outProj,lon,lat)
