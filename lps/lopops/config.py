import os.path
from lps.config import GlobalConfig


class LoPopSConfig(GlobalConfig):

    SOURCE = 'lopops'
    PREFIX = ''
    LIMIT = None  # Limit output
    NOFREQ = False  # Ignore plan frequency for sampling
    NORM = None
    DUMMIES = False  # Remove dummy trips
    ALLCARS = False  # Force all modes to cars
    FORCEHOME = False  # Force all plans to type 'home' at end of plan

    MODEMAP = {'Bus': 'pt',
               'Car_driver': 'car',
               'Car_passenger': 'car',
               'Cycle': 'bike',
               'Other': 'car',
               'Rail': 'pt',
               'Taxi': 'car',
               'Van': 'car',
               'Walk': 'walk',
               'dummy': 'car',
               'unknown': 'car'
               }

    ACTIVITYMAP = {'Edu': 'education',
                   'Escort_Oth': 'escort',
                   'Escort_edu': 'escort',
                   'Escort_health': 'escort',
                   'Escort_work': 'escort',
                   'Home': 'home',
                   'Medical': 'medical',
                   'Missing': 'other',
                   'Oth_social': 'personal',
                   'Other': 'other',
                   'Other_work': 'work',
                   'Personal_bus': 'personal',
                   'Recreation': 'recreation',
                   'Shop_Food': 'shop',
                   'Shop_Oth': 'shop',
                   'Sport': 'recreation',
                   'Usual_work': 'work',
                   'Visit': 'visit',
                   'dummy': 'other',
                   'religious': 'religious'
                   }

    def __init__(self, global_config):

        self.SAMPLE = global_config.SAMPLE
        self.EPSG = global_config.EPSG
        self.SEED = global_config.SEED
        self.VERBOSE = global_config.VERBOSE
        self.OUTPATH = global_config.OUTPATH
        self.XMLPATH = global_config.XMLPATH
        self.XMLPATHATTRIBS = global_config.XMLPATHATTRIBS

        self.INPUTPATH = self.valid_file(
            os.path.join(
                global_config.data_location, 'plans', 'TravelPlans.csv'
            ),
            "LoPopS demand"
        )
        self.ZONESPATH = self.valid_file(
            os.path.join(
                global_config.data_location, 'plans', 'zoneSystem', 'ABM_Zones_002_LSOA.shp'
            ),
            "LoPopS demand zones"
        )
        self.ATTRIBPATH = self.valid_file(
            os.path.join(
                global_config.data_location, 'plans', 'HHsPerson2016_cat.csv'
            ),
            "LoPopS attributes"
        )

        self.RECORDS = {
            'sample': self.SAMPLE,
            'limit': self.LIMIT,
            'norm': self.NORM,
            'demand': self.INPUTPATH,
            'attributes': self.ATTRIBPATH,
            'zones_path': self.ZONESPATH,
            'dummies': self.DUMMIES
        }
