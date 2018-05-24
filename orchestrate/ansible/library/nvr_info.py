#!/usr/bin/python

import os
from ansible.module_utils.basic import *

def nvr_info(data):
    has_changed =  False
    nvr_data = data["nvr"].split("-")
    nvr_data = "/".join(nvr_data)
    nvr_url = os.path.join(data["brew_root"], "packages", nvr_data, data["arch"])
    nvr_url = nvr_url + "/"
    metadata = {"data": nvr_url}
    return (has_changed, metadata)

def main():

        fields = {
              "nvr": {"required": True, "type":"str"},
              "brew_root": {"required":True, "type":"str"},
              "dest": {"required":False, "type":"str"},
              "arch": {"required":True, "type":"str"},
        }

	module = AnsibleModule(argument_spec=fields)
        has_changed, meta_data = nvr_info(module.params)
        module.exit_json(changed=has_changed, meta=meta_data)

if __name__ == '__main__':
    main()
