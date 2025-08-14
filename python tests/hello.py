import tkinter as tk
import pygame
from tkinter import messagebox
from PIL import Image, ImageTk  # Pillow library for images
import copy
import random

class ChessGUI:
    def __init__(self, master):
        self.time_limit = None  # seconds, None = unlimited
        self.white_time = None
        self.black_time = None
        self.timer_running = False
        self.check_sound_played = False
        self.master = master
        self.square_size = 60
        self.animating = False
        self.captured_white = []
        self.captured_black = []
        self.colors = ["#F0D9B5", "#B58863"]
        self.selected = None
        self.turn = "W"
        self.castling_rights = {
            "W": {"kingside": True, "queenside": True},
            "B": {"kingside": True, "queenside": True}
        }
        self.en_passant_target = None
        self.soundEffect = "piece_moving.mp3"

        self.master.title("Advanced Chess GUI")

        # Main container frame with grid layout: 2 columns, 1 row
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill="both", expand=True)

        # Board container to help vertical centering of canvas
        self.board_container = tk.Frame(self.main_frame)
        self.board_container.grid(row=0, column=0, sticky="ns")

        self.canvas = tk.Canvas(self.board_container,
                            width=8 * self.square_size,
                            height=8 * self.square_size)
        self.canvas.pack(pady=40)  # Add vertical padding for rough vertical centering

        # Sidebar frame at right side, fills height
        self.sidebar = tk.Frame(self.main_frame, width=200)
        self.sidebar.grid(row=0, column=1, sticky="ns")

        # Allow vertical expansion on the main frame row 0
        self.main_frame.grid_rowconfigure(0, weight=1)
        # Fixed column widths (no weight)
        self.main_frame.grid_columnconfigure(0, weight=0)
        self.main_frame.grid_columnconfigure(1, weight=0)

        # Sidebar Top section (white captured pieces)
        self.captured_top_frame = tk.Frame(self.sidebar)
        self.captured_top_frame.pack(side="top", fill="x", pady=10)

        self.captured_white_label = tk.Label(self.captured_top_frame,
                                         text="White Captured:",
                                         font=("Arial", 12, "bold"))
        self.captured_white_label.pack()

        self.captured_white_pieces_frame = tk.Frame(self.captured_top_frame)
        self.captured_white_pieces_frame.pack()

        # Points difference label in sidebar below top captured pieces
        self.points_label = tk.Label(self.sidebar, text="Points difference: 0",
                                 font=("Arial", 12))
        self.points_label.pack(pady=20)

        # Sidebar Bottom section (black captured pieces)
        self.captured_bottom_frame = tk.Frame(self.sidebar)
        self.captured_bottom_frame.pack(side="bottom", fill="x", pady=10)

        self.captured_black_label = tk.Label(self.captured_bottom_frame,
                                         text="Black Captured:",
                                         font=("Arial", 12, "bold"))
        self.captured_black_label.pack()

        self.captured_black_pieces_frame = tk.Frame(self.captured_bottom_frame)
        self.captured_black_pieces_frame.pack()
        self.white_timer_label = tk.Label(self.sidebar, text="White Time: --:--", font=("Arial", 12))
        self.white_timer_label.pack(pady=(10, 5))

        self.black_timer_label = tk.Label(self.sidebar, text="Black Time: --:--", font=("Arial", 12))
        self.black_timer_label.pack(pady=(5, 15))
        self.restart_button = tk.Button(self.sidebar, text="Restart Game", command=self.restart_game)
        self.restart_button.pack(pady=(10, 20))
        # Map pieces to uniquely named image files
        piece_to_file = {
        'K': 'w_king.png',
        'Q': 'w_queen.png',
        'R': 'w_rook.png',
        'B': 'w_bishop.png',
        'N': 'w_knight.png',
        'P': 'w_pawn.png',
        'k': 'b_king.png',
        'q': 'b_queen.png',
        'r': 'b_rook.png',
        'b': 'b_bishop.png',
        'n': 'b_knight.png',
        'p': 'b_pawn.png',
        }
        self.images = {}
        for piece, filename in piece_to_file.items():
            img = Image.open(filename)
            img = img.resize((self.square_size - 10, self.square_size - 10), Image.Resampling.LANCZOS)
            self.images[piece] = ImageTk.PhotoImage(img)

        self.setup_board()
        self.draw_board()
        self.draw_pieces()
        self.canvas.bind("<Button-1>", self.on_click)
    def restart_game(self):
        if self.animating:
            return  # Optionally prevent restart during animation
        if hasattr(self, 'timer_after_id') and self.timer_after_id:
            self.master.after_cancel(self.timer_after_id)
            self.timer_after_id = None

        self.master.destroy()  # Close current chess window

        # Create new root and start fresh GUI + time selection
        new_root = tk.Tk()
        new_app = ChessGUI(new_root)
        new_app.time_selection_dialog()
        new_root.mainloop()

    def format_time(self, seconds):
        if seconds is None:
            return "--:--"
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def update_timer(self):
        if not self.timer_running:
            return

        if self.turn == "W" and self.white_time is not None:
            self.white_time -= 1
        elif self.turn == "B" and self.black_time is not None:
            self.black_time -= 1

        # Update display labels
        if self.turn == "B":
            self.white_timer_label.config(text=f"White - {self.player1_name} - Time: {self.format_time(self.white_time)}")
            self.black_timer_label.config(text=f"Black - {self.player2_name} - Time: {self.format_time(self.black_time)}")
        else:
            self.black_timer_label.config(text=f"White - {self.player1_name} - Time: {self.format_time(self.white_time)}")
            self.white_timer_label.config(text=f"Black - {self.player2_name} - Time: {self.format_time(self.black_time)}")

        # Check for timeout
        if (self.white_time is not None and self.white_time <= 0):
            self.soundEffect="checkmate.mp3"
            self.playSound()
            self.timer_running = False
            messagebox.showinfo("Time Out", "White ran out of time! Black wins!")
            self.master.destroy()
            return
        elif (self.black_time is not None and self.black_time <= 0):
            self.soundEffect="checkmate.mp3"
            self.playSound()
            self.timer_running = False
            messagebox.showinfo("Time Out", "Black ran out of time! White wins!")
            self.master.destroy()
            return

        # Call this function again after 1 second
        self.timer_after_id = self.master.after(1000, self.update_timer)

    def start_timer(self):
        if self.time_limit is not None:
            self.timer_running = True
            self.update_timer()
        else:
            # Unlimited time, no timer countdown
            self.white_timer_label.config(text="White Time: --:--")
            self.black_timer_label.config(text="Black Time: --:--")


    def time_selection_dialog(self):
        # Create modal dialog to get time selection
        dialog = tk.Toplevel(self.master)
        dialog.title("Select Time Control")
        dialog.attributes('-fullscreen', True)
        dialog.transient(self.master)
        dialog.lift()
        # Player name entries
        tk.Label(dialog, text="Player 1 Name:").pack(pady=(20, 5))
        player1_entry = tk.Entry(dialog)
        player1_entry.pack(padx=20)
        player1_entry.insert(0, "Player 1")

        tk.Label(dialog, text="Player 2 Name:").pack(pady=(20, 5))
        player2_entry = tk.Entry(dialog)
        player2_entry.pack(padx=20)
        player2_entry.insert(0, "Player 2")

        tk.Label(dialog, text="Select time per player:").pack(pady=10)

        times = [("1 Minute", 60), ("3 Minutes", 180), ("5 Minutes", 300), ("10 Minutes", 600), ("Unlimited", None)]
        self.selected_time = tk.IntVar(value=300)  # default 5 min

        for label, seconds in times:
            r = tk.Radiobutton(dialog, text=label, variable=self.selected_time, value=seconds if seconds else -1)
            r.pack(fill='x', padx=20, anchor='center')
        tk.Label(dialog, text="Who should start?").pack(pady=(20, 5))
        self.selected_start = tk.StringVar(value="white")

        tk.Radiobutton(dialog, text="Player 1 starts", variable=self.selected_start, value="white").pack(fill='x', padx=20, anchor='center')
        tk.Radiobutton(dialog, text="Player 2 starts", variable=self.selected_start, value="black").pack(fill='x', padx=20, anchor='center')
        tk.Radiobutton(dialog, text="Random", variable=self.selected_start, value="random").pack(fill='x', padx=20, anchor='center')


        def on_confirm():
            val = self.selected_time.get()
            self.time_limit = None if val == -1 else val
            if self.time_limit:
                self.white_time = self.time_limit
                self.black_time = self.time_limit
            else:
                self.white_time = None
                self.black_time = None
            # Store player names
            player1_name_raw = player1_entry.get().strip() or "Player 1"
            player2_name_raw = player2_entry.get().strip() or "Player 2"

            # Decide who starts
            starter = self.selected_start.get()
            if starter == "random":
                # Randomly pick which player starts
                starter = random.choice(["white", "black"])

            if starter == "black":
                # Player 2 starts: swap names so Player 2 controls White pieces
                self.player1_name = player2_name_raw
                self.player2_name = player1_name_raw
            else:
                # Player 1 starts: no swapping
                self.player1_name = player1_name_raw
                self.player2_name = player2_name_raw
            # White always starts
            self.turn = "W"
            self.captured_white_label.config(text=f"{self.player2_name} Captured:")
            self.captured_black_label.config(text=f"{self.player1_name} Captured:")
            dialog.destroy()
            self.start_timer()
        tk.Button(dialog, text="Start Game", command=on_confirm).pack(pady=10)
        dialog.grab_set()  # modal
        self.master.wait_window(dialog)

    def update_sidebar(self):
        def clear_frame(frame):
            for widget in frame.winfo_children():
                widget.destroy()

        clear_frame(self.captured_white_pieces_frame)
        clear_frame(self.captured_black_pieces_frame)

        if self.turn== "B":
            self.captured_white_label.config(text=f"{self.player1_name} Captured:")
            self.captured_black_label.config(text=f"{self.player2_name} Captured:")
            # Show captured white pieces (White captured Black pieces)
            for p in self.captured_white:
                img = self.images[p]
                label = tk.Label(self.captured_white_pieces_frame, image=img)
                label.pack(side="left", padx=2)

            # Show captured black pieces (Black captured White pieces)
            for p in self.captured_black:
                img = self.images[p]
                label = tk.Label(self.captured_black_pieces_frame, image=img)
                label.pack(side="left", padx=2)
        else:
            self.captured_white_label.config(text=f"{self.player2_name} Captured:")
            self.captured_black_label.config(text=f"{self.player1_name} Captured:")
            # Show captured white pieces (White captured Black pieces)
            for p in self.captured_white:
                img = self.images[p]
                label = tk.Label(self.captured_black_pieces_frame, image=img)
                label.pack(side="left", padx=2)

            # Show captured black pieces (Black captured White pieces)
            for p in self.captured_black:
                img = self.images[p]
                label = tk.Label(self.captured_white_pieces_frame, image=img)
                label.pack(side="left", padx=2)

        # Calculate points difference and update label (values per piece type)
        piece_values = {'P':1, 'N':3, 'B':3, 'R':5, 'Q':9, 'K':0}
        white_points = sum(piece_values.get(p.upper(), 0) for p in self.captured_black)  # White captured black pieces
        black_points = sum(piece_values.get(p.upper(), 0) for p in self.captured_white)  # Black captured white pieces
        diff= (white_points - black_points) if (self.turn!= "W") else (black_points - white_points)
        self.points_label.config(text=f"Points Difference: {diff}")

    def playSound(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.soundEffect)
        pygame.mixer.music.play()

    def setup_board(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        # White pieces
        self.board[0][0] = self.board[0][7] = "R"
        self.board[0][1] = self.board[0][6] = "N"
        self.board[0][2] = self.board[0][5] = "B"
        self.board[0][3] = "Q"
        self.board[0][4] = "K"
        for i in range(8):
            self.board[1][i] = "P"
        # Black pieces
        self.board[7][0] = self.board[7][7] = "r"
        self.board[7][1] = self.board[7][6] = "n"
        self.board[7][2] = self.board[7][5] = "b"
        self.board[7][3] = "q"
        self.board[7][4] = "k"
        for i in range(8):
            self.board[6][i] = "p"
    
    def transform_coords(self, row, col):
        if self.turn == "W":
            return 7 - row, 7 - col
        else:  # Flip for Black turn
            return row, col


    def draw_pieces(self):
        self.canvas.delete("piece")
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    drow, dcol = self.transform_coords(row, col)
                    x = dcol * self.square_size + self.square_size // 2
                    y = drow * self.square_size + self.square_size // 2
                    self.canvas.create_image(x, y, image=self.images[piece], tags="piece")


    def draw_board(self):
        self.canvas.delete("square")
        for row in range(8):
            for col in range(8):
                drow, dcol = self.transform_coords(row, col)
                x1 = dcol * self.square_size
                y1 = drow * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                color = self.colors[(row + col) % 2]
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black", tags="square")
        if self.selected:
            drow, dcol = self.transform_coords(*self.selected)
            self.highlight_square(drow, dcol)



    def highlight_square(self, row, col):
        """Highlights a square using a red outline."""
        x1 = col * self.square_size
        y1 = row * self.square_size
        x2 = x1 + self.square_size
        y2 = y1 + self.square_size
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=3, tags="selection")

    def is_same_color(self, piece1, piece2):
        """Returns True if both pieces are of the same color."""
        return (piece1.isupper() and piece2.isupper()) or (piece1.islower() and piece2.islower())

    def clear_path(self, fr, fc, tr, tc, board=None):
        """Verifies that the path is clear from (fr,fc) to (tr,tc) for sliding pieces.
           Uses provided board or self.board if None."""
        if board is None:
            board = self.board
        d_row = tr - fr
        d_col = tc - fc
        step_row = (d_row // abs(d_row)) if d_row != 0 else 0
        step_col = (d_col // abs(d_col)) if d_col != 0 else 0
        r, c = fr + step_row, fc + step_col
        while (r, c) != (tr, tc):
            if board[r][c]:
                return False
            r += step_row
            c += step_col
        return True

    def find_king(self, board, color):
        """Finds the king of the specified color on a given board state."""
        king_symbol = "K" if color == "W" else "k"
        for r in range(8):
            for c in range(8):
                if board[r][c] == king_symbol:
                    return (r, c)
        return None

    def is_in_check_board(self, board, color):
        """
        Returns True if the king of the given color is under attack in the provided board.
        Uses the basic_validate move rule for opposing pieces.
        """
        if not hasattr(self, 'check_sound_played'):
            self.check_sound_played = False
        king_pos = self.find_king(board, color)
        if not king_pos:
            return True  # Should not happen; treat as check.
        kr, kc = king_pos
        opp_color = "B" if color == "W" else "W"
        for r in range(8):
            for c in range(8):
                opp = board[r][c]
                if opp and ((opp.isupper() and opp_color == "W") or (opp.islower() and opp_color == "B")):
                    if self.basic_validate(opp, r, c, kr, kc, board, check_king_safety=False):
                        if not self.check_sound_played:
                            self.soundEffect = "check.mp3"
                            self.playSound()
                            self.check_sound_played = True
                        return True
        self.check_sound_played = False
        return False

    def basic_validate(self, piece, fr, fc, tr, tc, board, check_king_safety=True):
        
        """
        Checks if a move follows piece-specific rules (ignoring overall king safety, unless specified).
        Works on the provided board state.
        """
        self.master.title(f"Chess - {self.player1_name} vs {self.player2_name} - {'White' if self.turn == 'W' else 'Black'} to move")
        if (fr, fc) == (tr, tc):
            return False
        dest_piece = board[tr][tc]
        if dest_piece and ((piece.isupper() and dest_piece.isupper()) or (piece.islower() and dest_piece.islower())):
            return False
        direction = 1 if piece.isupper() else -1
        piece_type = piece.upper()
        dr = tr - fr
        dc = tc - fc

        # Pawn moves and captures.
        if piece_type == "P":
            # Move forward.
            if dc == 0:
                if dr == direction and dest_piece is None:
                    return True
                start_row = 1 if piece.isupper() else 6
                if fr == start_row and dr == 2 * direction:
                    if dest_piece is None and board[fr + direction][fc] is None:
                        return True
            if abs(dc) == 1 and dr == direction:
                # Normal diagonal capture.
                if dest_piece and not self.is_same_color(piece, dest_piece):
                    return True
                # En passant.
                if dest_piece is None and self.en_passant_target == (tr, tc):
                    return True
            return False

        # Knight moves.
        elif piece_type == "N":
            return (abs(dr), abs(dc)) in [(2, 1), (1, 2)]

        # Bishop moves.
        elif piece_type == "B":
            if abs(dr) == abs(dc):
                return self.clear_path(fr, fc, tr, tc, board)
            return False

        # Rook moves.
        elif piece_type == "R":
            if dr == 0 or dc == 0:
                return self.clear_path(fr, fc, tr, tc, board)
            return False
        # Queen moves.
        elif piece_type == "Q":
            if abs(dr) == abs(dc) or dr == 0 or dc == 0:
                return self.clear_path(fr, fc, tr, tc, board)
            return False

        # King moves.
        elif piece_type == "K":
            if max(abs(dr), abs(dc)) == 1:
                return True
            # Castling: King moving two squares horizontally.
            if dr == 0 and abs(dc) == 2:
                # Do not castle if the king is in check.
                if check_king_safety and self.is_in_check_board(self.board, "W" if piece.isupper() else "B"):
                    return False
                color = "W" if piece.isupper() else "B"
                if dc > 0:
                    # Kingside castling.
                    if not self.castling_rights[color]["kingside"]:
                        return False
                    rook_col = 7
                else:
                    # Queenside castling.
                    if not self.castling_rights[color]["queenside"]:
                        return False
                    rook_col = 0
                # Rook must be present and unmoved.
                expected_rook = "R" if color == "W" else "r"
                if board[fr][rook_col] != expected_rook:
                    return False
                # Squares between king and rook must be clear.
                step = 1 if dc > 0 else -1
                for c in range(fc + step, rook_col, step):
                    if board[fr][c]:
                        return False
                print(f"Castling check: color={color}, kingside={dc>0}, rook at ({fr},{rook_col})={board[fr][rook_col]}, rights={self.castling_rights[color]}")
                # The king may not pass through an attacked square.
                for c in [fc, fc + step, fc + 2 * step]:
                    temp_board = copy.deepcopy(board)
                    temp_board[fr][fc] = None
                    temp_board[fr][c] = piece
                    if self.is_in_check_board(temp_board, color):
                        print(f"Castling invalid: square {(fr, c)} is attacked during castling move")
                        return False
                return True

        return False
    
    def get_valid_moves_for_piece(self, fr, fc):
        piece = self.board[fr][fc]
        if not piece:
            return []
        moves = []
        for tr in range(8):
            for tc in range(8):
                if self.validate_move(piece, fr, fc, tr, tc):
                    moves.append((tr, tc))
        return moves
    def draw_move_circles(self):
        self.canvas.delete("move_circle")
        if not self.selected:
            return
        fr, fc = self.selected
        moves = self.get_valid_moves_for_piece(fr, fc)
        for (tr, tc) in moves:
            drow, dcol = self.transform_coords(tr, tc)
            x = dcol * self.square_size + self.square_size // 2
            y = drow * self.square_size + self.square_size // 2
            radius = self.square_size // 6
            self.canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                outline="", fill="blue", stipple="gray12", tags="move_circle"
            )


    def simulate_move(self, fr, fc, tr, tc, extra_updates=None):
        """
        Create a deep copy of the board with a move applied. The extra_updates callback
        can be used for handling en passant captures or castling rook movement.
        """
        new_board = copy.deepcopy(self.board)
        piece = new_board[fr][fc]
        new_board[tr][tc] = piece
        new_board[fr][fc] = None
        if extra_updates:
            extra_updates(new_board)
        return new_board

    def get_extra_updates(self, piece, fr, fc, tr, tc):
        """
        Returns a callback function to update special moves (en passant and castling)
        on the simulated board.
        """
        def update(new_board):
            # En passant capture.
            if piece.upper() == "P" and (tr, tc) == self.en_passant_target and self.board[tr][tc] is None:
                cap_row = tr - (1 if piece.isupper() else -1)
                new_board[cap_row][tc] = None
            # Castling: Move the rook.
            if piece.upper() == "K" and abs(tc - fc) == 2:
                self.soundEffect="piece_capturing.mp3"
                self.playSound()
                color = "W" if piece.isupper() else "B"
                if tc > fc:
                    # Kingside castle.
                    rook_from = (fr, 7)
                    rook_to = (fr, fc + 1)
                else:
                    # Queenside castle.
                    rook_from = (fr, 0)
                    rook_to = (fr, fc - 1)
                new_board[rook_to[0]][rook_to[1]] = new_board[rook_from[0]][rook_from[1]]
                new_board[rook_from[0]][rook_from[1]] = None
        return update

    def validate_move(self, piece, fr, fc, tr, tc):
        """
        Validates a move by checking piece-specific rules and then simulating the move
        to verify that the moving side's king is not left in check.
        """
        if not self.basic_validate(piece, fr, fc, tr, tc, self.board):
            return False

        extra = self.get_extra_updates(piece, fr, fc, tr, tc)
        new_board = self.simulate_move(fr, fc, tr, tc, extra)
        moving_color = "W" if piece.isupper() else "B"
        if self.is_in_check_board(new_board, moving_color):
            return False

        return True

    def update_special_states(self, piece, fr, fc, tr, tc):
        """
        Updates castling rights, en passant target, and promotions. Also switches the turn.
        """
        color = "W" if piece.isupper() else "B"
        opponent = "B" if color == "W" else "W"
        self.en_passant_target = None

        # Pawn double move: set en passant target.
        if piece.upper() == "P" and abs(tr - fr) == 2:
            self.en_passant_target = (fr + (1 if piece.isupper() else -1), fc)

        # Promotion: when a pawn reaches the last rank.
        if piece.upper() == "P":
            if (piece.isupper() and tr == 7) or (piece.islower() and tr == 0):
                # Automatically promote to Queen.
                self.board[tr][tc] = "Q" if piece.isupper() else "q"

        # King move: lose castling rights.
        if piece.upper() == "K":
            self.castling_rights[color]["kingside"] = False
            self.castling_rights[color]["queenside"] = False

        # Rook move: update castling rights if it moves from its starting square.
        if piece.upper() == "R":
            if color == "W":
                if (fr, fc) == (0, 0):
                    self.castling_rights["W"]["queenside"] = False
                elif (fr, fc) == (0, 7):
                    self.castling_rights["W"]["kingside"] = False
            else:
                if (fr, fc) == (7, 0):
                    self.castling_rights["B"]["queenside"] = False
                elif (fr, fc) == (7, 7):
                    self.castling_rights["B"]["kingside"] = False

        # If a rook is captured from its starting square, adjust the opponent's castling rights.
        captured = self.board[tr][tc]
        if captured and captured.upper() == "R":
            if opponent == "W":
                if (tr, tc) == (0, 0):
                    self.castling_rights["W"]["queenside"] = False
                elif (tr, tc) == (0, 7):
                    self.castling_rights["W"]["kingside"] = False
            else:
                if (tr, tc) == (7, 0):
                    self.castling_rights["B"]["queenside"] = False
                elif (tr, tc) == (7, 7):
                    self.castling_rights["B"]["kingside"] = False

        # Switch turn.
        self.turn = opponent

    def get_all_valid_moves(self, color):
        """
        Returns a list of valid moves for the given color.
        Each move is represented as ((fr, fc), (tr, tc)).
        """
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece:
                    if (piece.isupper() and color == "W") or (piece.islower() and color == "B"):
                        for tr in range(8):
                            for tc in range(8):
                                if self.validate_move(piece, r, c, tr, tc):
                                    moves.append(((r, c), (tr, tc)))
        return moves

    def has_valid_moves(self, color):
        """Returns True if the player of the given color has any valid moves."""
        return len(self.get_all_valid_moves(color)) > 0

    def check_game_over(self):
        """
        Checks for end of game: if the current player has no valid moves,
        declares checkmate if in check or stalemate otherwise.
        """
        if not self.has_valid_moves(self.turn):
            self.soundEffect="checkmate.mp3"
            self.playSound()
            if self.is_in_check_board(self.board, self.turn):
                winner = "Black" if self.turn == "W" else "White"
                messagebox.showinfo("Checkmate", f"Checkmate! {winner} wins!")
            else:
                messagebox.showinfo("Stalemate", "Stalemate! The game is a draw.")
            self.master.quit()

    def on_click(self, event):
        if self.animating:
            return
        display_col = event.x // self.square_size
        display_row = event.y // self.square_size

        if self.turn == "W":
            row, col = 7 - display_row, 7 - display_col
        else:
            row, col = display_row, display_col

        if not (0 <= row < 8 and 0 <= col < 8):
            return

        piece = self.board[row][col]

        if self.selected is None:
            # No piece selected, try to select if friendly piece
            if piece and ((piece.isupper() and self.turn == "W") or (piece.islower() and self.turn == "B")):
                self.selected = (row, col)
                drow, dcol = self.transform_coords(row, col)
                self.canvas.delete("selection")
                self.highlight_square(drow, dcol)
                self.draw_move_circles()
            else:
                messagebox.showinfo("Not your turn", "Please select one of your own pieces.")
        else:
            fr, fc = self.selected
            selected_piece = self.board[fr][fc]

            if (row, col) == (fr, fc):
                # Clicked same square -> deselect
                self.selected = None
                self.canvas.delete("selection")
                self.canvas.delete("move_circle")
            elif piece and ((piece.isupper() and self.turn == "W") or (piece.islower() and self.turn == "B")):
                # Clicked different friendly piece -> change selection
                self.selected = (row, col)
                drow, dcol = self.transform_coords(row, col)
                self.canvas.delete("selection")
                self.highlight_square(drow, dcol)
                self.draw_move_circles()
            else:
                # Attempt move to empty or enemy square
                if self.validate_move(selected_piece, fr, fc, row, col):
                    self.timer_running = False
                    self.canvas.delete("move_circle")
                    self.canvas.delete("selection")

                    extra = self.get_extra_updates(selected_piece, fr, fc, row, col)
                    self.animate_move(selected_piece, fr, fc, row, col, extra)
                    self.soundEffect="piece_moving.mp3"
                    self.playSound()
                else:
                    messagebox.showinfo("Invalid Move", "That move is not allowed.")

    def animate_move(self, piece, fr, fc, tr, tc, extra_updates):
        if self.animating:
            return  # ignore new animation if one is running
        self.animating = True

        # Because the board might be flipped, transform coordinates appropriately
        start_drow, start_dcol = self.transform_coords(fr, fc)
        end_drow, end_dcol = self.transform_coords(tr, tc)
        start_x = start_dcol * self.square_size + self.square_size // 2
        start_y = start_drow * self.square_size + self.square_size // 2
        end_x = end_dcol * self.square_size + self.square_size // 2
        end_y = end_drow * self.square_size + self.square_size // 2

        # Create a piece image on canvas to animate (on top layer)
        anim_img = self.canvas.create_image(start_x, start_y, image=self.images[piece], tags="anim_piece")
        # Number of steps and delay per step for smooth 1 sec animation (e.g., 30 FPS)
        steps = 25
        delay = 30  # milliseconds ~30 FPS

        delta_x = (end_x - start_x) / steps
        delta_y = (end_y - start_y) / steps

        def move_step(step=0):
            if step < steps:
                self.canvas.move(anim_img, delta_x, delta_y)
                self.canvas.after(delay, move_step, step + 1)
            else:
                captured_piece = None
                # Determine captured piece before the move update
                # Normal capture
                if self.board[tr][tc] is not None and (tr, tc) != (fr, fc):
                    captured_piece = self.board[tr][tc]
                # En passant capture
                elif (piece.upper() == 'P' and self.en_passant_target == (tr, tc)):
                    cap_row = tr - (1 if piece.isupper() else -1)
                    captured_piece = self.board[cap_row][tc]

                # Update board state
                self.board = self.simulate_move(fr, fc, tr, tc, extra_updates)
                self.update_special_states(piece, fr, fc, tr, tc)

                # If captured piece detected, do sound + add to captured lists outside of animate_move maybe
                if captured_piece is not None:
                    self.soundEffect = "piece_capturing.mp3"
                    self.playSound()

                    # Add to captured list:
                    if captured_piece.isupper():
                        self.captured_black.append(captured_piece)
                    else:
                        self.captured_white.append(captured_piece)

                # Clean up animation image
                self.canvas.delete("anim_piece")

                # Redraw board and pieces normally
                self.draw_board()
                self.draw_pieces()
                self.check_game_over()

                # Clear selection and move indicators
                self.selected = None
                self.canvas.delete("selection")
                self.canvas.delete("move_circle")
                self.animating = False
                self.update_sidebar()
                self.timer_running = True
                self.update_timer()

        move_step()



def main():
    root = tk.Tk()
    app = ChessGUI(root)
    app.time_selection_dialog()
    root.mainloop()

if __name__ == "__main__":
    main()
