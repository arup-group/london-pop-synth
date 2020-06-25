"""
Integration tests.
"""

from shapely.geometry import Point
from . import env
from tests.configs import GlobalConfig, LoPopSConfig, LoHAMLGVConfig, MotionConfig, MoMoConfig

env.set_module()
from lps.core import samplers, output
from lps.core.population import Population, Agent, Plan, Activity, Leg
from lps.factory import synth_map
from lps.motion import motion
from lps.lopops import lopops
from lps.loham import loham
from lps.momo import momo

data_location = env.test_in_path
sample_percentage = 0.1
output_path = env.test_out_path


def test_build_population():
    test_pop = Population()

    act1 = Activity(uid='home1', seq=1, act='home',
                    point=Point((0, 0)),
                    start_time='00:00:00',
                    end_time='08:00:00')
    act2 = Activity(uid='work', seq=2, act='work',
                    point=Point((0, 0)),
                    start_time='09:00:00',
                    end_time='18:00:00')
    act3 = Activity(uid='home2', seq=3, act='home',
                    point=Point((0, 0)),
                    start_time='19:00:00',
                    end_time='23:59:59')
    acts = [act1, act2, act3]
    leg1 = Leg(uid='leg1', seq=1, mode='test',
               start_loc=Point((0, 0)), end_loc=Point((0, 0)),
               start_time='08:00:00', end_time='09:00:00')
    leg2 = Leg(uid='leg2', seq=1, mode='test',
               start_loc=Point((0, 0)), end_loc=Point((0, 0)),
               start_time='18:00:00', end_time='19:00:00')
    legs = [leg1, leg2]
    plan = Plan(activities=acts, legs=legs, source='test')
    attributes = {'income': 'excellent', 'gender': "unknown"}
    person = Agent('test', [plan], attributes=attributes)
    test_pop.agents.append(person)

    assert isinstance(test_pop.agents[0], Agent)
    assert isinstance(test_pop.agents[0].plans[0], Plan)
    assert isinstance(test_pop.agents[0].plans[0].activities[0], Activity)
    assert isinstance(test_pop.agents[0].plans[0].legs[0], Leg)

    return test_pop


def test_global_config_builder():
    global_config = GlobalConfig(env.test_config)
    assert global_config


global_config = GlobalConfig(env.test_config)


def test_config_builder():
    configurations = {}
    for source in ['loham_lgv', 'lopops', 'motion']:
        print(f"{source} config:")
        config = synth_map[source]['config'](global_config)
        configurations[source] = config


def test_momo_build_population():
    config = MoMoConfig(global_config)
    input_momo = momo.Data(config)
    momo_population = input_momo.make_pop()
    momo_population.make_records(config)
    output.print_records(momo_population.records)


def test_lopops_build_population():
    config = LoPopSConfig(global_config)
    input_plans = lopops.Data(config)
    sampler = samplers.ObjectSampler(config)
    lopops_population = input_plans.sample(sampler)
    lopops_population.make_records(config)
    output.print_records(lopops_population.records)


def test_loham_build_population():
    config = LoHAMLGVConfig(global_config)
    lgv = loham.Demand(config)
    sampler = samplers.DemandSampler(config)
    loham_lgv_population = lgv.sample(sampler)
    loham_lgv_population.make_records(config)
    output.print_records(loham_lgv_population.records)


def test_motion_build_population():
    config = MotionConfig(global_config)
    motion_plans = motion.Demand(config)
    sampler = samplers.DemandSampler(config)
    motion_population = motion_plans.sample(sampler)
    motion_population.make_records(config)
    output.print_records(motion_population.records)


def test_population_combine():
    final_population = Population()  # init empty pop object
    test_pop = test_build_population()
    final_population.add_agents(test_pop)


def test_population_build_record():
    test_pop = test_build_population()
    test_pop.add_records(global_config)  # add some records to population about provenance


def test_build_sub_cats():
    test_pop = test_build_population()
    test_pop.build_sub_categories()  # break down some activities into 'sub categories'


def test_write_plans():
    test_pop = test_build_population()
    output.write_xml_plans(test_pop, global_config)  # write plans to xml


def test_write_attributes():
    test_pop = test_build_population()
    output.write_xml_attributes(test_pop, global_config)  # write attributes to xml


def test_print_records():
    test_pop = test_build_population()
    output.print_records(test_pop.records)  # print records to terminal


def test_build_tables():
    test_pop = test_build_population()
    tables = output.Tables(global_config, test_pop)  # create flat format outputs
    return tables


def test_write_tables():
    test_tables = test_build_tables()
    test_tables.write('')


def test_describe_tables():
    test_tables = test_build_tables()
    test_tables.describe('')
