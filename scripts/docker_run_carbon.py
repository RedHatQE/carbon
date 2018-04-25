"""
Python script for executing carbon run command within containers.

This script accepts two parameter inputs:
    1. workspace
        - location where it can find the carbon object file
    2. tasks
        - the tasks you wish to run

This script is used directly with the carbon services project but others can
use this script if they wish. The carbon services project already have a
carbon object created and we wish to reuse that object inside the container.
The best approach for this is to serialize the object to a file and then
deserialize it to execute the run method using the same carbon object. This
script will then serialize the updated carbon object back to file for easy
loading the object at a later time.
"""
import pickle
import sys

import os

import carbon


def main():
    workspace = sys.argv[1]
    tasks = sys.argv[2].split(',')

    object_file = os.path.join(workspace, 'cbn_object.file')
    # First we need to load the carbon object from file
    with open(object_file, 'rb') as fh:
        cbn_dump = pickle.load(fh)

    # reset loggers
    cbn_dump.create_logger(carbon.__name__, cbn_dump.config)
    cbn_dump.create_logger('blaster', cbn_dump.config)

    # Now that we have the object, lets execute the carbon object
    getattr(cbn_dump, 'run')(tasklist=tasks)

    # If we got here, carbon succeeded and now we need to save the carbon
    # object to file.
    with open(object_file, 'wb') as f:
        pickle.dump(cbn_dump, f, pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    main()
