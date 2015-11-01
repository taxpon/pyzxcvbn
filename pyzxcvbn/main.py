# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime

from . import matching
from . import scoring
from . import time_estimates
from . import feedback


def zxcvbn(password, user_inputs=()):
    """Measure strength of the password
    :param str password:
    :param list user_inputs:
    :rtype: dict
    """
    start = datetime.datetime.now()
    # reset the user inputs matcher on a per-request basis to keep things stateless
    sanitized_inputs = []
    for arg in user_inputs:
        if isinstance(arg, (str, int, bool)):
            sanitized_inputs.append(str(arg).lower())
    matching.set_user_input_dictionary(sanitized_inputs)
    matches = matching.omnimatch(password)
    result = scoring.most_guessable_match_sequence(password, matches)
    result["calc_time"] = datetime.datetime.now() - start
    attack_time = time_estimates.estimate_attack_times(result["guesses"])
    for prop, val in attack_time.items():
        result[prop] = val
    result["feedback"] = feedback.get_feedback(result["score"], result["sequence"])
    return result
