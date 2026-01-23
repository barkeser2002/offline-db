import pytest

@pytest.fixture(autouse=True)
def skip_missing_crypto():
    try:
        import Cryptodome  # noqa: F401
    except ImportError:
        pytest.skip("pycryptodome not installed – skipping crypto‑dependent tests")
