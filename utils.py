from math import pow

K_FACTOR = 32

def expected_score(ra, rb):
    return 1 / (1 + pow(10, (rb - ra) / 400))

def calc_elo(elo_a, elo_b, score_a, score_b):
    ea = expected_score(elo_a, elo_b)
    eb = expected_score(elo_b, elo_a)
    sa = 1 if score_a > score_b else 0
    sb = 1 - sa
    delta_a = round(K_FACTOR * (sa - ea))
    delta_b = round(K_FACTOR * (sb - eb))
    return elo_a + delta_a, elo_b + delta_b