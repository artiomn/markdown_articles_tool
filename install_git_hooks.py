#!/usr/bin/env python3

from pathlib import Path

try:
    print('Trying to import Precommit framework...')
    from pre_commit.main import main as precommit
except ModuleNotFoundError:
    print('Precommit framework was not found!')
    from pip import main as pip_main

    print('Installing requirements...')
    pip_main(['install', '-r', str(Path(__file__).parent / 'requirements.txt')])

    print('Trying to import Precommit framework...')
    # pylint: disable=C0412(ungrouped-imports)
    from pre_commit.main import main as precommit


print('Installing precommit hooks...')
precommit(['install'])
print('Success.')
