# Othello tree

Generates optimal opening tree

Small web training app for openings



---

##### TODO Training
- [ ] Board
    - [ ] tests
- [ ] OpeningsTree
    - [ ] `__init__(filename)`
        - merge `{black,white}.json`
    - [ ] `OpeningsTree.validate()`:
        - [ ] leaves are final score or `transposition`
        - [ ] move validity (disallow `MOVE_PASS`)
        - [ ] check all moves present for opponent
        - [ ] no duplicate positions when normalizing
    - [ ] `OpeningsTree.get_openings(color)`

- [x] `GET /svg/board/<id>`
    - [x] basic functionality
    - [x] nicer discs
    - [x] mistakes param
- [x] `GET /api/board/<id>`
    - [x] initial
    - [x] xot
    - [x] any id
- [x] `GET /api/openings`
    - [x] redo it
