from mediatest.string_utils import str_has_leading_or_trailing_space


def test_str_has_leading_or_trailing_space():
    assert str_has_leading_or_trailing_space("foo") == False
    assert str_has_leading_or_trailing_space("foo ") == True
    assert str_has_leading_or_trailing_space(" foo") == True
    assert str_has_leading_or_trailing_space(" foo ") == True