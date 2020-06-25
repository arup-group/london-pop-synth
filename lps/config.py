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
