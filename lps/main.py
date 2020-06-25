import sys
import click

from lps.config import GlobalConfig
from lps.factory import synth_map
from lps.core import output, population


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument(
    'config_path',
    type=str
)
def cli(config_path):

    print('\n========================================================')
    print(' ------------------------ MIMI ------------------------- ')
    print('========================================================')

    print('Main config:')
    global_config = GlobalConfig(config_path)
    global_config.print_records()

    final_population = population.Population()  # init pop object

    configurations = {}
    for source in global_config.SOURCES:
        print(f"{source} config:")
        config = synth_map[source]['config'](global_config)
        config.print_records()
        configurations[source] = config

    value = click.prompt(f'Are you sure you want to continue? y/n', default='n')
    if not value.lower() == 'y':
        sys.exit('Cancelled population build.')

    for source, config in configurations.items():

        source_data = synth_map[source]['input'](config)
        sampler = synth_map[source]['sampler'](config)
        source_population = source_data.sample(sampler)
        source_population.make_records(config)
        output.print_records(source_population.records)
        final_population.add_agents(source_population)

        # TODO can implement caching of final_population to disk just in case

    print('\tCompleted Population Build')

    final_population.add_records(global_config)  # add some records to population about provenance
    final_population.build_sub_categories()  # break down some activities into 'sub categories'
    output.write_xml_plans(final_population, global_config)  # write plans to xml
    output.write_xml_attributes(final_population, global_config)  # write attributes to xml
    output.print_records(final_population.records)  # print records to terminal

    tables = output.Tables(global_config, final_population)  # create flat format outputs for validation
    tables.write('')
    tables.describe('')

    print('\nDone\n')
