#!/usr/bin/python
import unittest
import sys
import os

from dashbuilder import parser


class TestValueAtPath(unittest.TestCase):
    def test_empty_path(self):
        # Given
        data = {'a': 'b'}

        # Then
        self.assertEquals(parser.value_at_path(data, []),
                          data)

    def test_one_level(self):
        # Given
        data = {'a': 'b'}

        # Then
        self.assertEquals(parser.value_at_path(data, ['a']),
                          'b')

    def test_two_levels(self):
        # Given
        data = {'a': {'b': 'c'}}

        # Then
        self.assertEquals(parser.value_at_path(data, ['a', 'b']),
                          'c')

    def test_wrong_path(self):
        # Given
        data = {'a': 'b'}

        # Then
        with self.assertRaises(KeyError):
            parser.value_at_path(data, ['z'])


class TestExpandStr(unittest.TestCase):
    def test_nothing_to_replace(self):
        # Given
        data = "There is nothing to replace"

        # Then
        self.assertEquals(parser.expand_str(data, {}),
                          data)

    def test_one_level_replace(self):
        # Given
        data = 'There is {something} to replace'
        store = {'something': 'nothing'}

        # Then
        self.assertEquals(parser.expand_str(data, store),
                          'There is nothing to replace')

    def test_replace_same_input_twice(self):
        # Given
        data = '{number} is equal to {number}'
        store = {'number': 'five'}

        # Then
        self.assertEquals(parser.expand_str(data, store),
                          'five is equal to five')

    def test_replace_a_non_string_value(self):
        # Given
        data = '{five} = 2 + 3'
        store = {'five': 5}

        # Then
        self.assertEquals(parser.expand_str(data, store),
                          '5 = 2 + 3')

    def test_replace_nested(self):
        # Given
        data = '{numbers:five} = 2 + 3'
        store = {'numbers': {'five': 5}}

        # Then
        self.assertEquals(parser.expand_str(data, store),
                          '5 = 2 + 3')

    def test_replace_two_levels(self):
        # Given
        data = 'This is equal to {value}'
        store = {'value': '{part1}{part2}',
                 'part1': 'fi',
                 'part2': '{part3}e',
                 'part3': 'v'}

        # Then
        self.assertEquals(parser.expand_str(data, store),
                          'This is equal to five')

    def test_infinite_substitution_raises(self):
        # Given
        data = '{key1}'
        store = {'key1': '{key2}', 'key2': '{key1}'}

        # Then
        with self.assertRaises(RuntimeError):
            parser.expand_str(data, store)


if __name__ == '__main__':
    unittest.main()
