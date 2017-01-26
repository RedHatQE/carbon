import yaml

from carbon import Carbon

scenario_description = yaml.load(open('assets/scenario.yaml', 'r'))
cbn = Carbon(__name__)
cbn.load_from_yaml('assets/scenario.yaml')


def test_create_carbon_object():
    obj = Carbon(__name__)
    assert isinstance(obj, Carbon)


def test_change_carbon_name():
    obj = Carbon(__name__)
    assert obj.name == __name__
    obj.name = "my_scenario"
    assert obj.name == "my_scenario"
