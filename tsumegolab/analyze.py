def analyze_black_correct(
    analysis: list[dict[str, str]]
) -> list[tuple[bool, str]]:
    # correct and wrong moves
    return [(True, "A1"), (False, "A2"), (False, "A3")]


def analyze_black_wrong(
    analysis: list[dict[str, str]]
) -> list[tuple[bool, str]]:
    # should have only sensible moves for black to show
    # how black's group is dead (or how white's group is alive)
    # only wrong moves where the answer is not a pass
    return [(False, "C1"), (False, "C2")]


def analyze_white_correct(
    analysis: list[dict[str, str]]
) -> list[tuple[bool, str]]:
    # only correct moves, where the answer is not a pass
    return [(True, "B1"), (True, "B2")]


def analyze_white_wrong(
    analysis: list[dict[str, str]]
) -> list[tuple[bool, str]]:
    # only best white move
    return [(False, "D1")]


def analyze_tree(is_correct: bool, tree: list[str]) -> list[tuple[bool, str]]:
    if len(tree) > 2:
        return []

    # run kata-analyse
    analysis = ...
    pass_value = ...
    print(analysis, pass_value)

    if len(tree) % 2 == 0:
        if is_correct:
            return analyze_black_correct(analysis)
        else:
            return analyze_black_wrong(analysis)
    else:
        if is_correct:
            return analyze_white_correct(analysis)
        else:
            return analyze_white_wrong(analysis)


def analyze() -> dict:
    unexplored = [(True, [])]
    moves_tree = {}

    while unexplored:
        tree_is_correct, tree_to_explore = unexplored.pop(0)
        new_trees = analyze_tree(tree_is_correct, tree_to_explore)

        moves_subtree = moves_tree
        for item in tree_to_explore:
            moves_subtree = moves_subtree[item]["moves"]

        for is_correct, move in new_trees:
            moves_subtree[move] = {"correct": is_correct, "moves": {}}

            unexplored.append((is_correct, tree_to_explore + [move]))

    return moves_tree


if __name__ == "__main__":
    print(analyze())
