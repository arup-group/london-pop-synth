import os.path
from lps.config import GlobalConfig


class MoMoConfig(GlobalConfig):

    SOURCE = 'momo'
    PREFIX = ''
    cognito_region_name = '<REMOVED>'
    cognito_user_pool = '<REMOVED>'

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
