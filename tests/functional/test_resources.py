import yaml

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


class TestHost(object):

    def test_new_host_from_yaml(self):
        cp_scenario_description = dict(scenario_description)
        host = Host(parameters=cp_scenario_description.pop('provision')[0])
        assert isinstance(host, Host)
