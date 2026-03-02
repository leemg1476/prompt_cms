import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="Integration DB tests will be added with dedicated test database fixtures.")
def test_integration_placeholder() -> None:
    assert True
