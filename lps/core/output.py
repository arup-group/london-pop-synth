import os
import pandas as pd
from halo import Halo
from lxml import etree as et
from shapely.geometry import Point
import geopandas as gp

from utils import persistence


class Tables:
    """
    Class for building tables of plans
    """

    def __init__(self, config, population):
        self.config = config
        self.activity_df = None
        self.leg_df = None
        self.attrib_df = None
        self.build(population)

    def build(self, population):
        """
        TODO Fix x axis for start and end time plots - record Hour for simplicity?

        :param activity: activity type name
        :param duration: activity duration
        :param start: activity start time
        :param end: activity end time
        :return: None
        """
        # acts, legs = population.get_size()

        act_columns = [
            'source',
            'uid', 'sequence', 'activity', 'x', 'y',
            'start_time', 'end_time', 'start_time_mins', 'end_time_mins', 'duration_mins'
        ]

        leg_columns = [
            'source',
            'uid', 'sequence', 'mode',
            'ox', 'oy', 'dx', 'dy',
            'start_time', 'end_time', 'start_time_mins', 'end_time_mins',
            'duration_mins', 'distance'
        ]

        activity_data = []
        leg_data = []
        attrib_data = []

        with Halo(text='Building reports...', spinner='dots') as spinner:
            for p, person in enumerate(population.agents):
                attribs = person.attributes
                attribs.update({'uid': person.uid})
                attrib_data.extend([attribs])

                for plan in person.plans:
                    activity_data.extend(plan.activity_report())
                    leg_data.extend(plan.leg_report())

                    spinner.text = '{} plans added to table'.format(p)
            spinner.succeed('reporting completed')

        with Halo(text='Building tables...', spinner='dots') as spinner:
            self.activity_df = pd.DataFrame(activity_data, columns=act_columns)
            self.leg_df = pd.DataFrame(leg_data, columns=leg_columns)
            self.attrib_df = pd.DataFrame.from_dict(attrib_data)

            assert len(self.activity_df)
            assert len(self.leg_df)
            assert len(self.attrib_df)

            self.activity_df = self.activity_df.apply(pd.to_numeric, errors='ignore')
            self.leg_df = self.leg_df.apply(pd.to_numeric, errors='ignore')
            self.attrib_df = self.attrib_df.set_index('uid')

            spinner.succeed('output tables completed')

        # with Halo(text='converting activity locations to WGS84...', spinner='dots') as spinner:
            # TODO can this be done elsewhere? Currently assuming it's fastest as vector op on final table...
            locations = list(zip(self.activity_df.x, self.activity_df.y))
            gdf = gp.GeoDataFrame(geometry=[Point(xy) for xy in locations])
            gdf.crs = {'init': 'epsg:{}'.format(self.config.EPSG)}
            gdf = gdf.to_crs({'init': 'epsg:4326'})
            self.activity_df.x = list(gdf.geometry.apply(lambda p: p.x))
            self.activity_df.y = list(gdf.geometry.apply(lambda p: p.y))

            spinner.text = 'converting leg origins to WGS84...'
            locations = list(zip(self.leg_df.ox, self.leg_df.oy))
            gdf = gp.GeoDataFrame(geometry=[Point(xy) for xy in locations])
            gdf.crs = {'init': 'epsg:{}'.format(self.config.EPSG)}
            gdf = gdf.to_crs({'init': 'epsg:4326'})
            self.leg_df.ox = list(gdf.geometry.apply(lambda p: p.x))
            self.leg_df.oy = list(gdf.geometry.apply(lambda p: p.y))

            spinner.text = 'converting leg destinations to WGS84...'
            locations = list(zip(self.leg_df.dx, self.leg_df.dy))
            gdf = gp.GeoDataFrame(geometry=[Point(xy) for xy in locations])
            gdf.crs = {'init': 'epsg:{}'.format(self.config.EPSG)}
            gdf = gdf.to_crs({'init': 'epsg:4326'})
            self.leg_df.dx = list(gdf.geometry.apply(lambda p: p.x))
            self.leg_df.dy = list(gdf.geometry.apply(lambda p: p.y))
            spinner.succeed('tables converted to WGS84')

    def describe(self, prefix):
        print('\n==============================================================================')
        print('------------------------------ Activity Summary ------------------------------')
        print('==============================================================================')
        print('\nTotals:')
        print(self.activity_df.describe())
        print('\nGrouped by Activity Type:')
        summarise(self.activity_df, prefix, 'activity', self.config.OUTPATH,
                  'start_time_mins', 'end_time_mins', 'duration_mins')

        print('\n=============================================================================')
        print('-------------------------------- Leg Summary --------------------------------')
        print('=============================================================================')
        print('\nTotals:')
        print(self.leg_df.describe())
        print('\nGrouped by Mode:')
        summarise(self.leg_df, prefix, 'mode', self.config.OUTPATH,
                  'start_time_mins', 'end_time_mins', 'duration_mins')

        print('\n=============================================================================')
        print('----------------------------- Attributes Summary ----------------------------')
        print('=============================================================================')
        print('\nTotals:')
        summarise_cats(self.attrib_df)

    def write(self, prefix, act_path='activities.csv', leg_path='legs.csv', attrib_path='attributes.csv'):
        persistence.write_content(self.activity_df, location=os.path.join(self.config.OUTPATH, prefix + act_path))
        persistence.write_content(self.leg_df, location=os.path.join(self.config.OUTPATH, prefix + leg_path))
        persistence.write_content(self.attrib_df, location=os.path.join(self.config.OUTPATH, prefix + attrib_path))


def summarise(df, prefix, by, path, *cols):
    cols = list(cols)
    df = pd.DataFrame(df.loc[:, [by] + cols].groupby(by).describe())
    persistence.write_content(df, os.path.join(path, prefix + by + '_summary.csv'))
    for col in cols:
        print('\n{}:'.format(col))
        print(df.loc[:, col])


def summarise_cats(df):
    for col in list(df.columns):
        print('\n{}:'.format(col))
        print(df.loc[:, col].value_counts())


def write_xml_plans(population, config):
    population_xml = et.Element('population')

    # Add some useful comments
    population_xml.append(et.Comment('Input Records:'))
    for source, logs in population.records.items():
        population_xml.append(et.Comment(">>>>>>>>>>>Source: {}".format(source)))
        for log, value in logs.items():
            population_xml.append(et.Comment("{}: {}".format(log, value)))

    with Halo(text='Building plans xml...', spinner='dots') as spinner:
        for p, person in enumerate(population.agents):
            person_xml = et.SubElement(population_xml, 'person', {'id': person.uid})
            for plan in person.plans:
                plan_xml = et.SubElement(person_xml, 'plan', {'selected': 'yes'})
                for l in range(len(plan.legs)):
                    activity = plan.activities[l]
                    activity_xml = et.SubElement(plan_xml, 'act', {'type': activity.act,
                                                                   'x': str(int(activity.point.x)),
                                                                   'y': str(int(activity.point.y)),
                                                                   'end_time': activity.end_time})
                    leg = plan.legs[l]
                    leg_xml = et.SubElement(plan_xml, 'leg', {'mode': leg.mode})
                activity = plan.activities[-1]  # Deal with final activity
                activity_xml = et.SubElement(plan_xml, 'act', {'type': activity.act,
                                                               'x': str(int(activity.point.x)),
                                                               'y': str(int(activity.point.y))})
            spinner.text = '{} plans added to xml'.format(p)
        spinner.succeed('plans added to xml')

    persistence.write_content(population_xml, location=config.XMLPATH, matsim_DOCTYPE='population',
                              matsim_filename='population_v5')


def write_xml_attributes(population, config):
    with Halo(text='Building attributes xml...', spinner='dots') as spinner:
        attributes_xml = et.Element('objectAttributes')  # start forming xml

        # Add some useful comments
        attributes_xml.append(et.Comment('Input Records:'))
        for source, logs in population.records.items():
            attributes_xml.append(et.Comment(">>>>>>>>>>>Source: {}".format(source)))
            for log, value in logs.items():
                attributes_xml.append(et.Comment("{}: {}".format(log, value)))

        for p, person in enumerate(population.agents):
            person_e = et.SubElement(attributes_xml, 'object', {'id': person.uid})
            for k, v in person.attributes.items():
                attribute_e = et.SubElement(person_e, 'attribute', {'class': 'java.lang.String', 'name': k})
                attribute_e.text = v
            spinner.text = '{} people added to attributes xml'.format(p)
        spinner.succeed('attributes added to xml')

    persistence.write_content(attributes_xml, location=config.XMLPATHATTRIBS, matsim_DOCTYPE='objectAttributes',
                              matsim_filename='objectattributes_v1')


def dict_to_row(dict, columns):
    row = []
    for col in columns:
        row.append(dict[col])
    return row


def make_dirs(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print('creating {}'.format(directory))


def print_records(records):
    print('Input Records:')
    for source, logs in records.items():
        print("\t> Source: {}".format(source))
        for log, value in logs.items():
            print("\t\t> {}: {}".format(log, value))

