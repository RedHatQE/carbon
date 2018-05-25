import os
import pyaml

from carbon import Carbon

# Create a new carbon compound
cbn = Carbon(__name__)

# Read configuration first from etc, then overwrite from CARBON_SETTINGS
# environment variable and the look gor a carbon.cfg from within the
# directory where this command is running from.
cbn.config.from_pyfile('/etc/carbon/carbon.cfg', silent=True)
cbn.config.from_envvar('CARBON_SETTINGS', silent=True)
cbn.config.from_pyfile(os.path.join(os.getcwd(), 'my_config.cfg'), silent=True)

cbn.logger.info("Info")
cbn.logger.warn("Warn")
cbn.logger.debug("Debug")


if __name__ == '__main__':
    # This is the easiest way to configure a full scenario.
    cbn.load_from_yaml('test_scenario.yaml')

    # Save scenario before run
    with open('scenario-before-run.yaml', 'w') as yaml_file:
        pyaml.dump(cbn.scenario.profile(), yaml_file, vspacing=1)

    # The scenario will start the main pipeline and run through the ordered list
    # of pipelines. See :function:`~carbon.Carbon.run` for more details.
    cbn.run()

    # Save scenario after run
    with open('scenario-after-run.yaml', 'w') as yaml_file:
        pyaml.dump(cbn.scenario.profile(), yaml_file, vspacing=1)



