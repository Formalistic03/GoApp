import tkinter as tk
from tkinter import messagebox

# Constants for point occupation and alternation options
EMPTY: int = 0    # Empty intersection, also deleting stones
BLACK: int = 1    # Black stone, also only Black plays
WHITE: int = -BLACK    # White stone, also only White plays
ALTERNATE: int = 2    # The players alternate placing stones

MAX_UNDECIDED = 7    # Maximum number of undecided points when solving

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

    def _string_recursion(self, region: int) -> "String":
        """Find the point's string (region) recursively and determine its liberties."""
        string = String(self)
        self.active = False
        for neighbour in self.adjacent:
            if neighbour.active:
                if neighbour.colour == EMPTY:
                    string.liberties.add(neighbour)
                if (region == EMPTY and neighbour.colour == self.colour or
                    region != EMPTY and neighbour.colour in {EMPTY, -region}):
                    neighbour_string = neighbour._string_recursion(region)
                    string.points |= neighbour_string.points
                    string.liberties |= neighbour_string.liberties
        return string
    
    def find_string(self, region: int = EMPTY) -> "String":
        """Find the point's string (region).

        If the region option is EMPTY, find the string of intersections with the same colour.
        If it is BLACK or WHITE, find the region enclosed by the player containing itself.
        """
        string = self._string_recursion(region)
        if region != EMPTY and self.colour == EMPTY:
            # The origin was not added as a liberty
            string.liberties.add(self)
        for point in string:
            point.active = True
        return string

    def eye_recursion(self, player: int) -> "String":
        """Find the player-enclosed region and check whether it is territory.

        If it is, its alive attribute is set to True, else it is False or None.
        The region's points become inactive.
        """
        region = String(self)
        self.active = False
        region.alive = None
        for neighbour in self.adjacent:
            if neighbour.active:
                if (region.alive is None and
                    neighbour.colour == player and neighbour.string.alive):
                    region.alive = True
                if (neighbour.colour == -player and neighbour.string.alive or
                    neighbour.colour == player and not neighbour.string.alive):
                    region.alive = False
                if (neighbour.colour == EMPTY or
                    neighbour.colour == -player and not neighbour.string.alive):
                    neighbour_region = neighbour.eye_recursion(player)
                    region.points |= neighbour_region.points
                    if region.alive is None:
                        region.alive = neighbour_region.alive
                    elif neighbour_region.alive is not None:
                        region.alive &= neighbour_region.alive
        return region

class String:
    """Set of points connected by adjacency.

    Used in two ways:
    -- as a maximal set of same-coloured stones;
    -- as a maximal region without stones of one colour.
    """
    
    def __init__(self, point):
        self.points: set["Point"] = {point}    # The string's points
        self.liberties: set["Point"] = set()    # The string's liberties
                                                # or region's empty points
        self.vitals: set["String"] = set()    # The string's eyes (as regions)
                                              # or region's neighbouring alive strings
        self.alive: bool = False    # The string's life status

    def __iter__(self):
        """Iterate over the string's points."""
        yield from self.points

    def __len__(self) -> int:
        """Return the number of the string's points."""
        return len(self.points)

class Grid(list):
    """The stone layout as a matrix of points."""

    def __init__(self, rows, columns):
        self.m: int = rows
        self.n: int = columns    # The grid's dimensions
        
        list.__init__(self, [[Point(r, c) for c in range(columns)] for r in range(rows)])
        for i in range(rows):
            for j in range(columns):
                for a, b in [(i-1, j), (i, j-1), (i+1, j), (i, j+1)]:
                    if a not in {-1, rows} and b not in {-1, columns}:
                        self[i][j].adjacent.append(self[a][b])

    def __iter__(self):
        """Iterate over the grid's points."""
        for row in list.__iter__(self):
            yield from row

    def __eq__(self, other) -> bool:
        """Test the equality of stone layouts."""
        return ([point.colour for point in self] == [point.colour for point in other])

    def copy(self) -> "Grid":
        """Create a copy of the grid."""
        copy = Grid(self.m, self.n)
        for i in range(self.m):
            for j in range(self.n):
                copy[i][j].colour = self[i][j].colour
        return copy
                        
    def uncapturable(self, player: int):
        """For the player's unconditionally alive strings, set their status to alive.

        Benson's algorithm is implemented.
        Retain information about stone strings.
        """
        strings = set()
        for point in self:
            if point.string is None:
                if point.colour == player:
                    string = point.find_string()
                    strings.add(string)
                    for p in string:
                        p.string = string
                elif point.colour == EMPTY:
                    region = point.find_string(player)
                    for p in region:
                        if p.colour == EMPTY:
                            # Already determined strings of the other player are preserved;
                            # only the region's empty points need to be considered
                            p.string = region
        for string in strings:
            for liberty in string.liberties:
                if liberty.active:
                    region = liberty.string
                    for l in region.liberties:
                        l.active = False
                    if region.liberties <= string.liberties:
                        string.vitals.add(region)
                        region.vitals.add(string)
            for liberty in string.liberties:
                if not liberty.active:
                    for l in liberty.string.liberties:
                        l.active = True
                
        end = False
        while not end:
            end = True
            new_strings = strings.copy()
            for string in strings:
                if len(string.vitals) < 2:
                    # Not uncapturable
                    end = False
                    new_strings.remove(string)
                    for region in string.vitals:
                        region.vitals.remove(string)
                        for vital in region.vitals:
                            vital.vitals.remove(region)
            strings = new_strings
            
        for point in self:
            if point.colour == EMPTY:
                point.string = None

        for string in strings:
            string.alive = True
      

class Board:
    """Board state during the game.

    Contains information about the stone layout (Grid object),
    prisoner counts and game-specific states (ko, pass).
    """
    dictionary = {}    # Dictionary of board states for which the score was computed
    
    def __init__(self, grid, ko=None, prisoners=[0, 0], passes=0):
        self.grid: "Grid" = grid    # The stone layout on the board
        self.ko: tuple[int] = ko    # Coordinates of the ko intersection (if it exists)
        self.prisoners: list[int] = prisoners    # Black's and White's prisoners, respectively
        self.passes: int = passes    # The number of successive prior passes
        
        self.territory: list[set] = [set(), set()]    # Black's and White's territory points
        self.undecided: set = set()    # The points left to fight over
        self.score: int = None    # The game result upon perfect play (Black - White)
        self.solution: list = []    # The optimal moves for this position
        self.children: dict = {}    # Board states reachable by moves from this one

    def tuple(self, player: int) -> tuple:
        """Return an immutable object capturing the board-state and current player."""
        # The prisoner counts are not relevant for perfect play
        grid = tuple(point.colour for point in self.grid)
        return (grid, self.ko, self.passes, player)

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
                    if player == BLACK:
                        prisoners[0] += len(neighbour_string)
                    else:
                        prisoners[1] += len(neighbour_string)
                        
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
        colour = point.colour
        point.colour = EMPTY
        if take_prisoner:
            if colour == BLACK:
                prisoners[1] += 1
            else:
                prisoners[0] += 1

        return Board(grid, None, prisoners)

    def pass_turn(self):
        """Return a copy of itself after passing a turn."""
        return Board(self.grid, prisoners=self.prisoners, passes=min(self.passes + 1, 2))

    def _find_life(self, player: int):
        """For the player's uncapturable strings on the board, set their status to alive.

        Aside from unconditional life, also check life by miai
        (two different moves lead to unconditional life).
        Retain information about stone strings.
        """
        self.grid.uncapturable(player)
        for point in self.grid:
            if point.active and point.colour == player:
                string = point.string
                for p in string:
                    p.active = False
                if not string.alive:
                    candidate = False
                    for p in self.grid:
                        if p.colour == EMPTY:
                            try:
                                new_board = self.move(player, p.i, p.j, True)
                            except PlacementError:
                                continue
                            new_board.grid.uncapturable(player)
                            if new_board.grid[point.i][point.j].string.alive:
                                if candidate:
                                    string.alive = True
                                    break
                                else:
                                    candidate = True
        for point in self.grid:
            point.active = True

    def grade(self) -> int:
        """Determine the territories and undecided points, return the score of both players.

        The scoring assumes that strings are dead unless obviously alive,
        seki is not considered.
        Destroy string information.
        """
        territory = [set(), set()]
        placed_prisoners = [0, 0]
        self._find_life(BLACK)
        self._find_life(WHITE)
        for i, player in [(0, BLACK), (1, WHITE)]:
            for point in self.grid:
                if point.active and point.colour == EMPTY:
                    region = point.eye_recursion(player)
                    if region.alive:
                        territory[i] |= {(p.i, p.j) for p in region}
                        placed_prisoners[i] += len({p for p in region if p.colour != EMPTY})
            for point in self.grid:
                point.active = True

        for point in self.grid:
            point.string = None

        self.territory = territory
        self.undecided = {(p.i, p.j) for p in self.grid if p.colour == EMPTY
                          and (p.i, p.j) not in territory[0] | territory[1]}
        score = [len(territory[i]) + placed_prisoners[i] + self.prisoners[i]
                 for i in range(2)]
        
        return score

    def build_tree(self, player: int):
        """Create the tree of possible continuations."""
        if self.passes == 2:
            return
        can_move = False
        for i, j in self.undecided:
            try:
                new_board = self.move(player, i, j, False)
                can_move = True
            except PlacementError:
                continue
            if new_board.tuple(-player) in Board.dictionary:
                new_board = Board.dictionary[new_board.tuple(-player)]
            else:
                Board.dictionary[new_board.tuple(-player)] = new_board
                new_board.grade()
                new_board.territory = [set(), set()]
                new_board.build_tree(-player)
            self.children[(i, j)] = new_board
        if not can_move:
            new_board = self.pass_turn()
            if self.passes == 0:
                if new_board.tuple(-player) in Board.dictionary:
                    new_board = Board.dictionary[new_board.tuple(-player)]
                else:
                    Board.dictionary[new_board.tuple(-player)] = new_board
                    new_board.grade()
                    new_board.territory = [set(), set()]
                    new_board.build_tree(-player)
            self.children[None] = new_board

    def minmax(self, player: int, history: list["Board"], komi: float) -> list:
        """Recursively find the optimal moves from the given positions."""
        if not self.children:
            score = self.grade()
            self.score = score[0] - score[1] - komi
            history.pop()
            return
        repetition = test_repetition(history)
        if repetition is not None:
            self.score = repetition
            history.pop()
            return
        for child in self.children.values():
            history.append(child)
            child.minmax(-player, history, komi)
        history.pop()
        
        if player == BLACK:
            best_result = max(child.score for child in self.children.values())
        else:
            best_result = min(child.score for child in self.children.values())
        self.score = best_result
        self.solution = [move for move in self.children
                         if self.children[move].score == best_result]


def test_repetition(history: list["Board"]) -> int:
    """Test whether the stone placement has been repeated.

    Search only for long cycles (at least 3 moves).
    If repetition occurs, compute which player has gained more prisoners
    since the last occurence of the position and return
    infinity if Black, minus infinity if White and 0 if neither. ELse return None.
    """
    current_board = history[-1]
    if len(history) > 3:
        for board in reversed(history[:-3]):
            if board.grid == current_board.grid:     
                difference = [i-j for i, j in zip(current_board.prisoners, board.prisoners)]
                if difference[0] > difference[1]:
                    return float("inf")
                elif difference[0] < difference[1]:
                    return float("-inf")
                else:
                    return 0
    return None


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

    def update(self, board: Board):
        """Update the board display according to a Board object."""
        self.delete("stone", "ko", "territory", "solution")
        for i in range(self.m):
            for j in range(self.n):
                c = board.grid[i][j].colour
                if c != EMPTY:
                    if c == BLACK:
                        colour = "black"
                    elif c == WHITE:
                        colour = "white"
                    self.create_oval(self.size*j + 5 + 1, self.size*i + 5 + 1,
                                     self.size*(j+1) + 5 - 1, self.size*(i+1) + 5 - 1,
                                     outline="black", fill=colour, tag="stone")
        if board.ko is not None:
            i, j = board.ko
            self.create_rectangle(self.size*(j+0.3) + 5, self.size*(i+0.3) + 5,
                                  self.size*(j+0.7) + 5, self.size*(i+0.7) + 5,
                                  outline="black", tag="ko")
        for k, player, colour in [(0, BLACK, "black"), (1, WHITE, "white")]:
            for i, j in board.territory[k]:
                self.create_rectangle(self.size*(j+0.3) + 5, self.size*(i+0.3) + 5,
                                      self.size*(j+0.7) + 5, self.size*(i+0.7) + 5,
                                      outline="black", fill=colour, tag="territory")

    def solve(self, solution: list):
        """Display the suggestions for the best next plays."""
        self.delete("solution")
        for i, j in solution:
            self.create_oval(self.size*j + 5 + 1, self.size*i + 5 + 1,
                             self.size*(j+1) + 5 - 1, self.size*(i+1) + 5 - 1,
                             width = 2, outline="grey", dash=(4, 5),
                             tag="solution")

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
                (entry.isdigit() and int(entry) > 0 and int(entry) <= MAX_LENGTH))
    
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
        else:
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
            if self.size_fits(size, int(rows), int(columns)):
                if messagebox.askokcancel("New board", parent=self.view.root,
                                          message="Create new board?"):
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
        
        btn_score = self.view.score_menu.btn_score
        btn_solve = self.view.score_menu.btn_solve
        if self.view.sandbox.get():
            for widget in self.fr_alternation.winfo_children():
                widget.configure(state=tk.NORMAL)
            self.cbtn_prisoners.configure(state=tk.DISABLED)
            self.cbtn_repetition.configure(state=tk.DISABLED)
            btn_score.configure(state=tk.DISABLED)
            btn_solve.configure(state=tk.DISABLED)
        else:
            for widget in self.fr_alternation.winfo_children():
                widget.configure(state=tk.DISABLED)
            self.cbtn_repetition.configure(state=tk. NORMAL)
            btn_score.configure(state=tk.NORMAL)
            btn_solve.configure(state=tk.NORMAL)

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
        """Validate the komi entry."""
        return (entry == "" or
                (entry.removeprefix("-").removesuffix(".5").removesuffix(".0").isdigit() and
                 float(entry) >= -MAX_KOMI and float(entry) <= MAX_KOMI))
    

class GameModel:
    """Internal model of the game."""
    
    def __init__(self):
        self.history: list[Board] = []    # Past board-states
        self.undo_history: list[Board] = []    # Undone board-states
        self.player: int = EMPTY    # Current player
        
    def new_board(self, rows: int, columns: int):
        """Create a new, empty board of the given dimensions.

        Forget the solved positions.
        Cannot be undone.
        """
        Board.dictionary = {}
        self.history = [Board(Grid(rows, columns))]
        self.undo_history = []

    def reset_prisoners(self):
        """Reset the number of prisoners of both players.

        Cannot be undone.
        """
        board = self.history[-1]
        self.history = [Board(board.grid, ko=board.ko)]
        self.undo_history = []

    def placement(self, i: int, j: int, ignore_ko: bool, take_prisoner: bool):
        """Attempt to place or delete a stone at the given position."""
        if self.player == EMPTY:
            self.history.append(self.history[-1].erase(i, j, take_prisoner))
        else:
            self.history.append(self.history[-1].move(self.player, i, j, ignore_ko))
        self.undo_history = []

    def pass_turn(self):
        """Pass a turn without placing a stone."""
        self.history.append(self.history[-1].pass_turn())
        self.undo_history = []

    def undo(self):
        """Return to the previous board-state."""
        self.undo_history.append(self.history.pop())

    def redo(self):
        """Return to the previously undone board-state."""
        self.history.append(self.undo_history.pop())
        

class GameController:
    """Controller communicating between the model and the view."""
    
    def __init__(self, model, view):
        self.model: "GameModel" = model
        self.view: "GameView" = view

    def update_view(self):
        """Update the view according to the current board-state.

        If the number of prisoners were to exceed the maximum value,
        display the maximum value (the real number is retained in the model).
        """
        board = self.model.history[-1]
        self.view.goban.update(board)
        for prisoners, view_prisoners in zip(board.prisoners, self.view.prisoners):
            if prisoners <= MAX_PRISONERS:
                view_prisoners.set(prisoners)
            else:
                view_prisoners.set(MAX_PRISONERS)
    
    def test_repetition(self) -> bool:
        """Test whether the stone placement has been repeated.

        Tests only up to the first un-undoable action (i. e. in the current playing sequence).
        If repetition occurs, show which player (if any) has won
        according to the long cycle rule and ask whether to continue.
        If the user cancels the action, return False, if not, return True. Else return None.
        """
        repetition = test_repetition(self.model.history)
        if repetition is None:
            return None
        else:
            if repetition > 0:
                text = "Black wins by prisoner difference"
            elif repetition < 0:
                text = "White wins by prisoner difference"
            else:
                text = "No result by prisoner difference"
            return messagebox.askokcancel("Repetition", parent=self.view.root,
                                              message="Long cycle", detail=text)

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
            if action in {"Pass", "p"}:
                self.model.pass_turn()
                if not self.view.sandbox.get() and self.model.history[-1].passes == 2:
                    self.score()
                    self.set_start()
            elif action in {"Undo", "BackSpace"}:
                if len(self.model.history) > 1:
                    self.model.undo()
                else:
                    return
            elif action in {"Redo", "r"}:
                if self.model.undo_history:
                    self.model.redo()
                else:
                    return
                    
            if self.view.alternation.get() == ALTERNATE:
                self.model.player *= -1
        self.update_view()

    def score(self):
        """Score the board and display the result."""
        score = self.model.history[-1].grade()
        self.update_view()
        komi = float(self.view.score_menu.sp_komi.get())
        if komi.is_integer():
            komi = int(komi)
        score[1] += komi
        difference = score[0] - score[1]
        if difference > 0:
            text = f"Black wins by {difference} points"
        elif difference < 0:
            text = f"White wins by {-difference} points"
        else:
            text = "Tie"
        messagebox.showinfo("Game end", parent=self.view.root,
                            message=text,
                            detail = f"Black: {score[0]}, White: {score[1]}")

    def solve(self):
        """Attempt to find the optimal moves in the current position.

        If there are too many undecided points, display an error message.
        """
        board = self.model.history[-1]
        if board.tuple(self.model.player) in Board.dictionary:
            board = Board.dictionary[board.tuple(self.model.player)]
        else:
            board.grade()
            board.territory = [set(), set()]
            if len(board.undecided) > MAX_UNDECIDED:
                messagebox.showerror("Error", parent=self.view.root, message="Too complex")
                return
            Board.dictionary[board.tuple(self.model.player)] = board
            board.build_tree(self.model.player)
            komi = float(self.view.score_menu.sp_komi.get())
            board.minmax(self.model.player, self.model.history, komi)
            self.model.history.append(board)
        if None in board.solution:    # The best move is a pass
            messagebox.showinfo("Best move", parent=self.view.root, message="Pass")
        else:
            self.view.goban.solve(board.solution)
    
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
        self.model.history, self.model.undo_history = [self.model.history[-1]], []
        self.model.history[-1].passes = 0


class GameView:
    """Game graphics, passes user inputs to the controller."""
    
    def __init__(self, root, controller=None):
        self.root = root    # Root window
        self.controller: "GameController" = controller

        # The displayed numbers of prisoners
        self.prisoners = [tk.IntVar(root, 0), tk.IntVar(root, 0)]
        
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
        for colour, var in zip(["black", "white"], self.prisoners):
            stone = tk.Canvas(fr_prisoners, width=30, height=30)
            stone.create_oval(5, 5, 25, 25, outline="black", fill=colour)
            stone.pack(side=tk.LEFT)
            tk.Label(fr_prisoners, width=3, textvariable=var).pack(side=tk.LEFT)  
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
