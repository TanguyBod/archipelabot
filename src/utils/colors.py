async def get_ansi_color_from_flag(flag: int) -> int:
    if flag is None:
        return 37
    elif flag & 0b001:
        return 33
    elif flag & 0b010:
        return 34
    elif flag & 0b100:
        return 31
    else:
        return 37