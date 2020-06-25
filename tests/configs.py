import os
import toml
from typing import List
from datetime import datetime
from utils import persistence


class GlobalConfig:
    """
    Main Config.
    """
    def __init__(self, path: str) -> None:
        """
        Config object constructor.
        :param path: Path to scenario configuration TOML file
        """
        parsed_toml = toml.load(path, _dict=dict)

        # Scenario settings
        self.SOURCE = path

        # Setup
        self.SOURCES = self.valid_samplers(parsed_toml["setup"]["sources"])
        self.SAMPLE = self.valid_sample_float(parsed_toml["setup"]["sample"])
        self.EPSG = self.valid_int(parsed_toml["setup"]["epsg"], "epsg")
        self.SEED = self.valid_int(parsed_toml["setup"]["seed"], "seed")
        self.VERBOSE = self.valid_bool(parsed_toml["setup"]["verbose"], "verbose")

        # Paths
        self.data_location = self.valid_path(parsed_toml["paths"]["data_dir"], "data_dir")
        self.OUTPATH = self.valid_path(parsed_toml["paths"]["out_dir"], "out_dir", create=True)
        self.plans_name = parsed_toml["paths"]["plans_name"]
        self.XMLPATH = os.path.join(self.OUTPATH, self.plans_name)
        self.attributes_name = parsed_toml["paths"]["attributes_name"]
        self.XMLPATHATTRIBS = os.path.join(self.OUTPATH, self.attributes_name)

        # Records to include in output and log:
        self.RECORDS = {
            'config': self.SOURCE,
            'outpath': self.OUTPATH,
            'timestamp': str(datetime.now()),
            'data_dir': self.data_location,
            'sources': self.SOURCES,
            'sample': self.SAMPLE,
            'crs': self.EPSG,
            'seed': self.SEED,
            'plans_name': self.XMLPATH,
            'attributes_name': self.XMLPATHATTRIBS,
        }

    def print_records(self):
        for k, v in self.RECORDS.items():
            print('\t> {}: {}'.format(k, v))

    @staticmethod
    def valid_path(path: str, field_name: str = 'missing', create: bool = False) -> str:
        """
        Raise exception if specified path does not exist, otherwise return path.
        :param path: Path to check
        :param field_name: Field name to use in exception if path does not exist
        :param create: create given path if missing, boolean, default=False
        :return: Pass through path if it exists
        """
        if not persistence.dir_exists(path):
            if not persistence.is_s3_location(path) and create:
                print(f"Creating directory; {path}")
                os.mkdir(path)
            else:
                raise Exception(f"Specified path for {field_name}: {path} does not exist")
        return path

    @staticmethod
    def valid_file(path: str, field_name: str = 'missing') -> str:
        """
        Raise exception if specified path does not exist, otherwise return path.
        :param path: Path to check
        :param field_name: Field name to use in exception if path does not exist
        :return: Pass through path if it exists
        """
        if not persistence.file_exists(path):
            raise Exception(f"Specified path for {field_name}: {path} does not exist")
        return path

    @staticmethod
    def valid_samplers(inp: List[str]) -> List[str]:
        """
        :param inp: list if strings expected
        :return: list[str]
        """
        if not inp and not all(isinstance(s, str) for s in inp):
            raise Exception(
                f'Specified samplers: ({inp}) expected to be list of strings'
            )
        return inp

    @staticmethod
    def valid_sample_float(inp: float) -> float:
        """
        Raise exception if specified float is outside an acceptable range, i.e.
        beyond [0.01, 100], otherwise return scale factor.
        :param inp: Scale factor
        :return: Pass through scale factor if valid
        """
        if inp < 0.01 or inp > 100:
            raise Exception(
                "Specified sample percentage ({}) not in valid range".format(inp)
            )
        return float(inp)

    @staticmethod
    def valid_int(inp: int, field_name: str) -> int:
        """
        :param inp: integer expected
        :param field_name: Field name to use in exception
        :return: int
        """
        if not isinstance(inp, int):
            raise Exception(
                f'Specified {field_name}: ({inp}) expected to be integer'
            )
        return inp

    @staticmethod
    def valid_bool(inp: bool, field_name: str) -> bool:
        """
        :param inp: bool expected
        :param field_name: Field name to use in exception
        :return: bool
        """
        if not isinstance(inp, bool):
            raise Exception(
                f'Specified {field_name}: ({inp}) expected to be boolean'
            )
        return inp


class LoHAMLGVConfig(GlobalConfig):

    SOURCE = 'loham'
    MODE = 'car'
    PREFIX = 'lgv_'
    WEIGHTS = (1, 1, 1, 0.01)  # (am , inter, pm, night)
    NORM = None  # Set total number of plans (approx trips / 2)
    LIMIT = None  # Limit output

    def __init__(self, global_config):

        self.SAMPLE = global_config.SAMPLE
        self.EPSG = global_config.EPSG
        self.SEED = global_config.SEED
        self.VERBOSE = global_config.VERBOSE
        self.OUTPATH = global_config.OUTPATH
        self.XMLPATH = global_config.XMLPATH
        self.XMLPATHATTRIBS = global_config.XMLPATHATTRIBS

        self.root = self.valid_path(
            os.path.join(
                global_config.data_location, 'loham', 'lgv'
            ),
            "LGV demand root"
        )
        self.AMPATH = self.valid_file(
            os.path.join(
                self.root, 'L3_5194Z_R006_ADJ_R11_AM_E64_LGV.csv'
            ),
            "LGV LoHAM AM-period demand"
        )
        self.INTERPATH = self.valid_file(
            os.path.join(
                self.root, 'LGV_L3_5194Z_R005_ADJ_R11_IP_E64.csv'
            ),
            "LGV LoHAM INTER-period demand"
        )
        self.PMPATH = self.valid_file(
            os.path.join(
                self.root, 'LGV_L3_5194Z_R005_ADJ_R11_PM_E64.csv'
            ),
            "LGV LoHAM PM-period demand"
        )
        self.ZONESPATH = self.valid_path(
            os.path.join(
                global_config.data_location, 'loham', 'freight_zones'
            ),
            "LGV LoHAM demand zones"
        )
        self.FILTERPATH = self.valid_path(
            os.path.join(
                global_config.data_location, 'london', 'London-wards-2018_ESRI'
            ),
            "LGV LoHAM spatial filter"
        )

        self.RECORDS = {
            'sample': self.SAMPLE,
            'limit': self.LIMIT,
            'norm': self.NORM,
            'am_demand': self.AMPATH,
            'inter_demand': self.INTERPATH,
            'pm_path': self.PMPATH,
            'day_weights': self.WEIGHTS,
            'zones_path': self.ZONESPATH,
            'filter_path': self.FILTERPATH,
        }


class LoHAMHGVConfig(GlobalConfig):

    INCLUDE = False
    SOURCE = 'freight'
    MODE = 'car'
    PREFIX = 'hgv_'
    WEIGHTS = (1, 1, 1, 0.01)  # (am , inter, pm, night)
    NORM = None  # Set total number of plans (approx trips / 2)
    LIMIT = None  # Limit output

    def __init__(self, global_config):

        self.SAMPLE = global_config.SAMPLE
        self.EPSG = global_config.EPSG
        self.SEED = global_config.SEED
        self.VERBOSE = global_config.VERBOSE
        self.OUTPATH = global_config.OUTPATH
        self.XMLPATH = global_config.XMLPATH
        self.XMLPATHATTRIBS = global_config.XMLPATHATTRIBS

        self.root = self.valid_path(
            os.path.join(
                global_config.data_location, 'loham', 'hgv'
            ),
            "HGV demand root"
        )
        self.AMPATH = self.valid_path(
            os.path.join(
                self.root, 'HGV_L3_5194Z_R006_ADJ_R11_AM_E65.csv'
            ),
            "HGV LoHAM AM-period demand"
        )
        self.INTERPATH = self.valid_path(
            os.path.join(
                self.root, 'HGV_L3_5194Z_R005_ADJ_R11_IP_E65.csv'
            ),
            "HGV LoHAM INTER-period demand"
        )
        self.PMPATH = self.valid_path(
            os.path.join(
                self.root, 'HGV_L3_5194Z_R005_ADJ_R11_PM_E65.csv'
            ),
            "HGV LoHAM PM-period demand"
        )
        self.ZONESPATH = self.valid_path(
            os.path.join(
                global_config.data_location, 'loham', 'freight_zones'
            ),
            "HGV LoHAM demand zones"
        )
        self.FILTERPATH = self.valid_path(
            os.path.join(
                global_config.data_location, 'london', 'London-wards-2018_ESRI'
            ),
            "HGV LoHAM spatial filter"
        )

        self.RECORDS = {
            'sample': self.SAMPLE,
            'limit': self.LIMIT,
            'norm': self.NORM,
            'am_demand': self.AMPATH,
            'inter_demand': self.INTERPATH,
            'pm_path': self.PMPATH,
            'day_weights': self.WEIGHTS,
            'zones_path': self.ZONESPATH,
            'filter_path': self.FILTERPATH,
        }


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
                global_config.data_location, 'lopops', 'TravelPlans.csv'
            ),
            "LoPopS demand"
        )
        self.ZONESPATH = self.valid_file(
            os.path.join(
                global_config.data_location, 'lopops', 'zoneSystem', 'ABM_Zones_002_LSOA.shp'
            ),
            "LoPopS demand zones"
        )
        self.ATTRIBPATH = self.valid_file(
            os.path.join(
                global_config.data_location, 'lopops', 'HHsPerson2016_cat.csv'
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


class MoMoConfig(GlobalConfig):

    SOURCE = 'momo'
    PREFIX = ''
    cognito_region_name = 'eu-west-1'
    cognito_user_pool = 'momo-cognito-pool-tp50'

    def __init__(self, global_config):

        self.SAMPLE = global_config.SAMPLE
        self.EPSG = global_config.EPSG
        self.SEED = global_config.SEED
        self.VERBOSE = global_config.VERBOSE
        self.OUTPATH = global_config.OUTPATH
        self.XMLPATH = global_config.XMLPATH
        self.XMLPATHATTRIBS = global_config.XMLPATHATTRIBS

        self.MOMOTRIPSPATH = self.valid_file(
            os.path.join(
                global_config.data_location, 'momo', 'trips.csv'
            ),
            "LoPopS demand"
        )

        self.RECORDS = {
            'sample': 'NA',
            'demand': self.MOMOTRIPSPATH,
            'attributes': 'NA',
        }


class MotionConfig(GlobalConfig):

    SOURCE = 'motion'
    PREFIX = 'mot_'
    LIMIT = None  # Limit output
    NORM = None

    TOURS = [
        'BlueCommute',
        # 'WhiteCommute',
        # 'Business',
        # 'Shopping',
        # 'Other'
    ]

    TOURSSEGMENTMAP = {
        # map demand matrix name to appropriate segmentation inputs
        'BlueCommute': 'Commute',
        'WhiteCommute': 'Commute',
        'Business': 'Business',
        'Shopping': 'Other-Shopping',
        'Other': 'Other-Shopping'
    }

    TOURSFACTORSMAP = {
        # map demand matrix name to appropriate factor inputs
        'BlueCommute': 'WorkBlue',
        'WhiteCommute': 'WorkWhite',
        'Business': 'EmployerBusiness',
        'Shopping': 'Shopping',
        'Other': 'Other'
    }

    TOURSACTIVITYMAP = {
        # map demand matrix name to appropriate activity
        'BlueCommute': 'work',
        'WhiteCommute': 'work',
        'Business': 'work',
        'Shopping': 'shop',
        'Other': 'other'
    }

    MODES = [
        'M1',
        # 'M2',
        # 'M3',
        # 'M4',
        # 'M5',
        # 'M6',
        # 'M7',
    ]

    MODESMAP = {
        'M1': 'car',  # driver
        'M2': 'car',  # passenger
        'M3': 'pt',  # rail
        'M4': 'pt',  # bus
        'M5': 'bike',
        'M6': 'walk',
        'M7': 'car'  # taxi
    }

    MODESFACTORSMAP = {
        'M1': 'CAR DRIVER (out_mode = 6)',
        'M2': 'CAR PASSENGER (out_mode = 8)',
        'M3': 'RAIL (out_mode = 1+2+3)',
        'M4': 'BUS (out_mode = 4)',
        'M5': 'CYCLE (out_mode = 11)',
        'M6': 'WALK (out_mode = 12)',
        'M7': 'TAXI (out_mode = 10)'
    }

    PERIODS = [
        'AM',
        'IP',
        'PM'
    ]

    ALLPERIODS = [
        'AM',
        'IP',
        'PM',
        'night'
    ]

    PERIODTIMES = {
        'AM': list(range(7, 10)),
        'IP': list(range(10, 16)),
        'PM': list(range(16, 19)),
        'night': [i for j in (range(7), range(19, 24)) for i in j]
    }

    INCOMEMAP = {
        'inc16': 'Household Income <35k',
        'inc78': 'Household Income £35k-£75k',
        'inc9p': 'Household Income >£75k',
        'inc17': 'Household Income <50k',
        'inc8p': 'Household Income >£50k',
        'inc18': 'Household Income <75k',
        'unknown': 'All'
    }

    INCOMECONVERT = {
        'inc16': 'inc56',
        'inc78': 'inc7p',
        'inc9p': 'inc7p',
        'inc17': 'inc56',
        'inc8p': 'inc7p',
        'inc18': 'inc56',
        'unknown': 'inc56'
    }

    MODEMAP = {
        'Bus': 'pt',
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

    ACTIVITYMAP = {
        'Edu': 'education',
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

        self.DEMANDPATH = self.valid_path(
            os.path.join(
                global_config.data_location, 'motion'
            ),
            "Motion demand"
        )
        self.ZONESPATH = self.valid_path(
            os.path.join(
                global_config.data_location, 'motion', 'DZ'
            ),
            "Motion demand zones"
        )
        self.FILTERPATH = self.valid_path(
            os.path.join(
                global_config.data_location, 'london', 'London-wards-2018_ESRI'
            ),
            "Motion spatial filter"
        )
        self.SEGMENTSPATH = self.valid_file(
            os.path.join(
                global_config.data_location, 'motion', 'Segment Numbering_edit.xlsx'
            ),
            "Motion demand"
        )
        self.OUTBOUNDFACTORPATH = self.valid_file(
            os.path.join(
                global_config.data_location, 'motion',
                '20170829_Target Period to 24hr factors_v3.7_Output - Outbound.xlsx'
            ),
            "Motion demand"
        )
        self.RETURNFACTORPATH = self.valid_file(
            os.path.join(
                global_config.data_location, 'motion',
                '20170829_Target Period to 24hr factors_v3.7_Output - Return.xlsx'
            ),
            "Motion demand"
        )

        self.RECORDS = {
            'sample': self.SAMPLE,
            'limit': self.LIMIT,
            'norm': self.NORM,
            'demand': self.DEMANDPATH,
            'zones_path': self.ZONESPATH,
            'filter_path': self.FILTERPATH
        }
