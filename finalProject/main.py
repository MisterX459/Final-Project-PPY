from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import threading
import random
import time
from collections import deque

app = Flask(__name__)
app.secret_key = 'qwerty'

example_map = [
    [1, 1, 1, 0, 0],
    [0, 0, 1, 1, 0],
    [1, 1, 1, 0, 0],
    [0, 0, 0, 1, 1],
    [0, 0, 0, 1, 1]
]

game_board = []
robot_position = [0, 1]
board_lock = threading.Lock()
update_thread = None


def validate_size(size):
    try:
        size = int(size)
        if size < 10:
            size = 11
        elif size > 25:
            size = 25

        if size % 2 == 0:
            size += 1 if size < 25 else -1

        return size
    except ValueError:
        return 11


def make_maze(w, h):
    maze = [[0] * w for _ in range(h)]
    stack = [(1, 1)]
    maze[1][1] = 1

    def valid_neighbours(x, y):
        neighbours = []
        if x > 2 and maze[y][x - 2] == 0:
            neighbours.append((x - 2, y))
        if x < w - 3 and maze[y][x + 2] == 0:
            neighbours.append((x + 2, y))
        if y > 2 and maze[y - 2][x] == 0:
            neighbours.append((x, y - 2))
        if y < h - 3 and maze[y + 2][x] == 0:
            neighbours.append((x, y + 2))
        return neighbours

    while stack:
        x, y = stack[-1]
        neighbours = valid_neighbours(x, y)
        if not neighbours:
            stack.pop()
        else:
            nx, ny = random.choice(neighbours)
            maze[ny][nx] = 1
            maze[(ny + y) // 2][(nx + x) // 2] = 1
            stack.append((nx, ny))

    maze[0][1] = 1
    maze[h - 1][w - 2] = 1

    for i in range(w):
        maze[0][i] = 0
        maze[h - 1][i] = 0
    for j in range(h):
        maze[j][0] = 0
        maze[j][w - 1] = 0

    maze[0][1] = 1
    maze[h - 1][w - 2] = 1

    for _ in range(w * h // 10):
        rx = random.randint(1, w - 2)
        ry = random.randint(1, h - 2)
        if maze[ry][rx] == 0:
            maze[ry][rx] = 1

    return maze

def bfs(maze, start, end):
    queue = deque([start])
    visited = set()
    visited.add(start)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while queue:
        x, y = queue.popleft()
        if (x, y) == end:
            return True
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and maze[ny][nx] == 1 and (nx, ny) not in visited:
                queue.append((nx, ny))
                visited.add((nx, ny))
    return False

def move_robot_step_by_step(moves):
    global robot_position
    direction_map = {
        'u': (-1, 0),
        'd': (1, 0),
        'l': (0, -1),
        'r': (0, 1)
    }

    for move in moves[:5]:  # Process up to 5 moves at a time
        if move == 'n':
            continue
        if move in direction_map:
            dx, dy = direction_map[move]
            new_x = robot_position[0] + dx
            new_y = robot_position[1] + dy

            if 0 <= new_x < len(game_board) and 0 <= new_y < len(game_board[0]) and game_board[new_x][new_y] == 1:
                robot_position = [new_x, new_y]
            else:
                return False, robot_position
            time.sleep(0.5)  # Slow down the movement for step-by-step animation
    return True, robot_position

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        size = validate_size(request.form['size'])
        map_type = request.form.get('map_type', 'random')
        session['player_name'] = request.form['name']
        session['size'] = size
        session['map_type'] = map_type
        return redirect(url_for('board'))
    return render_template('index.html')

@app.route('/board', methods=['GET'])
def board():
    size = session.get('size', 20)
    map_type = session.get('map_type', 'random')
    global game_board, robot_position

    if map_type == 'premade':
        game_board = example_map
    else:
        start = (1, 0)
        end = (size - 2, size - 1)
        game_board = make_maze(size, size)
        while not bfs(game_board, start, end):
            game_board = make_maze(size, size)
        game_board[0][1] = 2
        game_board[size - 1][size - 2] = 3
    robot_position = [0, 1]

    return render_template('board.html', board=game_board, name=session['player_name'])

@app.route('/start_game', methods=['POST'])
def start_game():
    return jsonify({'status': 'started'})

@app.route('/get_board')
def get_board():
    with board_lock:
        return jsonify(game_board)

@app.route('/move', methods=['POST'])
def move():
    moves = request.json.get('moves', [])
    result, position = move_robot_step_by_step(moves)
    return jsonify({'result': result, 'position': position})

if __name__ == '__main__':
    app.run(debug=True)
