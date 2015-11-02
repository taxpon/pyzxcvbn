# -*- coding: utf-8 -*-
from __future__ import absolute_import
import re

from . import scoring

default_feedback = {
    "warning": "",
    "suggestions": [
        "Use a few words, avoid common phrases",
        "No need for symbols, digits, or uppercase letters"
    ]
}


def get_feedback(score, sequence):
    # starting feedback
    if len(sequence) == 0:
        return default_feedback

    # no feedback if score is good or great.
    if score > 2:
        return {
            "warning": "",
            "suggestions": []
        }

    # tie feedback to the longest match for longer sequences
    longest_match = sequence[0]
    for match in sequence[1:]:
        if len(match["token"]) > len(longest_match["token"]):
            longest_match = match
    feedback = get_match_feedback(longest_match, len(sequence) == 1)
    extra_feedback = "Add another word or two. Uncommon words are better."

    if feedback:
        feedback["suggestions"].insert(1, extra_feedback)
        if "warning" not in feedback or feedback["warning"] is None:
            feedback["warning"] = ""
    else:
        feedback = {
            "warning": "",
            "suggestions": [extra_feedback]
        }

    return feedback


def get_match_feedback(match, is_sole_match):

    if "pattern" not in match:
        return

    elif match["pattern"] == "dictionary":
        return get_dictionary_match_feedback(match, is_sole_match)

    elif match["pattern"] == "spatial":
        if "turns" in match and match["turns"] == 1:
            warning = "Straight rows of keys are easy to guess"
        else:
            warning = "Short keyboard patterns are easy to guess"

        return {
            "warning": warning,
            "suggestions": [
                "Use a longer keyboard pattern with more turns"
            ]
        }

    elif match["pattern"] == "repeat":
        if len(match["base_token"]) == 1:
            warning = "Repeats like 'aaa' are easy to guess"
        else:
            warning = "Repeats like 'abcabcabc' are only slightly harder to guess than 'abc'"
        return {
            "warning": warning,
            "suggestions": [
                "Avoid repeated words and characters"
            ]
        }

    elif match["pattern"] == "sequence":
        return {
            "warning": "Sequences like abc or 6543 are easy to guess",
            "suggestions": [
                "Avoid sequences"
            ]
        }

    elif match["pattern"] == "regex":
        if match["regex_name"] == "recent_year":
            return {
                "warning": "Recent years are easy to guess",
                "suggestions": [
                    "Avoid recent years",
                    "Avoid years that are associated with you"
                ]
            }

    elif match["pattern"] == "date":
        return {
            "warning": "Dates are often easy to guess",
            "suggestions": [
                "Avoid dates and years that are associated with you"
            ]
        }


def get_dictionary_match_feedback(match, is_sole_match):

    warning = ""
    if "dictionary_name" not in match:
        warning = ""

    elif match["dictionary_name"] == "passwords":
        if is_sole_match and \
                (("l33t" not in match) or not match["l33t"]) and \
                (("reversed" not in match) or not match["reversed"]):
            if match["rank"] <= 10:
                warning = "This is a top-10 common password"
            elif match["rank"] <= 100:
                warning = "This is a top-100 common password"
            else:
                warning = "This is a very common password"
        elif match["guesses_log10"] <= 4:
            warning = "This is similar to a commonly used password"

    elif match["dictionary_name"] == "english":
        if is_sole_match:
            warning = "A word by itself is easy to guess"

    elif match["dictionary_name"] in ["surnames", "male_names", "female_names"]:
        if is_sole_match:
            warning = "Names and surnames by themselves are easy to guess"
        else:
            warning = "Common names and surnames are easy to guess"

    else:
        warning = ""

    suggestions = []
    word = match["token"]

    if re.match(scoring.START_UPPER, word):
        suggestions.append("Capitalization doesn't help very much")
    elif re.match(scoring.ALL_UPPER, word):
        suggestions.append("All-uppercase is almost as easy to guess as all-lowercase")

    if "reversed" in match and match["reversed"] and len(match["token"]) >= 4:
        suggestions.append("Reversed words aren't much harder to guess")

    if "l33t" in match and match["l33t"]:
        suggestions.append("Predictable substitutions like '@' instead of 'a' don't help very much")

    return {
        "warning": warning,
        "suggestions": suggestions
    }
