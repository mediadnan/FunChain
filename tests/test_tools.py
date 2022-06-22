import unittest

from funchain.tools import validate


class TestValidate(unittest.TestCase):
    def test_validation_good_types(self):
        self.assertEqual("", validate("", 'string', str))
        self.assertEqual(0, validate(0, 'integer', int))
        self.assertEqual(0.0, validate(0.0, 'floating_point', float))
        self.assertEqual({}, validate({}, 'dictionary', dict))
        self.assertEqual([], validate([], 'list', list))

    def test_validation_bad_types(self):
        with self.assertRaises(TypeError) as cm:
            validate("", 'string', int)
            self.assertIn('string', str(cm.exception))
        self.assertRaises(TypeError, validate, *(0, 'integer', str))
        self.assertRaises(TypeError, validate, *(0.0, 'floating_point', dict))
        self.assertRaises(TypeError, validate, *({}, 'dictionary', float))
        self.assertRaises(TypeError, validate, *([], 'list', tuple))

    def test_validation_good_truthy_values(self):
        self.assertEqual("abc", validate("abc", 'string', str))
        self.assertEqual(1, validate(1, 'integer', int))
        self.assertEqual(1.0, validate(1.0, 'floating_point', float))
        self.assertEqual({'item': 0}, validate({'item': 0}, 'dictionary', dict))
        self.assertEqual([0], validate([0], 'list', list))

    def test_validation_bad_truthy_values(self):
        with self.assertRaises(ValueError) as cm:
            validate("", 'string', str, True)
            self.assertIn('string', str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            validate(0, 'integer', int, True)
            self.assertIn('integer', str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            validate(0.0, 'floating_point', float, True)
            self.assertIn('floating_point', str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            validate({}, 'dictionary', dict, True)
            self.assertIn('dictionary', str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            validate([], 'list', list, True)
            self.assertIn('list', str(cm.exception))

    def test_conditions(self):
        self.assertEqual(0, validate(
                    0,
                    'x',
                    int,
                    lambda n: n % 2 == 0,
                    lambda n: n >= 0,
                ))
        for x in (3, -2, 11, 13):
            with self.assertRaises(ValueError):
                validate(
                    x,
                    'x',
                    int,
                    lambda n: n % 2 == 0,
                    lambda n: n >= 0,
                    True,
                )

    def test_conditions_with_truthy(self):
        for x in (0, 3, -2, 11, 13):
            with self.assertRaises(ValueError):
                validate(
                    x,
                    'x',
                    int,
                    lambda n: n % 2 == 0,
                    lambda n: n >= 0,
                    True,
                )

    def test_conditions_with_message(self):
        message = f"x must be a positive even integer"
        for x in (0, 3, -2, 11, 13):
            with self.assertRaises(ValueError) as cm:
                validate(
                    x,
                    'x',
                    int,
                    lambda n: n % 2 == 0,
                    lambda n: n >= 0,
                    True,
                    err_msg=message
                )
                self.assertEqual(message, str(cm.exception))


if __name__ == '__main__':
    unittest.main()
