from pathlib import Path
from configparser import ConfigParser
from fastchain import __version__


root = Path(__file__).parent.parent


def test_sync_version():
    """ensures the version is updated anywhere"""
    config = ConfigParser()
    config.read(root / 'setup.cfg')
    assert __version__ == config['metadata']['version'], "version should be updated everywhere"
