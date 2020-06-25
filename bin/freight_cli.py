import os
import argparse

from mimi.core import samplers, output
from mimi.loham import loham
from input.config import LoHAMLGVConfig, LoHAMHGVConfig


def get_args():
    """
    Gets command line args. Includes a number of defaults for input and output paths.
    :return: argparse arguments object
    """

    zones_input = os.path.join('data', 'freight', 'freight_zones')

    parser = argparse.ArgumentParser()

    parser.add_argument('--input', '-I',
                        default='lgv',
                        type=str,
                        help="Output mode ie lgv or hgv (default: lgv)"
                        )
    parser.add_argument('--prefix', '-P',
                        default='lgv_',
                        type=str,
                        help="Output prefix (default: lgv_)"
                        )
    parser.add_argument('--out', '-O',
                        default=os.path.join('outputs'),
                        type=str,
                        help="Output population location"
                        )
    parser.add_argument('--name', '-N',
                        default=os.path.join('freight_pop.xml'),
                        type=str,
                        help="Output population name"
                        )
    parser.add_argument('--weights', '-W',
                        nargs=4,
                        default=(1, 1, 1, 0.1),
                        type=float,
                        help="24 hour distribution of demand by Peak(am), IP(day), Peak(pm) and IP(night),"
                             "(default: 1, 1, 1, 0.1)"
                        )
    parser.add_argument('--norm',
                        default=None,
                        type=int,
                        help='define total daily number of trips (default: None)'
                        )
    parser.add_argument('--sample', '-S',
                        default=10.,
                        type=float,
                        help="% sampling as float from >0 to 100 (default = 10%)"
                        )
    parser.add_argument('--limit', '-L',
                        default=0,
                        type=int,
                        help='set plan limit, eg 1000 plans, default 0 denotes no limit'
                        )
    parser.add_argument('--epsg',
                        default=27700,
                        type=int,
                        help="Input required crs (default: 27700 (UK Grid))"
                        )
    # MATSim docs recommend local coordinates system over global eg 4326 (~WGS84)
    parser.add_argument('--zones', '-Z',
                        default=zones_input,
                        type=str,
                        help="Input string areas shapes path (default: {})".format(zones_input)
                        )
    parser.add_argument('--verbose', '-V',
                        action='store_true'
                        )
    parser.add_argument('--savefig', '-SF',
                        action='store_true'
                        )
    parser.add_argument('--seed',
                        default=1234,
                        type=int
                        )
    arguments = parser.parse_args()

    assert arguments.sample <= 100, 'Sampling must be 100% or less'

    return arguments


if __name__ == '__main__':

    args = get_args()
    if args.input == 'lgv':
        config = LoHAMLGVConfig
    elif args.input == 'hgv':
        config = LoHAMHGVConfig
    else:
        raise ValueError('unknown config: lgv or hgv?')

    config.VERBOSE = args.verbose
    config.OUTPATH = args.out
    config.XMLNAME = args.name
    config.XMLPATH = os.path.join(config.OUTPATH, config.XMLNAME)
    config.SAMPLE = args.sample
    config.EPSG = args.epsg
    config.SEED = args.seed
    config.INCLUDE = True
    config.PREFIX = args.prefix
    config.ZONESPATH = args.zones
    config.LIMIT = args.limit
    config.WEIGHTS = args.weights  # (am , inter, pm, night)
    config.NORM = None  # Set total number of plans (approx trips / 2)

    freight = loham.Demand(config)

    sampler = samplers.DemandSampler(config)
    population = samplers.make_pop(freight, sampler)
    population.make_records(config)

    output.write_xml_plans(population, config)  # write
    output.write_xml_attributes(population, config)  # write

    tables = output.Tables(config, population)
    tables.write(config.PREFIX)
    tables.describe(config.PREFIX)
