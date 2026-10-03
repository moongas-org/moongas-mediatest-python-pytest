from mediascan.genres import Genre


def get_all_genre_strings() -> list[str]:
    return [g.value for g in Genre]
