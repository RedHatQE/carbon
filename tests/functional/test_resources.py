import yaml

from carbon import Carbon, Scenario, Host

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
        # TODO: Revisit this test case
        # cp_scenario_description = dict(scenario_description)
        # host = Host(parameters=cp_scenario_description.pop('provision')[0])
        # assert isinstance(host, Host)
        pass

    def test_new_host_from_carbon_object(self):
        cbn = Carbon(__name__)
        cbn.load_from_yaml('assets/scenario.yaml')
        assert isinstance(cbn.scenario._hosts.pop(0), Host)
