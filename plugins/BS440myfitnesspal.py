# -----------------------------------------------------------------------------------------
# BS440 plugin template  BS440template.py
# About:
# [Describe the use of this plugin here]
#
# Plugin scripts should be named BS440<pluginname>.py
# Any personalization or parameters should be put in BS440<pluginnname>.ini
# Note: The plugin is now an object of class Plugin which affects the way of how
# to declare functions and the way to use them. See BS440mail.py as example
#
# Author: Specify the owner and contact details. Plugins will not be maintained by the
# developer of BS440.py unless specified otherwise.
#
#
# ------------------------------------------------------------------------------------------
import datetime
from configparser import ConfigParser
import logging
import os
from typing import Mapping, List

import myfitnesspal
from datetime import datetime


# Add any imports specific to your plugin here.
# it is no problem to import modules already imported elsewhere
# if you need them, don't rely on someone else to import them for you.

log = logging.getLogger(__name__)
KNOWN_KEYS = ['bone', 'fat', 'tbw', 'muscle']

class Plugin:
    def __init__(self):
        # put any commands here you would like to be run to initialize your plugin
        return

    def update_measurements(self, client: myfitnesspal.Client, new_data: List[Mapping[str, float]], internal_key: str,
                            fitness_pal_key: str):
        # Retrieve existing measurements from myfitnesspal in the interval of received data and check if some of
        # the data points already exist. If they do, we don't send them again.
        if new_data:
            oldest_timestamp = datetime.fromtimestamp(sorted([value['timestamp'] for value in new_data])[0])
            try:
                existing_measurements = client.get_measurements(fitness_pal_key, lower_bound=oldest_timestamp.date())
            except ValueError:
                log.debug(f"Measurement of type {fitness_pal_key} does not exist yet.")
                existing_measurements = {}
                pass
            for value in new_data:
                timestamp = datetime.fromtimestamp(value['timestamp'])
                if not timestamp.date() in existing_measurements:
                    client.set_measurements(measurement=fitness_pal_key, value=value[internal_key], date=timestamp.date())

    def execute(self, globalconfig, persondata, weightdata, bodydata):
        # --- part of plugin skeleton
        # your plugin receives the config details from BS440.ini as well as
        # all the data received frm the scale
        log.info('Starting plugin: ' + __name__)
        # read ini file from same location as plugin resides, named [pluginname].ini
        configfile = os.path.dirname(os.path.realpath(__file__)) + '/' + __name__ + '.ini'
        pluginconfig = ConfigParser()
        pluginconfig.read(configfile)
        log.info('ini read from: ' + configfile)
        # Thats it! From here do your thing with the data.
        # Be sure to catch and log errors if you're doing risky stuff

        # Initialize all configured clients
        self.person_clients = {}
        for person_section in pluginconfig.sections():
            try:
                if person_section.startswith("Person"):
                    person_id = int(person_section[len("Person"):])
                else:
                    raise ValueError("Illegal section")
            except ValueError:
                logging.error(f"Illegal section name {person_section}. Expected person configs with section name of "
                              f"the form 'Person<nr>'.")
                continue

            scaleuser = pluginconfig.get(person_section, 'username')
            if not scaleuser:
                log.error(f"Missing 'username' for section {person_section}.")
                continue
            password = pluginconfig.get(person_section, 'password')
            if not password:
                log.error(f"Missing 'password' for section {person_section}.")
                continue

            client = myfitnesspal.Client(username=scaleuser, password=password)
            # Update weight measurements
            log.info(f"Updating weight data for user {scaleuser}")
            self.update_measurements(
                client,
                [data for data in weightdata if int(data['person']) == person_id],
                'weight',
                'Weight'
            )
            # Update body data measurements
            for key, mapped_key in dict(pluginconfig.items(person_section)).items():
                if key in KNOWN_KEYS:
                    log.info(f"Updating {mapped_key} values for user {scaleuser}")
                    self.update_measurements(client, new_data=bodydata, internal_key=key, fitness_pal_key=mapped_key)


        # finally end this plugin execution with
        log.info('Finished plugin: ' + __name__)

