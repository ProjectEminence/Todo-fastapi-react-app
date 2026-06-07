"""CodeValid seed test — validates that the pytest environment is set up correctly."""


def test_codevalid_seed():
    """Emits the onboarding marker in pytest output for log validation."""
    print("CODEVALID_SEED_ASSERTION_OK")
    assert True