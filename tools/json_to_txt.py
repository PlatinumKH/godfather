"""Python script to transform old JSON style setups into new setup formats.
Make sure it's in the 'tools' directory of the project before using it."""

import os
import typing
import json
from collections import Counter

def json_to_py(setup) -> str:
    name = setup['name']
    total = len(setup['roles'])
    role_occurence: typing.Counter[typing.Tuple(str, str)] = Counter()

    for role in setup['roles']:
        role_occurence[(role['faction'], role['id'])] += 1

    return(f"{name}: {total}. " +
           ", ".join([f"({role[0]}, {role[1]}, {occurence})"
                      for role, occurence in role_occurence.items()]))

def main():
    rootdir = os.path.dirname(os.path.dirname(__file__))
    setups_json = os.path.join(rootdir, 'setups/setups.json')
    setups_txt = os.path.join(rootdir, 'setups/setups.txt')

    setups = json.load(open(setups_json))

    with open(setups_txt, 'w') as txtf:
        txtf.write("\n".join([json_to_py(setup) for setup in setups]))

if __name__ == "__main__":
    main()
