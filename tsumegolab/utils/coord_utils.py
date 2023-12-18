import string

SGF_COORDS = string.ascii_lowercase[:19]
GTP_COORDS = string.ascii_uppercase[:20].replace("I", "")


def sgf_to_int_coord(coord: str) -> tuple:
    x, y = coord
    return SGF_COORDS.index(y), SGF_COORDS.index(x)


def int_to_sgf_coord(coord: tuple) -> str:
    x, y = coord
    return f"{SGF_COORDS[y]}{SGF_COORDS[x]}"


def int_to_gtp_coord(coord: tuple[int, int]) -> str:
    x, y = coord
    return f"{GTP_COORDS[y]}{19 - x}"


def gtp_to_int_coord(coord: str) -> tuple[int, int]:
    x, y = coord[0], int(coord[1:])
    return 19 - y, GTP_COORDS.index(x)


def sgf_to_gtp_coord(coord: str) -> str:
    return int_to_gtp_coord(sgf_to_int_coord(coord))


def gtp_to_sgf_coord(coord: str) -> str:
    return int_to_sgf_coord(gtp_to_int_coord(coord))
