from __future__ import annotations

import neat
import os
import pickle
import pygame
import sys
import time

from random import randrange
from typing import List, Tuple

pygame.font.init()
pygame.mixer.init(buffer=512)


class Board:
    def __init__(self, size: Tuple[int, int], window: pygame.Surface):
        self.size = size
        self.window = window

    def __contains__(self, position: Tuple[int, int]) -> bool:
        return 0 <= position[0] < self.size[0] and 0 <= position[1] < self.size[1]

    def draw_block(self, position: Tuple[int, int], color: Tuple[int, int, int]) -> None:
        block_width = self.window.get_width() // self.size[0]
        block_height = self.window.get_height() // self.size[1]

        pygame.draw.rect(self.window, color, (position[0] * block_width, position[1] * block_height, block_width, block_height))


class Snake:
    HEAD_COLOR = (191, 141, 65)
    BODY_COLOR_1 = (13, 105, 33)
    BODY_COLOR_2 = (97, 163, 71)
    DIRECTION_UP = (0, -1)
    DIRECTION_DOWN = (0, 1)
    DIRECTION_LEFT = (-1, 0)
    DIRECTION_RIGHT = (1, 0)

    def __init__(self, position: Tuple[int, int], direction: Tuple[int, int]):
        self.body = [position]
        self.direction = direction
        self.extend = 2

    def draw(self, board: Board) -> None:
        board.draw_block(self.body[0], self.HEAD_COLOR)
        for i, position in enumerate(self.body[1:]):
            board.draw_block(position, self.BODY_COLOR_1 if i % 2 == 0 else self.BODY_COLOR_2)

    def move(self) -> None:
        old_head = self.body[0]
        new_head = (old_head[0] + self.direction[0], old_head[1] + self.direction[1])

        if self.extend > 0:
            self.body = [new_head] + self.body
            self.extend -= 1
        else:
            self.body = [new_head] + self.body[:-1]


class Food:
    COLOR = (255, 87, 51)

    def __init__(self, position: Tuple[int, int]):
        self.position = position

    @staticmethod
    def random(board: Board) -> Food:
        return Food((randrange(0, board.size[0]), randrange(0, board.size[1])))

    def draw(self, board: Board) -> None:
        board.draw_block(self.position, self.COLOR)


fast_mode = True

class Game:
    BOARD_COLOR = (243, 236, 219)
    KEY_MAP = {
        pygame.K_UP: Snake.DIRECTION_UP,
        pygame.K_DOWN: Snake.DIRECTION_DOWN,
        pygame.K_LEFT: Snake.DIRECTION_LEFT,
        pygame.K_RIGHT: Snake.DIRECTION_RIGHT,
    }
    POINTS_FONT = pygame.font.SysFont('fsdfds', 30)
    POINTS_COLOR = (191, 141, 65)

    EAT_SOUND = pygame.mixer.Sound(os.path.join('sounds', 'coin.wav'))
    DIE_SOUND = pygame.mixer.Sound(os.path.join('sounds', 'bump.wav'))

    def __init__(self, window_size: Tuple[int, int], board_size: Tuple[int, int], start_position: Tuple[int, int]):
        self.window = pygame.display.set_mode(window_size)
        self.board = Board(board_size, self.window)
        self.start_position = start_position

    def redraw(self, snake: Snake, food: Food, points: int, time_left: int) -> None:
        self.window.fill(self.BOARD_COLOR)
        snake.draw(self.board)
        food.draw(self.board)

        self.window.blit(self.POINTS_FONT.render('Points: %d' % points, 1, self.POINTS_COLOR), (10, 10))
        self.window.blit(self.POINTS_FONT.render('Time Left: %d' % time_left, 1, self.POINTS_COLOR), (10, 30))

        pygame.display.update()

    def play(self, net) -> int:
        snake = Snake(self.start_position, Snake.DIRECTION_DOWN)
        food = Food.random(self.board)
        points = 0
        time_increment = sum(self.board.size)
        time_left = 2 * time_increment

        clock = pygame.time.Clock()

        global fast_mode

        while True:
            if not fast_mode:
                clock.tick(10)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        fast_mode = not fast_mode
                    # elif event.key in self.KEY_MAP:
                    #     direction = self.KEY_MAP[event.key]
                    #     if (snake.direction[0] + direction[0], snake.direction[1] + direction[1]) != (0, 0):
                    #         snake.direction = direction

            snake.move()
            head, *tail = snake.body

            time_left -= 1
            if time_left < 0:
                return points

            points += 0.005

            l = 0
            for x in range(head[0]):
                if (x, head[1]) in snake.body:
                    l = x

            r = self.board.size[0]
            for x in range(self.board.size[0], head[0], -1):
                if (x, head[1]) in snake.body:
                    r = x

            u = 0
            for y in range(head[1]):
                if (head[0], y) in snake.body:
                    u = y

            d = self.board.size[1]
            for y in range(self.board.size[1], head[1], -1):
                if (head[0], y) in snake.body:
                    d = y

            du = head[1] - u
            dd = d - head[1]
            dl = head[0] - l
            dr = r - head[0]

            dx, dy = snake.direction

            data = (du, dd, dl, dr, food.position[0] - head[0], food.position[1] - head[1], dx, dy)

            output = net.activate(data)

            if not fast_mode:
                print('Inputs', data)
                print('Outputs', output)

            directions = [
                [Snake.DIRECTION_DOWN, Snake.DIRECTION_LEFT],
                [Snake.DIRECTION_RIGHT, Snake.DIRECTION_UP],
            ]

            snake.direction = directions[output[0] > 0.5][output[1] > 0.5]

            if head not in self.board or head in tail:
                #self.DIE_SOUND.play()
                #time.sleep(1)
                return points

            if head == food.position:
                self.EAT_SOUND.play()
                points += 1
                snake.extend += 1
                food = Food.random(self.board)
                time_left += time_increment

            self.redraw(snake, food, points, time_left)


def fitness(genomes, config):
    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        if not genome.fitness:
            genome.fitness = 0

        game = Game((800, 600), (40, 30), (5, 5))
        genome.fitness += game.play(net)


def save_population(population):
    with open('population.dat', 'wb') as file:
        pickle.dump(population, file, pickle.HIGHEST_PROTOCOL)


def load_population(file_name):
    with open(file_name, 'rb') as file:
        return pickle.load(file)


def run(config_path, population):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    if not population:
        population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    winner = population.run(fitness, 10000)
    save_population(population)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')

    population = None
    if len(sys.argv) > 1:
        population = load_population(sys.argv[1])

    run(config_path, population)
