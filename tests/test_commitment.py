from crypto.commitment import generate_nonce, make_commitment, verify_commitment

def test_commitment_verifies():
    n = generate_nonce(); c = make_commitment(2, n)
    assert verify_commitment(c, 2, n)

def test_modified_vote_fails():
    n = generate_nonce(); c = make_commitment(2, n)
    assert not verify_commitment(c, 1, n)

def test_modified_nonce_fails():
    n = generate_nonce(); c = make_commitment(2, n)
    assert not verify_commitment(c, 2, generate_nonce())
