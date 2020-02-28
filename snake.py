from __future__ import annotations

import os
import pygame
import time

from random import randrange
from typing import Tuple

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

    def __init__(self, window_size: Tuple[int, int], board_size: Tuple[int, int], snake_position: Tuple[int, int]):
        self.window = pygame.display.set_mode(window_size)
        self.board = Board(board_size, self.window)
        self.snake_position = snake_position

    def redraw(self, snake: Snake, food: Food, points: int) -> None:
        self.window.fill(self.BOARD_COLOR)
        snake.draw(self.board)
        food.draw(self.board)

        self.window.blit(self.POINTS_FONT.render('Points: %d' % points, 1, self.POINTS_COLOR), (10, 10))

        pygame.display.update()

    def play(self) -> int:
        snake = Snake(self.snake_position, Snake.DIRECTION_DOWN)
        food = Food.random(self.board)
        points = 0

        clock = pygame.time.Clock()

        while True:
            clock.tick(10)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key in self.KEY_MAP:
                        direction = self.KEY_MAP[event.key]
                        if (snake.direction[0] + direction[0], snake.direction[1] + direction[1]) != (0, 0):
                            snake.direction = direction

            snake.move()
            head, *tail = snake.body

            if head not in self.board or head in tail:
                self.DIE_SOUND.play()
                time.sleep(1)
                return points

            if head == food.position:
                self.EAT_SOUND.play()
                points += 1
                snake.extend += 1
                food = Food.random(self.board)

            self.redraw(snake, food, points)


if __name__ == '__main__':
    game = Game((800, 600), (80, 60), (10, 10))
    score = game.play()

    print('Finished with score = %d' % score)
