from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import threading
import random
import time

app = Flask(__name__)
app.secret_key = 'qwerty'

game_board = []
board_lock = threading.Lock()
update_thread = None


def validate_size(size):
    try:
        size = int(size)
        if 10 <= size <= 25:
            return size
        else:
            return 20
    except ValueError:
        return 20


def update_board():
    global game_board
    while True:
        time.sleep(1)
        # TEMPORARY. Thread test
        with board_lock:
            for row in game_board:
                for i in range(len(row)):
                    row[i] = 0
            i = random.randint(0, len(game_board) - 1)
            j = random.randint(0, len(game_board[0]) - 1)
            game_board[i][j] = 1
        # TEMPORARY. Thread test


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        size = validate_size(request.form['size'])
        session['player_name'] = request.form['name']
        session['size'] = size
        return redirect(url_for('board'))
    return render_template('index.html')


@app.route('/board', methods=['GET'])
def board():
    size = session.get('size', 20)
    global game_board
    game_board = [[0 for _ in range(size)] for _ in range(size)]
    return render_template('board.html', size=size, name=session.get('player_name'))


@app.route('/start_game', methods=['POST'])
def start_game():
    global update_thread
    if update_thread is None:
        update_thread = threading.Thread(target=update_board)
        update_thread.daemon = True
        update_thread.start()
    return jsonify({'status': 'started'})


@app.route('/get_board')
def get_board():
    with board_lock:
        return jsonify(game_board)


if __name__ == '__main__':
    app.run(debug=True)
