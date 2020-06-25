import os.path
from lps.config import GlobalConfig


class MotionConfig(GlobalConfig):

    SOURCE = 'motion'
    PREFIX = 'mot_'
    LIMIT = None  # Limit output
    NORM = None

    TOURS = [
        'BlueCommute',
        'WhiteCommute',
        'Business',
        'Shopping',
        'Other'
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
        'M2',
        'M3',
        'M4',
        'M5',
        'M6',
        'M7',
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
