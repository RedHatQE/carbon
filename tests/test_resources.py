import yaml

from carbon import CustomDict
from carbon import Scenario, Host

scenario_description = yaml.load(open('assets/scenario.yaml', 'r'))


class TestScenario(object):

    def test_new_scenario_from_yaml(self):
        scenario = Scenario(scenario_description)
        assert isinstance(scenario, Scenario)
        assert len(scenario.hosts) == 0

    def test_new_attribute(self):
        scenario = Scenario(scenario_description)
        scenario.newattribute = 'value'
        assert scenario.newattribute == str('value')

    def test_dict_to_class(self):
        scenario = Scenario(scenario_description)
        assert isinstance(scenario.scenario_data, CustomDict)

    def test_pop_attribute(self):
        scenario = Scenario(scenario_description)
        scenario.newattribute = 'value'
        assert scenario.newattribute == str('value')
        scenario.pop('newattribute')
        assert scenario.newattribute is None


class TestHost(object):

    def test_new_host_from_yaml(self):
        cp_scenario_description = dict(scenario_description)
        host = Host(cp_scenario_description.pop('hosts')[0])
        assert isinstance(host, Host)

    def test_new_attribute(self):
        cp_scenario_description = dict(scenario_description)
        host = Host(cp_scenario_description.pop('hosts')[0])
        host.newattribute = 'value'
        assert host.newattribute == str('value')

    def test_dict_to_class(self):
        cp_scenario_description = dict(scenario_description)
        host = Host(cp_scenario_description.pop('hosts')[0])
        assert isinstance(host.host_data, CustomDict)

    def test_pop_attribute(self):
        cp_scenario_description = dict(scenario_description)
        host = Host(cp_scenario_description.pop('hosts')[0])
        host.newattribute = 'value'
        assert host.newattribute == str('value')
        host.pop('newattribute')
        assert host.newattribute is None
