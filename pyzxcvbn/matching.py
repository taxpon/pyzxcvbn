# -*- coding: utf-8 -*-
from __future__ import absolute_import
import re
import math

from pyzxcvbn import scoring
from .adjacency_graphs import adjacency_graphs
from .frequency_lists import frequency_lists
from six.moves import filter
from six.moves import range


def build_ranked_dict(ordered_list):
    """Return ranked dict of word list
    :param list ordered_list:
    :rtype: dict
    """

    result = {}
    i = 1
    for word in ordered_list:
        result[word] = i
        i += 1
    return result

RANKED_DICTIONARIES = {
    "passwords": build_ranked_dict(frequency_lists["passwords"]),
    "english": build_ranked_dict(frequency_lists["english"]),
    "surnames": build_ranked_dict(frequency_lists["surnames"]),
    "male_names": build_ranked_dict(frequency_lists["male_names"]),
    "female_names": build_ranked_dict(frequency_lists["female_names"])
}

GRAPHS = {
    "qwerty": adjacency_graphs["qwerty"],
    "dvorak": adjacency_graphs["dvorak"],
    "keypad": adjacency_graphs["keypad"],
    "mac_keypad": adjacency_graphs["mac_keypad"]
}

SEQUENCES = {
    "lower": "abcdefghijklmnopqrstuvwxyz",
    "upper": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "digits": "0123456789"
}

L33T_TABLE = {
    "a": ['4', '@'],
    "b": ['8'],
    "c": ['(', '{', '[', '<'],
    "e": ['3'],
    "g": ['6', '9'],
    "i": ['1', '!', '|'],
    "l": ['1', '|', '7'],
    "o": ['0'],
    "s": ['$', '5'],
    "t": ['+', '7'],
    "x": ['%'],
    "z": ['2']
}

REGEXEN = {
    "alphanumeric": "[a-zA-Z0-9]{2,}",
    "alpha":        "[a-zA-Z]{2,}",
    "alpha_lower":  "[a-z]{2,}",
    "alpha_upper":  "[A-Z]{2,}",
    "digits":       "\d{2,}",
    "symbols":      "[\W_]{2,}",  # includes non-latin unicode chars
    "recent_year":  "19\d\d|200\d|201\d",
}

REGEX_PRECEDENCE = {
    "alphanumeric": 0,
    "alpha":        1,
    "alpha_lower":  2,
    "alpha_upper":  2,
    "digits":       2,
    "symbols":      2,
    "recent_year":  3
}

DATE_MAX_YEAR = 2050
DATE_MIN_YEAR = 1000
DATE_SPLITS = {
    4: [      # for length-4 strings, eg 1191 or 9111, two ways to split:
        [1, 2],  # 1 1 91 (2nd split starts at index 1, 3rd at index 2)
        [2, 3]   # 91 1 1
    ],
    5: [
        [1, 3],  # 1 11 91
        [2, 3]   # 11 1 91
    ],
    6: [
        [1, 2],  # 1 1 1991
        [2, 4],  # 11 11 91
        [4, 5]   # 1991 1 1
    ],
    7: [
        [1, 3],  # 1 11 1991
        [2, 3],  # 11 1 1991
        [4, 5],  # 1991 1 11
        [4, 6]   # 1991 11 1
    ],
    8: [
        [2, 4],  # 11 11 1991
        [4, 6]   # 1991 11 11
    ]
}


def is_empty(obj):
    return len([k for k in obj]) == 0


def translate(string, c_map):
    """Translate according to character mapping table
    :param str string:
    :param dict c_map:
    :rtype: str
    """
    mapped_string = ""
    for c in string:
        if c in c_map:
            mapped_string += c_map[c]
        else:
            mapped_string += c
    return mapped_string


def mod(n, m):
    return ((n % m) + m) % m


def omnimatch(password):
    """Apply all match functions
    :param str password:
    :rtype: list
    """
    matches_all = []
    matchers = [
        dictionary_match,
        reverse_dictionary_match,
        l33t_match,
        spatial_match,
        repeat_match,
        sequence_match,
        regex_match,
        date_match
    ]

    for matcher in matchers:
        matches = matcher(password)
        matches_all += matches
    return sorted(matches_all, key=lambda x: (x['i'], x['j']))


def dictionary_match(password, _ranked_dictionaries=RANKED_DICTIONARIES):
    """

    :param str password:
    :param dict _ranked_dictionaries:
    :return:
    """
    matches = []
    length = len(password)

    password_lower = password.lower()

    for dictionary_name, ranked_dict in _ranked_dictionaries.items():
        for i in range(length):
            for j in range(length):
                token = password_lower[i:j+1]
                if token in ranked_dict:
                    word = token
                    rank = ranked_dict[word]
                    matches.append({
                        "pattern": "dictionary",
                        "i": i,
                        "j": j,
                        "token": password[i:j+1],
                        "matched_word": word,
                        "rank": rank,
                        "dictionary_name": dictionary_name,
                        "reversed": False
                    })

    return sorted(matches, key=lambda x: (x['i'], x['j']))


def reverse_dictionary_match(password, _ranked_dictionaries=RANKED_DICTIONARIES):
    reversed_password = password[::-1]
    matches = dictionary_match(reversed_password, _ranked_dictionaries)
    for match in matches:
        match["token"] = match["token"][::-1]
        match["reversed"] = True
        match["i"], match["j"] = (len(password) - 1 - match["j"], len(password) - 1 - match["i"])

    return sorted(matches, key=lambda x: (x['i'], x['j']))


def set_user_input_dictionary(ordered_list):
    """Set user-defined dictionary
    :param list ordered_list:
    :return: None
    """
    RANKED_DICTIONARIES["user_inputs"] = build_ranked_dict(ordered_list[:])


# #########################################################
# dictionary match with common l33t substitutions
# #########################################################


def relevant_l33t_subtable(password, table):
    password_chars = {}
    for c in password:
        password_chars[c] = True
    subtable = {}
    for letter, subs in table.items():
        relevant_subs = [sub for sub in subs if sub in password_chars]
        if len(relevant_subs) > 0:
            subtable[letter] = relevant_subs
    return subtable


def enumerate_l33t_subs(table):
    """

    :param dict table:
    :return:
    """
    keys = [key for key in table.keys()]
    subs = [[[]]]

    def dedup(sub_list):
        """Delete duplicated data
        :param list of list sub_list:
        :return:
        """
        deduped = []
        members = {}
        for sub in sub_list:

            assoc = [[k, v] for k, v in sub]
            assoc.sort()
            label = "-".join([str(k) + "," + str(v) for k, v in assoc])
            if label not in members:
                members[label] = True
                deduped.append(sub)
        return deduped

    def helper(helper_keys):
        if len(helper_keys) == 0:
            return
        first_key = helper_keys[0]
        rest_keys = helper_keys[1:]
        next_subs = []
        for l33t_chr in table[first_key]:
            for sub in subs[0]:
                dup_l33t_index = [-1]
                for i in range(len(sub)):
                    if sub[i][0] == l33t_chr:
                        dup_l33t_index[0] = i
                        break
                if dup_l33t_index[0] == -1:
                    sub_extension = sub + [[l33t_chr, first_key]]
                    next_subs.append(sub_extension)
                else:
                    sub_alternative = sub[:]
                    sub_alternative.pop(dup_l33t_index[0])
                    sub_alternative.append([l33t_chr, first_key])
                    next_subs.append(sub)
                    next_subs.append(sub_alternative)
        subs[0] = dedup(next_subs)
        helper(rest_keys)

    helper(keys)
    sub_dicts = []  # convert from assoc lists to dicts
    for sub in subs[0]:
        sub_dict = {}
        for l33t_c, c in sub:
            sub_dict[l33t_c] = c
        sub_dicts.append(sub_dict)
    return sub_dicts


def l33t_match(password, _ranked_dictionaries=RANKED_DICTIONARIES, _l33t_table=L33T_TABLE):
    matches = []
    for sub in enumerate_l33t_subs(relevant_l33t_subtable(password, _l33t_table)):
        if is_empty(sub):
            break
        subbed_password = translate(password, sub)
        for match in dictionary_match(subbed_password, _ranked_dictionaries):
            token = password[match["i"]:match["j"]+1]
            if token.lower() == match["matched_word"]:
                continue
            match_sub = {}
            for subbed_c, c in sub.items():
                if token.find(subbed_c) == -1:
                    continue
                match_sub[subbed_c] = c

            match["l33t"] = True
            match["token"] = token
            match["sub"] = match_sub
            match["sub_display"] = ", ".join(["{} -> {}".format(k, v) for k, v in match_sub.items()])
            matches.append(match)
    return sorted([m for m in matches if len(m["token"]) > 1], key=lambda x: (x['i'], x['j']))


# #########################################################
# spatial match (qwerty/dvorak/keypad)
# #########################################################

SHIFTED_RX = '[~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?]'


def spatial_match(password, _graphs=GRAPHS):
    matches = []
    for graph_name, graph in _graphs.items():
        matches.extend(spatial_match_helper(password, graph, graph_name))
    return sorted(matches, key=lambda x: (x["i"], x["j"]))


def spatial_match_helper(password, graph, graph_name):
    matches = []
    i = 0
    while i < len(password) - 1:
        j = i + 1
        last_direction = None
        turns = 0

        if graph_name in ['qwerty', 'dvorak'] and re.findall(SHIFTED_RX, password[i]):
            # initial character is shifted
            shifted_count = 1
        else:
            shifted_count = 0

        while True:
            prev_char = password[j - 1]
            found = False
            found_direction = -1
            cur_direction = -1
            adjacents = graph[prev_char] if prev_char in graph else []
            # consider growing pattern by one character if j hasn't gone over the edge
            if j < len(password):
                cur_char = password[j]
                for adj in adjacents:
                    cur_direction += 1
                    if adj and adj.find(cur_char) != -1:
                        found = True
                        found_direction = cur_direction
                        if adj.find(cur_char) == 1:
                            shifted_count += 1
                        if last_direction != found_direction:
                            turns += 1
                            last_direction = found_direction
                        break

            if found:
                j += 1

            else:
                if (j - i) > 2:
                    matches.append({
                        "pattern": "spatial",
                        "i": i,
                        "j": j - 1,
                        "token": password[i:j],
                        "graph": graph_name,
                        "turns": turns,
                        "shifted_count": shifted_count
                    })
                i = j
                break

    return matches


# #########################################################
# repeats (aaa, abcabcabc) and sequences (abcdef)
# #########################################################

def repeat_match(password):
    matches = []
    greedy = r"(.+)\1+"
    lazy = r"(.+?)\1+"
    lazy_anchored = r"^(.+?)\1+$"
    lastIndex = 0

    while lastIndex < len(password):
        greedy_match = re.search(greedy, password[lastIndex:])
        lazy_match = re.search(lazy, password[lastIndex:])

        if greedy_match is None:
            break

        if len(greedy_match.group(0)) > len(lazy_match.group(0)):
            match = greedy_match
            base_token = re.search(lazy_anchored, match.group(0)).group(1)

        else:
            match = lazy_match
            base_token = match.group(1)

        i, j = [match.start() + lastIndex, match.start() + len(match.group(0)) - 1 + lastIndex]

        # TODO: Implement base analysis
        base_analysis = scoring.most_guessable_match_sequence(base_token, omnimatch(base_token))
        base_matches = base_analysis["match_sequence"] if "match_sequence" in base_analysis and base_analysis["match_sequence"] is not None else None
        base_guesses = base_analysis["guesses"]
        matches.append({
            "pattern": "repeat",
            "i": i,
            "j": j,
            "token": match.group(0),
            "base_token": base_token,
            "base_guesses": base_guesses,
            "base_matches": base_matches,
            "repeat_count": len(match.group(0)) / len(base_token)
        })
        lastIndex = j + 1
    return matches


def sequence_match(password):
    matches = []
    for sequence_name, sequence in SEQUENCES.items():
        for direction in [1, -1]:
            i = 0
            while i < len(password):
                if password[i] not in sequence:
                    i += 1
                    continue
                j = i + 1
                sequence_position = sequence.find(password[i])

                while j < len(password):
                    next_sequence_position = mod(sequence_position + direction, len(sequence))
                    if sequence.find(password[j]) != next_sequence_position:
                        break
                    j += 1
                    sequence_position = next_sequence_position
                j -= 1
                if (j - i + 1) > 1:
                    matches.append({
                        "pattern": "sequence",
                        "i": i,
                        "j": j,
                        "token": password[i:j+1],
                        "sequence_name": sequence_name,
                        "sequence_space": len(sequence),
                        "ascending": direction == 1
                    })
                i = j + 1

    return sorted(matches, key=lambda x: (x['i'], x['j']))


# #########################################################
# regex matching
# #########################################################

def regex_match(password, _regexen=REGEXEN):
    matches = []
    for name, regex in _regexen.items():
        rx_matches = re.finditer(regex, password)
        for rx_match in rx_matches:
            token = rx_match.group(0)
            matches.append({
                "pattern": "regex",
                "token": token,
                "i": rx_match.start(),
                "j": rx_match.start() + len(rx_match.group(0)) - 1,
                "regex_name": name,
                "regex_match": rx_match
            })

    precedence_map = {}

    def get_key(m):
        return "{}-{}".format(m["i"], m["j"])

    for match in matches:
        key = get_key(match)
        precedence = REGEX_PRECEDENCE[match["regex_name"]]
        if key in precedence_map:
            highest_precedence = precedence_map[key]
            if highest_precedence >= precedence:
                continue
        precedence_map[key] = precedence

    return sorted(
        [m for m in matches if precedence_map[get_key(m)] == REGEX_PRECEDENCE[m["regex_name"]]],
        key=lambda x: (x["i"], x["j"])
    )


# #########################################################
# date matching
# #########################################################

def date_match(password):
    matches = []
    maybe_date_no_separator = r"^\d{4,8}$"
    maybe_date_with_separator = r"^(\d{1,4})([\s/\\_.-])(\d{1,2})\2(\d{1,4})$"

    # dates without separators are between length 4 '1985' and 8 '29051985'
    for i in range(len(password) - 3):
        for j in range(i+3, i+8):
            if j >= len(password):
                break
            token = password[i:j+1]
            rx_match = re.match(maybe_date_no_separator, token)
            if rx_match is None:
                continue
            candidates = []
            for k, l in DATE_SPLITS[len(token)]:
                dmy = map_ints_to_dmy([
                    int(token[0:k]),
                    int(token[k:l]),
                    int(token[l:])
                ])
                if dmy is not None:
                    candidates.append(dmy)

            if not len(candidates) > 0:
                continue

            def metric(candidate_date):
                return math.fabs(candidate_date['year'] - scoring.REFERENCE_YEAR)

            best_candidate = candidates[0]
            min_distance = metric(candidates[0])

            for candidate in candidates[1:]:
                distance = metric(candidate)
                if distance < min_distance:
                    best_candidate = candidate
                    min_distance = distance

            matches.append({
                "pattern": "date",
                "token": token,
                "i": i,
                "j": j,
                "separator": "",
                "year": best_candidate["year"],
                "month": best_candidate["month"],
                "day": best_candidate["day"]
            })

    # dates with separators are between length 6 '5/9/91' and 10 '05/29/1985'
    for i in range(len(password) - 5):
        for j in range(i+5, i+10):
            if j >= len(password):
                break
            token = password[i:j+1]
            rx_match = re.match(maybe_date_with_separator, token)
            if rx_match is None:
                continue

            dmy = map_ints_to_dmy([
                int(rx_match.group(1)),
                int(rx_match.group(3)),
                int(rx_match.group(4))
            ])

            if dmy is None:
                continue

            matches.append({
                "pattern": "date",
                "token": token,
                "i": i,
                "j": j,
                "separator": rx_match.group(2),
                "year": dmy["year"],
                "month": dmy["month"],
                "day": dmy["day"],
            })

    def del_submatch(match):
        is_submatch = False
        for other_match in matches:
            if match is other_match:
                continue
            if other_match["i"] <= match["i"] and other_match["j"] >= match["j"]:
                is_submatch = True
                break
        return not is_submatch

    return sorted(filter(del_submatch, matches))


def map_ints_to_dmy(int_list):
    """Convert list of integer into dict of (year, month, day)
    :param list of int int_list:
    :retype: dict
    """
    if int_list[1] > 31 or int_list[1] <= 0:
        return None

    over_12 = 0
    over_31 = 0
    under_1 = 0
    for i in int_list:
        if 99 < i < DATE_MIN_YEAR or i > DATE_MAX_YEAR:
            return None

        if i > 31:
            over_31 += 1
        if i > 12:
            over_12 += 1
        if i <= 0:
            under_1 += 1

    if over_31 >= 2 or over_12 == 3 or under_1 >= 2:
        return None

    possible_year_splits = [
        [int_list[2], int_list[:2]],  # year last
        [int_list[0], int_list[1:]]   # year first
    ]
    for [y, rest] in possible_year_splits:
        if DATE_MIN_YEAR <= y <= DATE_MAX_YEAR:
            dm = map_ints_to_dm(rest)
            if dm is not None:
                return {
                    "year": y,
                    "month": dm["month"],
                    "day": dm["day"]
                }
            else:
                return None

    for [y, rest] in possible_year_splits:
        dm = map_ints_to_dm(rest)
        if dm is not None:
            y = two_to_four_digit_year(y)
            return {
                "year": y,
                "month": dm["month"],
                "day": dm["day"]
            }


def map_ints_to_dm(int_list):
    """Convert list of integer into dict of (day, month)
    :param list int_list:
    :rtype: dict
    """
    for d, m in [int_list, reversed(int_list)]:
        if 1 <= d <= 31 and 1 <= m <= 12:
            return {
                "day": d,
                "month": m
            }
    return None


def two_to_four_digit_year(year):
    """Convert two-digits year into four-digits year
    :param int year:
    :rtype: int
    """
    if year > 99:
        return year
    elif year > 50:
        # 85 -> 1985
        return year + scoring.REFERENCE_YEAR - 100
    else:
        # 15 -> 2015
        return year + scoring.REFERENCE_YEAR
