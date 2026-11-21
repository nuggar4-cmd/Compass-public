"""Copy third-party notices for the Python and PyInstaller files in the Windows bundle."""

from ast import literal_eval
from importlib.metadata import distributions
from pathlib import Path
from shutil import copyfile, copytree
import sys


def bundled_sources(analysis_path):
    # Each file table in Analysis contains (destination, source, type) rows.
    analysis = literal_eval(analysis_path.read_text(encoding='utf-8'))
    return {
        Path(row[1])
        for table in analysis if isinstance(table, list)
        for row in table
        if isinstance(row, tuple) and len(row) == 3 and isinstance(row[1], str)
    }


def copy_distribution_notices(distribution, files, destination):
    copied = False
    for file in sorted(files):
        if not any(part.endswith('.dist-info') for part in file.parts[:-1]):
            continue
        if 'licenses' not in file.parts and not file.name.upper().startswith(
            ('LICENSE', 'COPYING', 'NOTICE', 'AUTHORS')
        ):
            continue
        target = destination.joinpath(*file.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(file.locate(), target)
        copied = True
    if not copied:
        raise ValueError(f'No licensing files found for bundled dependency {distribution.metadata["Name"]}.')


def main(analysis_path, package):
    license_directory = package / 'licenses'
    checked_in = Path(__file__).resolve().parents[1] / 'licenses'
    copytree(checked_in, license_directory)

    cpython = license_directory / 'CPython'
    cpython.mkdir()
    copyfile(Path(sys.base_prefix) / 'LICENSE.txt', cpython / 'LICENSE.txt')

    sources = bundled_sources(analysis_path)
    for distribution in distributions():
        name = distribution.metadata['Name'].lower().replace('_', '-')
        files = distribution.files or ()
        if name == 'proxy-tools':
            continue  # The published sdist lacks its upstream license file.
        if name == 'pyinstaller' or any(file.locate() in sources for file in files):
            copy_distribution_notices(distribution, files, license_directory / name)


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
