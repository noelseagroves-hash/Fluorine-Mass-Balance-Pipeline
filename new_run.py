"""Start a new batch run.

    python new_run.py 2026-08-04-oyster

Creates runs/<name>/ and puts a fresh copy of the template notebook in it.
Work in that copy. The template in the repository root stays blank so it can
be shared, reviewed and improved without carrying any batch's data around.
"""

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
TEMPLATE = REPO / 'TA_Processing.ipynb'


def main(argv):
    if len(argv) != 2 or argv[1] in {'-h', '--help'}:
        print(__doc__)
        return 1

    name = argv[1].strip().strip('/\\')
    if not name:
        print('Give the run a name, for example: python new_run.py 2026-08-04-oyster')
        return 1

    destination = REPO / 'runs' / name / TEMPLATE.name
    if destination.exists():
        print(f'That run already exists:\n  {destination}\n'
              'Pick another name, or open the existing one.')
        return 1

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEMPLATE, destination)

    print(f'Created {destination}\n')
    print('Next:')
    print('  1. Open that notebook in VS Code.')
    print('  2. Run the first cells — it will ask once for your data folder.')
    print('  3. In section 4, set PHASE and fill in SAMPLE_AMOUNTS.')
    print('  4. Run all.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
