"""Card rank tables and poker hand ordering for the score estimator."""

# --- card value tables ------------------------------------------------------

RANK_CHIPS = {
    "A": 11,
    "K": 10,
    "Q": 10,
    "J": 10,
    "T": 10,
    "9": 9,
    "8": 8,
    "7": 7,
    "6": 6,
    "5": 5,
    "4": 4,
    "3": 3,
    "2": 2,
}
RANK_ORDER = {
    "A": 14,
    "K": 13,
    "Q": 12,
    "J": 11,
    "T": 10,
    "9": 9,
    "8": 8,
    "7": 7,
    "6": 6,
    "5": 5,
    "4": 4,
    "3": 3,
    "2": 2,
}
EVEN_RANKS = {"2", "4", "6", "8", "10", "T"}
ODD_RANKS = {"A", "3", "5", "7", "9"}
FIBONACCI_RANKS = {"A", "2", "3", "5", "8"}
FACE_RANKS = {"J", "Q", "K"}
LOW_RANKS = {"2", "3", "4", "5"}

# Type jokers: bonus when played hand matches poker type (card.lua joker_main).
TYPE_MULT_JOKERS: dict[str, tuple[str, int]] = {
    "j_jolly": ("Pair", 8),
    "j_zany": ("Three of a Kind", 12),
    "j_mad": ("Two Pair", 10),
    "j_crazy": ("Straight", 12),
    "j_droll": ("Flush", 10),
}
TYPE_CHIPS_JOKERS: dict[str, tuple[str, int]] = {
    "j_sly": ("Pair", 50),
    "j_wily": ("Three of a Kind", 100),
    "j_clever": ("Two Pair", 80),
    "j_devious": ("Straight", 100),
    "j_crafty": ("Flush", 80),
}
# Planets: ×Mult when played hand matches poker type (card.lua joker_main x_mult).
TYPE_XMULT_JOKERS: dict[str, tuple[str, float]] = {
    "j_duo": ("Pair", 2),
    "j_trio": ("Three of a Kind", 3),
    "j_order": ("Straight", 3),
    "j_tribe": ("Flush", 2),
}

# Poker hand type -> Balatro order (lower = better). Matches `query hands`.
HAND_ORDER = {
    "Flush Five": 1,
    "Flush House": 2,
    "Five of a Kind": 3,
    "Straight Flush": 4,
    "Four of a Kind": 5,
    "Full House": 6,
    "Flush": 7,
    "Straight": 8,
    "Three of a Kind": 9,
    "Two Pair": 10,
    "Pair": 11,
    "High Card": 12,
}
