"""conftest.py file for testing houdini_package_runner."""

# =============================================================================
# IMPORTS
# =============================================================================

# Third Party
import pytest

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def remove_abstract_methods(mocker):
    """Remove abstract methods for base class test purposes."""

    def _remove(cls):
        mocker.patch.object(cls, "__abstractmethods__", set())

    yield _remove
