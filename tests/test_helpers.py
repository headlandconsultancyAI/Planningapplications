from download import safe_name, same_host

def test_safe_name():
    assert safe_name('hello / world.pdf') == 'hello_world.pdf'

def test_host_validation():
    assert same_host('https://planninganddevelopment.nelincs.gov.uk/path')
    assert not same_host('https://planninganddevelopment.nelincs.gov.uk.evil.example/path')
