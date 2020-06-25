import xml.etree.ElementTree as ET
import os
import argparse
import numpy as np
import pandas as pd


"""
Helper CLI for converting raw attribute data (one hot encoded) into classes
"""

def get_args():
    """
    Gets command line args. Includes a number of defaults for input and output paths.
    :return: argparse arguments object
    """
    data_path = os.path.join('data', 'plans',
                             'HHsPerson2016.csv')

    # keep = ['recID', 'bname', 'Freq16']

    # categories = {'hsize': ['hsize1', 'hsize2', 'hsize3', 'hsize4'],
    #               'car': ['car0', 'car1', 'car2'],
    #               'inc': ['inc12', 'inc34', 'inc56', 'inc7p'],
    #               'hstr': ['hstr1', 'hstr2', 'hstr3'],
    #               'gender': ['male', 'female'],
    #               'age': ['age5', 'age11', 'age18p', 'age30', 'age65', 'age65p'],
    #               'race': ['white', 'mixed', 'india', 'pakbag', 'asian', 'black'],
    #               'license': ['pdlcar', 'pdlnone'],
    #               'job': ['ft', 'pt', 'edu', 'retired'],
    #               'occ': ['occ1', 'occ2', 'occ3', 'occ4', 'occ5', 'occ6', 'occ7', 'occ8']
    #               }
    keep = ['thid', 'tpid', 'hincome', 'age', 'Borough', 'Freq16']  # columns to keep as is

    categories = {
        'day': ['mon', 'tues', 'wed', 'thur', 'fri', 'sat', 'sun'],
        'hsize': ['hsize1', 'hsize2', 'hsize3', 'hsize4', 'hsize5', 'hsize6p'],
        'car': ['car0', 'car1', 'car2', 'car2p'],
        'hstr': ['hstr1', 'hstr2', 'hstr3', 'hstr4', 'hstr5', 'hstr6'],
        'gender': ['male', 'female'],
        'age': ['age5', 'age11', 'age16', 'age18', 'age30', 'age65', 'age65p'],
        'race': ['white', 'mixed', 'india', 'pakbag', 'asian', 'black'],
        'license': ['pdlcar', 'pdlnone'],
        'job': ['ft', 'pt', 'student', 'retired'],
        'occ': ['occ1', 'occ2', 'occ3', 'occ4', 'occ5', 'occ6', 'occ7', 'occ8'],
        }

    parser = argparse.ArgumentParser()

    parser.add_argument('--att', '-I', default=data_path, type=str,
                        help="Population attributes path (.csv)")
    parser.add_argument('--out', '-O', default=None, type=str,
                        help="Population attributes path (.csv)")
    parser.add_argument('--verbose', '-V', action='store_true')

    arguments = parser.parse_args()
    arguments.categories = categories
    arguments.keep = keep

    if not arguments.out:
        name = os.path.basename(arguments.att).split('.')[0] + '_cat.csv'
        arguments.out = os.path.join('outputs', name)

    print("\t> pop attribute inputs from: {}".format(arguments.att))
    print("\t> output to: {}".format(arguments.out))
    print("\t> conversion using:")
    for name, columns in arguments.categories.items():
        print("{}: {}".format(name, columns))

    return arguments


def get_category(row, columns):
    if sum(row) == 0:
        return 'unknown'
    for column in columns:
        if row[column] == 1:
            return column


def to_categorical(args):

    # convert csv to categorical format
    attributes_raw = pd.read_csv(args.att)

    attributes_categorical = attributes_raw.loc[:, args.keep]

    for category, columns in args.categories.items():
        for column in columns:
            assert column in attributes_raw.columns, '{} header not found in input data headers'.format(column)
        # select input columns for category
        cols = attributes_raw[columns]
        # extract category from boolean
        cat = cols.apply(get_category, args=(columns,), axis=1)
        # cat = pd.Series(cols.columns[np.where(cols != 0)[1]])  # this is fast but can't deal with missing 1
        # add to new df
        attributes_categorical[category] = cat

    return attributes_categorical


if __name__ == '__main__':
    args = get_args()
    print('converting data...')
    df = to_categorical(args)
    print('saving to disk as {}'.format(args.out))
    df.to_csv(args.out, index=False)
    print('done')

#
# tree = ET.parse('tfl_pop_transformer/test1.xml')
# root = tree.getroot()
# print(len(root))
# for child in root:
#     print(child.attrib['id'])