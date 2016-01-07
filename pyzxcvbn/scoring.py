import math
import re
from decimal import Decimal

from adjacency_graphs import adjacency_graphs

# on qwerty, 'g' has degree 6, being adjacent to 'ftyhbv'. '\' has degree 1.
# this calculates the average over all keys.


def calc_average_degree(graph):
    average = 0
    for key, neighbors in graph.items():
        average += len([n for n in neighbors if n])
    average /= len([k for k in graph.keys()])
    return average

BRUTEFORCE_CARDINALITY = 10
MIN_GUESSES_BEFORE_GROWING_SEQUENCE = 10000
MIN_SUBMATCH_GUESSES_SINGLE_CHAR = 10
MIN_SUBMATCH_GUESSES_MULTI_CHAR = 50
REFERENCE_YEAR = 2000


def binom(n, k):
    """
    Returns binomial coefficient (n choose k).
    """
    # http://blog.plover.com/math/choose.html
    if k > n:
        return 0
    if k == 0:
        return 1
    result = 1
    for denom in range(1, k + 1):
        result *= n
        result /= denom
        n -= 1
    return result


def log10(n):
    """
    Returns logarithm of n in base 10.
    """
    return math.log(float(n), 10)


def log2(n):
    """
    Returns logarithm of n in base 2.
    """
    return math.log(n, 2)


def factorial(n):
    """
    Return factorial of n
    """
    if n < 2:
        return 1
    f = 1
    for i in range(1, n):
        f *= i
    return f


def insert_val_to_arr(array, index, value, default=None):
        if (len(array) - 1) > index:
            array[index] = value
        else:
            for i in range(len(array), index+1):
                array.append(default)
            array[index] = value


def most_guessable_match_sequence(password, matches, _exclude_additive=False):
    optimal_product = [[] for _ in range(len(password)+1)]
    backpointers = [[] for _ in range(len(password)+1)]

    max_l = 0
    optimal_l = None

    def make_bruteforce_match(i, j):
        return {
            "pattern": "bruteforce",
            "token": password[i:j+1],
            "i": i,
            "j": j
        }

    def score(guess_product, sequence_length):
        result = math.factorial(sequence_length) * guess_product
        if not _exclude_additive:
            result += math.pow(MIN_GUESSES_BEFORE_GROWING_SEQUENCE, sequence_length - 1)
        return result

    for k in range(len(password)):
        backpointers[k] = []
        optimal_product[k] = []
        optimal_score = Decimal("Infinity")

        for prev_l in range(max_l + 1):
            # for each new k, starting scenario to try to beat: bruteforce matches
            # involving the lowest-possible l. three cases:
            #
            # 1. all-bruteforce match (for length-1 sequences.)
            # 2. extending a previous bruteforce match
            #    (possible when optimal[k-1][l] ends in bf.)
            # 3. starting a new single-char bruteforce match
            #    (possible when optimal[k-1][l] exists but does not end in bf.)
            #
            # otherwise: there is no bruteforce starting scenario that might be better
            # than already-discovered lower-l sequences.
            consider_bruteforce = True
            bf_j = k
            try:
                if prev_l == 0:
                    bf_i = 0
                    new_l = 1
                elif "pattern" in backpointers[k-1][prev_l] and \
                        backpointers[k-1][prev_l]["pattern"] == "bruteforce":
                    bf_i = backpointers[k-1][prev_l]["i"]
                    new_l = prev_l
                elif backpointers[k-1][prev_l] is not None:
                    bf_i = k
                    new_l = prev_l + 1
                else:
                    # bf_i = 0
                    # new_l = None
                    consider_bruteforce = False
            except:
                # bf_i = 0
                # new_l = None
                consider_bruteforce = False

            if consider_bruteforce:
                bf_match = make_bruteforce_match(bf_i, bf_j)
                prev_j = k - len(bf_match["token"])  # end of preceeding match
                candidate_product = estimate_guesses(bf_match, password)
                if new_l > 1:
                    candidate_product *= optimal_product[prev_j][new_l - 1]
                candidate_score = score(candidate_product, new_l)

                if candidate_score < optimal_score:
                    optimal_score = candidate_score
                    # optimal_product[k][new_l] = candidate_product
                    insert_val_to_arr(optimal_product[k], new_l, candidate_product)
                    optimal_l = new_l
                    max_l = max(max_l, new_l)
                    # backpointers[k][new_l] = bf_match
                    insert_val_to_arr(backpointers[k], new_l, bf_match)

            # now try beating those bruteforce starting scenarios.
            # for each match m ending at k, see if forming a (prev_l + 1) sequence
            # ending at m is better than the current optimum.
            for match in matches:
                if match["j"] != k:
                    continue
                i, j = (match["i"], match["j"])

                if prev_l == 0:
                    # if forming a len-1 sequence [match], match.i must fully cover [0..k]
                    if i != 0:
                        continue
                else:
                    # it's only possible to form a new potentially-optimal sequence ending at
                    # match when there's an optimal length-prev_l sequence ending at match.i-1.
                    try:
                        if not optimal_product[i-1][prev_l]:
                            continue
                    except:
                        continue

                candidate_product = estimate_guesses(match, password)
                if prev_l > 0:
                    candidate_product *= optimal_product[i-1][prev_l]
                candidate_score = score(candidate_product, prev_l + 1)
                if candidate_score < optimal_score:
                    optimal_score = candidate_score
                    insert_val_to_arr(optimal_product[k], prev_l + 1, candidate_product)
                    # optimal_product[k][prev_l+1] = candidate_product
                    optimal_l = prev_l + 1
                    max_l = max(max_l, prev_l+1)
                    insert_val_to_arr(backpointers[k], prev_l + 1, match)
                    # backpointers[k][prev_l+1] = match

    # walk backwards and decode the optimal sequence
    match_sequence = []
    l = optimal_l
    k = len(password) - 1

    while k >= 0:
        match = backpointers[k][l]
        match_sequence.append(match)
        k = match["i"] - 1
        l -= 1
    match_sequence.reverse()

    # final result object
    return {
        "password": password,
        "guesses": optimal_score,
        "guesses_log10": log10(optimal_score),
        "sequence": match_sequence
    }


# ------------------------------------------------------------------------------
# guess estimation -- one function per match pattern ---------------------------
# ------------------------------------------------------------------------------
def estimate_guesses(match, password):
    if "guesses" in match and match["guesses"]:
        return match["guesses"]  # a match's guess estimate doesn't change. cache it.
    min_guesses = 1
    if len(match["token"]) < len(password):
        if len(match["token"]) == 1:
            min_guesses = MIN_SUBMATCH_GUESSES_SINGLE_CHAR
        else:
            min_guesses = MIN_SUBMATCH_GUESSES_MULTI_CHAR

    estimation_functions = {
        "bruteforce": bruteforce_guesses,
        "dictionary": dictionary_guesses,
        "spatial":    spatial_guesses,
        "repeat":     repeat_guesses,
        "sequence":   sequence_guesses,
        "regex":      regex_guesses,
        "date":       date_guesses
    }
    guesses = estimation_functions[match["pattern"]](match)
    if not isinstance(guesses, (int, float)):
        print "hoge"
    match["guesses"] = max(guesses, min_guesses)
    match["guesses_log10"] = log10(match["guesses"])
    return match["guesses"]


def bruteforce_guesses(match):
    guesses = math.pow(BRUTEFORCE_CARDINALITY, len(match["token"]))
    # small detail: make bruteforce matches at minimum one guess bigger than smallest allowed
    # submatch guesses, such that non-bruteforce submatches over the same [i..j] take precidence.
    if len(match["token"]) == 1:
        min_guesses = MIN_SUBMATCH_GUESSES_SINGLE_CHAR + 1
    else:
        min_guesses = MIN_SUBMATCH_GUESSES_MULTI_CHAR + 1
    return max(guesses, min_guesses)


def repeat_guesses(match):
    return match["base_guesses"] * match["repeat_count"]


def sequence_guesses(match):
    first_chr = match["token"][0]
    # lower guesses for obvious starting points
    if first_chr in ["a", "A", "z", "Z", "0", "1", "9"]:
        base_guesses = 4
    else:
        if first_chr.isdigit():
            base_guesses = 10  # digits
        else:
            # could give a higher base for uppercase,
            # assigning 26 to both upper and lower sequences is more conservative.
            base_guesses = 26
    if not match["ascending"]:
        # need to try a descending sequence in addition to every ascending sequence ->
        # 2x guesses
        base_guesses *= 2
    return base_guesses * len(match["token"])


MIN_YEAR_SPACE = 20


def regex_guesses(match):
    char_class_bases = {
        "alpha_lower":  26,
        "alpha_upper":  26,
        "alpha":        52,
        "alphanumeric": 62,
        "digits":       10,
        "symbols":      33
    }

    if "regex_name" in match and match["regex_name"] in char_class_bases:
        return math.pow(char_class_bases[match["regex_name"]], len(match["token"]))
    elif "regex_name" in match and match["regex_name"] == "recent_year":
        # conservative estimate of year space: num years from REFERENCE_YEAR.
        # if year is close to REFERENCE_YEAR, estimate a year space of MIN_YEAR_SPACE.
        year_space = math.fabs(int(match["regex_match"].group(0))) - REFERENCE_YEAR
        year_space = max(year_space, MIN_YEAR_SPACE)
        return year_space


def date_guesses(match):
    # base guesses: (year distance from REFERENCE_YEAR) * num_days * num_years
    year_space = max(math.fabs(match["year"] - REFERENCE_YEAR), MIN_YEAR_SPACE)
    guesses = year_space * 31 * 12

    # double for four-digit years
    if "has_full_year" in match and match["has_full_year"]:
        guesses *= 2
    # add factor of 4 for separator selection (one of ~4 choices)
    if "separator" in match and match["separator"]:
        guesses *= 4
    return guesses


KEYBOARD_AVERAGE_DEGREE = calc_average_degree(adjacency_graphs["qwerty"])
# slightly different for keypad/mac keypad, but close enough
KEYPAD_AVERAGE_DEGREE = calc_average_degree(adjacency_graphs["keypad"])

KEYBOARD_STARTING_POSITIONS = len([k for k, v in adjacency_graphs["qwerty"].items()])
KEYPAD_STARTING_POSITIONS = len([k for k, v in adjacency_graphs["keypad"].items()])


def spatial_guesses(match):
    if "graph" in match and match["graph"] in ['qwerty', 'dvorak']:
        s = KEYBOARD_STARTING_POSITIONS
        d = KEYBOARD_AVERAGE_DEGREE
    else:
        s = KEYPAD_STARTING_POSITIONS
        d = KEYPAD_AVERAGE_DEGREE
    guesses = 0
    L = len(match["token"])
    t = match["turns"]
    # estimate the number of possible patterns w/ length L or less with t turns or less.
    for i in range(2, L + 1):
        possible_turns = min(t, i - 1)
        for j in range(1, possible_turns + 1):
            guesses += binom(i - 1, j - 1) * s * math.pow(d, j)

    # add extra guesses for shifted keys. (% instead of 5, A instead of a.)
    # math is similar to extra guesses of l33t substitutions in dictionary matches.
    if "shifted_count" in match and match["shifted_count"]:
        S = match["shifted_count"]
        U = len(match["token"]) - match["shifted_count"]  # unshifted count
        if S == 0 or U == 0:
            guesses *= 2
        else:
            shifted_variations = 0
            for i in range(1, min(S, U) + 1):
                shifted_variations += binom(S + U, i)
            guesses *= shifted_variations
    return guesses


def dictionary_guesses(match):
    match["base_guesses"] = match["rank"]  # keep these as properties for display purposes
    match["uppercase_variations"] = uppercase_variations(match)
    match["l33t_variations"] = l33t_variations(match)
    reversed_variations = 2 if "reversed" in match and match["reversed"] else 1
    return match["base_guesses"] * match["uppercase_variations"] * match["l33t_variations"] * reversed_variations


START_UPPER = r"^[A-Z][^A-Z]+$"
END_UPPER = r"^[^A-Z]+[A-Z]$"
ALL_UPPER = r"^[^a-z]+$"
ALL_LOWER = r"^[^A-Z]+$"
NO_LETTER = r"^$"


def uppercase_variations(match):
    word = match["token"]
    if re.search(ALL_LOWER, word) or re.search(NO_LETTER, word):
        return 1

    # a capitalized word is the most common capitalization scheme,
    # so it only doubles the search space (uncapitalized + capitalized).
    # allcaps and end-capitalized are common enough too, underestimate as 2x factor to be safe.
    for regex in [START_UPPER, END_UPPER, ALL_UPPER]:
        if re.search(regex, word):
            return 2

    # otherwise calculate the number of ways to capitalize U+L uppercase+lowercase letters
    # with U uppercase letters or less. or, if there's more uppercase than lower (for eg. PASSwORD),
    # the number of ways to lowercase U+L letters with L lowercase letters or less.
    U = len([c for c in word if re.match(u"[A-Z]", c)])
    L = len([c for c in word if re.match(u"[a-z]", c)])

    variations = 0
    for i in range(1, min(U, L) + 1):
        variations += binom(U + L, i)
    return variations


def l33t_variations(match):
    if "l33t" not in match or not match["l33t"]:
        return 1
    variations = 1

    for subbed, unsubbed in match["sub"].items():
        # lower-case match.token before calculating: capitalization shouldn't affect l33t calc.
        c_list = match["token"].lower()
        num_subbed = len([c for c in c_list if c == subbed])
        num_unsubbed = len([c for c in c_list if c == unsubbed])

        if num_subbed == 0 or num_unsubbed == 0:
            # for this sub, password is either fully subbed (444) or fully unsubbed (aaa)
            # treat that as doubling the space (attacker needs to try fully subbed chars in addition to
            # unsubbed.)
            variations *= 2

        else:
            # this case is similar to capitalization:
            # with aa44a, U = 3, S = 2, attacker needs to try unsubbed + one sub + two subs
            p = min(num_unsubbed, num_subbed)
            possibilities = 0
            for i in range(1, p+1):
                possibilities += binom(num_unsubbed + num_subbed, i)
            variations *= possibilities

    return variations
