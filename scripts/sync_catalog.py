"""Generate an offline design-preview catalog from the authoritative Python catalog."""
import argparse
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from compass.catalog import public_catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify the bundled catalog without writing it.')
    args = parser.parse_args()
    target = ROOT / 'ui' / 'catalog.js'
    data = json.dumps(public_catalog(), ensure_ascii=True, indent=2)
    content = f'"use strict";\nwindow.COMPASS_CATALOG = {data};\n'
    if args.check:
        if not target.is_file() or target.read_text(encoding='utf-8') != content:
            parser.exit(1, 'Bundled catalog is out of date. Run python scripts/sync_catalog.py.\n')
    else:
        target.write_text(content, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
