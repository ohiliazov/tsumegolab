## Analysis logic

### Blacks turn
Analyse all possible moves, where the best response is not a pass.
Moves, which lose less than half of initial score difference, are correct.
Other moves are wrong.
Analyse wrong variation until white can pass on every move.
Moves with pass response are not included in a tree.

# Whites turn
if black made a mistake before, find one best move
if black is correct analyze all possible moves,
a response to which is not a pass
