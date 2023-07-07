from clients.sync_client import TestSafetyKey


def test_safety_key():
    item = TestSafetyKey(for_="str value", with_dot_and_hyphens=1)
    
    assert item.model_dump() == {
        'with_dot_and_hyphens': 1,
        'old_feature_priority': None,
        'class_': None,
        'for_': 'str value',
    }

    assert item.model_dump(by_alias=True) == {
        '33with.dot-and-hyphens&*': 1,
        '34with.dot-and-hyphens&*': None,
        'class': None,
        'for': 'str value',
    }

    assert item.model_dump(exclude_none=True) == {
        'with_dot_and_hyphens': 1,
        'for_': 'str value',
    }

    assert item.model_dump(exclude_unset=True) == {
        'with_dot_and_hyphens': 1,
        'for_': 'str value',
    }

    assert item.model_dump(exclude_unset=True, by_alias=True) == {
        '33with.dot-and-hyphens&*': 1,
        'for': 'str value',
    }

    assert item.model_dump(exclude_unset=True, exclude_none=True, by_alias=True) == {
        '33with.dot-and-hyphens&*': 1,
        'for': 'str value',
    }
