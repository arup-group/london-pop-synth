import os
import argparse

from mimi.core import samplers, output
from mimi.motion import motion
from input.config import MotionConfig


def get_args():
    """
    Gets command line args. Includes a number of defaults for input and output paths.
    :return: argparse arguments object
    """

    demand_root = os.path.join('data', 'motion')
    zones_input = os.path.join('data', 'motion', 'DZ')
    filter_input = os.path.join('data', 'london', 'London-wards-2018_ESRI')

    parser = argparse.ArgumentParser()

    parser.add_argument('--input', '-I',
                        default=demand_root,
                        type=str,
                        help="Input csv"
                        )
    parser.add_argument('--out', '-O',
                        default=os.path.join('outputs'),
                        type=str,
                        help="Output population location"
                        )
    parser.add_argument('--name', '-N',
                        default=os.path.join('mot_pop.xml'),
                        type=str,
                        help="Output population location"
                        )
    parser.add_argument('--prefix', '-P',
                        default='mot_',
                        type=str,
                        help="Output population prefix"
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
    parser.add_argument('--norm',
                        default=0,
                        type=int,
                        help='set plan norm, eg 1000 plans, default 0 denotes none'
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
    parser.add_argument('--filter', '-F',
                        default=filter_input,
                        type=str,
                        help="Input string filter shape path (default: {})".format(filter_input)
                        )
    parser.add_argument('--verbose', '-V',
                        action='store_true'
                        )
    parser.add_argument('--seed',
                        default=1234,
                        type=int
                        )
    arguments = parser.parse_args()

    arguments.mode = 'mot_'

    assert arguments.sample <= 100, 'Sampling must be 100% or less'
    return arguments


if __name__ == '__main__':

    args = get_args()
    config = MotionConfig

    config.OUTPATH = args.out
    config.XMLNAME = args.name
    config.XMLPATH = os.path.join(args.out, args.name)
    config.XMLPATHATTRIBS = os.path.join(config.OUTPATH, config.XMLNAMEATTRIBS)
    config.SAMPLE = args.sample
    config.EPSG = args.epsg
    config.SEED = args.seed
    config.PREFIX = args.prefix
    # config.INPUTPATH = args.input
    # config.ZONESPATH = args.zones
    config.LIMIT = args.limit
    config.PREFIX = args.prefix
    config.FILTERPATH = args.filter

    motion = motion.Demand(config)

    sampler = samplers.DemandSampler(config)
    population = samplers.make_pop(motion, sampler)
    population.make_records(config)

    output.write_xml_plans(population, config)  # write
    output.write_xml_attributes(population, config)  # write
    tables = output.Tables(config, population)
    tables.write(config.PREFIX)
    tables.describe(config.PREFIX)
