import unittest
from datetime import datetime
from flask import Flask, session, json
from main import app, validate_size, make_maze, bfs, move_robot_step_by_step, spawn_evil_robot, can_see_player, \
    evil_robot_position


class MazeAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        with self.app as c:
            with c.session_transaction() as sess:
                sess['player_name'] = 'test_player'
                sess['size'] = 15
                sess['map_type'] = 'random'
                sess['gear_count'] = 0
                sess['star_count'] = 0
                sess['start_time'] = datetime.now()

    def test_index_get(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_index_post(self):
        response = self.app.post('/', data={'name': 'test', 'size': '15', 'map_type': 'random'})
        self.assertEqual(response.status_code, 302)  # Redirect status code

    def test_board_get(self):
        response = self.app.get('/board')
        self.assertEqual(response.status_code, 200)
        data = response.data.decode('utf-8')
        self.assertIn('test_player', data)

    def test_can_see_player(self):
        result = can_see_player((0, 0), (0, 1))
        self.assertIsInstance(result, bool)

    def test_maze_obstacle_generation(self):
        maze = make_maze(15, 15)
        open_paths = sum(cell == 1 for row in maze for cell in row)
        stars = sum(cell == 4 for row in maze for cell in row)
        gears = sum(cell == 5 for row in maze for cell in row)
        self.assertGreater(open_paths, 0, "Maze should have open paths.")
        self.assertEqual(stars, 3, "Maze should have exactly 3 stars.")
        self.assertEqual(gears, 5, "Maze should have exactly 5 gears.")

    def test_robot_wall_collision(self):
        global game_board, robot_position
        game_board = [
            [0, 2, 0],
            [0, 1, 0],
            [0, 0, 0]
        ]
        robot_position = [0, 1]
        moves = ['r']
        result, position, collected_star, collected_gear = move_robot_step_by_step(moves)
        self.assertFalse(result)
        self.assertEqual(position, [0, 1])

    def test_evil_robot_spawn(self):
        global game_board
        game_board = make_maze(15, 15)
        spawn_evil_robot()
        ex, ey = evil_robot_position
        self.assertTrue(game_board[ex][ey] == 1)

    def test_bfs(self):
        maze = make_maze(15, 15)
        result = bfs(maze, (0, 1), (14, 13))
        self.assertIn(result, [True, False])

    def test_make_maze(self):
        maze = make_maze(15, 15)
        self.assertEqual(len(maze), 15)
        self.assertEqual(len(maze[0]), 15)

    def test_start_game_post(self):
        response = self.app.post('/start_game')
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'started')

if __name__ == '__main__':
    unittest.main()
