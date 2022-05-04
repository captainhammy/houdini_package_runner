"""Initialize the houdini_package_runner package."""

# Standard Library
from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:  # pragma: no cover
    pass
