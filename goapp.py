import tkinter as tk
from tkinter import messagebox
from functools import total_ordering
from itertools import product
from math import inf, isinf

# Constants for point occupation and alternation options
EMPTY: int = 0    # Empty intersection, also deleting stones
BLACK: int = 1    # Black stone, also only Black plays
WHITE: int = -BLACK    # White stone, also only White plays
ALTERNATE: int = 2    # The players alternate placing stones

# Constants for restricting solving
MAX_UNDECIDED = 12    # Maximum number of undecided points
MAX_DEPTH = 50    # Maximum search depth
MAX_COMPLEXITY = 10000000   # Maximum number of stored points when computing

# Constants for graphic realisation
MAX_LENGTH = 25    # Maximum dimension of the board
MIN_SIZE = 16    # Minimum tile size
MAX_SIZE = 99    # Maximum tile size
MAX_GOBAN_SIZE = 700    # Maximum size of the displayed goban
MAX_PRISONERS = 999    # Maximum displayed number of prisoners
MAX_KOMI = 99.5    # Maximum value of komi

class GoError(Exception):
    """Exception class for handling Go-related errors."""

    
class PlacementError(GoError):
    """GoError subclass for rule-violating stone placement (or erasure)."""


class Point:
    """Grid intersection."""
    
    def __init__(self, row, column):
        self.i: int = row
        self.j: int = column    # The point's coordinates
        self.colour: int = EMPTY    # Which stone (if any) occupies the point
        self.adjacent: list["Point"] = []    # Adjacent points
        self.string: "String" = None    # The string (region) the point is part of
        self.active: bool = True    # Whether the point was already processed;
                                    # for use in algorithms, as a mask

    def _string_recursion(self) -> "String":
        """Find the point's string recursively and determine its liberties.

        The string's points and liberties become inactive.
        """
        string = String(self)
        self.active = False
        for neighbour in self.adjacent:
            if neighbour.active:
                if neighbour.colour == EMPTY:
                    neighbour.active = False
                    string.liberties.append(neighbour)
                if neighbour.colour == self.colour:
                    neighbour_string = neighbour._string_recursion()
                    string.points.extend(neighbour_string.points)
                    string.liberties.extend(neighbour_string.liberties)
        return string

    def _region_recursion(self, player: int) -> "String":
        """Find the player-enclosed region containing the point recursively.

        Its empty points are stored as liberties.
        If the region is small (it has no internal empty intersections),
        its alive attribute is set to True, else it is False.
        If the point is occupied by the player, return None.
        The region's points become inactive.
        """
        if self.colour == player:
            return None
        
        region = String(self)
        self.active = False
        region.alive = True
        for neighbour in self.adjacent:
            if neighbour.active and neighbour.colour != player:
                neighbour_region = neighbour._region_recursion(player)
                region.points.extend(neighbour_region.points)
                region.liberties.extend(neighbour_region.liberties)
                region.alive &= neighbour_region.alive
        if self.colour == EMPTY:
            region.liberties.append(self)
            if region.alive and player not in [n.colour for n in self.adjacent]:
                region.alive = False
        return region
    
    def find_string(self, region: int = EMPTY) -> "String":
        """Find the point's string (region).

        If the region option is EMPTY, find the string of intersections with the same colour.
        If it is BLACK or WHITE, find the region enclosed by the player containing the point,
        but if the point is occupied by the player, return None.
        """
        if region == EMPTY:
            string = self._string_recursion()
            for liberty in string.liberties:
                liberty.active = True
        if region != EMPTY:
            string = self._region_recursion(region)
        if string is not None:
            for point in string:
                point.active = True
        return string

    def territory_recursion(self, player: int) -> "String":
        """Find the player-enclosed region and check whether it is territory.

        If it is, its alive attribute is set to True, else it is False or None.
        The obviously alive strings of both players need to have been determined.
        If the point is part of the player's living string, return None.
        The region's points become inactive.
        """
        if self.colour == player and self.string.alive:
            return None
        
        region = String(self)
        self.active = False
        region.alive = None    # Unknown status
        for neighbour in self.adjacent:
            if neighbour.active:
                if (region.alive is None and
                    neighbour.colour == player and neighbour.string.alive):
                    region.alive = True
                elif neighbour.colour == -player and neighbour.string.alive:
                    region.alive = False
                if neighbour.colour == EMPTY or not neighbour.string.alive:
                    neighbour_region = neighbour.territory_recursion(player)
                    region.points.extend(neighbour_region.points)
                    if region.alive is None:
                        region.alive = neighbour_region.alive
                    elif neighbour_region.alive is not None:
                        region.alive &= neighbour_region.alive
        return region

    def isolated(self) -> bool:
        """Whether the newly placed point cannot change life status of the player's strings.

        If no point was placed, return None.
        """
        player = self.colour
        if player == EMPTY:
            return None
        
        # A lone locally dead stone
        if player not in [n.colour for n in self.adjacent]:
            vitals = 0    # The number of the stone's eyes
            for neighbour in filter(lambda n: n.colour == EMPTY, self.adjacent):
                if neighbour.string is None:
                    region = neighbour.find_string(player)
                    for point in region.liberties:
                        point.string = region
                    if len(region.liberties) == 1:
                        vitals += 1
            for neighbour in filter(lambda n: n.colour == EMPTY, self.adjacent):
                if neighbour.string is not None:
                    for point in region.liberties:
                        point.string = None
            if vitals < 2:
                return True
            return False
        
        # Simple string extension
        self.colour = EMPTY
        point = next(filter(lambda n: n.colour == player, self.adjacent))
        string = point.find_string()
        for p in string:
            p.active = False
        if any(n.active for n in self.adjacent if n.colour == player):
            # Different strings were connected
            for p in string:
                p.active = True
            self.colour = player
            return False
        self.colour = player
        other_neighbours = [n for n in self.adjacent if n.colour != player]
        isolated = True
        if other_neighbours:
            region = other_neighbours[0]._region_recursion(player)
            # Whether no new small region was created
            isolated = not (any(n.active for n in self.adjacent if n.colour != player) or
                            region.alive)
            for p in region:
                p.active = True
        for p in string:
            p.active = True
        return isolated

    def dame(self) -> bool:
        """Test whether the point is empty and adjacent to both players' alive strings."""
        if self.colour != EMPTY:
            return False
        stone_neighbours = [n for n in self.adjacent if n.colour != EMPTY]
        return (BLACK in [n.colour for n in stone_neighbours] and
                WHITE in [n.colour for n in stone_neighbours])


class String:
    """Set of points connected by adjacency.

    Used in two ways:
    -- as a maximal set of same-coloured stones;
    -- as a maximal region without stones of one colour.
    """
    
    def __init__(self, point):
        self.points: list["Point"] = [point]    # The string's points
        self.liberties: list["Point"] = []    # The string's liberties
                                              # or region's empty points
        self.vitals: list["String"] = []    # The string's eyes (as regions)
                                            # or the region's enclosing strings
        self.alive: bool = False    # The string's life status
                                    # or whether the region is small / territory

    def __iter__(self):
        """Iterate over the string's points."""
        yield from self.points

    def __len__(self) -> int:
        """Return the number of the string's points."""
        return len(self.points)

    def vital(self, string, player):
        """Check whether the region is an eye of the player's string."""
        for liberty in self.liberties:
            if string not in [p.string for p in liberty.adjacent if p.colour == player]:
                return False
        return True

class Grid(list):
    """The stone layout as a matrix of points."""

    def __init__(self, rows, columns):
        self.m: int = rows
        self.n: int = columns    # The grid's dimensions
        
        list.__init__(self, [[Point(r, c) for c in range(columns)] for r in range(rows)])
        for i, j in product(range(rows), range(columns)):
            for a, b in [(i-1, j), (i, j-1), (i+1, j), (i, j+1)]:
                if a not in {-1, rows} and b not in {-1, columns}:
                    self[i][j].adjacent.append(self[a][b])

    def __iter__(self):
        """Iterate over the grid's points."""
        for row in list.__iter__(self):
            yield from row

    def __eq__(self, other) -> bool:
        """Test the equality of stone layouts."""
        if not isinstance(other, Grid):
            return NotImplemented
        return ([point.colour for point in self] == [point.colour for point in other])

    def copy(self, symmetry: tuple[tuple, int] = ((False, False, False), 1)) -> "Grid":
        """Create a copy of the grid.

        If the symmetric option is non-default, apply the symmetry.
        """
        copy = Grid(self.m, self.n)
        mapping, switch = symmetry
        reflect_i, reflect_j, swap_ij = mapping
        for i, j in product(range(self.m), range(self.n)):
            k = i if not reflect_i else self.m - i - 1
            l = j if not reflect_j else self.n - j - 1
            if swap_ij:
                k, l = l, k
            copy[k][l].colour = switch*self[i][j].colour
        return copy
        
                        
    def uncapturable(self, player: int) -> tuple[list["String"]]:
        """For the player's unconditionally alive strings, set their status to alive.

        Return a list of the player's eyes and the remaining strings with more liberties.
        Benson's algorithm is implemented.
        Retain information about stone strings.
        """
        strings, eyes = [], []
        for point in self:
            if point.string is None:
                if point.colour == player:
                    string = point.find_string()
                    string.alive = True
                    strings.append(string)
                    for p in string:
                        p.string = string
                elif point.colour == EMPTY:
                    region = point.find_string(player)
                    for l in region.liberties:
                        # Already determined strings of the other player are preserved;
                        # only the region's empty points need to be considered
                        l.string = region
                    if region.alive:
                        eyes.append(region)
        for string in strings:
            for liberty in string.liberties:
                if liberty.active:
                    region = liberty.string
                    if region.alive:
                        for l in region.liberties:
                            l.active = False
                        if region.vital(string, player):
                            string.vitals.append(region)
                        region.vitals.append(string)
            for liberty in string.liberties:
                if not liberty.active:
                    for l in liberty.string.liberties:
                        l.active = True

        end = False
        while not end:
            end = True
            for string in filter(lambda s: s.alive, strings):
                if [r.alive for r in string.vitals].count(True) < 2:
                    # Not uncapturable
                    end = False
                    string.alive = False
                    for region in string.vitals:
                        region.alive = False
        for eye in filter(lambda e: e.alive, eyes):
            if not all(s.alive for s in eye.vitals):
                eye.alive = False
            
        for point in filter(lambda p: p.colour == EMPTY, self):
            point.string = None

        return ([s for s in strings if not s.alive and len(s.liberties) > 1],
                [e for e in eyes if e.alive])

    def find_territory(self, player) -> list["Point"]:
        """Return a list of the points which are territory of the player.

        The obvisouly alive strings need to have been determined.
        Assumes that other strings of the player are dead unless they are in their territory.
        Retain stone strings.
        """
        
        territory = []
        for point in self:
            if point.active and point.colour == EMPTY:
                region = point.territory_recursion(player)
                if region.alive:
                    territory.extend([p for p in region.points if p.colour != player])
        for point in self:
            point.active = True
        return territory
        

@total_ordering
class Result:
    """The optimal result and moves."""
    
    def __init__(self, value, heuristic=False, depth=None):
        self.value: float = value    # The obtained value
        self.heuristic: bool = heuristic    # Whether the value is heuristic
        self.depth = depth    # The depth which was searched
        self.children: dict[tuple, "Result"] = {}
        # The optimal continuations indexed by moves
        self.parent = None    # The parent result

        if isinf(self.value):     # The infinities are made absolute
            if self.value > 0:    # so as to yield valid comparisons
                self.heuristic = False
            else:
                self.heuristic = True

    def __neg__(self) -> "Result":
        """Negate the value, retain children."""
        negative = Result(-self.value, self.heuristic)
        negative.children = self.children
        return negative

    def __eq__(self, other) -> bool:
        """Whether the values and heuristic qualities are the same.

        Infinities diregard heuristic value."""
        if not isinstance(other, Result):
            return NotImplemented
        return self.value == other.value and self.heuristic == other.heuristic

    def __lt__(self, other) -> bool:
        """Compare the values.

        Non-heuristic values always dominate heuristic ones.
        """
        if not isinstance(other, Result):
            return NotImplemented
        return (self.heuristic and not other.heuristic or
                self.heuristic == other.heuristic and self.value < other.value)

    def symmetric(self, symmetry: tuple[tuple, int], m: int, n: int) -> "Result":
        """Return a result with the symmetry un-applied, recursively."""
        mapping, switch = symmetry
        reflect_i, reflect_j, swap_ij = mapping
        result = Result(self.value, self.heuristic)
        for move in self.children:
            if move is None:
                result.children[None] = self.children[None].symmetric(symmetry, m, n)
                continue
            i, j = move
            if swap_ij:
                i, j = j, i
            k = i if not reflect_i else m - i - 1
            l = j if not reflect_j else n - j - 1
            result.children[(k, l)] = self.children[move].symmetric(symmetry, m, n)
        return result

    
class Board:
    """Board state during the game.

    Contains information about the stone layout (Grid object),
    prisoner counts and game-specific states (ko, pass).
    """
    
    def __init__(self, grid, ko=None, prisoners={BLACK: 0, WHITE: 0}, passes=0):
        self.grid: Grid = grid    # The stone layout on the board
        self.ko: tuple[int] = ko    # Coordinates of the ko intersection (if it exists)
        self.prisoners: dict[int, int] = prisoners
        # Black's and White's prisoners, respectively
        self.passes: int = passes    # The number of successive prior passes
        
        self.scored = False    # Whether to display the territory
        
        self.territory: dict[int, list] = {BLACK: [], WHITE: []}
        # Black's and White's territory points
        self.undecided: list = []    # The points left to fight over
        self.score: dict[int, int] = {BLACK: 0, WHITE: 0}    # The score of each player
        self.children: dict[tuple, dict[tuple, "Board"]] = {BLACK: {}, WHITE: {}}
        # Board states reachable by moves, indexed by the coordinates (or None for passing)

    def tuple(self) -> tuple:
        """Return an immutable object capturing the board-state."""
        grid = tuple(point.colour for point in self.grid)
        return (grid, self.ko, self.prisoners[BLACK] - self.prisoners[WHITE], self.passes)

    def symmetric(self) -> dict[tuple, "Board"]:
        """Return a dictionary of the symmetric variants of the board.

        The boards are indexed by symmetry type: rotation, reflection and colour switch.
        """
        symmetric = {}
        # The symmetries are given by relecting coordinates, swapping them
        # and switching players; the first three are a 3-tuple of boolean values,
        # switching is denoted by -1 if switch, else 1
        swaps = [False, True] if self.grid.m == self.grid.n else [False]
        mappings = list(product([False, True], [False, True], swaps))
        # Oblong boards cannot swap coordinates
        for symmetry in product(mappings, [1, -1]):
            grid = self.grid.copy(symmetry)
            prisoners = {symmetry[1]*p: _ for p, _ in self.prisoners.items()}
            symmetric[symmetry] = Board(grid, self.ko, prisoners, self.passes)
        return symmetric

    def move(self, player: int, i: int, j: int, ignore_ko: bool) -> "Board":
        """Attempt to place a new stone on the board.

        Raise PlacementError if it were illegal,
        else return a new Board object with the new stone.
        """
        if self.grid[i][j].colour != EMPTY:
            raise PlacementError
        if not ignore_ko and (i, j) == self.ko:
            raise PlacementError

        grid = self.grid.copy()
        ko = None
        prisoners = self.prisoners.copy()
        
        point = grid[i][j]
        point.colour = player
        # Test capture
        for neighbour in point.adjacent:
            if neighbour.colour == -player:
                neighbour_string = neighbour.find_string()
                if not neighbour_string.liberties:
                    prisoners[player] += len(neighbour_string)
                    if len(neighbour_string) == 1:
                        # Ko candidate if only one stone was captured
                        ko = (neighbour.i, neighbour.j)
                    for captured in neighbour_string:
                        captured.colour = EMPTY

        string = point.find_string()
        if not string.liberties:
            raise PlacementError

        # In order for ko to arise, the new string needs to have one stone and one liberty
        if not (ko is not None and len(string) == 1 and
                len(string.liberties) == 1):
            ko = None
            
        return Board(grid, ko, prisoners)

    def erase(self, i: int, j: int, take_prisoner: bool = False) -> "Board":
        """Attempt to delete a stone from the board.

        Raise PlacementError if it were impossible,
        else return a new Board object without the stone.
        The stone is taken as a prisoner if specified.
        """
        if self.grid[i][j].colour == EMPTY:
            raise PlacementError

        grid = self.grid.copy()
        prisoners = self.prisoners.copy()

        point = grid[i][j]
        if take_prisoner:
            prisoners[-point.colour] += 1
        point.colour = EMPTY
            
        return Board(grid, None, prisoners)

    def pass_turn(self) -> "Board":
        """Return a copy of itself after passing a turn."""
        return Board(self.grid, prisoners=self.prisoners, passes=(self.passes + 1))

    def _find_life(self, fast: bool) -> list[tuple]:
        """For the uncapturable strings on the board, set their status to alive.

        If the fast parameter is false, also check life by miai
        (two different moves lead to unconditional life).
        Return the dame (points which are not territory, but of no value).
        Retain stone strings.
        """
        b_strings, b_eyes = self.grid.uncapturable(BLACK)
        w_strings, w_eyes = self.grid.uncapturable(WHITE)
        eye_points = []
        dame = []
        for eye in b_eyes + w_eyes:
            eye_points.extend([(l.i, l.j) for l in eye.liberties])
        for point in filter(lambda p: p.colour == EMPTY, self.grid):
            if (all(n.string.alive for n in point.adjacent if n.colour != EMPTY) and
                (EMPTY in [n.colour for n in point.adjacent] or point.dame()) and
                all(n.dame() for n in point.adjacent if n.colour == EMPTY)):
                dame.append((point.i, point.j))

        if not fast:
            for player, strings in [(BLACK, b_strings), (WHITE, w_strings)]:
                representatives = [(s.points[0].i, s.points[0].j) for s in strings]
                for point in filter(lambda p: p.colour == EMPTY and
                                    (p.i, p.j) not in eye_points and
                                    (p.i, p.j) not in dame, self.grid):
                    try:
                        new_board = self.move(player, point.i, point.j, True)
                    except PlacementError:
                        continue
                    if new_board.grid[point.i][point.j].isolated():
                        continue
                    for string, representative in zip(strings, representatives):
                        if not string.alive:
                            i, j = representative
                            new_board.grid.uncapturable(player)
                            new_string = new_board.grid[i][j].string
                            if new_string.alive:
                                if string.alive is None:
                                    string.alive = True
                                else:
                                    string.alive = None    # Candidate for life
                for string in strings:
                    if string.alive is None:
                        string.alive = False
        return dame
                                                                
    def grade(self, fast: bool = False):
        """Determine the territories, undecided points and score of both players.

        If the fast parameter is true, the computation is less thorough.
        Destroy string information.
        """
        placed_prisoners = {}
        dame = self._find_life(fast)
        for player in [BLACK, WHITE]:
            territory = self.grid.find_territory(player)
            self.territory[player] = [(p.i, p.j) for p in territory]
            placed_prisoners[player] = [p.colour for p in territory].count(-player)
            self.score[player] = (len(self.territory[player]) + placed_prisoners[player]
                                  + self.prisoners[player])

        self.undecided = [(p.i, p.j) for p in self.grid if
                          p.colour == EMPTY and (p.i, p.j) not in dame and
                          (p.i, p.j) not in self.territory[BLACK] + self.territory[WHITE]]

        for point in self.grid:
            point.string = None

    def solve(self, starting_player: int, history: list["Board"],
              dict_graded: dict[tuple, tuple]) -> Result:
        """Attempt to determine the optimal result and moves.

        Return None if the situation is too complex,
        else return the solution as a Result object remembering the principal variation.
        Defines functions for finding children of the boards, ordering moves,
        board evaluation and search for easier handling.
        Employs iterative deepening negamax with alpha-beta pruning,
        transposition tables, symmetry lookups and heuristics.
        """
        
        def make_children(board: "Board", player: int, fast_grading: bool):
            """Find the boards reachable from this one with the player to move"""
            nonlocal dict_graded

            new_board = board.pass_turn()
            if new_board.tuple() in dict_graded:
                new_board = dict_graded[new_board.tuple()][0]
            else:
                # Grading is the same after a pass
                new_board.score = board.score
                new_board.undecided = board.undecided.copy()
                dict_graded[new_board.tuple()] = (new_board, fast_grading)
            board.children[player][None] = new_board    # Passing is denoted by None
            
            for i, j in board.undecided:
                try:
                    new_board = board.move(player, i, j, False)
                except PlacementError:
                    continue
                if new_board.tuple() in dict_graded:
                    new_board = dict_graded[new_board.tuple()][0]
                else:
                    point = new_board.grid[i][j]
                    if (fast_grading and new_board.prisoners == board.prisoners and
                        point.isolated()):
                        # The new stone did not change territory and did not capture;
                        # this can result only in new dame
                        new_board.score = board.score
                        new_board.undecided = board.undecided.copy()
                        new_board.undecided.remove((i, j))
                    else:
                        new_board.grade(True)
                    fast = True
                    if not fast_grading:
                        undecided = new_board.undecided
                        new_board.grade()
                        fast = (undecided == new_board.undecided)
                        # Fast grading can be applied if all territory is unconditional
                    dict_graded[new_board.tuple()] = (new_board, fast)
                board.children[player][(i, j)] = new_board

        def order_children(board: "Board", player: int, depth: int):
            """Order the board's children according to the heuristics.

            The order is: transposition moves, pass, killer moves,
            and the rest sorted by the history heuristic.
            """
            nonlocal dict_solved, heur_killer, heur_history
            children = board.children[player]
            
            stored = ([] if board.tuple() not in dict_solved[player] else
                      dict_solved[player][board.tuple()].children.keys())
            k_moves = [m for m in heur_killer[depth] if m in children]
            h_moves = sorted([m for m in children if m is not None],
                             key=(lambda m: -heur_history[player][m[0]][m[1]]))

            moves = []
            for move_list in [stored, k_moves, [None], h_moves]:
                moves.extend([m for m in move_list if m not in moves])
            
            board.children[player] = {m: children[m] for m in moves}

        def evaluate(board: "Board") -> float:
            """Calculate the heuristic value of the board."""
            value = {}
            for player in [BLACK, WHITE]:
                value[player] = board.score[player]    # Reward captures and territory
                value[player] += (0.2 * [p.colour for p in board.grid].count(player)
                                  + 0.2 * [player in [l.colour for l in p.adjacent]
                                           for p in board.grid].count(True))
                # Play stones with liberties
                
                m, n = board.grid.m, board.grid.n
                for p in filter(lambda p: p.colour == player, board.grid):
                    if any((n.i, n.j) in board.undecided for n in p.adjacent):
                        # Do not play moves on the edges and corners
                        if 0 in {p.i, p.j} or p.i == m or p.j == n:
                            value[player] -= 0.1
                        if (p.i, p.j) in {(0, 0), (0, n), (m, 0), (n, 0)}:
                            value[player] -= 0.2
            return value[BLACK] - value[WHITE]
            
        def negamax(board: "Board", alpha: Result, beta: Result,
                    player: int, depth: int) -> Result:
            """Find the (perhaps provisional) value of the board.

            Return a Result object capturing the value.
            Implements the fixed-depth negamax algortihm with alpha-beta pruning.
            """
            nonlocal history, dict_graded, max_depth, end
            nonlocal dict_solved, heur_killer, heur_history
            
            history.append(board)
            colour = 1 if player == BLACK else -1
            if board.passes == 2:
                history.pop()
                return Result(colour*(board.score[BLACK] - board.score[WHITE]), False)
            repetition = Board.test_repetition(history)
            if repetition is not None:
                history.pop()
                # Draw by repetition is treated as heuristic
                # because it is assumed that optimal play ends with two passes
                return Result(colour*repetition, True)
            if depth == max_depth:    # Heuristic result
                end = False
                history.pop()
                return Result(colour*evaluate(board), True)

            if not board.children[player]:
                fast_grading = dict_graded[board.tuple()][1]
                make_children(board, player, fast_grading)

            if board.tuple() in dict_solved[player]:
                stored = dict_solved[player][board.tuple()]
                if stored.depth >= max_depth - depth:    # Result beyond current max_depth
                    history.pop()
                    return stored
            if board.grid.m * board.grid.n < 25 and depth < 6:
                # Symmetry lookups for small boards
                for symmetry, b in board.symmetric().items():
                    if symmetry == ((False, False, False), 1):    # Identity
                        continue
                    p = symmetry[1]*player
                    if b.tuple() in dict_solved[p]:
                        stored = dict_solved[p][b.tuple()]
                        if stored.depth >= max_depth - depth:
                            history.pop()
                            return stored.symmetric(symmetry, board.grid.m, board.grid.n)

            order_children(board, player, depth)

            options = {}
            best = Result(-inf)
            for move, child in board.children[player].items():
                r = -negamax(child, -beta, -alpha, -player, depth + 1)
                options[move] = r
                best = max(best, r)
                if best > beta:    # Cutoff
                    if move not in heur_killer[depth]:
                        pass
                        heur_killer[depth] = [heur_killer[depth][1], move]
                    if move is not None:
                        i, j = move
                        heur_history[player][i][j] += depth ** 2
                    break
                alpha = max(alpha, best)
            history.pop()

            result = Result(best.value, best.heuristic, max_depth - depth)
            result.children = {m: r for m, r in options.items() if r == best}
            dict_solved[player][board.tuple()] = result
            return result


        self.grade(True)
        undecided = self.undecided
        self.grade()
        dict_graded[self.tuple()] = (self, (undecided == self.undecided))
        if len(self.undecided) > MAX_UNDECIDED:    # Too complex
            return None

        dict_solved: dict[int, dict[tuple, Result]] = {BLACK: {}, WHITE: {}}
        # The transposition table for each player
        heur_killer: list[list] = []    # Two last killer moves for each depth
        heur_history: dict[int, list[list[float]]] = {player:
            [[0 for _ in range(self.grid.n)] for __ in range(self.grid.m)]
                                                      for player in [BLACK, WHITE]}
        
        # The history heuristic for each player
        
        max_depth = 0
        end = False
        while not end:
            end = True
            max_depth += 1
            heur_killer.append([None, None])
            negamax(self, Result(-inf), Result(inf), starting_player, 0)
            
            if (max_depth > MAX_DEPTH or
                ((len(dict_solved[BLACK]) + len(dict_solved[WHITE]))
                      *self.grid.m*self.grid.n > MAX_COMPLEXITY)):
                return None
            
        return dict_solved[starting_player][self.tuple()]

    @staticmethod
    def test_repetition(history: list["Board"]) -> float:
        """Test whether the stone placement has been repeated.

        Search only for long cycles (at least 3 moves).
        If repetition occurs, compute which player has gained more prisoners
        since the last occurence of the position and return
        infinity if Black, minus infinity if White and 0 if neither (as strings).
        ELse return None.
        """
        if not history:
            return None
        
        current = history[-1]
        if len(history) > 3:
            for board in reversed(history[:-3]):
                if board.grid == current.grid:     
                    difference = {player: current.prisoners[player] - board.prisoners[player]
                                  for player in [BLACK, WHITE]}
                    if difference[BLACK] > difference[WHITE]:
                        return inf
                    elif difference[BLACK] < difference[WHITE]:
                        return -inf
                    else:
                        return 0.
        return None
    

class GameModel:
    """Internal model of the game."""
    
    def __init__(self):
        self.dict_graded: dict[tuple, tuple[Board, bool]] = {}
        # Dictionary of the graded board-states and whether the grading was fast
        
        self.history: list[Board] = []    # Past board-states
        self.undo_history: list[Board] = []    # Undone board-states
        self.solution: Result = None    # The stored principal variation
        
        self.player: int = EMPTY    # Current player
        
    def new_board(self, rows: int, columns: int):
        """Create a new, empty board of the given dimensions.

        Forget the graded positions.
        Cannot be undone.
        """
        self.dict_graded = {}
        self.history = [Board(Grid(rows, columns))]
        self.undo_history = []
        self.solution = None

    def reset_prisoners(self):
        """Reset the number of prisoners of both players.

        Cannot be undone.
        """
        board = self.history[-1]
        self.history = [Board(board.grid, ko=board.ko)]
        self.undo_history = []

    def placement(self, i: int, j: int, ignore_ko: bool, take_prisoner: bool):
        """Attempt to place or delete a stone at the given position.

        Show the solution if in the principal variation, else forget it.
        """
        if self.player == EMPTY:
            self.history.append(self.history[-1].erase(i, j, take_prisoner))
        else:
            self.history.append(self.history[-1].move(self.player, i, j, ignore_ko))
            if self.solution is not None:
                for child in self.solution.children.values():
                    child.parent = self.solution
                if (i, j) in self.solution.children:
                    self.solution = self.solution.children[(i, j)]
                else:
                    self.solution = None
        self.undo_history = []

    def pass_turn(self):
        """Pass a turn without placing a stone."""
        self.history.append(self.history[-1].pass_turn())
        self.undo_history = []
        if self.solution is not None:
            for child in self.solution.children.values():
                child.parent = self.solution
            if None in self.solution.children:
                self.solution = self.solution.children[None]

    def undo(self):
        """Return to the previous board-state.

        Remember the previous solution if possible.
        """
        self.undo_history.append(self.history.pop())
        if self.solution is not None:
            self.solution = self.solution.parent

    def redo(self):
        """Return to the previously undone board-state.

        Forget the solution.
        """
        self.history.append(self.undo_history.pop())
        self.solution = None

    def test_superko(self) -> list[tuple]:
        """Try all moves to determine whether position repetition can occur.

        Return a list of the found moves.
        """
        board = self.history[-1]
        superko = []
        for i, j in product(range(board.grid.m), range(board.grid.n)):
            try:
                self.history.append(board.move(self.player, i, j, False))
            except PlacementError:
                continue
            if Board.test_repetition(self.history) is not None:
                superko.append((i, j))
            self.history.pop()
        return superko
        

class GameController:
    """Controller communicating between the model and the view."""
    
    def __init__(self, model, view):
        self.model: "GameModel" = model
        self.view: "GameView" = view

    def update_view(self):
        """Update the view according to the current board-state.

        Display the solution if it is known.
        If the number of prisoners were to exceed the maximum value,
        display the maximum value (the real number is retained in the model).
        """
        board = self.model.history[-1]
        self.view.goban.update(board)
        if not self.view.sandbox.get():
            self.view.goban.superko(self.model.test_superko())
        for player in [BLACK, WHITE]:
            prisoners = board.prisoners[player]
            if prisoners <= MAX_PRISONERS:
                view.prisoners[player].set(prisoners)
            else:
                view_prisoners[player].set(MAX_PRISONERS)
        if self.model.solution is not None:
            moves = [m for m in self.model.solution.children.keys() if m is not None]
            self.view.goban.solve(moves)

    def new_board(self, rows: int, columns: int):
        """Create a new, empty board of the given dimensions.

        If the players alternate, Black plays first.
        """
        self.model.new_board(rows, columns)
        if self.view.alternation.get() == ALTERNATE:
            self.model.player = BLACK
        
    def placement(self, i: int, j: int):
        """Attempt to place or delete a stone at the given position.

        If in Sandbox mode, ko and repetition testing is to be ignored.
        The latter is also ignored if it is not enabled.
        If the board state was repeated, end playing sequence. 
        If the players alternate, change player.
        """
        try:
            self.model.placement(i, j, self.view.sandbox.get(), self.view.take_prisoners.get())
        except PlacementError:
            return
        
        if not self.view.sandbox.get() and self.view.test_repetition.get():
            repetition = self.test_repetition()
            if repetition is not None:
                if repetition:
                    self.set_start()
                else:    # The move was cancelled
                    self.model.history.pop()
                    return
                
        if self.view.alternation.get() == ALTERNATE:
            self.model.player *= -1
        self.update_view()

    def control(self, action: str):
        """Attempt to modify the model according to the given action.

        Possible actions are prisoner reset, pass, undo and redo.
        If two passes in succession have been made (in the current playing sequence),
        end the playing sequence and display the result.
        Except prisoner reset, change player if they alternate.
        """
        if action == "Reset prisoners":
            self.model.reset_prisoners()
        else:
            match action:
                case "Pass" | "p":
                    self.model.pass_turn()
                    if not self.view.sandbox.get() and self.model.history[-1].passes == 2:
                        self.score()
                        self.set_start()
                case "Undo" | "BackSpace":
                    if len(self.model.history) > 1:
                        self.model.undo()
                    else:
                        return
                case "Redo" | "r":
                    if self.model.undo_history:
                        self.model.redo()
                    else:
                        return
            if self.view.alternation.get() == ALTERNATE:
                self.model.player *= -1
        self.update_view()

    def score(self):
        """Score the board and display the result."""
        board = self.model.history[-1]
        board.grade()
        board.scored = True
        self.update_view()

        score = board.score
        komi = float(self.view.score_menu.sp_komi.get())
        if komi.is_integer():
            komi = int(komi)
        difference = score[BLACK] - score[WHITE] - komi
        if difference > 0:
            text = f"Black wins by {difference} points"
        elif difference < 0:
            text = f"White wins by {-difference} points"
        else:
            text = "Tie"
        messagebox.showinfo("Game end", parent=self.view.root,
                            message=text,
                            detail = f"Black: {score[BLACK]}, White: {score[WHITE] + komi}")

    def solve(self):
        """Find the optimal moves in the current position and display them.

        If the situation is too complex, display an error message.
        """
        if self.model.solution is not None:    # Already computed
            return
        
        board = self.model.history[-1]
        solution = board.solve(self.model.player, self.model.history,
                               self.model.dict_graded,)
        if solution is None:
            messagebox.showerror("Error", parent=self.view.root, message="Too complex")
            return
        if None in solution.children:    # The best move is a pass
                messagebox.showinfo("Best move", parent=self.view.root, message="Pass")
        self.model.solution = solution
        self.update_view()

    def test_repetition(self) -> bool:
        """Test whether the stone placement has been repeated.

        Tests only up to the first un-undoable action (i. e. in the current playing sequence).
        If repetition occurs, show which player (if any) has won
        according to the long cycle rule and ask whether to continue.
        If the user cancels the action, return False, if not, return True. Else return None.
        """
        repetition = Board.test_repetition(self.model.history)
        if repetition is None:
            return None
        match isinf(repetition), repetition > 0:
            case True, True:
                text = "Black wins by prisoner difference"
            case True, False:
                text = "White wins by prisoner difference"
            case False, _:
                text = "No result by prisoner difference"
        return messagebox.askokcancel("Repetition", parent=self.view.root,
                                      message="Long cycle", detail=text)
    
    def set_player(self):
        """Set the player according to the current alternation choice.

        If the players start alternating, the previous option is retained
        as the player who plays first, unless in stone erasure mode;
        in such case, Black plays first.
        """
        alternation = self.view.alternation.get()
        if alternation == ALTERNATE:
            if self.model.player == EMPTY:
                self.model.player = BLACK
        else:
            self.model.player = alternation

    def set_start(self):
        """Reset history and start a new playing sequence from the current board."""
        board = self.model.history[-1]
        self.model.history, self.model.undo_history = [board], []
        self.model.solution = None
        board.ko = None
        board.passes = 0
        board.scored = False


class Goban(tk.Canvas):
    """Tkinter Canvas subclass for displaying the board state."""

    def __init__(self, master, size, rows, columns):
        tk.Canvas.__init__(self, master, bg="#edb96f", highlightthickness=0)

        self.size: int = size    # Distance between adjacent intersections (tile size)
        self.m: int = rows
        self.n: int = columns    # Board dimensions

        self.redraw()
           
    def redraw(self):
        """Redraw the underlying grid according to the current attributes."""
        self.delete(tk.ALL)
        self.configure(height = self.m*self.size + 10, width = self.n*self.size + 10)
        for i in range(self.m):
            self.create_line(self.size/2 + 5, self.size*(i+1/2) + 5,
                             self.size*(self.n-1/2) + 5, self.size*(i+1/2) + 5,
                             fill="black")
        for j in range(self.n):
            self.create_line(self.size*(j+1/2) + 5, self.size/2 + 5,
                             self.size*(j+1/2) + 5, self.size*(self.m-1/2) + 5,
                             fill="black")

        # Highlight certain intersections for easier orientation
        if self.m == 1:
            hoshi = [(0, j) for j in range(self.n)]
        elif self.n == 1:
            hoshi = [(i, 0) for i in range(self.m)]
        else:
            hoshi = list(product(Goban.hoshi(self.m), Goban.hoshi(self.n)))
            if (0 not in {self.m % 2, self.n % 2} and (self.m > 5 or self.n > 5)):
                hoshi.append((self.m//2, self.n//2))
        for i, j in hoshi:
            self.create_oval(self.size*(j+0.4) + 5, self.size*(i+0.4) + 5,
                             self.size*(j+0.6) + 5, self.size*(i+0.6) + 5,
                             outline="black", fill="black")
            
    def update(self, board: Board):
        """Update the board display according to a Board object."""
        self.delete("stone", "ko", "territory", "superko", "solution")
        for i, j in product(range(self.m), range(self.n)):
            c = board.grid[i][j].colour
            if c != EMPTY:
                colour = "black" if c == BLACK else "white"
                self.create_oval(self.size*j + 5 + 1, self.size*i + 5 + 1,
                                 self.size*(j+1) + 5 - 1, self.size*(i+1) + 5 - 1,
                                 outline="black", fill=colour, tag="stone")
        if board.ko is not None:
            i, j = board.ko
            self.create_rectangle(self.size*(j+0.3) + 5, self.size*(i+0.3) + 5,
                                  self.size*(j+0.7) + 5, self.size*(i+0.7) + 5,
                                  outline="black", tag="ko")
        if board.scored:
            for player, colour in [(BLACK, "black"), (WHITE, "white")]:
                for i, j in board.territory[player]:
                    self.create_rectangle(self.size*(j+0.3) + 5, self.size*(i+0.3) + 5,
                                          self.size*(j+0.7) + 5, self.size*(i+0.7) + 5,
                                          outline="black", fill=colour, tag="territory")

    def superko(self, moves):
        """Draw the superko points."""
        for i, j in moves:
            self.create_oval(self.size*(j+0.3) + 5, self.size*(i+0.3) + 5,
                             self.size*(j+0.7) + 5, self.size*(i+0.7) + 5,
                             outline="black", tag="superko")

    def solve(self, solution: list):
        """Display the suggestions for the best next plays."""
        self.delete("solution")
        for i, j in solution:
            self.create_oval(self.size*j + 5 + 1, self.size*i + 5 + 1,
                             self.size*(j+1) + 5 - 1, self.size*(i+1) + 5 - 1,
                             width = 2, outline="grey", dash=(4, 5), tag="solution")

    @staticmethod
    def hoshi(length: int) -> list[int]:
        """Find the lines for hoshi to be on. Length is the perpendicular dimension."""
        lines = []
        if length > 7:
            if length < 12:
                l = 2
            elif length < 25:
                l = 3
            else:
                l = 4
            lines = [l, length - l - 1]
        if length > 3 and length % 2 == 1 and length != 9:
            lines.append(length//2)
        return lines


class SizeMenu(tk.Frame):
    """Menu for adjusting the board parameters."""
    
    def __init__(self, master, view):
        tk.Frame.__init__(self, master)
        self.view: "GameView" = view

        self.square = tk.BooleanVar(self, True)    # Whether the board grid is a square
        
        tk.Label(self, text="Rows:").grid(row=0, column=0)
        self.l_columns = tk.Label(self, text="Columns:")
        self.l_columns.grid(row=1, column=0)

        # For entering the number of rows and columns
        self.rows, self.columns = tk.IntVar(self, 9), tk.IntVar(self, 9)
        vcmd = self.register(self.validate)
        self.sp_rows = tk.Spinbox(self, width=2,
                                  from_=1, to=MAX_LENGTH, textvariable=self.rows,
                                  validate="key", validatecommand=(vcmd, "%P"))
        self.sp_columns = tk.Spinbox(self, width=2,
                                     from_=1, to=MAX_LENGTH, textvariable=self.columns,
                                     validate="key", validatecommand=(vcmd, "%P"))
        for row, widget in enumerate([self.sp_rows, self.sp_columns]):
            widget.bind("<Return>", lambda e: self.new_board())
            widget.grid(row=row, column=1)

        tk.Checkbutton(self, text="Square", takefocus=False,
                       variable=self.square,
                       command=self.toggle_columns).grid(row=2)
        self.toggle_columns()

        tk.Label(self, text="Tile size:").grid(row=3)
        
        # For choosing the tile size
        self.sc_size = tk.Scale(self, orient=tk.HORIZONTAL,
                                from_=MIN_SIZE, to=MAX_SIZE, variable=tk.IntVar(self, 36))
        self.sc_size.grid(row=4)

        tk.Button(self, text="Resize", takefocus=False,
                  command=self.resize).grid(row=5)
        tk.Button(self, text="New Board", takefocus=False,
                  command=self.new_board).grid(row=6)
        
    def validate(self, entry: str) -> bool:
        """Validate the board dimensions entry."""
        return (entry == "" or
                (entry.isdigit() and not entry.startswith("0") and int(entry) <= MAX_LENGTH))
    
    def toggle_columns(self):
        """Set the columns option depending on whether the board is square.

        If square, the the board dimensions are always set equal and columns are disabled.
        """
        if self.square.get():
            self.l_columns.configure(state=tk.DISABLED)
            self.sp_columns.configure(state=tk.DISABLED,
                                      textvariable=self.rows)
        else:
            self.l_columns.configure(state=tk.NORMAL)
            self.sp_columns.configure(state=tk.NORMAL,
                                      textvariable=self.columns)
            self.columns.set(self.rows.get())

    def size_fits(self, size: int, rows: int, columns: int) -> bool:
        """Check whether the size of the displayed goban would be small enough.

        Display an error message if it is not the case.
        """
        if size*max(rows, columns) + 10 > MAX_GOBAN_SIZE:
            messagebox.showerror("Error", parent=self.view.root,
                                 message="Board too large")
            return False
        return True

    def resize(self):
        """Change the size of the displayed board if it fits."""
        size = self.sc_size.get()
        if self.size_fits(size, self.view.goban.m, self.view.goban.n):
            self.view.resize(size)
        
    def new_board(self):
        """Create a new, empty board with the chosen parameters, if its size fits.

        Ask for confirmation.
        Display an error message if some of the parameters are left unspecified.
        """
        if (rows := self.sp_rows.get()) and (columns := self.sp_columns.get()):
            size = self.sc_size.get()
            if (self.size_fits(size, int(rows), int(columns)) and
                messagebox.askokcancel("New board", parent=self.view.root,
                                       message="Create new board?")):
                self.view.new_board(size, int(rows), int(columns))
        else:
            messagebox.showerror("Error", parent=self.view.root,
                                 message="Grid parameters not specified")


class ModeMenu(tk.Frame):
    """Menu for adjusting the playing mode.

    The modes are:
    Play -- the players alternate as during a game,
    Sandbox -- free stone placement.
    """

    def __init__(self, master, view):
        tk.Frame.__init__(self, master)
        self.view: "GameView" = view

        for mode, value in [("Play", False), ("Sandbox", True)]:
            tk.Radiobutton(self, text=mode, takefocus=False,
                           variable=self.view.sandbox, value=value,
                           command=self.toggle_mode).pack(anchor=tk.W)

        fr_sandbox = tk.Frame(self)
        self.fr_alternation = tk.Frame(fr_sandbox)
        for text, value in [
                            ("Alternate", ALTERNATE),
                            ("Black only", BLACK),
                            ("White only", WHITE),
                            ("Erase", EMPTY),
                            ]:
            tk.Radiobutton(self.fr_alternation, text=text, takefocus=False, state=tk.DISABLED,
                           variable=self.view.alternation, value=value,
                           command=self.toggle_alternation).pack(anchor=tk.W)
        self.cbtn_prisoners = tk.Checkbutton(self.fr_alternation, text="Take prisoners",
                                             state=tk.DISABLED, takefocus=False,
                                             variable=self.view.take_prisoners)
        self.cbtn_prisoners.pack()
        tk.Frame(fr_sandbox, width=20).pack(side=tk.LEFT)
        self.fr_alternation.pack(side=tk.LEFT)
        fr_sandbox.pack(anchor=tk.W)

        self.cbtn_repetition = tk.Checkbutton(self, text="Test repetition", takefocus=False,
                                              variable=self.view.test_repetition)
        self.cbtn_repetition.pack(anchor=tk.W)

    def toggle_mode(self):
        """Set the current playing mode."""
        self.view.set_mode()

        play_widgets = [self.cbtn_repetition,
                        self.view.score_menu.btn_score, self.view.score_menu.btn_solve]
        if self.view.sandbox.get():
            for widget in self.fr_alternation.winfo_children():
                if widget != self.cbtn_prisoners:
                    widget.configure(state=tk.NORMAL)
            for widget in play_widgets:
                widget.configure(state=tk.DISABLED)
        else:
            for widget in self.fr_alternation.winfo_children():
                widget.configure(state=tk.DISABLED)
            for widget in play_widgets:
                widget.configure(state=tk.NORMAL)

    def toggle_alternation(self):
        """Set the current alternation option."""
        self.view.controller.set_player()
        
        if self.view.alternation.get() == EMPTY:
            self.cbtn_prisoners.configure(state=tk.NORMAL)
        else:
            self.cbtn_prisoners.configure(state=tk.DISABLED)
        

class ScoreMenu(tk.Frame):
    """Menu for adjusting komi and evaluating the board position."""

    def __init__(self, master, view):
        tk.Frame.__init__(self, master)
        self.view: "GameView" = view

        # For setting the komi
        tk.Label(self, text="Komi:").grid(row=0, column=0)
        self.sp_komi = tk.Spinbox(self, width=4,
                                  from_=-MAX_KOMI, to=MAX_KOMI, increment=0.5,
                                  textvariable=tk.DoubleVar(self, 6.5),
                                  validate="key",
                                  validatecommand=(self.register(self.validate), "%P"))
        self.sp_komi.grid(row=0, column=1)

        self.btn_score = tk.Button(self, text="Score", takefocus=False,
                                   command=self.view.score)
        self.btn_score.grid(row=2)
        self.btn_solve = tk.Button(self, text="Best move", takefocus=False,
                                   command=self.view.solve)
        self.btn_solve.grid(row=3)

    def validate(self, entry: str) -> bool:
        """Validate the komi entry, as a half-integer."""
        value = entry.removeprefix("-")
        return (entry == "" or
                ((value.removesuffix(".5").isdigit() or value.removesuffix(".0").isdigit()) and
                 (not value.startswith("0") or value.startswith("0.") or value == "0") and
                 float(value) <= MAX_KOMI))
    

class GameView:
    """Game graphics, passes user inputs to the controller."""
    
    def __init__(self, root, controller=None):
        self.root = root    # Root window
        self.controller: "GameController" = controller

        # The displayed numbers of prisoners
        self.prisoners = {BLACK: tk.IntVar(root, 0), WHITE: tk.IntVar(root, 0)}
        
        self.sandbox = tk.BooleanVar(root, False)    # The playing mode
        self.alternation = tk.IntVar(root, ALTERNATE)    # The alternation option
        self.take_prisoners = tk.BooleanVar(root, False)    # Whether to take prisoners
                                                            # when deleting stones
        self.test_repetition = tk.BooleanVar(root, True)    # Whether to test board repetition
        
        self.configure()
        self.create_widgets()
        
    def configure(self):
        """Configure the root window."""
        self.root.title("GoApp")
        self.root.resizable(False, False)
        
    def create_widgets(self):
        """Create the root window graphics."""
        # Main frame with prisoner display, goban and button controls
        fr_main = tk.Frame(self.root)

        self.goban = Goban(fr_main, 0, 0, 0)    # Board display
        self.goban.bind("<Button-1>", self.placement)
        self.goban.bind("<B1-Motion>", self.placement)

        fr_prisoners = tk.Frame(fr_main)
        tk.Label(fr_prisoners, text="Prisoners:").pack(side=tk.LEFT)
        for player, colour in [(BLACK, "black"), (WHITE, "white")]:
            stone = tk.Canvas(fr_prisoners, width=30, height=30)
            stone.create_oval(5, 5, 25, 25, fill=colour)
            stone.pack(side=tk.LEFT)
            tk.Label(fr_prisoners, width=3, textvariable=self.prisoners[player]).pack(side=tk.LEFT)  
        btn = tk.Button(fr_prisoners, text="Reset prisoners", takefocus=False)
        btn.bind("<ButtonRelease-1>", self.control)
        btn.pack(side=tk.LEFT)

        fr_controls = tk.Frame(fr_main)
        # The controls may be called either by button or key presses
        for action, key in [
                            ("Pass", "<p>"),
                            ("Undo", "<BackSpace>"),
                            ("Redo", "<r>"),
                            ]:
            btn = tk.Button(fr_controls, text=action, takefocus=False)
            btn.bind("<ButtonRelease-1>", self.control)
            btn.pack(side=tk.LEFT)
            self.goban.bind(key, self.control)

        fr_prisoners.pack()
        self.goban.pack()
        fr_controls.pack()
        fr_main.pack(side=tk.LEFT)
        self.goban.focus_set()

        # Side menu for board and alternation adjustment and game evaluation
        fr_menu = tk.Frame(self.root)
        self.size_menu = SizeMenu(fr_menu, self)
        self.size_menu.pack(anchor=tk.N)
        self.mode_menu = ModeMenu(fr_menu, self)
        self.mode_menu.pack(anchor=tk.N)
        self.score_menu = ScoreMenu(fr_menu, self)
        self.score_menu.pack(anchor=tk.S)
        fr_menu.pack(side=tk.RIGHT)

        self.root.bind("<Button-1>", self.defocus)

    def defocus(self, event):
        """Upon a click outside of an entry field, set keyboard focus to the goban."""
        if event.widget not in {self.size_menu.sp_rows, self.size_menu.sp_columns,
                                self.score_menu.sp_komi}:
            if not self.score_menu.sp_komi.get():
                self.score_menu.sp_komi.insert(0, "0")
            self.goban.focus_set()

    def new_board(self, size: int, rows: int, columns: int):
        """Create a new, empty board of the given dimensions and display it."""
        self.controller.new_board(rows, columns)
        self.goban.size = size
        self.goban.m, self.goban.n = rows, columns
        self.goban.redraw()
        self.controller.update_view()

    def resize(self, size: int):
        """Change the size of the displayed board."""
        self.goban.size = size
        self.goban.redraw()
        self.controller.update_view()

    def placement(self, event):
        """Attempt to place (or delete) a stone where the user clicked on the goban."""
        i, j = (event.y - 5)//self.goban.size, (event.x - 5)//self.goban.size
        if i >= 0 and i < self.goban.m and j >= 0 and j < self.goban.n:
            self.controller.placement(i, j)

    def control(self, event):
        """Handle button and key presses controlling the board-state."""
        if event.type == "5":    # Button click (and release)
            action = event.widget.cget("text")
        elif event.type == "2":    # Key press
            action = event.keysym
        self.controller.control(action)

    def set_mode(self):
        """Start a new playing sequence.

        If the mode was set to Play, fix the alternation option to ALTERNATE.
        """
        self.controller.set_start()
        if not self.sandbox.get():
            self.alternation.set(ALTERNATE)
            self.controller.set_player()

    def score(self):
        """Score the current position."""
        self.controller.score()

    def solve(self):
        """Attempt to find the optimal moves."""
        self.controller.solve()


if __name__ == "__main__":
    root = tk.Tk()
    model, view = GameModel(), GameView(root)
    controller = GameController(model, view)
    view.controller = controller
    view.new_board(36, 9, 9)
    root.mainloop()
