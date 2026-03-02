import pytest

from app.services.hash_utils import compute_checksum


@pytest.mark.unit
def test_compute_checksum_is_deterministic() -> None:
    content = "SYSTEM: hello world"
    first = compute_checksum(content)
    second = compute_checksum(content)
    assert first == second
    assert len(first) == 64
