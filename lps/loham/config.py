import os.path
from lps.config import GlobalConfig


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
                global_config.data_location, 'freight', 'lgv'
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
                global_config.data_location, 'freight', 'freight_zones'
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
                global_config.data_location, 'freight', 'hgv'
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
                global_config.data_location, 'freight', 'freight_zones'
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
