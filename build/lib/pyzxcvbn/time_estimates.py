
def estimate_attack_times(guesses):
    crack_times_seconds = {
        "online_throttling_100_per_hour": guesses / (100.0 / 3600.0),
        "online_no_throttling_10_per_second": guesses / 1e2,
        "offline_slow_hashing_1e4_per_second": guesses / 1e4,
        "offline_fast_hashing_1e10_per_second": guesses / 1e10
    }

    crack_times_display = {}
    for scenario, seconds in crack_times_seconds.items():
        crack_times_display[scenario] = display_time(seconds)

    return {
        "crack_times_seconds": crack_times_seconds,
        "crack_times_display": crack_times_display,
        "score": guesses_to_score(guesses)
    }


def guesses_to_score(guesses):
    DELTA = 5
    if guesses < (1e3 + DELTA):
        # risky password: "too guessable"
        return 0
    elif guesses < (1e6 + DELTA):
        # modest protection from throttled online attacks: "very guessable"
        return 1
    elif guesses < (1e8 + DELTA):
        # modest protection from unthrottled online attacks: "somewhat guessable"
        return 2
    elif guesses < (1e10 + DELTA):
        # modest protection from offline attacks: "safely unguessable"
        # assuming a salted, slow hash function like bcrypt, scrypt, PBKDF2, argon, etc
        return 3
    else:
        # strong protection from offline attacks under same scenario: "very unguessable"
        return 4


def display_time(seconds):
    minute = 60
    hour = minute * 60
    day = hour * 24
    month = day * 31
    year = month * 12
    century = year * 100

    if seconds < 1:
        display_num, display_str = (None, "less than a second")
    elif seconds < minute:
        base = round(seconds)
        display_num, display_str = (base, "{} second".format(base))
    elif seconds < hour:
        base = round(seconds / minute)
        display_num, display_str = (base, "{} minute".format(base))
    elif seconds < day:
        base = round(seconds / hour)
        display_num, display_str = (base, "{} hour".format(base))
    elif seconds < month:
        base = round(seconds / day)
        display_num, display_str = (base, "{} day".format(base))
    elif seconds < year:
        base = round(seconds / month)
        display_num, display_str = (base, "{} month".format(base))
    elif seconds < century:
        base = round(seconds / year)
        display_num, display_str = (base, "{} year".format(base))

    else:
        display_num, display_str = (None, "centuries")

    if display_num is not None and display_num != 1:
        display_str += "s"
    return display_str
