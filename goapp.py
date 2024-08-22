import tkinter as tk
from tkinter import messagebox
from copy import deepcopy


# Constants for point occupation and alternation options
EMPTY: int = 0    # Empty intersection, also deleting stones
BLACK: int = 1    # Black stone, also only Black plays
WHITE: int = -BLACK    # White stone, also only White plays
ALTERNATE: int = 2    # The players alternate placing stones

# Constants for graphic realisation
MAX_LENGTH = 25    # Maximum dimension of the board
MIN_SIZE = 16    # Minimum tile size
MAX_SIZE = 99    # Maximum tile size
MAX_GOBAN_SIZE = 700    # Maximum size of the displayed goban
MAX_PRISONERS = 999    # Maximum displayed number of prisoners


class GoError(Exception):
    """Exception class for handling Go-related errors."""

    
class PlacementError(GoError):
    """GoError subclass for rule-violating stone placement (or erasure)."""

    
class ActionError(GoError):
    """GoError subclass for impossible board-state modification."""


class Point:
    """Grid intersection."""
    
    def __init__(self):
        self.colour: int = EMPTY    # Which stone (if any) occupies the point
        self.adjacent: list = []    # Coordinates of adjacent points


class String:
    """Maximal set of same-coloured stones connected by adjacency."""
    
    def __init__(self, point):
        self.points: set = {point}    # The string's points (coordinates)
        self.liberties: bool = False    # Whether the string posseses any liberties


def create_grid(rows: int, columns: int) -> list[list[Point]]:
    """Create an empty rectangular grid of points of the given dimensions."""
    empty_grid = [[Point() for _ in range(columns)] for __ in range(rows)]
    for i in range(rows):
        for j in range(columns):
            for a, b in [(i-1, j), (i, j-1), (i+1, j), (i, j+1)]:
                if a not in {-1, rows} and b not in {-1, columns}:
                    empty_grid[i][j].adjacent.append((a, b))
    return empty_grid


def find_string(grid: list[list[Point]], i: int, j: int) -> String:
    """Determine the string of the point (given by coordinates) on the given grid."""
    string = String((i, j))
    point = grid[i][j]
    colour = point.colour

    # The string is found recursively
    # After connecting a new point, it is temporarily removed from the grid
    point.colour = None
    for a, b in point.adjacent:
        neighbour = grid[a][b]
        if neighbour.colour == EMPTY:
            string.liberties = True
        elif neighbour.colour == colour and (a, b) not in string.points:
            neighbour_string = find_string(grid, a, b)
            string.points |= neighbour_string.points
            string.liberties |= neighbour_string.liberties
    point.colour = colour
        
    return string


class Board:
    """Board state during the game.

    Contains information about the stone layout,
    prisoner counts and game-specific states (ko, pass).
    """
    
    def __init__(self, grid, ko=None, prisoners=[0, 0], passed=False):
        self.grid: list[list[Point]] = grid    # The stone layout on the board
        self.ko: tuple[int] = ko    # Coordinates of ko intersection (if it exists)
        self.prisoners: list[int] = prisoners    # Black's and White's prisoners, respectively
        self.passed: bool = passed    # Whether the last move was a pass

    def __eq__(self, other) -> bool:
        """Test whether the two boards have the same stone layout."""
        return ([[point.colour for point in row] for row in self.grid]
                == [[point.colour for point in row] for row in other.grid])

    def move(self, player: int, i: int, j: int, ignore_ko: bool) -> "Board":
        """Attempt to place a new stone on the board.

        Raise PlacementError if it were illegal,
        else return a new Board object with the new stone.
        """
        if self.grid[i][j].colour != EMPTY:
            raise PlacementError
        if not ignore_ko and (i, j) == self.ko:
            raise PlacementError

        new_grid = deepcopy(self.grid)
        ko = None
        prisoners = self.prisoners.copy()
        
        point = new_grid[i][j]
        point.colour = player
        # Test capture
        for a, b in point.adjacent:
            if new_grid[a][b].colour == -player:
                neighbour_string = find_string(new_grid, a, b)
                if not neighbour_string.liberties:
                    if player == BLACK:
                        prisoners[0] += len(neighbour_string.points)
                    else:
                        prisoners[1] += len(neighbour_string.points)
                        
                    if len(neighbour_string.points) == 1:
                        ko = (a, b)    # Ko candidate if only one stone was captured
                    for k, l in neighbour_string.points:
                        new_grid[k][l].colour = EMPTY

        string = find_string(new_grid, i, j)
        if not string.liberties:
            raise PlacementError

        # In order for ko to arise, the new string has to have one stone and one liberty
        if not (ko is not None and len(string.points) == 1 and
                len([0 for a, b in point.adjacent if new_grid[a][b].colour == EMPTY]) == 1):
            ko = None
            
        return Board(new_grid, ko, prisoners)

    def erase(self, i: int, j: int) -> "Board":
        """Attempt to delete a stone from the board.

        Raise PlacementError if it were impossible,
        else return a new Board object with the new stone.
        """
        if self.grid[i][j].colour == EMPTY:
            raise PlacementError

        new_grid = deepcopy(self.grid)
        new_grid[i][j].colour = EMPTY

        return Board(new_grid, None, self.prisoners.copy())


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
                             fill = "black")
        for j in range(self.n):
            self.create_line(self.size*(j+1/2) + 5, self.size/2 + 5,
                             self.size*(j+1/2) + 5, self.size*(self.m-1/2) + 5,
                             fill = "black")

    def update(self, board: Board):
        """Update the board display according to a Board object."""
        self.delete("stone")
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
                                     outline = "black", fill = colour, tag = "stone")
        self.delete("ko")
        if board.ko is not None:
            i, j = board.ko
            self.create_rectangle(self.size*(j+0.3) + 5, self.size*(i+0.3) + 5,
                                  self.size*(j+0.7) + 5, self.size*(i+0.7) + 5,
                                  outline = "black", tag = "ko")

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
                (str.isdigit(entry) and int(entry) > 0 and int(entry) <= MAX_LENGTH))
    
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
        if messagebox.askokcancel("New board", parent=self.view.root,
                                  message="Create new board?"):
            if (rows := self.sp_rows.get()) and (columns := self.sp_columns.get()):
                size = self.sc_size.get()
                if self.size_fits(size, int(rows), int(columns)):
                    self.view.new_board(size, int(rows), int(columns))
            else:
                messagebox.showerror("Error", parent=self.view.root,
                                     message="Grid parameters not specified")


class ModeMenu(tk.Frame):
    """Menu for adjusting playing mode.

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

        self.fr_sandbox = tk.Frame(self)
        for text, value in [
                            ("Alternate", ALTERNATE),
                            ("Black only", BLACK),
                            ("White only", WHITE),
                            ("Erase", EMPTY),
                            ]:
            tk.Radiobutton(self.fr_sandbox, text=text, takefocus=False, state=tk.DISABLED,
                           variable=self.view.alternation, value=value,
                           command=self.view.set_player).pack(anchor=tk.W)
        self.fr_sandbox.pack()

        self.cbtn_repetition = tk.Checkbutton(self, text="Test repetition", takefocus=False,
                                              variable=self.view.test_repetition)
        self.cbtn_repetition.pack()

    def toggle_mode(self):
        """Set the current playing mode."""
        self.view.set_mode()
        if self.view.sandbox.get():
            for widget in self.fr_sandbox.winfo_children():
                widget.configure(state=tk.NORMAL)
            self.cbtn_repetition.configure(state=tk.DISABLED)
        else:
            for widget in self.fr_sandbox.winfo_children():
                widget.configure(state=tk.DISABLED)
            self.cbtn_repetition.configure(state=tk. NORMAL)


class GameModel:
    """Internal model of the game."""
    
    def __init__(self):
        self.history: list[Board] = []    # Past board-states
        self.undo_history: list[Board] = []    # Undone board-states
        self.player: int = EMPTY    # Current player
        
    def new_board(self, rows: int, columns: int):
        """Create a new, empty board of the given dimensions.

        Cannot be undone.
        """
        self.history = [Board(create_grid(rows, columns))]
        self.undo_history = []

    def reset_prisoners(self):
        """Reset the number of prisoners of both players.

        Cannot be undone.
        """
        board = self.history[-1]
        self.history = [Board(board.grid, ko=board.ko)]
        self.undo_history = []

    def placement(self, i: int, j: int, ignore_ko: bool):
        """Attempt to place or delete a stone at the given position."""
        if self.player == EMPTY:
            self.history.append(self.history[-1].erase(i, j))
        else:
            self.history.append(self.history[-1].move(self.player, i, j, ignore_ko))
        self.undo_history = []

    def pass_turn(self):
        """Pass a turn without placing a stone."""
        board = self.history[-1]
        self.history.append(Board(board.grid, prisoners=board.prisoners, passed=True))
        self.undo_history = []

    def undo(self):
        """Return to the previous board-state.

        If not possible, raise ActionError.
        """
        if len(self.history) == 1:
            raise ActionError
        else:
            self.undo_history.append(self.history.pop())

    def redo(self):
        """Return to the previously undone board-state.

        If not possible, raise ActionError.
        """
        if not self.undo_history:
            raise ActionError
        else:
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
    
    def test_repetition(self):
        """Test whether the stone placement has been repeated.

        Tests only up to the first un-undoable action (i. e. in the current playing sequence).
        If repetition occurs, show which player (if any) has gained more prisoners
        since the latest occurence of the position and ask whether to continue.
        If the user cancels the action, raise ActionError.
        """
        current_board = self.model.history[-1]
        for board in reversed(self.model.history[:-1]):
            if board == current_board:     
                difference = [i-j for i, j in zip(current_board.prisoners, board.prisoners)]
                if difference[0] > difference[1]:
                    text = "Black wins by prisoner difference"
                elif difference[0] < difference[1]:
                    text = "White wins by prisoner difference"
                else:
                    text = "No result by prisoner difference"
                    
                if not messagebox.askokcancel("Repetition", parent=self.view.root,
                                              message="Long cycle", detail=text):
                    self.model.history.pop()
                    raise ActionError
                break

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
        If the players alternate, change player.
        """
        try:
            self.model.placement(i, j, self.view.sandbox.get())
            if not self.view.sandbox.get() and self.view.test_repetition.get():
               self.test_repetition()
            if self.view.alternation.get() == ALTERNATE:
                self.model.player *= -1
            self.update_view()
        except (PlacementError, ActionError):
            pass

    def control(self, action: str):
        """Attempt to modify the model according to the given action.

        Possible actions are prisoner reset, pass, undo and redo.
        If two passes in succession have been made (in the current playing sequence),
        display a message saying so.
        Except prisoner reset, change player if they alternate.
        """
        try:
            if action == "Reset prisoners":
                self.model.reset_prisoners()
            else:
                if action in {"Pass", "p"}:
                    if not self.view.sandbox.get() and self.model.history[-1].passed == 1:
                        messagebox.showinfo("Game end", parent = self.view.root,
                                            message = "Double pass")
                    self.model.pass_turn()
                elif action in {"Undo", "BackSpace"}:
                    self.model.undo()
                elif action in {"Redo", "r"}:
                    self.model.redo()
                    
                if self.view.alternation.get() == ALTERNATE:
                    self.model.player *= -1
            self.update_view()
        except ActionError:
            pass
    
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
        self.model.history[-1].passed = False


class GameView:
    """Game graphics, passes user inputs to the controller."""
    
    def __init__(self, root, controller=None):
        self.root = root    # Root window
        self.controller: "GameController" = controller

        # The displayed numbers of prisoners
        self.prisoners = [tk.IntVar(root, 0), tk.IntVar(root, 0)]
        
        self.sandbox = tk.BooleanVar(root, False)    # The playing mode
        self.alternation = tk.IntVar(self.root, ALTERNATE)    # The alternation option
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

        # Side menu for board and alternation adjustment
        fr_menu = tk.Frame(self.root)
        self.size_menu = SizeMenu(fr_menu, self)
        self.size_menu.pack(anchor=tk.N)
        ModeMenu(fr_menu, self).pack(anchor=tk.N)
        fr_menu.pack(side=tk.LEFT, anchor=tk.N)

        self.root.bind("<Button-1>", self.defocus)

    def defocus(self, event):
        """Upon a click outside of an entry field, set keyboard focus to the goban."""
        if event.widget not in {self.size_menu.sp_rows, self.size_menu.sp_columns}:
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
        i, j = event.y//self.goban.size, event.x//self.goban.size
        if i >= 0 and i < self.goban.m and j >= 0 and j < self.goban.n:
            self.controller.placement(i, j)

    def control(self, event):
        """Handle button and key presses controlling the board-state."""
        if event.type == "5":    # Button click (and release)
            action = event.widget.cget("text")
        elif event.type == "2":    # Key press
            action = event.keysym
        self.controller.control(action)

    def set_player(self):
        """Set player to the current alternation choice."""
        self.controller.set_player()

    def set_mode(self):
        """Start a new playing sequence.

        If the mode was set to Play, fix the alternation option to ALTERNATE.
        """
        self.controller.set_start()
        if not self.sandbox.get():
            self.alternation.set(ALTERNATE)
            self.controller.set_player()


if __name__ == "__main__":
    root = tk.Tk()
    model, view = GameModel(), GameView(root)
    controller = GameController(model, view)
    view.controller = controller
    view.new_board(36, 9, 9)
    root.mainloop()
