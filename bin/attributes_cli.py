import os
import argparse
import numpy as np
import pandas as pd
from lxml import etree as et
from datetime import datetime as dt

"""
CLI for building population attributes input
- currently only implemented for TFL synthesised population data
"""


def get_args():
    """
    Gets command line args. Includes a number of defaults for input and output paths.
    :return: argparse arguments object
    """
    attrib_path = os.path.join('data', 'plans',
                               'HHsPerson2016_cat.csv')
    dict_path = os.path.join('data', 'plans',
                             'HHsDictionary_clean.csv')
    pop_path = os.path.join('outputs',
                            'population.xml')

    parser = argparse.ArgumentParser()

    parser.add_argument('--pop', '-I', default=pop_path, type=str,
                        help="Population path (.xml)")
    parser.add_argument('--out', '-O', default='outputs', type=str,
                        help="Output path (.xml")
    parser.add_argument('--att', default=attrib_path, type=str,
                        help="Population attributes path (.csv)")
    parser.add_argument('--dict', default=dict_path, type=str,
                        help="Population attributes dictionary path (.csv)")
    parser.add_argument('--verbose', '-V', action='store_true')

    arguments = parser.parse_args()

    name = os.path.basename(arguments.pop).split('.')[0] + '_attribs.xml'
    arguments.out = os.path.join('outputs', name)

    print("\t> loading pop from: {}".format(arguments.pop))
    print("\t> pop attribute inputs from: {}".format(arguments.att))
    print("\t> output to: {}".format(arguments.out))

    return arguments


def get_pop(args):
    pids = []
    tree = et.parse(args.pop)
    # population = tree.getroot()
    for person in tree.iter('person'):
        uid = person.attrib['id']
        pids.append(uid)
    return pids


def build_pop_attributes(args, pids, attributes):
    columns = attributes.columns[2:]
    population_attributes = et.Element('objectAttributes')  # start forming xml

    # Add some useful comments
    population_attributes.append(et.Comment("pop inputs from: {}".format(args.pop)))
    population_attributes.append(et.Comment("attrib inputs from: {}".format(args.att)))
    population_attributes.append(et.Comment("created: {}".format(dt.now())))

    for pid in pids:
        ident = int(pid.split('_')[0])
        pid_attributes = attributes.loc[ident][2:]
        dic = dict(zip(columns, pid_attributes))
        person = et.SubElement(population_attributes, 'object', {'id': pid})
        for k, v in dic.items():
            attribute = et.SubElement(person, 'attribute', {'class': 'java.lang.String', 'name': k})
            attribute.text = v
    return population_attributes


def write_pop_attributes(args, population_attributes):
    print("Forming tree")
    # tree = et.ElementTree(population_attributes)
    xml_object = et.tostring(population_attributes,
                             pretty_print=True,
                             xml_declaration=False,
                             encoding='UTF-8')
    print("Saving to disk as {}".format(args.out))
    with open(args.out, 'wb') as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>')
        f.write(b'<!DOCTYPE objectAttributes SYSTEM "http://matsim.org/files/dtd/objectattributes_v1.dtd">')
        f.write(xml_object)


if __name__ == '__main__':
    args = get_args()
    attributes = pd.read_csv(args.att, index_col='recID')
    pids = get_pop(args)
    population_attributes = build_pop_attributes(args, pids, attributes)
    write_pop_attributes(args, population_attributes)
    print("\t> done")

