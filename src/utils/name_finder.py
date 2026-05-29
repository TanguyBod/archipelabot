import unicodedata
from difflib import get_close_matches


def normalize_name(name: str) -> str:
    """Normalize a name (case-insensitive + suppression accents + trim)."""
    name = name.strip().lower()
    name = unicodedata.normalize("NFD", name)
    return "".join(c for c in name if unicodedata.category(c) != "Mn")


def resolve_player_name(input_name: str, player_names: list[str], cutoff: float = 0.75) -> str | None:
    """
    Return the name in player_names that best matches input_name, or None if no good match is found.

    - Handle case insensitivity
    - Handle accents
    - Handle typos (fuzzy matching)
    - Handle duplicates differentiated only by case
    """

    if not player_names:
        return None
    
    if input_name in player_names:
        return input_name
    normalized_map: dict[str, list[str]] = {}

    for name in player_names:
        norm = normalize_name(name)
        normalized_map.setdefault(norm, []).append(name)

    input_norm = normalize_name(input_name)

    if input_norm in normalized_map:
        return normalized_map[input_norm][0]

    all_norm_names = list(normalized_map.keys())
    close_matches = get_close_matches(input_norm, all_norm_names, n=1, cutoff=cutoff)

    if not close_matches:
        return None

    best_norm = close_matches[0]
    return normalized_map[best_norm][0]