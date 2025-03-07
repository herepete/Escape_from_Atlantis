#!/usr/bin/python3
import random
import time

# ANSI color codes for nicer output
RESET   = "\033[0m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
CYAN    = "\033[36m"

# Tile info
TILE_INFO = {
    "beach":    {"icon": "♒",    "distance": 3, "color": CYAN,   "letter": "B"},
    "forest":   {"icon": "♣",    "distance": 2, "color": GREEN,  "letter": "F"},
    "mountain": {"icon": "♦",    "distance": 1, "color": YELLOW, "letter": "M"},
    "volcano":  {"icon": "☆VOL", "distance": 1, "color": RED,    "letter": "V"}
}

COL_LETTERS = ['A', 'B', 'C', 'D', 'E']
MAX_TURNS = 20

class Tile:
    def __init__(self, id, tile_type):
        self.id = id
        info = TILE_INFO[tile_type]
        self.type = tile_type
        self.icon = info["icon"]
        self.distance = info["distance"]
        self.color = info["color"]
        self.letter = info["letter"]
        self.villagers = []
        self.capacity = 3

class Villager:
    def __init__(self, id, owner, treasure, state="land", distance_remaining=None, tile=None):
        self.id = id
        self.owner = owner
        self.treasure = treasure
        self.state = state        # "land", "water", "safe", or "dead"
        self.distance_remaining = distance_remaining
        self.tile = tile

class Player:
    def __init__(self, name, is_human):
        self.name = name
        self.is_human = is_human
        self.villagers = []
        self.score = 0

class Game:
    def __init__(self):
        # Three players: 1 human, 2 computer
        self.players = [
            Player("Human", True),
            Player("Computer1", False),
            Player("Computer2", False)
        ]
        # Build 3x5 board, center cell = volcano
        remaining_types = (["beach"] * 7) + (["forest"] * 4) + (["mountain"] * 3)
        random.shuffle(remaining_types)
        self.board = []
        tile_id = 1
        for r in range(3):
            row = []
            for c in range(5):
                if r == 1 and c == 2:
                    tile = Tile(tile_id, "volcano")
                else:
                    tile_type = remaining_types.pop()
                    tile = Tile(tile_id, tile_type)
                row.append(tile)
                tile_id += 1
            self.board.append(row)
        self.tiles = [tile for row in self.board for tile in row]
        self.total_turns = 0
        self.villager_counter = 1
        self.game_end_reason = ""

    def print_introduction(self):
        intro = f"""
Welcome to {GREEN}Escape from Atlantis{RESET}!
------------------------------------------------
Each player must place 10 villagers.
You (and two computer opponents) will try to rescue your villagers
from a sinking island. The island is displayed as a table with columns
A–E and rows 1–3. Each cell is 5 characters wide, e.g. " B:3 " or "  X  ".
Tile types:
  {CYAN}♒{RESET} = Beach (B) – needs 3 moves to be safe.
  {GREEN}♣{RESET} = Forest (F) – needs 2 moves.
  {YELLOW}♦{RESET} = Mountain (M) – needs 1 move.
  {RED}☆VOL{RESET} = Volcano (V) – a dangerous tile.
Every turn you get 3 movement points to move your villagers closer to safety.
You might choose NOT to move a villager if you want to save your movement
points for a different villager or keep them in place strategically.
After movement, a tile sinks and any villager on it falls into water.
A creature phase may attack swimmers.
At game’s end, safe villagers add points equal to their treasure (1–6).
The highest total wins!
------------------------------------------------
"""
        print(intro)

    def print_board(self):
        """
        Print the board as a table with columns A–E, rows 1–3,
        each cell exactly 5 characters wide. If a tile is sunk, show "  X  ".
        """
        cell_width = 5
        # Print column headers
        header = "    " + " ".join([col.center(cell_width) for col in COL_LETTERS])
        print(header)

        # Horizontal border
        # e.g. "    +-----+-----+-----+-----+-----+"
        horizontal_border = "    +" + "+".join(["-" * cell_width for _ in range(5)]) + "+"

        print(horizontal_border)
        for r, row in enumerate(self.board):
            row_str = f"{r+1}".rjust(4) + "|"
            for tile in row:
                if tile is None:
                    # Sunk tile => "  X  "
                    cell_text = "  X  "
                else:
                    # e.g. " B:3 "
                    cell_text = f"{tile.color}{tile.letter}{RESET}:{len(tile.villagers)}"
                    # We'll center it in 5 spaces
                    cell_text = cell_text.center(cell_width)
                row_str += cell_text + "|"
            print(row_str)
            print(horizontal_border)

    def print_player_statuses(self):
        """
        Print how many villagers each player has:
        - Remaining (land/water)
        - Saved (safe)
        - Killed (dead)
        Aligned in columns for neatness.
        """
        print("\nPlayer Status:")
        for player in self.players:
            remaining = sum(1 for v in player.villagers if v.state in ["land", "water"])
            saved = sum(1 for v in player.villagers if v.state == "safe")
            killed = sum(1 for v in player.villagers if v.state == "dead")
            # Adjust name spacing for alignment, e.g. 10 chars wide
            print(f"  {player.name:10s}: Remaining = {remaining}, Saved = {saved}, Killed = {killed}")
        print()

    def print_human_villagers(self, human_player):
        """Show the human player's villagers, with location and moves needed."""
        print("\nYour Villagers:")
        for v in human_player.villagers:
            if v.state in ["land", "water"]:
                if v.state == "land" and v.tile:
                    r, c, _ = self.find_tile_by_id(v.tile.id)
                    coord = f"{COL_LETTERS[c]}{r+1}"
                else:
                    coord = "in water"
                print(f"  ID {v.id}: {coord}, moves needed: {v.distance_remaining}")
        print()

    def get_all_tiles(self):
        return [tile for row in self.board for tile in row if tile is not None]

    def find_tile_by_id(self, tid):
        for r, row in enumerate(self.board):
            for c, tile in enumerate(row):
                if tile and tile.id == tid:
                    return (r, c, tile)
        return (None, None, None)

    def setup(self):
        self.print_introduction()
        print("Setting up the game and placing villagers on the island...\n")
        for player in self.players:
            print(f"Placing villagers for {player.name}:")
            random_place = False
            if player.is_human:
                choice = input("Do you want to randomly place your villagers? (y/n): ").strip().lower()
                if choice == "y":
                    random_place = True
            for _ in range(10):
                treasure = random.randint(1, 6)
                valid_tiles = [tile for tile in self.get_all_tiles() if len(tile.villagers) < tile.capacity]
                if not valid_tiles:
                    print("No available tiles to place a villager!")
                    break
                if player.is_human and not random_place:
                    self.print_board()
                    print("Available Tiles:")
                    for tile in valid_tiles:
                        r, c, _ = self.find_tile_by_id(tile.id)
                        coord = f"{COL_LETTERS[c]}{r+1}"
                        print(f"  {coord} - {tile.type.capitalize()} (Tile {tile.id})")
                    coord_input = input("Enter tile coordinate (e.g., A1) to place villager: ")
                    r_c = self.coordinate_to_index_reprompt(coord_input, valid_tiles)
                    if r_c is None:
                        # random fallback
                        chosen_tile = random.choice(valid_tiles)
                    else:
                        rr, cc = r_c
                        chosen_tile = self.board[rr][cc]
                else:
                    chosen_tile = random.choice(valid_tiles)
                villager = Villager(self.villager_counter, player.name, treasure,
                                    state="land", distance_remaining=chosen_tile.distance, tile=chosen_tile)
                player.villagers.append(villager)
                chosen_tile.villagers.append(villager)
                print(f"  {player.name} placed villager {self.villager_counter} (treasure {treasure}) on tile {chosen_tile.id} ({chosen_tile.type}).")
                self.villager_counter += 1
            print()
        print("Setup complete!\n")
        time.sleep(2)

    def coordinate_to_index_reprompt(self, coord_input, valid_tiles):
        """
        Helper to re-prompt if user enters invalid coordinate for villager placement.
        Returns (row, col) or None if we eventually pick randomly.
        """
        attempts = 3
        while attempts > 0:
            r_c = self._coord_to_index(coord_input)
            if r_c is None:
                attempts -= 1
                if attempts == 0:
                    print("Too many invalid attempts. Using random tile.")
                    return None
                print("Invalid coordinate. Try again.")
                coord_input = input("Enter tile coordinate again: ")
                continue
            rr, cc = r_c
            chosen_tile = self.board[rr][cc]
            if chosen_tile is None or len(chosen_tile.villagers) >= chosen_tile.capacity:
                attempts -= 1
                if attempts == 0:
                    print("Tile not available. Using random tile.")
                    return None
                print("Tile not available. Try again.")
                coord_input = input("Enter tile coordinate again: ")
                continue
            return rr, cc
        return None

    def _coord_to_index(self, coord):
        """ Convert e.g. 'A1' to (row, col), or None if invalid. """
        coord = coord.strip().upper()
        if len(coord) < 2:
            return None
        col_letter = coord[0]
        row_part = coord[1:]
        if col_letter not in COL_LETTERS:
            return None
        try:
            row_number = int(row_part)
        except ValueError:
            return None
        row_index = row_number - 1
        col_index = COL_LETTERS.index(col_letter)
        if row_index < 0 or row_index >= 3 or col_index < 0 or col_index >= 5:
            return None
        return row_index, col_index

    def player_move_phase(self, player):
        points = 3
        water_moved = set()

        print(f"\n--- {CYAN}{player.name}'s Movement Phase{RESET} ---")

        if player.is_human:
            self.print_human_villagers(player)

        while points > 0 and any(v.state in ["land", "water"] for v in player.villagers):
            if player.is_human:
                # Prompt y/n to move a villager, re-prompt on invalid input
                while True:
                    choice = input(f"{player.name} has {points} movement point(s) left. Move a villager? (y/n): ").strip().lower()
                    if choice in ["y", "n"]:
                        break
                    else:
                        print("Invalid input. Please type 'y' or 'n' only.")
                if choice != "y":
                    break

                # Prompt for villager ID
                villager = self.prompt_for_villager_id(player, water_moved, points)
                if not villager:
                    # user canceled or no valid input
                    continue

                # Now we have a valid villager to move
                if villager.state == "land":
                    max_move = min(points, villager.distance_remaining)
                else:
                    max_move = 1

                if max_move <= 0:
                    print("This villager cannot move further.")
                    continue

                move_points = self.prompt_for_move_points(max_move)
                if move_points < 1:
                    # user canceled or invalid
                    continue

                villager.distance_remaining -= move_points
                points -= move_points

                if villager.distance_remaining <= 0:
                    villager.state = "safe"
                    if villager.tile:
                        villager.tile.villagers.remove(villager)
                    print(f"Villager {villager.id} has reached safety!")
                else:
                    if villager.state == "water":
                        water_moved.add(villager.id)

                self.print_human_villagers(player)
                time.sleep(1)

            else:
                # Computer
                comp_movable = [v for v in player.villagers if v.state in ["land", "water"]]
                if not comp_movable:
                    break
                # pick villager with smallest distance_remaining
                v = min(comp_movable, key=lambda x: x.distance_remaining)

                if v.state == "water" and v.id in water_moved:
                    # try a land villager instead
                    land_only = [vv for vv in comp_movable if vv.state == "land"]
                    if not land_only:
                        break
                    v = min(land_only, key=lambda x: x.distance_remaining)

                if v.state == "land":
                    max_move = min(points, v.distance_remaining)
                else:
                    if v.id in water_moved:
                        break
                    max_move = 1

                if max_move <= 0:
                    break

                move_points = max_move
                print(f"{player.name} moves villager {v.id} by {move_points} space(s).")
                v.distance_remaining -= move_points
                points -= move_points
                if v.distance_remaining <= 0:
                    v.state = "safe"
                    if v.tile:
                        v.tile.villagers.remove(v)
                    print(f"{player.name}'s villager {v.id} has reached safety!")
                else:
                    if v.state == "water":
                        water_moved.add(v.id)
                time.sleep(1)

        print(f"--- End of {CYAN}{player.name}'s Movement Phase{RESET} ---\n")
        time.sleep(2)
        self.print_player_statuses()

    def prompt_for_villager_id(self, player, water_moved, points):
        """Prompt user for a villager ID to move, re-prompt on invalid input."""
        while True:
            raw_vid = input("Enter the villager ID to move (refer to your summary above): ").strip()
            if not raw_vid.isdigit():
                print("Invalid input. Please enter a numeric ID or type 'n' to skip.")
                # Could add an option to skip
                continue
            vid = int(raw_vid)
            villager = next((v for v in player.villagers if v.id == vid and v.state in ["land", "water"]), None)
            if not villager:
                print("Invalid ID or that villager is not movable. Try again.")
                continue
            if villager.state == "water" and villager.id in water_moved:
                print("You have already moved this villager in water this turn.")
                continue
            return villager

    def prompt_for_move_points(self, max_move):
        """Prompt user for how many spaces to move, from 1..max_move. Returns int or 0 if invalid/cancel."""
        while True:
            raw_move = input(f"Enter number of spaces to move (1..{max_move}): ").strip()
            if not raw_move.isdigit():
                print("Invalid input. Please enter a numeric value.")
                continue
            move_points = int(raw_move)
            if move_points < 1 or move_points > max_move:
                print(f"Invalid movement. Enter a value from 1 to {max_move}.")
                continue
            return move_points

    def sink_tile(self):
        tiles = self.get_all_tiles()
        beach_tiles = [t for t in tiles if t.type == "beach"]
        forest_tiles = [t for t in tiles if t.type == "forest"]
        mountain_tiles = [t for t in tiles if t.type == "mountain"]
        volcano_tiles = [t for t in tiles if t.type == "volcano"]

        tile_to_sink = None
        if beach_tiles:
            tile_to_sink = random.choice(beach_tiles)
        elif forest_tiles:
            tile_to_sink = random.choice(forest_tiles)
        elif mountain_tiles:
            tile_to_sink = random.choice(mountain_tiles)
        elif volcano_tiles:
            tile_to_sink = random.choice(volcano_tiles)

        if tile_to_sink:
            r, c, tile = self.find_tile_by_id(tile_to_sink.id)
            print(f"Sinking tile {tile.id} ({tile.type}).")
            for v in tile.villagers:
                if v.state == "land":
                    v.state = "water"
                    v.tile = None
                    print(f"  Villager {v.id} from {v.owner} falls into the water!")
            self.board[r][c] = None
        else:
            print("No tiles left to sink.")
        time.sleep(2)

    def creature_phase(self):
        print("--- Creature Phase ---")
        roll = random.randint(1, 6)
        print(f"Creature die roll: {roll}")
        if roll in [1, 2]:
            all_water = []
            for player in self.players:
                for v in player.villagers:
                    if v.state == "water":
                        all_water.append(v)
            if all_water:
                victim = random.choice(all_water)
                victim.state = "dead"
                print(f"Shark attack! Villager {victim.id} from {victim.owner} is killed in the water!")
            else:
                print("No villagers in water for the shark to attack.")
        else:
            print("No creature attack this turn.")
        print("----------------------\n")
        time.sleep(2)

    def all_tiles_sunk(self):
        return not any(tile for row in self.board for tile in row if tile)

    def play(self):
        self.print_introduction()
        self.setup()
        game_over = False

        while not game_over:
            if self.all_tiles_sunk():
                self.game_end_reason = "All tiles have sunk!"
                break

            self.total_turns += 1
            print(f"\n{YELLOW}=========== Turn {self.total_turns} ==========={RESET}")
            self.print_board()

            for player in self.players:
                if self.all_tiles_sunk():
                    self.game_end_reason = "All tiles have sunk!"
                    game_over = True
                    break

                print(f"\n>>> {CYAN}{player.name}'s Turn{RESET} <<<")
                self.player_move_phase(player)
                if self.all_tiles_sunk():
                    self.game_end_reason = "All tiles have sunk!"
                    game_over = True
                    break
                self.sink_tile()
                if self.all_tiles_sunk():
                    self.game_end_reason = "All tiles have sunk!"
                    game_over = True
                    break
                self.creature_phase()

            if self.total_turns >= MAX_TURNS and not game_over:
                self.game_end_reason = "Reached maximum turns (volcano erupts)!"
                game_over = True

        print(f"\n{RED}========== GAME OVER! =========={RESET}")
        if not self.game_end_reason:
            self.game_end_reason = "End condition met."
        print(f"Reason: {self.game_end_reason}\n")

        print("Calculating scores...\n")
        time.sleep(2)
        for player in self.players:
            safe_villagers = [v for v in player.villagers if v.state == "safe"]
            score = sum(v.treasure for v in safe_villagers)
            player.score = score
            print(f"{player.name} rescued {len(safe_villagers)} villagers with total treasure {score}.")
            time.sleep(1)

        winner = max(self.players, key=lambda p: p.score)
        print(f"\nThe winner is {winner.name}!")
        time.sleep(2)

# ---------- Main Execution ----------
if __name__ == "__main__":
    game = Game()
    game.play()

