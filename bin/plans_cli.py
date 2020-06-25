"""
Fred Shone
20th Nov 2018
Command line script for converting TFL csv simulated population data into Matsim xml format
- Sampling
- Activity inference
- Mode conversion
- Activity inference validation
- Write to xml format for MATSim
- Write to csv format for viz
"""

import argparse
import os
from mimi.core import samplers, output
from mimi.lopops import lopops
from input.config import LoPopSConfig


def get_args():
    """
    Gets command line args. Includes a number of defaults for input and output paths.
    :return: argparse arguments object
    """
    population_input = os.path.join('data', 'plans',
                                    'TravelPlans.csv')
    geo_input = os.path.join('data', 'plans',
                             'zoneSystem',
                             'ABM_Zones_002_LSOA.shp')

    parser = argparse.ArgumentParser()

    parser.add_argument('--out', '-O',
                        default='outputs',
                        type=str,
                        help="Output population path"
                        )
    parser.add_argument('--name', '-N',
                        default='pop.xml',
                        type=str,
                        help="Output population name (.xml)"
                        )
    parser.add_argument('--prefix',
                        default='',
                        type=str,
                        help="Outputs prefix"
                        )
    parser.add_argument('--sample',
                        '-S',
                        default=10.,
                        type=float,
                        help="% sampling as float from >0 to 100 (default = 10%)"
                        )
    parser.add_argument('--no_freq',
                        '-NF',
                        action='store_true',
                        help="Sample to approx. 2.5% by setting plan weightings to 1"
                        )
    parser.add_argument('--limit', '-L',
                        default=0,
                        type=int,
                        help='set plan limit, eg 1000 plans, default 0 denotes no limit'
                        )
    parser.add_argument('--keep_dummies', '-KD',
                        action='store_true',
                        help='keep dummies from input plans'
                        )
    parser.add_argument('--epsg',
                        default=27700,  # MATSim docs recommend local coordinates system over global eg 4326 (~WGS84)
                        type=int,
                        help="Input required crs (default: 27700 (UK Grid))"
                        )
    parser.add_argument('--input',
                        default=population_input,
                        type=str,
                        help="Input string population path (default: {})".format(population_input)
                        )
    parser.add_argument('--zones',
                        default=geo_input,
                        type=str,
                        help="Input string areas shapes path (default: {})".format(geo_input)
                        )
    parser.add_argument('--verbose', '-V',
                        action='store_true'
                        )
    parser.add_argument('--all_cars', '-AC',
                        action='store_true'
                        )
    parser.add_argument('--force_home', '-FH',
                        action='store_true'
                        )
    parser.add_argument('--seed',
                        default=1234,
                        type=int
                        )
    arguments = parser.parse_args()

    assert arguments.sample <= 100

    return arguments


if __name__ == '__main__':
    args = get_args()
    config = LoPopSConfig

    config.VERBOSE = args.verbose
    config.OUTPATH = args.out
    config.XMLNAME = args.name
    config.XMLPATH = os.path.join(config.OUTPATH, config.XMLNAME)
    config.SAMPLE = args.sample
    config.EPSG = args.epsg
    config.SEED = args.seed
    config.PREFIX = args.prefix
    config.INPUTPATH = args.input
    config.ZONESPATH = args.zones
    config.LIMIT = args.limit
    config.NOFREQ = args.no_freq
    config.NORM = None
    config.DUMMIES = args.keep_dummies
    config.ALLCARS = args.all_cars
    config.FORCEHOME = args.force_home

    plans = lopops.Data(config)  # Load raw plans and prepare

    sampler = samplers.ObjectSampler(config)

    population = samplers.make_pop(plans, sampler)  # sample from synth
    population.make_records(config)

    output.write_xml_plans(population, config)  # write
    output.write_xml_attributes(population, config)  # write

    tables = output.Tables(config, population)
    tables.write(config.PREFIX)
    tables.describe(config.PREFIX)

