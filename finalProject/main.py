from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import threading
import random
import time
from collections import deque
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'qwerty'
# client=MongoClient("mongodb+srv://admin:1234@cluster0.euh9fdb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
# db=client.MazeDB
# collection=db.MazeCollection


example_map = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0],
    [0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0],
    [0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0],
    [0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0],
    [0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0],
    [0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0],
    [0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0],
    [0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0],
    [0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

game_board = []
robot_position = [0, 1]
evil_robot_position = [0, 1]
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


    stars_added = 0
    while stars_added < 3:
        sx = random.randint(1, w - 2)
        sy = random.randint(1, h - 2)
        if maze[sy][sx] == 1:
            maze[sy][sx] = 4
            stars_added += 1

    gears_added = 0
    while gears_added < 5:
        gx = random.randint(1, w - 2)
        gy = random.randint(1, h - 2)
        if maze[gy][gx] == 1 and maze[gy][gx] != 4:
            maze[gy][gx] = 5
            gears_added += 1


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
    collected_star = False
    collected_gear = False
    direction_map = {
        'u': (-1, 0),
        'd': (1, 0),
        'l': (0, -1),
        'r': (0, 1)
    }

    for move in moves[:5]:
        if move == 'n':
            continue
        if move in direction_map:
            dx, dy = direction_map[move]
            new_x = robot_position[0] + dx
            new_y = robot_position[1] + dy

            if 0 <= new_x < len(game_board) and 0 <= new_y < len(game_board[0]) and game_board[new_x][new_y] in [1, 4, 5]:
                robot_position = [new_x, new_y]
                if game_board[new_x][new_y] == 4:
                    collected_star = True
                    game_board[new_x][new_y] = 1

                if game_board[new_x][new_y] == 5:
                    collected_gear = True
                    game_board[new_x][new_y] = 1
            else:
                return False, robot_position, collected_star,collected_gear
            time.sleep(0.5)
    return True, robot_position, collected_star,collected_gear

def spawn_evil_robot():
    global evil_robot_position
    size = len(game_board)
    corners = [
        (size // 2, 0, size, size // 2),
        (size // 2, size // 2, size, size)
    ]
    q = random.choice(corners)
    while True:
        x = random.randint(q[0], q[2] - 1)
        y = random.randint(q[1], q[3] - 1)
        if game_board[x][y] == 1:
            evil_robot_position = [x, y]
            break

def move_evil_robot_step_by_step():
    global evil_robot_position
    ex, ey = evil_robot_position
    px, py = robot_position
    path = bfs_find_path(game_board, (ex, ey), (px, py))

    if path:
        for nx, ny in path[:5]:
            if game_board[nx][ny] == 1:
                evil_robot_position = [nx, ny]
                if evil_robot_position == robot_position:
                    break
                time.sleep(0.5)



def can_see_player(evil_pos, player_pos):
    ex, ey = evil_pos
    px, py = player_pos
    if ex == px:
        step = 1 if ey < py else -1
        for y in range(ey, py + step, step):
            if game_board[ex][y] == 0:
                return False
        return True
    elif ey == py:
        step = 1 if ex < px else -1
        for x in range(ex, px + step, step):
            if game_board[x][ey] == 0:
                return False
        return True
    return False

def bfs_find_path(maze, start, end):
    queue = deque([(start, [])])
    visited = set()
    visited.add(start)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while queue:
        (x, y), path = queue.popleft()
        if (x, y) == end:
            return path
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and maze[ny][nx] == 1 and (nx, ny) not in visited:
                queue.append(((nx, ny), path + [(nx, ny)]))
                visited.add((nx, ny))
    return []

def move_evil_robot():
    global evil_robot_position
    ex, ey = evil_robot_position
    px, py = robot_position
    path = bfs_find_path(game_board, (ex, ey), (px, py))

    if path:
        for nx, ny in path[:5]:
            evil_robot_position = [nx, ny]
            if evil_robot_position == robot_position:
                break
            time.sleep(0.5)
            ex, ey = evil_robot_position
            path = bfs_find_path(game_board, (ex, ey), (px, py))

# def save_user_data(name, size, map_type):
#     collection.insert_one({"name": name, "size": size, "map_type": map_type})
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        size = validate_size(request.form['size'])
        map_type = request.form.get('map_type', 'random')
        session['player_name'] = request.form['name']
        session['size'] = size
        session['map_type'] = map_type

        # save_user_data(session['player_name'], session['size'], session['map_type'])

        return redirect(url_for('board'))
    return render_template('index.html')

@app.route('/board', methods=['GET'])
def board():
    size = session.get('size', 20)
    map_type = session.get('map_type', 'random')
    global game_board, robot_position, evil_robot_position

    session['gear_count'] = 0

    if map_type == 'premade':
        game_board = example_map
        size = 15
        game_board[0][1] = 2
        game_board[size - 2][size - 2] = 3
    else:
        game_board = make_maze(size, size)
        start = (1, 0)
        end = (size - 2, size - 1)

        while not bfs(game_board, start, end):
            game_board = make_maze(size, size)

        game_board[0][1] = 2
        game_board[size - 1][size - 2] = 3
    robot_position = [0, 1]
    spawn_evil_robot()

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
    result, position, collected_star,collected_gear = move_robot_step_by_step(moves)
    if collected_gear:
        session['gear_count'] += 1
    print(f"Blue robot moved to: {position}")
    return jsonify({'result': result, 'position': position, 'evil_position': evil_robot_position, 'collected_star': collected_star, 'collected_gear':collected_gear,'gear_count': session['gear_count']})

@app.route('/move_evil_robot', methods=['POST'])
def move_evil_robot_route():
    move_evil_robot_step_by_step()
    return jsonify({'evil_position': evil_robot_position})


if __name__ == '__main__':
    app.run(debug=True)