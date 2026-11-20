import json
import os
import re

README_PATH = "README.md"
DATA_PATH = "data/tictactoe.json"
REPO = "paazil3rdviz/paazil3rdviz"

START_TAG = "<!-- START_SECTION:tictactoe -->"
END_TAG = "<!-- END_SECTION:tictactoe -->"

WIN_COMBOS = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
    [0, 4, 8], [2, 4, 6]              # Diagonals
]

def check_winner(board):
    for a, b, c in WIN_COMBOS:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    if " " not in board:
        return "draw"
    return None

def minimax(board, depth, is_maximizing):
    res = check_winner(board)
    if res == "O":
        return 10 - depth
    elif res == "X":
        return depth - 10
    elif res == "draw":
        return 0

    if is_maximizing:
        best_score = -float("inf")
        for i in range(9):
            if board[i] == " ":
                board[i] = "O"
                score = minimax(board, depth + 1, False)
                board[i] = " "
                best_score = max(best_score, score)
        return best_score
    else:
        best_score = float("inf")
        for i in range(9):
            if board[i] == " ":
                board[i] = "X"
                score = minimax(board, depth + 1, True)
                board[i] = " "
                best_score = min(best_score, score)
        return best_score

def get_best_bot_move(board):
    best_score = -float("inf")
    best_move = -1
    for i in range(9):
        if board[i] == " ":
            board[i] = "O"
            score = minimax(board, 0, False)
            board[i] = " "
            if score > best_score:
                best_score = score
                best_move = i
    return best_move

def render_board_markdown(state):
    board = state["board"]
    status = state["status"]
    winner = state["winner"]
    last_player = state.get("last_player")

    reset_url = f"https://github.com/{REPO}/issues/new?title=ttc%7Creset&body=Click+'Submit+new+issue'+to+reset+the+game+board."

    def cell_view(idx):
        val = board[idx]
        if val == "X":
            return "❌"
        elif val == "O":
            return "⭕"
        else:
            if status == "in_progress":
                move_url = f"https://github.com/{REPO}/issues/new?title=ttc%7Cmove%7C{idx}&body=Click+'Submit+new+issue'+to+play+your+turn."
                return f"[&nbsp;⬜&nbsp;]({move_url})"
            else:
                return "⬜"

    rows = []
    for r in range(3):
        c0 = cell_view(r * 3)
        c1 = cell_view(r * 3 + 1)
        c2 = cell_view(r * 3 + 2)
        rows.append(f"| {c0} | {c1} | {c2} |")

    table_md = "\n".join([
        "| Col 1 | Col 2 | Col 3 |",
        "| :---: | :---: | :---: |",
        rows[0],
        rows[1],
        rows[2]
    ])

    if status == "in_progress":
        if last_player:
            status_text = f"🎮 <b>Your turn!</b> (Last move by @{last_player}) — Click an empty square `⬜` to play as <b>❌</b>."
        else:
            status_text = "🎮 <b>Your turn!</b> Click any empty square `⬜` to play as <b>❌</b>."
    elif winner == "X":
        status_text = f"🏆 <b>@{last_player} (❌) won the game!</b>"
    elif winner == "O":
        status_text = f"🤖 <b>Tokyo Bot (⭕) won the game!</b> Good match against @{last_player}."
    else:
        status_text = f"🤝 <b>Game ended in a draw!</b> Well played @{last_player}."

    action_bar = f"<br />\n\n{status_text}\n\n<a href=\"{reset_url}\"><img src=\"https://img.shields.io/badge/RESET-GAME_BOARD-1A1B26?style=flat-square&logo=github&logoColor=73DACA\" alt=\"Reset Board\" /></a>\n"

    return f"\n<div align=\"center\">\n\n{table_md}\n{action_bar}\n</div>\n"

def main():
    issue_title = os.environ.get("ISSUE_TITLE", "").strip()
    author = os.environ.get("ISSUE_AUTHOR", "anonymous")

    if not os.path.exists(DATA_PATH):
        state = {"board": [" "] * 9, "status": "in_progress", "winner": None, "last_player": None}
    else:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)

    if issue_title == "ttc|reset":
        state = {"board": [" "] * 9, "status": "in_progress", "winner": None, "last_player": author}
        print("Reset game board.")
    elif issue_title.startswith("ttc|move|"):
        try:
            cell_idx = int(issue_title.split("|")[2])
        except (IndexError, ValueError):
            print("Invalid move index.")
            return

        if state["status"] != "in_progress":
            print("Game already finished. Reset required.")
            return

        if state["board"][cell_idx] != " ":
            print("Cell already occupied.")
            return

        # Player move (X)
        state["board"][cell_idx] = "X"
        state["last_player"] = author
        winner = check_winner(state["board"])

        if winner:
            state["status"] = "finished"
            state["winner"] = winner
        else:
            # Bot move (O)
            bot_move = get_best_bot_move(state["board"])
            if bot_move != -1:
                state["board"][bot_move] = "O"
                bot_winner = check_winner(state["board"])
                if bot_winner:
                    state["status"] = "finished"
                    state["winner"] = bot_winner
    else:
        print("Unrecognized title, skipping.")
        return

    # Save state
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    # Render into README
    board_markdown = render_board_markdown(state)

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme_content = f.read()

    pattern = re.compile(f"{re.escape(START_TAG)}(.*?){re.escape(END_TAG)}", re.DOTALL)
    if not pattern.search(readme_content):
        print("Tic-tac-toe tags not found in README.md")
        return

    updated_readme = pattern.sub(f"{START_TAG}{board_markdown}{END_TAG}", readme_content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_readme)

    print("Tic-Tac-Toe state updated successfully.")

if __name__ == "__main__":
    main()
