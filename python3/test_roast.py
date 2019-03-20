import roast_api as ra


def test_host_header():
    req = ra.build_request([
        'Host: https://httpbin.org',
        'GET /get',
    ], 1)

    assert req.method == 'GET'
    assert 'host' not in req.headers
    assert req.url == 'https://httpbin.org/get'


def test_header_collection():
    req = ra.build_request([
        'Accept: application/json',
        'X-Custom-Header: nonsense',
        'GET https://httpbin.org/get',
    ], 2)

    assert req.method == 'GET'
    assert req.headers['x-custom-header'] == 'nonsense'
    assert req.url == 'https://httpbin.org/get'


def test_post_body():
    req = ra.build_request([
        'POST https://httpbin.org/post <<body',
        'one=1',
        'two=2',
        'body',
        'three=3',
    ], 0)

    assert req.method == 'POST'
    assert req.data == 'one=1\ntwo=2'


def test_params_with_special():
    req = ra.build_request([
        'GET https://httpbin.org/get answer="forty two" more="one=two=three"',
    ], 0)

    assert req.params == {'answer': 'forty two', 'more': 'one=two=three'}


def test_variable_interpolation_in_params():
    req = ra.build_request([
        'set answer 42',
        'GET https://httpbin.org/get answer=num_{answer}',
    ], 1)

    assert req.params == {'answer': 'num_42'}


def test_interpolation_shortcut_in_params():
    req = ra.build_request([
        'set answer 42',
        'GET https://httpbin.org/get answer',
    ], 1)

    assert req.params == {'answer': '42'}


def test_interpolation_with_other_params():
    req = ra.build_request([
        'GET https://httpbin.org/get name=stark answer=ans_by_{@name}',
    ], 0)

    assert req.params == {'name': 'stark', 'answer': 'ans_by_stark'}
