import uuid
from django.test import SimpleTestCase
from common.utils import chunk_list, generate_uuid, normalize_email, safe_getattr


class DummyObject:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class UtilsTestCase(SimpleTestCase):
    """
    Test cases for helper utility functions.
    """

    def test_generate_uuid(self):
        val = generate_uuid()
        self.assertIsInstance(val, uuid.UUID)

    def test_normalize_email(self):
        self.assertEqual(normalize_email("  TEST@EXAMPLE.COM "), "TEST@example.com")
        self.assertEqual(normalize_email("user@Domain.Co.Uk"), "user@domain.co.uk")
        self.assertEqual(normalize_email(""), "")
        self.assertEqual(normalize_email(None), "")

    def test_safe_getattr(self):
        inner = DummyObject(city="New York")
        middle = DummyObject(address=inner)
        outer = DummyObject(profile=middle)

        self.assertEqual(safe_getattr(outer, "profile.address.city"), "New York")
        self.assertEqual(safe_getattr(outer, "profile.address.state", default="NY"), "NY")
        self.assertIsNone(safe_getattr(outer, "profile.nonexistent.attr"))
        self.assertEqual(safe_getattr(outer, "nonexistent", "fallback"), "fallback")

    def test_chunk_list(self):
        lst = [1, 2, 3, 4, 5]
        self.assertEqual(chunk_list(lst, 2), [[1, 2], [3, 4], [5]])
        self.assertEqual(chunk_list(lst, 5), [[1, 2, 3, 4, 5]])
        self.assertEqual(chunk_list(lst, 10), [[1, 2, 3, 4, 5]])
        self.assertEqual(chunk_list([], 3), [])

        with self.assertRaises(ValueError):
            chunk_list(lst, 0)

        with self.assertRaises(ValueError):
            chunk_list(lst, -1)
