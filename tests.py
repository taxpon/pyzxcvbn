# -*- coding: utf-8 -*-
from __future__ import absolute_import
import math
import unittest

from pyzxcvbn import scoring
from pyzxcvbn.scoring import binom

from pyzxcvbn import matching
from pyzxcvbn.matching import is_empty
from pyzxcvbn.adjacency_graphs import adjacency_graphs


class TestScoringFunctions(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_insert_val_to_arr(self):

        # Case
        a1 = [0, 0, 0]
        scoring.insert_val_to_arr(a1, 5, 1)
        self.assertEqual(a1, [0, 0, 0, None, None, 1])

        # Case
        a2 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        scoring.insert_val_to_arr(a2, 5, 100)
        self.assertEqual(a2, [1, 2, 3, 4, 5, 100, 7, 8, 9])

    def test_search(self):
        def m(i, j, guesses):
            return {
                "i": i,
                "j": j,
                "guesses": guesses
            }
        password = "0123456789"

        # for tests, set additive penalty to zero.
        exclude_additive = True

        # Case
        def msg1(s):
            return "returns one bruteforce match given an empty match sequence: {}".format(s)

        result = scoring.most_guessable_match_sequence(password, [])
        self.assertEqual(len(result["sequence"]), 1, msg1("len(result) == 1"))
        m0 = result["sequence"][0]
        self.assertEqual(m0["pattern"], "bruteforce", msg1("match['pattern'] == 'bruteforce'"))
        self.assertEqual(m0["token"], password, msg1("match['token'] == '{}'".format(password)))
        self.assertEqual([m0["i"], m0["j"]], [0, 9], msg1("[i, j] == [{}, {}]".format(m0["i"], m0["j"])))

        # Case
        def msg2(s):
            return "returns match + bruteforce when match covers a prefix of password: {}".format(s)
        m0 = m(0, 5, 1)
        matches = [m0]
        result = scoring.most_guessable_match_sequence(password, matches, exclude_additive)
        self.assertEqual(len(result["sequence"]), 2, msg2("len(result.match.sequence) == 2"))
        self.assertEqual(result["sequence"][0], m0, msg2("first match is the provided match object"))
        m1 = result["sequence"][1]
        self.assertEqual(m1["pattern"], "bruteforce", msg2("second match is bruteforce"))
        self.assertEqual([m1["i"], m1["j"]], [6, 9], msg2("second match covers full suffix after first match"))

        # Case
        def msg3(s):
            return "returns bruteforce + match when match covers a suffix: {}".format(s)
        m1 = m(3, 9, 1)
        matches = [m1]
        result = scoring.most_guessable_match_sequence(password, matches, exclude_additive)
        self.assertEqual(len(result["sequence"]), 2, msg3("result.match.sequence.length == 2"))
        m0 = result["sequence"][0]
        self.assertEqual(m0["pattern"], "bruteforce", msg3("first match is bruteforce"))
        self.assertEqual([m0["i"], m0["j"]], [0, 2], msg3("first match covers full prefix before second match"))
        self.assertEqual(result["sequence"][1], m1, msg3("second match is the provided match object"))

        # Case
        def msg4(s):
            return "returns bruteforce + match + bruteforce when match covers an infix: {}".format(s)
        m1 = m(1, 8, 1)
        matches = [m1]
        result = scoring.most_guessable_match_sequence(password, matches, exclude_additive)
        self.assertEqual(len(result["sequence"]), 3, msg4("result.length == 3"))
        self.assertEqual(result["sequence"][1], m1, msg4("middle match is the provided match object"))
        m0 = result["sequence"][0]
        m2 = result["sequence"][2]
        self.assertEqual([m0["i"], m0["j"]], [0, 0], msg4("first match covers full prefix before second match"))
        self.assertEqual([m2["i"], m2["j"]], [9, 9], msg4("third match covers full suffix after second match"))

        # Case
        def msg5(s):
            return "chooses lower-guesses match given two matches of the same span: {}".format(s)
        m0, m1 = (m(0, 9, 1), m(0, 9, 2))
        matches = [m0, m1]
        result = scoring.most_guessable_match_sequence(password, matches, exclude_additive)
        self.assertEqual(len(result["sequence"]), 1, msg5("result.length == 1"))
        self.assertEqual(result["sequence"][0], m0, msg5("result.sequence[0] == m0"))
        m0["guesses"] = 3
        result = scoring.most_guessable_match_sequence(password, matches, exclude_additive)
        self.assertEqual(len(result["sequence"]), 1, msg5("result.length == 1"))
        self.assertEqual(result["sequence"][0], m1, msg5("result.sequence[0] == m1"))

        # Case
        def msg6(s):
            return "when m0 covers m1 and m2, choose [m0] when m0 < m1 * m2 * fact(2): {}".format(s)
        m0, m1, m2 = (m(0, 9, 3), m(0, 3, 2), m(4, 9, 1))
        matches = [m0, m1, m2]
        result = scoring.most_guessable_match_sequence(password, matches, exclude_additive)
        self.assertEqual(result["guesses"], 3, msg6("total guesses == 3"))
        self.assertEqual(result["sequence"], [m0], msg6("sequence is [m0]"))

        # Case
        def msg7(s):
            return "when m0 covers m1 and m2, choose [m1, m2] when m0 > m1 * m2 * fact(2): {}".format(s)
        m0["guesses"] = 5
        result = scoring.most_guessable_match_sequence(password, matches, exclude_additive)
        self.assertEqual(result["guesses"], 4, msg7("total guesses == 3"))
        self.assertEqual(result["sequence"], [m1, m2], msg7("sequence is [m0]"))

    def test_calc_guesses(self):

        # Case
        match = {"guesses": 1}
        msg = "estimate_guesses returns cached guesses when available"
        self.assertEqual(scoring.estimate_guesses(match, ''), 1, msg)

        match = {
            "pattern": 'date',
            "token": '1977',
            "year": 1977,
            "month": 7,
            "day": 14
        }
        msg = "estimate_guesses delegates based on pattern"
        self.assertEqual(scoring.estimate_guesses(match, "1977"), scoring.date_guesses(match))

    def test_repeat_guesses(self):
        pattern_list = [
            ["aa",   "a",  2],
            ["999",  "9",  3],
            ["$$$$", "$",  4],
            ["abab", "ab", 2],
            ["batterystaplebatterystaplebatterystaple", "batterystaple", 3]
        ]
        for [token, base_token, repeat_count] in pattern_list:
            base_guesses = scoring.most_guessable_match_sequence(
                base_token,
                matching.omnimatch(base_token)
            )["guesses"]
            match = {
                "token": token,
                "base_token": base_token,
                "base_guesses": base_guesses,
                "repeat_count": repeat_count
            }

            expected_guesses = base_guesses * repeat_count
            msg = "the repeat pattern '{}' has guesses of {}".format(token, expected_guesses)
            self.assertEqual(scoring.repeat_guesses(match), expected_guesses, msg)

    def test_sequence_guesses(self):

        # Case
        pattern_list = [
            ["ab",   True,  4 * 2],       # obvious start * len-2
            ["XYZ",  True,  26 * 3],      # base26 * len-3
            ["4567", True,  10 * 4],      # base10 * len-4
            ["7654", False, 10 * 4 * 2],  # base10 * len 4 * descending
            ["ZYX",  False, 4 * 3 * 2]    # obvious start * len-3 * descending
        ]
        for token, ascending, guesses in pattern_list:
            match = {
                "token": token,
                "ascending": ascending
            }
            msg = "the sequence pattern '{}' has guesses of {}".format(token, guesses)
            self.assertEqual(scoring.sequence_guesses(match), guesses, msg)

    def test_regex_guesses(self):
        match = {
            "token": 'aizocdk',
            "regex_name": 'alpha_lower',
            "regex_match": ['aizocdk']
        }
        msg = "guesses of 26^7 for 7-char lowercase regex"
        self.assertEqual(scoring.regex_guesses(match), math.pow(26, 7), msg)

    def test_date_guesses(self):

        # Case
        match = {
            "token": "1123",
            "separator": "",
            "has_full_year": False,
            "year": 1923,
            "month": 1,
            "day": 1
        }
        msg = "guesses for {} is days * months * distance_from_ref_year", format(match["token"])
        self.assertEqual(scoring.date_guesses(match), 12 * 31 * math.fabs(scoring.REFERENCE_YEAR - match["year"]), msg)

        # Case
        match = {
            "token": "1/1/2010",
            "separator": "/",
            "has_full_year": True,
            "year": 2010,
            "month": 1,
            "day": 1
        }
        msg = "recent years assume MIN_YEAR_SPACE."
        msg += " extra guesses is added for separators and a 4-digit year."
        self.assertEqual(scoring.date_guesses(match), 12 * 31 * scoring.MIN_YEAR_SPACE * 4 * 2, msg)

    def test_spatial_guesses(self):

        # Case
        match = {
            "token": "zxcvbn",
            "graph": "qwerty",
            "turns": 1,
            "shifted_count": 0
        }

        base_guesses = (
            scoring.KEYBOARD_STARTING_POSITIONS *
            scoring.KEYBOARD_AVERAGE_DEGREE *
            # - 1 term because: not counting spatial patterns of length 1
            # eg for length==6, multiplier is 5 for needing to try len2,len3,..,len6
            (len(match["token"]) - 1)
        )
        msg = "with no turns or shifts, guesses is starts * degree * (len-1)"
        self.assertEqual(scoring.spatial_guesses(match), base_guesses, msg)

        # Case
        match["guesses"] = None
        match["token"] = "ZxCvbn"
        match["shifted_count"] = 2
        shifted_guesses = base_guesses * (binom(6, 2) + binom(6, 1))
        msg = "guesses is added for shifted keys, similar to capitals in dictionary matching"
        self.assertEqual(scoring.spatial_guesses(match), shifted_guesses, msg)

        # Case
        match["guesses"] = None
        match["token"] = "ZXCVBN"
        match["shifted_count"] = 6
        shifted_guesses = base_guesses * 2
        msg = "when everything is shifted, guesses are doubled"
        self.assertEqual(scoring.spatial_guesses(match), shifted_guesses, msg)

        # Case
        match = {
            "token": "zxcft6yh",
            "graph": "qwerty",
            "turns": 3,
            "shifted_count": 0,
        }
        guesses = 0
        L = len(match["token"])
        s = scoring.KEYBOARD_STARTING_POSITIONS
        d = scoring.KEYBOARD_AVERAGE_DEGREE
        for i in range(2, L + 1):
            for j in range(1, min(match["turns"], i - 1) + 1):
                guesses += binom(i-1, j-1) * s * math.pow(d, j)
        msg = "spatial guesses accounts for turn positions, directions and starting keys"
        self.assertEqual(scoring.spatial_guesses(match), guesses, msg)

    def test_dictionary_guesses(self):

        # Case
        match = {
            "token": "aaaaa",
            "rank": 32
        }
        msg = "base guesses == the rank"
        self.assertEqual(scoring.dictionary_guesses(match), 32, msg)

        # Case
        match = {
            "token": "AAAaaa",
            "rank": 32
        }
        msg = "extra guesses are added for capitalization"
        self.assertEqual(scoring.dictionary_guesses(match), 32 * scoring.uppercase_variations(match), msg)

        # Case
        match = {
            "token": "aaa",
            "rank": 32,
            "reversed": True
        }
        msg = "guesses are doubled when word is reversed"
        self.assertEqual(scoring.dictionary_guesses(match), 32 * 2, msg)

        # Case
        match = {
            "token": 'aaa@@@',
            "rank": 32,
            "l33t": True,
            "sub": {'@': 'a'}
        }
        msg = "extra guesses are added for common l33t substitutions"
        self.assertEqual(scoring.dictionary_guesses(match), 32 * scoring.l33t_variations(match), msg)

        # Case
        match = {
            "token": 'AaA@@@',
            "rank": 32,
            "l33t": True,
            "sub": {'@': 'a'}
        }
        msg = "extra guesses are added for both capitalization and common l33t substitutions"
        expected = 32 * scoring.l33t_variations(match) * scoring.uppercase_variations(match)
        self.assertEqual(scoring.dictionary_guesses(match), expected, msg)

    def test_uppercase_variations(self):

        # Case
        pattern_list = [
            ['', 1],
            ['a', 1],
            ['A', 2],
            ['abcdef', 1],
            ['Abcdef', 2],
            ['abcdeF', 2],
            ['ABCDEF', 2],
            ['aBcdef', binom(6, 1)],
            ['aBcDef', binom(6, 1) + binom(6, 2)],
            ['ABCDEf', binom(6, 1)],
            ['aBCDEf', binom(6, 1) + binom(6, 2)],
            ['ABCdef', binom(6, 1) + binom(6, 2) + binom(6, 3)]
        ]
        for word, variants in pattern_list:
            msg = "guess multiplier of {} is {}".format(word, variants)
            self.assertEqual(scoring.uppercase_variations({"token": word}), variants, msg)

    def test_l33t_variations(self):

        # Case
        match = {"l33t": False}
        self.assertEqual(scoring.l33t_variations(match), 1, "1 variant for non-l33t matches")

        # Case
        pattern_list = [
            ['',  1, {}],
            ['a', 1, {}],
            ['4', 2, {'4': 'a'}],
            ['4pple', 2, {'4': 'a'}],
            ['abcet', 1, {}],
            ['4bcet', 2, {'4': 'a'}],
            ['a8cet', 2, {'8': 'b'}],
            ['abce+', 2, {'+': 't'}],
            ['48cet', 4, {'4': 'a', '8': 'b'}],
            ['a4a4aa',  binom(6, 2) + binom(6, 1), {'4': 'a'}],
            ['4a4a44',  binom(6, 2) + binom(6, 1), {'4': 'a'}],
            ['a44att+', (binom(4, 2) + binom(4, 1)) * binom(3, 1), {'4': 'a', '+': 't'}]
        ]
        for word, variants, sub in pattern_list:
            match = {
                "token": word,
                "sub": sub,
                "l33t": not is_empty(sub)
            }
            msg = "extra l33t guesses of {} is {}".format(word, variants)
            self.assertEqual(scoring.l33t_variations(match), variants, msg)

        # Case
        match = {
            "token": 'Aa44aA',
            "l33t": True,
            "sub": {'4': 'a'}
        }
        variants = binom(6, 2) + binom(6, 1)
        msg = "capitalization doesn't affect extra l33t guesses calc"
        self.assertEqual(scoring.l33t_variations(match), variants, msg)


class TestMatchingFunctions(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def genpws(self, pattern, prefixes, suffixes):
        for lst in [prefixes, suffixes]:
            if "" not in lst:
                lst.insert(0, "")
        result = []
        for prefix in prefixes:
            for suffix in suffixes:
                i = len(prefix)
                j = len(prefix) + len(pattern) - 1
                result.append([prefix + pattern + suffix, i, j])
        return result

    def check_matches(self, prefix, matches, pattern_names, patterns, ijs, props):
        if isinstance(pattern_names, (str, unicode)):
            pattern_names = [pattern_names for _ in range(len(patterns))]

        # Length check
        is_equal_len_args = len(pattern_names) == len(patterns) == len(ijs)
        for prop, lst in props.items():
            is_equal_len_args = is_equal_len_args and (len(lst) == len(patterns))
        self.assertTrue(is_equal_len_args)

        msg = "{}: matches.length({}) != {}".format(
            prefix, len(matches), len(patterns)
        )
        self.assertEqual(len(matches), len(patterns), msg=msg)

        for k in range(len(patterns)):
            match = matches[k]
            pattern_name = pattern_names[k]
            pattern = patterns[k]
            i, j = ijs[k]

            # pattern_name
            msg = "{}: matches[{}].pattern == '{}'".format(prefix, k, pattern_name)
            self.assertEqual(match["pattern"], pattern_name, msg=msg)

            # ijs
            msg = "{}: matches[{}] should have [i, j] of [{}, {}]".format(prefix, k, i, j)
            self.assertEqual([match["i"], match["j"]], [i, j], msg=msg)

            # token
            msg = "{}: matches[{}].token({}) == '{}'".format(prefix, k, match["token"],  pattern)
            self.assertEqual(match["token"], pattern, msg=msg)

            # Property check
            for prop_name, prop_list in props.items():
                prop_msg = prop_list[k]
                if isinstance(prop_msg, (str, unicode)):
                    prop_msg = "'{}'".format(prop_msg)
                msg = "{}: matches[{}].{}({}) == {}".format(prefix, k, prop_name, match[prop_name], prop_msg)
                self.assertEqual(match[prop_name], prop_list[k], msg=msg)

    def test_dictionary_match(self):
        test_dicts = {
            "d1": {
                "motherboard": 1,
                "mother": 2,
                "board": 3,
                "abcd": 4,
                "cdef": 5
            },
            "d2": {
                "z": 1,
                "8": 2,
                "99": 3,
                "$": 4,
                "asdf1234&*": 5
            }
        }

        def dm(pw):
            return matching.dictionary_match(pw, test_dicts)

        # Case
        matches = dm("motherboard")
        patterns = ["mother", "motherboard", "board"]
        msg = "matches words that contain other words"
        self.check_matches(msg, matches, "dictionary", patterns, [[0, 5], [0, 10], [6, 10]], {
            "matched_word": ["mother", "motherboard", "board"],
            "rank": [2, 1, 3],
            "dictionary_name": ["d1", "d1", "d1"]
        })

        # Case
        matches = dm("abcdef")
        patterns = ["abcd", "cdef"]
        msg = "matches multiple words when they overlap"
        self.check_matches(msg, matches, "dictionary", patterns, [[0, 3], [2, 5]], {
            "matched_word": ["abcd", "cdef"],
            "rank": [4, 5],
            "dictionary_name": ["d1", "d1"]
        })

        # Case
        matches = dm("BoaRdZ")
        patterns = ["BoaRd", "Z"]
        msg = "ignores uppercasing"
        self.check_matches(msg, matches, "dictionary", patterns, [[0, 4], [5, 5]], {
            "matched_word": ["board", "z"],
            "rank": [3, 1],
            "dictionary_name": ["d1", "d2"]
        })

        # Case
        prefixes = ["q", "%%"]
        suffixes = ["%", "qq"]
        word = "asdf1234&*"
        for password, i, j in self.genpws(word, prefixes, suffixes):
            matches = dm(password)
            msg = "identifies words surrounded by non-words"
            self.check_matches(msg, matches, "dictionary", [word], [[i, j]], {
                "matched_word": [word],
                "rank": [5],
                "dictionary_name": ["d2"]
            })

        # Case
        for name, dic in test_dicts.items():
            for word, rank in dic.items():
                if word is "motherboard":
                    continue  # skip words that contain others
                matches = dm(word)
                msg = "matches against all words in provided dictionaries"
                self.check_matches(msg, matches, "dictionary", [word], [[0, len(word) - 1]], {
                    "matched_word": [word],
                    "rank": [rank],
                    "dictionary_name": [name]
                })

        # Case
        # test the default dictionaries
        matches = matching.dictionary_match("rosebud")
        patterns = ["ros", "rose", "rosebud", "bud"]
        ijs = [[0, 2], [0, 3], [0, 6], [4, 6]]
        msg = "default dictionaries"
        self.check_matches(msg, matches, "dictionary", patterns, ijs, {
            "matched_word": patterns,
            "rank": [13085, 65, 245, 786],
            "dictionary_name": ["surnames", "female_names", "passwords", "male_names"]
        })

        # Case
        matching.set_user_input_dictionary(["foo", "bar"])
        matches = matching.dictionary_match("foobar")
        matches = filter(lambda m: m["dictionary_name"] == "user_inputs", matches)
        msg = "matches with provided user input dictionary"
        self.check_matches(msg, matches, "dictionary", ["foo", "bar"], [[0, 2], [3, 5]], {
            "matched_word": ["foo", "bar"],
            "rank": [1, 2]
        })

    def test_reversed_dictionary_match(self):

        # Case
        test_dicts = {
            "d1": {
                "123": 1,
                "321": 2,
                "456": 3,
                "654": 4
            }
        }
        password = "0123456789"
        matches = matching.reverse_dictionary_match(password, test_dicts)
        msg = "matches against reversed words"
        self.check_matches(msg, matches, "dictionary", ["123", "456"], [[1, 3], [4, 6]], {
            "matched_word": ["321", "654"],
            "reversed": [True, True],
            "dictionary_name": ["d1", "d1"],
            "rank": [2, 4]
        })

    def test_l33t_match(self):
        test_table = {
            "a": ["4", "@"],
            "c": ["(", "{", "[", "<"],
            "g": ["6", "9"],
            "o": ["0"]
        }
        tests_dict = {
            "words": {
                "aac": 1,
                "password": 3,
                "paassword": 4,
                "asdf0": 5
            },
            "words2": {
                "cgo": 1
            }
        }

        # Case
        pattern_list = [
            ["", {}],
            ["abcdefgo123578!#$&*)]}>", {}],
            ["a",     {}],
            ["4",     {"a": ["4"]}],
            ["4@",    {"a": ["4", "@"]}],
            ["4({60", {"a": ["4"], "c": ["(", "{"], "g": ["6"], "o": ["0"]}]
        ]
        for pw, expected in pattern_list:
            msg = "reduces l33t table to only the substitutions that a password might be employing"
            self.assertEqual(matching.relevant_l33t_subtable(pw, test_table), expected, msg)

        # Case
        pattern_list2 = [
            [{},                        [{}]],
            [{"a": ["@"]},                [{"@": "a"}]],
            [{"a": ["@", "4"]},            [{"@": "a"}, {"4": "a"}]],
            [{"a": ["@", "4"], "c": ["("]},  [{"@": "a", "(": "c"}, {"4": "a", "(": "c"}]]
        ]
        for table, subs in pattern_list2:
            msg = "enumerates the different sets of l33t substitutions a password might be using"
            self.assertEqual(matching.enumerate_l33t_subs(table), subs, msg)

        # Case
        def lm(password):
            return matching.l33t_match(password, tests_dict, test_table)
        self.assertEqual(lm(""), [], "doesn't match ''")
        self.assertEqual(lm("password"), [], "doesn't match pure dictionary words")

        # Case
        pattern_list3 = [
            # ["p4ssword",   "p4ssword", "password", "words",  3, [0, 7],  {"4": "a"}],
            ["p@ssw0rd",    "p@ssw0rd", "password", "words",  3, [0, 7],  {"@": "a", "0": "o"}],
            ["aSdfO{G0asDfO", "{G0",    "cgo",      "words2", 1, [5, 7], {"{": "c", "0": "o"}]
        ]
        for password, pattern, word, dictionary_name, rank, ij, sub in pattern_list3:
            msg = "matches against common l33t substitutions"
            self.check_matches(msg, lm(password), "dictionary", [pattern], [ij], {
                "l33t": [True],
                "sub": [sub],
                "matched_word": [word],
                "rank": [rank],
                "dictionary_name": [dictionary_name]
            })

        # Case
        matches = lm("@a(go{G0")
        msg = "matches against overlapping l33t patterns"
        self.check_matches(msg, matches, "dictionary", ["@a(", "(go", "{G0"], [[0, 2], [2, 4], [5, 7]], {
            "l33t": [True, True, True],
            "sub": [{"@": "a", "(": "c"}, {"(": "c"}, {"{": "c", "0": "o"}],
            "matched_word": ["aac", "cgo", "cgo"],
            "rank": [1, 1, 1],
            "dictionary_name": ["words", "words2", "words2"]
        })

        # Case
        msg = "doesn't match when multiple l33t substitutions are needed for the same letter"
        self.assertEqual(lm("p4@ssword"), [], msg)

        # Case
        msg = "doesn't match single-character l33ted words"
        matches = matching.l33t_match("4 1 @")
        self.assertEqual(matches, [], msg)

    def test_spatial_match(self):

        # Case
        for password in ["", "/", "qw", "*/"]:
            msg = "doesn't match 1- and 2-character spatial patterns"
            self.assertEqual(matching.spatial_match(password), [], msg)

        # Case
        _graphs = {
            "qwerty": adjacency_graphs["qwerty"]
        }
        pattern = "6tfGHJ"
        matches = matching.spatial_match("rz!{}%z:".format(pattern), _graphs)
        msg = "matches against spatial patterns surrounded by non-spatial patterns"
        self.check_matches(msg, matches, "spatial", [pattern], [[3, 3 + len(pattern) - 1]], {
            "graph": ["qwerty"],
            "turns": [2],
            "shifted_count": [3]
        })

        # Case
        pattern_list = [
            ["12345",        "qwerty",     1, 0],
            ["@WSX",         "qwerty",     1, 4],
            ["6tfGHJ",       "qwerty",     2, 3],
            ["hGFd",         "qwerty",     1, 2],
            ["/;p09876yhn",  "qwerty",     3, 0],
            ["Xdr%",         "qwerty",     1, 2],
            ["159-",         "keypad",     1, 0],
            ["*84",          "keypad",     1, 0],
            ["/8520",        "keypad",     1, 0],
            ["369",          "keypad",     1, 0],
            ["/963.",        "mac_keypad", 1, 0],
            ["*-632.0214",   "mac_keypad", 9, 0],
            ["aoEP%yIxkjq:", "dvorak",     4, 5],
            [";qoaOQ:Aoq;a", "dvorak",    11, 4]
        ]
        for pattern, keyboard, turns, shifts in pattern_list:
            _graphs = {
                keyboard: adjacency_graphs[keyboard]
            }
            matches = matching.spatial_match(pattern, _graphs)
            msg = "matches '{}' as a {} pattern".format(pattern, keyboard)
            self.check_matches(msg, matches, "spatial", [pattern], [[0, len(pattern) - 1]], {
                "graph": [keyboard],
                "turns": [turns],
                "shifted_count": [shifts]
            })

    def test_sequence_match(self):

        # Case
        for password in ["", "a", "1"]:
            msg = "doesn't match length-{} sequences".format(len(password))
            self.assertEqual(matching.sequence_match(password), [], msg)

        # Case
        matches = matching.sequence_match("abcbabc")
        msg = "matches overlapping patterns"
        self.check_matches(msg, matches, "sequence",  ["abc", "cba", "abc"], [[0, 2], [2, 4], [4, 6]], {
            "ascending": [True, False, True]
        })

        # Case
        msg = "matches sequences that wrap from end to start"
        self.assertEqual(len(matching.sequence_match("xyzabc")), 1, msg)

        # Case
        msg = "matches reverse sequences that wrap from start to end"
        self.assertEqual(len(matching.sequence_match("cbazyx")), 1, msg)

        # Case
        prefixes = ["!", "22"]
        suffixes = ["!", "22"]
        pattern = "jihg"
        for password, i, j in self.genpws(pattern, prefixes, suffixes):
            matches = matching.sequence_match(password)
            msg = "matches embedded sequence patterns"
            self.check_matches(msg, matches, "sequence", [pattern], [[i, j]], {
                "sequence_name": ["lower"],
                "ascending": [False]
            })

        # Case
        pattern_list = [
            ['ABC',   'upper',  True],
            ['CBA',   'upper',  False],
            ['PQR',   'upper',  True],
            ['RQP',   'upper',  False],
            ['XYZ',   'upper',  True],
            ['ZYX',   'upper',  False],
            ['abcd',  'lower',  True],
            ['dcba',  'lower',  False],
            ['jihg',  'lower',  False],
            ['wxyz',  'lower',  True],
            ['zyxw',  'lower',  False],
            ['01234', 'digits', True],
            ['43210', 'digits', False],
            ['67890', 'digits', True],
            ['09876', 'digits', False]
        ]
        for pattern, name, is_ascending in pattern_list:
            matches = matching.sequence_match(pattern)
            msg = "matches '{}' as a '{}' sequence".format(pattern, name)
            self.check_matches(msg, matches, "sequence", [pattern], [[0, len(pattern) - 1]], {
                "sequence_name": [name],
                "ascending": [is_ascending]
            })

    def test_repeat_match(self):

        # Case
        for password in ["", "#"]:
            msg = "doesn't match length-{} repeat patterns".format(len(password))
            self.assertEqual(matching.repeat_match(password), [], msg)

        # Case
        prefixes = ["@", "y4@"]
        suffixes = ["u", "u%7"]
        pattern = '&&&&&'
        for password, i, j in self.genpws(pattern, prefixes, suffixes):
            matches = matching.repeat_match(password)
            msg = "matches embedded repeat patterns"
            self.check_matches(msg, matches, "repeat", [pattern], [[i, j]], {
                "base_token": ["&"]
            })

        # Case
        for length in [3, 12]:
            for c in ["a", "Z", "4", "&"]:
                pattern = "".join([c for _ in range(length + 1)])
                matches = matching.repeat_match(pattern)
                msg = "matches repeats with base character '{}'".format(c)
                self.check_matches(msg, matches, "repeat",
                                   [pattern], [[0, len(pattern) - 1]],
                                   {
                                       "base_token": [c]
                                   })

        # Case
        matches = matching.repeat_match("BBB1111aaaaa@@@@@@")
        patterns = ["BBB", "1111", "aaaaa", "@@@@@@"]
        msg = "matches multiple adjacent repeats"
        self.check_matches(msg, matches, "repeat",
                           patterns, [[0, 2], [3, 6], [7, 11], [12, 17]],
                           {
                               "base_token": ["B", "1", "a", "@"]
                           })

        # Case
        matches = matching.repeat_match("2818BBBbzsdf1111@*&@!aaaaaEUDA@@@@@@1729")
        msg = "matches multiple repeats with non-repeats in-between"
        self.check_matches(msg, matches, "repeat",
                           patterns, [[4, 6], [12, 15], [21, 25], [30, 35]],
                           {
                               "base_token": ["B", "1", "a", "@"]
                           })

        # Case
        pattern = "abab"
        matches = matching.repeat_match(pattern)
        msg = "matches multi-character repeat pattern"
        self.check_matches(msg, matches, "repeat", [pattern], [[0, len(pattern) - 1]], {
            "base_token": ["ab"]
        })

        # Case
        pattern = "aabaab"
        matches = matching.repeat_match(pattern)
        msg = "matches aabaab as a repeat instead of the aa prefix"
        self.check_matches(msg, matches, "repeat", [pattern], [[0, len(pattern) - 1]], {
            "base_token": ["aab"]
        })

        # Case
        pattern = "abababab"
        matches = matching.repeat_match(pattern)
        msg = "identifies ab as repeat string, even though abab is also repeated"
        self.check_matches(msg, matches, "repeat", [pattern], [[0, len(pattern) - 1]], {
            "base_token": ["ab"]
        })

    def test_regex_match(self):

        # Case
        pattern_list = [
            ['aaa', 'alpha_lower'],
            ['a7c8D9', 'alphanumeric'],
            ['aAaA', 'alpha'],
            ['1922', 'recent_year'],
            ['&@*#', 'symbols'],
            ['94113', 'digits'],
        ]
        for pattern, name in pattern_list:
            matches = matching.regex_match(pattern)
            msg = "matches {} as a {} pattern".format(pattern, name)
            self.check_matches(
                msg,
                matches, "regex", [pattern], [[0, len(pattern) - 1]],
                {
                    "regex_name": [name]
                }
            )

        # Case
        password = 'a7c8D9vvv2015'
        matches = matching.regex_match(password)
        ijs = [[0, 12], [6, 8], [9, 12]]
        msg = "matches multiple overlapping regex patterns"
        self.check_matches(
            msg, matches, "regex", ['a7c8D9vvv2015', 'vvv', '2015'], ijs,
            {
                "regex_name": ['alphanumeric', 'alpha_lower', 'recent_year']
            }
        )

    def test_date_match(self):

        # Case
        for sep in ["", " ", "-", "/", "\\", "_", "."]:
            password = "13{sep}2{sep}1921".format(sep=sep)
            matches = matching.date_match(password)
            self.check_matches(
                "matches dates with '{}' format".format(sep),
                matches, "date", [password], [[0, len(password) - 1]],
                {
                    "separator": [sep],
                    "year": [1921],
                    "month": [2],
                    "day": [13]
                }
            )

        # Case
        for order in ["mdy", "dmy", "ymd", "ydm"]:
            d, m, y = [8, 8, 88]
            password = order\
                .replace("y", str(y))\
                .replace("m", str(m))\
                .replace("d", str(d))
            matches = matching.date_match(password)
            self.check_matches(
                "matches dates with '{}' format".format(order),
                matches, "date", [password], [[0, len(password) - 1]],
                {
                    "separator": [''],
                    "year": [1988],
                    "month": [8],
                    "day": [8]
                }
            )

        # Case
        password = "111504"
        matches = matching.date_match(password)
        self.check_matches(
            "matches the date with year closest to REFERENCE_YEAR when ambiguous",
            matches, "date", [password], [[0, len(password) - 1]],
            {
                "separator": [''],
                "year": [2004],
                "month": [11],
                "day": [15]
            }
        )

        # Case
        date_list = [[1, 1, 1999], [11, 8, 2000], [9, 12, 2005], [22, 11, 1551]]
        for day, month, year in date_list:
            password = "{}{}{}".format(year, month, day)
            matches = matching.date_match(password)
            self.check_matches(
                "matches {}".format(password),
                matches, "date", [password], [[0, len(password) - 1]],
                {
                    "separator": [''],
                    "year": [year]
                }
            )

            password = "{}.{}.{}".format(year, month, day)
            matches = matching.date_match(password)
            self.check_matches(
                "matches {}".format(password),
                matches, "date", [password], [[0, len(password) - 1]],
                {
                    "separator": ['.'],
                    "year": [year]
                }
            )

        # Case
        password = "02/02/02"
        matches = matching.date_match(password)
        self.check_matches(
            "matches zero-padded dates",
            matches, "date", [password], [[0, len(password) - 1]],
            {
                "separator": ["/"],
                "year": [2002],
                "month": [2],
                "day": [2]
            })

        # Case
        prefixes = ["a", "ab"]
        suffixes = ["!"]
        pattern = "1/1/91"
        for password, i, j in self.genpws(pattern, prefixes, suffixes):
            matches = matching.date_match(password)
            self.check_matches(
                "matches embedded dates",
                matches, "date", [pattern], [[i, j]],
                {
                    "year": [1991],
                    "month": [1],
                    "day": [1]
                }
            )

        # Case
        matches = matching.date_match("12/20/1991.12.20")
        self.check_matches(
            "matches overlapping dates",
            matches, "date", ['12/20/1991', '1991.12.20'], [[0, 9], [6, 15]],
            {
                "separator": ["/", "."],
                "year": [1991, 1991],
                "month": [12, 12],
                "day": [20, 20]
            }
        )

        # Case
        matches = matching.date_match("912/20/919")
        self.check_matches(
            "matches dates padded by non-ambiguous digits",
            matches, "date", ['12/20/91'], [[1, 8]],
            {
                "separator": ["/"],
                "year": [1991],
                "month": [12],
                "day": [20]
            }
        )


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTests(unittest.makeSuite(TestMatchingFunctions))
    test_suite.addTests(unittest.makeSuite(TestScoringFunctions))
    return test_suite

if __name__ == "__main__":
    unittest.main()
