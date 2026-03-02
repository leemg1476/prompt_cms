import pytest


@pytest.mark.e2e
@pytest.mark.skip(reason="E2E tests are reserved for service-level integration phase.")
def test_e2e_placeholder() -> None:
    assert True
