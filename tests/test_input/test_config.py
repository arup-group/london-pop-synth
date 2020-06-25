import os


class Config:
    def __init__(self, sample_percentage, output_path):
        self.output_path = output_path
        self.SAMPLE = sample_percentage  # percent (minimum is 0.01% or 1ppt)
        self.OUTPATH = os.path.join(output_path, 'plans{}perc'.format(self.SAMPLE))
        self.XMLPATH = os.path.join(self.OUTPATH, self.XMLNAME)
        self.XMLPATHATTRIBS = os.path.join(self.OUTPATH, self.XMLNAMEATTRIBS)

        # Attributes to include in output comments and terminal log:
        self.RECORDS = {
            'outpath': self.OUTPATH,
            'plans_name': self.XMLNAME,
            'attributes_name': self.XMLNAMEATTRIBS,
            'crs': self.EPSG,
            'seed': self.SEED
        }

    SOURCE = 'all'  # keep
    VERBOSE = False
    XMLNAME = 'plans.xml'
    XMLNAMEATTRIBS = 'attributes.xml'
    EPSG = 27700
    SEED = 1234


class LoPopSConfig(Config):
    def __init__(self, data_location, Global_Config):
        Config.__init__(self, Global_Config.SAMPLE, Global_Config.output_path)
        self.INPUTPATH = os.path.join(data_location, 'lopops', 'TravelPlans.csv')
        self.ZONESPATH = os.path.join(data_location, 'lopops', 'zoneSystem',
                                      'ABM_Zones_002_LSOA.shp')
        self.ATTRIBPATH = os.path.join(data_location, 'lopops', 'HHsPerson2016_cat.csv')

        self.RECORDS = {
            'sample': self.SAMPLE,
            'limit': self.LIMIT,
            'norm': self.NORM,
            'demand': self.INPUTPATH,
            'zones_path': self.ZONESPATH,
            'dummies': self.DUMMIES
        }

    INCLUDE = True
    SOURCE = 'plans'
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


class MoMoConfig(LoPopSConfig):
    def __init__(self, data_location, Global_Config):
        LoPopSConfig.__init__(self, data_location, Global_Config)
        # csv or read directly from db?
        self.MOMOTRIPSPATH = os.path.join(data_location, 'momo', 'trips.csv')

    INCLUDE = True
    SOURCE = 'momo'
    PREFIX = ''
    cognito_region_name = 'eu-west-1'
    cognito_user_pool = 'momo-cognito-pool-tp50'


class LoHAMLGVConfig(Config):
    def __init__(self, data_location, Global_Config):
        Config.__init__(self, Global_Config.SAMPLE, Global_Config.output_path)
        self.lgv_root = os.path.join(data_location, 'loham', 'lgv')
        self.AMPATH = os.path.join(self.lgv_root, 'L3_5194Z_R006_ADJ_R11_AM_E64_LGV.csv')
        self.INTERPATH = os.path.join(self.lgv_root, 'LGV_L3_5194Z_R005_ADJ_R11_IP_E64.csv')
        self.PMPATH = os.path.join(self.lgv_root, 'LGV_L3_5194Z_R005_ADJ_R11_PM_E64.csv')
        self.ZONESPATH = os.path.join(data_location, 'loham', 'freight_zones')
        self.FILTERPATH = os.path.join(data_location, 'london', 'London-wards-2018_ESRI')

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

    INCLUDE = True
    SOURCE = 'freight'
    MODE = 'car'
    PREFIX = 'lgv_'
    WEIGHTS = (1, 1, 1, 0.01)  # (am , inter, pm, night)
    NORM = None  # Set total number of plans (approx trips / 2)
    LIMIT = None  # Limit output

#
# class LoHAMHGVConfig(Config):
#     def __init__(self, data_location, Global_Config):
#         Config.__init__(self, Global_Config.SAMPLE, Global_Config.output_path)
#         self.hgv_root = os.path.join(data_location, 'freight', 'hgv')
#         self.AMPATH = os.path.join(self.hgv_root, 'HGV_L3_5194Z_R006_ADJ_R11_AM_E65.csv')
#         self.INTERPATH = os.path.join(self.hgv_root, 'HGV_L3_5194Z_R005_ADJ_R11_IP_E65.csv')
#         self.PMPATH = os.path.join(self.hgv_root, 'HGV_L3_5194Z_R005_ADJ_R11_PM_E65.csv')
#         self.ZONESPATH = os.path.join(data_location, 'freight', 'freight_zones')
#         self.FILTERPATH = os.path.join(data_location, 'london', 'London-wards-2018_ESRI')
#
#         self.RECORDS = {
#             'sample': self.SAMPLE,
#             'limit': self.LIMIT,
#             'norm': self.NORM,
#             'am_demand': self.AMPATH,
#             'inter_demand': self.INTERPATH,
#             'pm_path': self.PMPATH,
#             'day_weights': self.WEIGHTS,
#             'zones_path': self.ZONESPATH,
#             'filter_path': self.FILTERPATH,
#         }
#
#     INCLUDE = False
#     SOURCE = 'freight'
#     MODE = 'car'
#     PREFIX = 'hgv_'
#     WEIGHTS = (1, 1, 1, 0.01)  # (am , inter, pm, night)
#     NORM = None  # Set total number of plans (approx trips / 2)
#     LIMIT = None  # Limit output


class MotionConfig(Config):
    def __init__(self, data_location, Global_Config):
        Config.__init__(self, Global_Config.SAMPLE, Global_Config.output_path)
        self.DEMANDPATH = os.path.join(data_location, 'motion')
        self.ZONESPATH = os.path.join(data_location, 'motion', 'DZ')
        self.FILTERPATH = os.path.join(data_location, 'london', 'London-wards-2018_ESRI')
        self.SEGMENTSPATH = os.path.join(data_location, 'motion', 'Segment Numbering_edit.xlsx')
        self.OUTBOUNDFACTORPATH = os.path.join(data_location, 'motion',
                                               '20170829_Target Period to 24hr factors_v3.7_Output - Outbound.xlsx')
        self.RETURNFACTORPATH = os.path.join(data_location, 'motion',
                                             '20170829_Target Period to 24hr factors_v3.7_Output - Return.xlsx')

        self.RECORDS = {
            'sample': self.SAMPLE,
            'limit': self.LIMIT,
            'norm': self.NORM,
            'demand': self.DEMANDPATH,
            'zones_path': self.ZONESPATH,
            'filter_path': self.FILTERPATH
        }

    INCLUDE = True
    SOURCE = 'motion'
    PREFIX = 'mot'

    LIMIT = None  # Limit output
    NORM = None

    TOURS = ['BlueCommute',
             # 'WhiteCommute',
             # 'Business',
             # 'Shopping',
             # 'Other'
             ]

    #TOURS = ['Other']

    TOURSSEGMENTMAP = {'BlueCommute': 'Commute',  # map demand matrix name to appropriate segmentation inputs
                       'WhiteCommute': 'Commute',
                       'Business': 'Business',
                       'Shopping': 'Other-Shopping',
                       'Other': 'Other-Shopping'
                       }

    TOURSFACTORSMAP = {'BlueCommute': 'WorkBlue',  # map demand matrix name to appropriate factor inputs
                       'WhiteCommute': 'WorkWhite',
                       'Business': 'EmployerBusiness',
                       'Shopping': 'Shopping',
                       'Other': 'Other'
                       }

    TOURSACTIVITYMAP = {'BlueCommute': 'work',  # map demand matrix name to appropriate activity
                        'WhiteCommute': 'work',
                        'Business': 'work',
                        'Shopping': 'shop',
                        'Other': 'other'
                        }

    MODES = [
        # 'M1',
         # 'M2',
         # 'M3',
         'M4',
         # 'M5',
         # 'M6',
         # 'M7',
         ]

    MODESMAP = {'M1': 'car',  # driver
                'M2': 'car',  # passenger
                'M3': 'pt',  # rail
                'M4': 'pt',  # bus
                'M5': 'bike',
                'M6': 'walk',
                'M7': 'car'  # taxi
                }

    MODESFACTORSMAP = {'M1': 'CAR DRIVER (out_mode = 6)',
                       'M2': 'CAR PASSENGER (out_mode = 8)',
                       'M3': 'RAIL (out_mode = 1+2+3)',
                       'M4': 'BUS (out_mode = 4)',
                       'M5': 'CYCLE (out_mode = 11)',
                       'M6': 'WALK (out_mode = 12)',
                       'M7': 'TAXI (out_mode = 10)'
                       }

    PERIODS = ['AM',
               'IP',
               'PM']

    ALLPERIODS = ['AM',
                  'IP',
                  'PM',
                  'night']

    PERIODTIMES = {'AM': list(range(7, 10)),
                   'IP': list(range(10, 16)),
                   'PM': list(range(16, 19)),
                   'night': [i for j in (range(7), range(19, 24)) for i in j]
                   }

    INCOMEMAP = {'inc16': 'Household Income <35k',
                 'inc78': 'Household Income £35k-£75k',
                 'inc9p': 'Household Income >£75k',
                 'inc17': 'Household Income <50k',
                 'inc8p': 'Household Income >£50k',
                 'inc18': 'Household Income <75k',
                 'unknown': 'All'
                 }

    INCOMECONVERT = {'inc16': 'inc56',
                     'inc78': 'inc7p',
                     'inc9p': 'inc7p',
                     'inc17': 'inc56',
                     'inc8p': 'inc7p',
                     'inc18': 'inc56',
                     'unknown': 'inc56'
                     }


class TouristConfig(Config):  # TODO
    ON = False
    SOURCE = 'tours'
    PREFIX = 'tou_'





