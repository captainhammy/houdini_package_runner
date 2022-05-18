"""Initialize the houdini_package_runner package."""

# Standard Library
import contextlib

# Third Party
from pkg_resources import DistributionNotFound, get_distribution

with contextlib.suppress(DistributionNotFound):
    __version__ = get_distribution(__name__).version
