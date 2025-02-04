from calendar_app import CalendarApp
import os
import sqlite3
import sys
import time
import calendar
from datetime import datetime, timedelta
import random
import psutil
import pygame
from apvia import ApviaApp
from browser import BrowserApp
from ZOffice import ZTextApp, ZDBApp, ZTableApp
from IZ import InfZovApp

# --- SNAKE GAME CLASSES ---
# --- SNAKE GAME CLASSES ---
GRID_SIZE = 20
CELL_SIZE = 30

# --- Enhanced Color Palette ---
SNAKE_HEAD_COLOR = (0, 220, 0)         # Even Brighter Green for head
SNAKE_BODY_COLOR = (80, 200, 80)      # More Distinct Body Color
FOOD_COLOR = (255, 100, 100)         # Slightly Softer Red for food
BACKGROUND_COLOR = (230, 230, 230)     # Softer Light Gray background
GRID_LINE_COLOR = (210, 210, 210)      # Even Fainter Gray for grid lines
GAME_OVER_COLOR = (60, 60, 60, 220)    # Slightly Darker Overlay
SCORE_TEXT_COLOR = (40, 40, 40)        # Darker Grey for score text
GAME_OVER_TEXT_COLOR = (255, 255, 255)           # White for Game Over text
BORDER_COLOR = (20, 20, 20)            # Darker Border for better visibility
PAUSE_OVERLAY_COLOR = (200, 200, 200, 50)
PARTICLE_COLORS = [(255, 200, 0), (255, 150, 0), (255, 100, 0), (255, 50, 0)]


class Snake:
    def __init__(self, start_position):
        self.body = [start_position]
        self.direction = random.choice(
            [(0, -1), (0, 1), (-1, 0), (1, 0)])
        self.next_direction = self.direction
        self.move_timer = 0
        self.move_interval = 0.15
        self.speed_multiplier = 1.0  # Speed multiplier for difficulty levels
        self.particle_effects = []  # List to store particle effects

    def update_speed(self):
        # Adjust interval based on multiplier
        self.move_interval = 0.15 / self.speed_multiplier

    def increase_speed(self, factor):
        self.speed_multiplier *= factor
        self.update_speed()

    def reset_speed(self):
        self.speed_multiplier = 1.0
        self.update_speed()

    def move(self):
        self.direction = self.next_direction
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        self.body.insert(0, new_head)
        removed_segment = self.body.pop()  # Remove tail, store for particle effect
        return removed_segment  # Return removed segment for particle effect

    def create_move_particles(self, position):
        for _ in range(3):  # Create a few particles per move
            offset_x = random.uniform(-CELL_SIZE/4, CELL_SIZE/4)
            offset_y = random.uniform(-CELL_SIZE/4, CELL_SIZE/4)
            start_pos = (position[0] * CELL_SIZE + CELL_SIZE/2 + offset_x,
                         position[1] * CELL_SIZE + CELL_SIZE/2 + offset_y)
            end_pos = (start_pos[0] + random.uniform(-20, 20),
                       start_pos[1] + random.uniform(-20, 20))
            color = random.choice(PARTICLE_COLORS)
            size = random.randint(2, 5)
            duration = random.uniform(0.3, 0.7)
            self.particle_effects.append({'start_pos': start_pos, 'end_pos': end_pos,
                                         'color': color, 'size': size, 'duration': duration, 'time': time.time()})

    def update_particles(self):
        self.particle_effects = [
            p for p in self.particle_effects if time.time() - p['time'] <= p['duration']]

    def draw_particles(self, screen_surface):
        for particle in self.particle_effects:
            progress = (time.time() - particle['time']) / particle['duration']
            current_pos = (particle['start_pos'][0] + (particle['end_pos'][0] - particle['start_pos'][0]) * progress,
                           particle['start_pos'][1] + (particle['end_pos'][1] - particle['start_pos'][1]) * progress)
            pygame.draw.circle(screen_surface, particle['color'], (int(
                current_pos[0]), int(current_pos[1])), particle['size'])

    def grow(self):
        tail_segment = self.body[-1]
        self.body.append(tail_segment)

    def change_direction(self, new_direction):
        if (new_direction[0], new_direction[1]) != (-self.direction[0], -self.direction[1]):
            self.next_direction = new_direction

    def check_collision(self):
        head_x, head_y = self.body[0]
        if not (0 <= head_x < GRID_SIZE and 0 <= head_y < GRID_SIZE):
            return True
        if self.body[0] in self.body[1:]:
            return True
        return False

    def draw(self, screen_surface):
        for index, segment in enumerate(self.body):
            x = segment[0] * CELL_SIZE
            y = segment[1] * CELL_SIZE
            segment_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            color = SNAKE_HEAD_COLOR if index == 0 else SNAKE_BODY_COLOR
            pygame.draw.rect(screen_surface, color, segment_rect,
                             border_radius=5)  # Rounded corners
            pygame.draw.rect(screen_surface, BORDER_COLOR,
                             segment_rect, 1, border_radius=5)


class Food:
    def __init__(self, snake_positions):
        self.position = self.generate_food_position(snake_positions)
        self.respawn_effect_timer = 0
        self.respawn_effect_duration = 0.5
        self.is_respawning = False

    def generate_food_position(self, snake_positions):
        while True:
            position = (random.randint(0, GRID_SIZE - 1),
                        random.randint(0, GRID_SIZE - 1))
            if position not in snake_positions:
                return position

    def respawn(self, snake_positions):
        self.is_respawning = True
        self.respawn_effect_timer = time.time()
        self.position = self.generate_food_position(snake_positions)

    def draw(self, screen_surface):
        x = self.position[0] * CELL_SIZE
        y = self.position[1] * CELL_SIZE
        food_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

        if self.is_respawning:
            time_elapsed = time.time() - self.respawn_effect_timer
            if time_elapsed < self.respawn_effect_duration:
                # Scale down effect
                scale = 1 + 0.5 * (1 - time_elapsed /
                                   self.respawn_effect_duration)
                scaled_size = (int(CELL_SIZE * scale), int(CELL_SIZE * scale))
                scaled_rect = pygame.Rect(0, 0, *scaled_size)
                scaled_rect.center = food_rect.center
                pygame.draw.rect(screen_surface, BACKGROUND_COLOR,
                                 food_rect)  # Clear original area
                pygame.draw.rect(screen_surface, FOOD_COLOR,
                                 scaled_rect, border_radius=5)
                return  # Skip normal draw, continue effect

            self.is_respawning = False  # Effect finished

        pygame.draw.rect(screen_surface, FOOD_COLOR,
                         food_rect, border_radius=5)


class SnakeGameApp:
    def __init__(self, game_font, window_color, text_color, red, black):
        self.width = GRID_SIZE * CELL_SIZE
        self.height = GRID_SIZE * CELL_SIZE
        self.snake = Snake(start_position=(GRID_SIZE // 2, GRID_SIZE // 2))
        self.food = Food(self.snake.body)
        self.score = 0
        self.high_score = self.load_high_score()  # Load high score from file
        self.game_over = False
        self.paused = False
        self.last_move_time = time.time()
        self.move_interval = 0.15
        self.game_font = game_font
        self.window_color = window_color
        self.text_color = text_color
        self.red = red
        self.black = black
        self.running = True
        self.difficulty_level = 1  # 1: Normal, 2: Fast, 3: Very Fast
        self.difficulty_settings = {
            1: {'speed_multiplier': 1.0, 'label': 'Нормально'},
            2: {'speed_multiplier': 1.5, 'label': 'Быстро'},
            3: {'speed_multiplier': 2.0, 'label': 'Очень быстро'}
        }

    def load_high_score(self):
        try:
            with open("snake_highscore.txt", "r") as f:
                return int(f.read())
        except FileNotFoundError:
            return 0
        except ValueError:  # In case file is corrupted
            return 0

    def save_high_score(self):
        with open("snake_highscore.txt", "w") as f:
            f.write(str(self.high_score))

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if not self.game_over and not self.paused:
                        if event.key == pygame.K_UP:
                            self.snake.change_direction((0, -1))
                        elif event.key == pygame.K_DOWN:
                            self.snake.change_direction((0, 1))
                        elif event.key == pygame.K_LEFT:
                            self.snake.change_direction((-1, 0))
                        elif event.key == pygame.K_RIGHT:
                            self.snake.change_direction((1, 0))
                        elif event.key == pygame.K_p:
                            self.paused = True
                        elif event.key == pygame.K_1:
                            self.set_difficulty(1)
                        elif event.key == pygame.K_2:
                            self.set_difficulty(2)
                        elif event.key == pygame.K_3:
                            self.set_difficulty(3)
                    elif self.game_over:
                        if event.key == pygame.K_r:
                            self.restart_game()
                    elif self.paused:
                        if event.key == pygame.K_p:
                            self.paused = False

            if not self.game_over and not self.paused:
                if time.time() - self.last_move_time >= self.snake.move_interval:
                    removed_segment = self.snake.move()  # Get removed segment position
                    self.snake.create_move_particles(
                        removed_segment)  # Create particles at tail
                    self.update_game()
                    self.last_move_time = time.time()

            screen_surface = pygame.Surface(
                (self.width, self.height), pygame.SRCALPHA)  # Add SRCALPHA flag
            screen_surface.fill(BACKGROUND_COLOR)
            self.draw_game(screen_surface)
            yield screen_surface

    def set_difficulty(self, level):
        if level in self.difficulty_settings:
            self.difficulty_level = level
            self.snake.speed_multiplier = self.difficulty_settings[level]['speed_multiplier']
            self.snake.update_speed()

    def update_game(self):
        self.snake.update_particles()  # Update particle positions

        if self.snake.check_collision():
            self.game_over = True
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            return

        if self.snake.body[0] == self.food.position:
            self.snake.grow()
            self.food.respawn(self.snake.body)
            self.score += 1
            # Very slight speed increase on eating
            self.snake.increase_speed(1.005)

    def draw_game(self, screen_surface):
        for x in range(0, self.width, CELL_SIZE):
            pygame.draw.line(screen_surface, GRID_LINE_COLOR,
                             (x, 0), (x, self.height))
        for y in range(0, self.height, CELL_SIZE):
            pygame.draw.line(screen_surface, GRID_LINE_COLOR,
                             (0, y), (self.width, y))

        self.food.draw(screen_surface)
        self.snake.draw(screen_surface)
        self.snake.draw_particles(screen_surface)  # Draw particles

        self.draw_score(screen_surface)

        if self.game_over:
            self.draw_game_over(screen_surface)
        if self.paused:
            self.draw_pause_screen(screen_surface)

    def draw_score(self, screen_surface):
        score_text_surface = self.game_font.render(
            f"Счет: {self.score}  Рекорд: {self.high_score}", True, SCORE_TEXT_COLOR)
        difficulty_text_surface = self.game_font.render(
            f"Уровень сложности: {self.difficulty_settings[self.difficulty_level]['label']}", True, SCORE_TEXT_COLOR)
        screen_surface.blit(score_text_surface, (10, 10))
        screen_surface.blit(difficulty_text_surface,
                            (10, 40))  # Position below score

    def draw_game_over(self, screen_surface):
        overlay = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA)
        overlay.fill(GAME_OVER_COLOR)
        screen_surface.blit(overlay, (0, 0))

        game_over_text = self.game_font.render(
            "Игра окончена!", True, GAME_OVER_TEXT_COLOR)
        restart_text = self.game_font.render(
            "Нажмите 'R' для перезапуска", True, GAME_OVER_TEXT_COLOR)
        final_score_text = self.game_font.render(
            f"Ваш счет: {self.score}, Рекорд: {self.high_score}", True, GAME_OVER_TEXT_COLOR)

        text_x = self.width // 2
        text_y_start = self.height // 2 - 80  # Shifted up slightly
        line_height = 40

        game_over_rect = game_over_text.get_rect(center=(text_x, text_y_start))
        final_score_rect = final_score_text.get_rect(
            # Score below game over
            center=(text_x, text_y_start + line_height))
        restart_rect = restart_text.get_rect(
            # Restart prompt below score
            center=(text_x, text_y_start + 2 * line_height))

        screen_surface.blit(game_over_text, game_over_rect)
        screen_surface.blit(final_score_text, final_score_rect)
        screen_surface.blit(restart_text, restart_rect)

    def draw_pause_screen(self, screen_surface):
        overlay = pygame.Surface(
            # Make overlay transparent
            (self.width, self.height), pygame.SRCALPHA)
        overlay.fill(PAUSE_OVERLAY_COLOR)  # Light semi-transparent overlay
        screen_surface.blit(overlay, (0, 0))

        pause_text = self.game_font.render(
            "Пауза - нажмите 'P' для продолжения", True, SCORE_TEXT_COLOR)
        text_rect = pause_text.get_rect(
            center=(self.width // 2, self.height // 2))
        screen_surface.blit(pause_text, text_rect)

    def restart_game(self):
        self.snake = Snake(start_position=(GRID_SIZE // 2, GRID_SIZE // 2))
        self.food = Food(self.snake.body)
        self.score = 0
        self.game_over = False
        self.paused = False
        self.last_move_time = time.time()
        self.snake.reset_speed()  # Reset speed on restart

    def handle_event(self, event, window_rect):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            if not self.game_over and not self.paused:
                if event.key == pygame.K_UP:
                    self.snake.change_direction((0, -1))
                elif event.key == pygame.K_DOWN:
                    self.snake.change_direction((0, 1))
                elif event.key == pygame.K_LEFT:
                    self.snake.change_direction((-1, 0))
                elif event.key == pygame.K_RIGHT:
                    self.snake.change_direction((1, 0))
                elif event.key == pygame.K_p:
                    self.paused = True
                elif event.key == pygame.K_1:
                    self.set_difficulty(1)
                elif event.key == pygame.K_2:
                    self.set_difficulty(2)
                elif event.key == pygame.K_3:
                    self.set_difficulty(3)
            elif self.game_over:
                if event.key == pygame.K_r:
                    self.restart_game()
            elif self.paused:
                if event.key == pygame.K_p:
                    self.paused = False

    def stop_running(self):
        self.running = False
# --- END SNAKE GAME CLASSES ---


# --- MINESWEEPER GAME CLASSES ---
BOARD_SIZE = 10
NUM_MINES = 15
CELL_SIZE_MINESWEEPER = 40

CELL_COVERED = -1
CELL_EMPTY = 0
CELL_MINE = 9
CELL_FLAGGED = 10

# --- Redesigned Colors ---
MINESWEEPER_COVERED_GRAY = (170, 170, 170)  # Slightly darker for covered cells
MINESWEEPER_UNCOVERED_GRAY = (230, 230, 230)  # Lighter for uncovered cells
MINE_BLACK = (30, 30, 30)  # Darker mine color
FLAG_RED = (230, 0, 0)    # Brighter flag color
GRID_LINE_COLOR = (140, 140, 140)  # Grid lines for better definition
NUMBER_COLORS = [(0, 0, 220),     # 1 - Darker blue
                 (0, 120, 0),     # 2 - Darker green
                 (220, 0, 0),     # 3 - Darker red
                 (0, 0, 120),     # 4 - Darker dark blue
                 (120, 0, 0),     # 5 - Darker dark red
                 (0, 220, 220),   # 6 - Darker cyan
                 (60, 60, 60),    # 7 - Darker grey
                 (120, 120, 120)]  # 8 - Slightly lighter grey

# --- Load Icons ---
try:
    # Replace with your flag icon path
    FLAG_ICON = pygame.image.load("images/flag_icon.png")
    # Replace with your mine icon path
    MINE_ICON = pygame.image.load("images/mine_icon.png")
    FLAG_ICON = pygame.transform.scale(
        # Scale icons
        # Slightly smaller icons
        FLAG_ICON, (CELL_SIZE_MINESWEEPER - 8, CELL_SIZE_MINESWEEPER - 8))
    MINE_ICON = pygame.transform.scale(
        # Scale icons
        # Slightly smaller icons
        MINE_ICON, (CELL_SIZE_MINESWEEPER - 8, CELL_SIZE_MINESWEEPER - 8))
except FileNotFoundError:
    FLAG_ICON = None
    MINE_ICON = None
    print("Warning: Flag or Mine icons not found. Using text/shapes instead.")


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.state = CELL_COVERED
        self.is_mine = False
        self.adjacent_mines = 0
        self.reveal_animation_timer = 0
        self.reveal_animation_duration = 0.2
        self.is_revealing = False
        self.flag_animation_timer = 0
        self.flag_animation_duration = 0.15
        self.is_flagging = False

    def reveal(self):
        if self.state == CELL_COVERED or self.state == CELL_FLAGGED:
            if not self.is_revealing:  # Prevent overlapping animations
                self.is_revealing = True
                self.reveal_animation_timer = time.time()
                if self.is_mine:
                    self.state = CELL_MINE
                else:
                    self.state = self.adjacent_mines
                return True
        return False

    def flag(self):
        if self.state == CELL_COVERED:
            if not self.is_flagging:  # Prevent overlapping animations
                self.is_flagging = True
                self.flag_animation_timer = time.time()
                self.state = CELL_FLAGGED
                return True
        elif self.state == CELL_FLAGGED:
            if not self.is_flagging:  # Prevent overlapping animations
                self.is_flagging = True
                self.flag_animation_timer = time.time()
                self.state = CELL_COVERED
                return True
        return False

    def draw(self, screen_surface, x, y, game_font, black):
        rect = pygame.Rect(x, y, CELL_SIZE_MINESWEEPER, CELL_SIZE_MINESWEEPER)

        if self.state == CELL_COVERED:
            pygame.draw.rect(screen_surface, MINESWEEPER_COVERED_GRAY, rect)
            pygame.draw.rect(screen_surface, GRID_LINE_COLOR, rect, 1)
        elif self.state == CELL_FLAGGED:
            pygame.draw.rect(screen_surface, MINESWEEPER_COVERED_GRAY, rect)
            pygame.draw.rect(screen_surface, GRID_LINE_COLOR, rect, 1)
            if FLAG_ICON:
                icon_rect = FLAG_ICON.get_rect(center=rect.center)
                if self.is_flagging:  # Flag animation
                    time_elapsed = time.time() - self.flag_animation_timer
                    if time_elapsed < self.flag_animation_duration:
                        # Scale up effect
                        scale = 1 + 0.3 * \
                            (1 - time_elapsed / self.flag_animation_duration)
                        scaled_size = (
                            int(FLAG_ICON.get_width() * scale), int(FLAG_ICON.get_height() * scale))
                        scaled_icon = pygame.transform.scale(
                            FLAG_ICON, scaled_size)
                        scaled_icon_rect = scaled_icon.get_rect(
                            center=rect.center)
                        screen_surface.blit(scaled_icon, scaled_icon_rect)
                        return  # Skip normal draw, continue animation
                    self.is_flagging = False  # Animation finished

                screen_surface.blit(FLAG_ICON, icon_rect)
            else:
                pygame.draw.polygon(screen_surface, FLAG_RED, [(x + 10, y + 5), (x + CELL_SIZE_MINESWEEPER - 10, y + 5),
                                                               (x + CELL_SIZE_MINESWEEPER - 10,
                                                                y + CELL_SIZE_MINESWEEPER - 15),
                                                               (x + CELL_SIZE_MINESWEEPER // 2,
                                                                y + CELL_SIZE_MINESWEEPER - 15),
                                                               (x + CELL_SIZE_MINESWEEPER // 2,
                                                                y + CELL_SIZE_MINESWEEPER - 5),
                                                               (x + 10, y + CELL_SIZE_MINESWEEPER - 5)])
                pygame.draw.line(screen_surface, black, (x + CELL_SIZE_MINESWEEPER - 10, y + 5),
                                 (x + CELL_SIZE_MINESWEEPER - 10, y + CELL_SIZE_MINESWEEPER - 15), 2)

        elif self.state == CELL_MINE:
            pygame.draw.rect(screen_surface, MINESWEEPER_UNCOVERED_GRAY, rect)
            pygame.draw.rect(screen_surface, GRID_LINE_COLOR, rect, 1)
            if MINE_ICON:
                icon_rect = MINE_ICON.get_rect(center=rect.center)
                screen_surface.blit(MINE_ICON, icon_rect)
            else:
                pygame.draw.circle(screen_surface, MINE_BLACK,
                                   rect.center, CELL_SIZE_MINESWEEPER // 3)
        elif self.state > CELL_EMPTY and self.state < CELL_MINE:
            pygame.draw.rect(screen_surface, MINESWEEPER_UNCOVERED_GRAY, rect)
            pygame.draw.rect(screen_surface, GRID_LINE_COLOR, rect, 1)

            if self.is_revealing:  # Reveal animation
                time_elapsed = time.time() - self.reveal_animation_timer
                if time_elapsed < self.reveal_animation_duration:
                    # Fade-in effect
                    alpha = int(
                        255 * (time_elapsed / self.reveal_animation_duration))
                    overlay = pygame.Surface(
                        (CELL_SIZE_MINESWEEPER, CELL_SIZE_MINESWEEPER), pygame.SRCALPHA)
                    # Apply alpha to uncovered color
                    overlay.fill(
                        (MINESWEEPER_UNCOVERED_GRAY[0], MINESWEEPER_UNCOVERED_GRAY[1], MINESWEEPER_UNCOVERED_GRAY[2], alpha))
                    screen_surface.blit(overlay, rect.topleft)
                    number_color = NUMBER_COLORS[self.state - 1]
                    text_surface = game_font.render(
                        str(self.state), True, number_color)
                    text_rect = text_surface.get_rect(center=rect.center)
                    screen_surface.blit(text_surface, text_rect)
                    return  # Skip normal draw, continue animation
                self.is_revealing = False  # Animation finished

            number_color = NUMBER_COLORS[self.state - 1]
            text_surface = game_font.render(
                str(self.state), True, number_color)
            text_rect = text_surface.get_rect(center=rect.center)
            screen_surface.blit(text_surface, text_rect)
        elif self.state == CELL_EMPTY:
            pygame.draw.rect(screen_surface, MINESWEEPER_UNCOVERED_GRAY, rect)
            pygame.draw.rect(screen_surface, GRID_LINE_COLOR, rect, 1)


class MinesweeperApp:
    def __init__(self):
        self.width = BOARD_SIZE * CELL_SIZE_MINESWEEPER
        self.height = BOARD_SIZE * CELL_SIZE_MINESWEEPER
        self.board = [[Cell(row, col) for col in range(BOARD_SIZE)]
                      for row in range(BOARD_SIZE)]
        self.num_mines = NUM_MINES
        self.mines_placed = False
        self.first_click = True
        self.game_over = False
        self.game_won = False
        self.running = True
        self.game_font = None
        self.start_time = 0
        self.game_time = 0
        self.timer_running = False
        self.difficulty_level = 1  # 1: Beginner, 2: Intermediate, 3: Expert
        self.difficulty_settings = {
            1: {'board_size': 10, 'num_mines': 15, 'label': 'Новичок'},
            2: {'board_size': 16, 'num_mines': 40, 'label': 'Средний'},
            3: {'board_size': 22, 'num_mines': 99, 'label': 'Эксперт'}
        }
        self.flags_placed = 0

    def reset_game(self):
        self.board = [[Cell(row, col) for col in range(BOARD_SIZE)]
                      for row in range(BOARD_SIZE)]
        self.num_mines = NUM_MINES
        self.mines_placed = False
        self.first_click = True
        self.game_over = False
        self.game_won = False
        self.running = True
        self.start_time = 0
        self.game_time = 0
        self.timer_running = False
        self.flags_placed = 0

    def set_difficulty(self, level):
        if level in self.difficulty_settings:
            setting = self.difficulty_settings[level]
            global BOARD_SIZE, NUM_MINES  # Modify global constants
            BOARD_SIZE = setting['board_size']
            NUM_MINES = setting['num_mines']
            self.width = BOARD_SIZE * CELL_SIZE_MINESWEEPER
            self.height = BOARD_SIZE * CELL_SIZE_MINESWEEPER
            self.reset_game()  # Reset game with new settings

    def run(self, events, screen_surface, game_font, window_color, text_color, red, green, black):
        self.game_font = game_font

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                # Restart on 'R'
                if event.key == pygame.K_r and (self.game_over or self.game_won):
                    self.reset_game()
                if event.key == pygame.K_1:
                    self.set_difficulty(1)
                if event.key == pygame.K_2:
                    self.set_difficulty(2)
                if event.key == pygame.K_3:
                    self.set_difficulty(3)

            if not self.game_over and not self.game_won:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    cell_x = event.pos[0] // CELL_SIZE_MINESWEEPER
                    cell_y = event.pos[1] // CELL_SIZE_MINESWEEPER
                    if 0 <= cell_x < BOARD_SIZE and 0 <= cell_y < BOARD_SIZE:
                        clicked_cell = self.board[cell_y][cell_x]
                        if event.button == 1:  # Left click
                            if self.first_click:
                                self.place_mines(clicked_cell)
                                self.first_click = False
                                self.timer_running = True  # Start timer on first click
                                self.start_time = time.time()
                            self.handle_click(clicked_cell)
                        elif event.button == 3:  # Right click
                            self.handle_flag(clicked_cell)

        if self.timer_running and not self.game_over and not self.game_won:
            self.game_time = time.time() - self.start_time

        screen_surface.fill(window_color)
        self.draw_board(screen_surface, game_font, black)
        # Draw timer, mine count etc.
        self.draw_hud(screen_surface, game_font, text_color)

        if self.game_over:
            draw_text(screen_surface, "Игра окончена!", game_font, red,
                      (self.width // 2, self.height // 2 - 50), 'center')
            draw_text(screen_surface, "Нажмите 'R' для перезапуска", game_font, text_color,
                      # Restart instruction
                      (self.width // 2, self.height // 2 + 10), 'center')
            self.timer_running = False  # Stop timer when game over

        if self.game_won:
            draw_text(screen_surface, "Вы выиграли!", game_font, green,
                      (self.width // 2, self.height // 2 - 50), 'center')
            draw_text(screen_surface, "Нажмите 'R' для перезапуска", game_font, text_color,
                      # Restart instruction
                      (self.width // 2, self.height // 2 + 10), 'center')
            self.timer_running = False  # Stop timer when game won

        yield screen_surface

    def draw_hud(self, screen_surface, game_font, text_color):
        timer_text = f"Время: {
            int(self.game_time)}" if self.timer_running else "Время: 0"
        flags_text = f"Флаги: {self.flags_placed}/{self.num_mines}"
        difficulty_label = f"Уровень сложности: {
            self.difficulty_settings[self.difficulty_level]['label']} (1-Новичок, 2-Средний, 3-Эксперт)"

        draw_text(screen_surface, timer_text, game_font,
                  text_color, (10, 10), 'topleft')
        draw_text(screen_surface, flags_text, game_font, text_color,
                  (10, 40), 'topleft')  # Flags below timer
        draw_text(screen_surface, difficulty_label, game_font,
                  text_color, (10, 70), 'topleft')  # Difficulty below flags

    def handle_click(self, cell):
        if cell.state == CELL_COVERED:
            if cell.is_mine:
                self.game_over = True
                self.timer_running = False  # Stop timer on game over
                self.reveal_all_mines()
            else:
                if cell.adjacent_mines == 0:
                    self.reveal_empty_cells(cell)
                else:
                    cell.reveal()
                if self.check_win_condition():
                    self.game_won = True
                    self.timer_running = False  # Stop timer on win

    def handle_flag(self, cell):
        if cell.state == CELL_COVERED:
            cell.flag()
            self.flags_placed += 1
        elif cell.state == CELL_FLAGGED:
            cell.flag()
            self.flags_placed -= 1

    def place_mines(self, initial_click_cell):
        mines_placed = 0
        possible_mine_positions = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] != initial_click_cell:
                    possible_mine_positions.append(self.board[r][c])

        random.shuffle(possible_mine_positions)

        for i in range(min(self.num_mines, len(possible_mine_positions))):
            possible_mine_positions[i].is_mine = True

        self.calculate_adjacent_mines()
        self.mines_placed = True

    def calculate_adjacent_mines(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if not self.board[r][c].is_mine:
                    mines_count = 0
                    for row_offset in range(-1, 2):
                        for col_offset in range(-1, 2):
                            if row_offset == 0 and col_offset == 0:
                                continue
                            neighbor_row, neighbor_col = r + row_offset, c + col_offset
                            if 0 <= neighbor_row < BOARD_SIZE and 0 <= neighbor_col < BOARD_SIZE and self.board[neighbor_row][neighbor_col].is_mine:
                                mines_count += 1
                    self.board[r][c].adjacent_mines = mines_count

    def reveal_empty_cells(self, cell):
        if cell.state != CELL_COVERED or cell.is_mine:
            return

        cell.reveal()
        if cell.adjacent_mines == 0:
            for row_offset in range(-1, 2):
                for col_offset in range(-1, 2):
                    if row_offset == 0 and col_offset == 0:
                        continue
                    neighbor_row, neighbor_col = cell.row + row_offset, cell.col + col_offset
                    if 0 <= neighbor_row < BOARD_SIZE and 0 <= neighbor_col < BOARD_SIZE:
                        self.reveal_empty_cells(
                            self.board[neighbor_row][neighbor_col])

    def reveal_all_mines(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c].is_mine:
                    self.board[r][c].reveal()

    def check_win_condition(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                cell = self.board[r][c]
                if not cell.is_mine and cell.state == CELL_COVERED:
                    return False
        return True

    def draw_board(self, screen_surface, game_font, black):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                cell = self.board[r][c]
                cell.draw(screen_surface, c * CELL_SIZE_MINESWEEPER,
                          r * CELL_SIZE_MINESWEEPER, game_font, black)

    def stop_running(self):
        self.running = False

    def handle_event(self, event, window_rect):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            # Restart on 'R'
            if event.key == pygame.K_r and (self.game_over or self.game_won):
                self.reset_game()
            if event.key == pygame.K_1:
                self.set_difficulty(1)
            if event.key == pygame.K_2:
                self.set_difficulty(2)
            if event.key == pygame.K_3:
                self.set_difficulty(3)
        if event.type == pygame.MOUSEBUTTONDOWN:
            relative_mouse_pos = (
                event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
            cell_x = relative_mouse_pos[0] // CELL_SIZE_MINESWEEPER
            cell_y = relative_mouse_pos[1] // CELL_SIZE_MINESWEEPER
            if 0 <= cell_x < BOARD_SIZE and 0 <= cell_y < BOARD_SIZE:
                clicked_cell = self.board[cell_y][cell_x]
                if event.button == 1:  # Left click
                    if self.first_click:
                        self.place_mines(clicked_cell)
                        self.first_click = False
                        self.timer_running = True  # Start timer on first click
                        self.start_time = time.time()
                    self.handle_click(clicked_cell)
                elif event.button == 3:  # Right click
                    self.handle_flag(clicked_cell)


class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 10, 100)
        self.speed = 5

    def move(self, direction):
        if direction == "up":
            self.rect.y -= self.speed
        elif direction == "down":
            self.rect.y += self.speed

        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > screen_height - taskbar_height:  # Используем taskbar_height
            self.rect.bottom = screen_height - taskbar_height

    def draw(self, screen_surface, color):
        pygame.draw.rect(screen_surface, color, self.rect)


class Ball:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 15, y - 15, 30, 30)
        self.speed_x = 5 * random.choice([-1, 1])
        self.speed_y = 5 * random.choice([-1, 1])

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.top < 0 or self.rect.bottom > screen_height - taskbar_height:  # Используем taskbar_height
            self.speed_y *= -1

    def draw(self, screen_surface, color):
        pygame.draw.ellipse(screen_surface, color, self.rect)


class PongGameApp:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.player1_score = 0
        self.player2_score = 0
        # Используем self.height
        self.paddle1 = Paddle(50, self.height // 2 - 50)
        # Используем self.width и корректируем позицию
        self.paddle2 = Paddle(self.width - 60, self.height // 2 - 50)
        # Используем self.width и self.height
        self.ball = Ball(self.width // 2, self.height // 2)
        self.game_font = game_font
        self.running = True
        # Флаг для предотвращения многократного счета за один выход мяча за границу
        self.score_counted = False

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                self.paddle1.move("up")
            if keys[pygame.K_s]:
                self.paddle1.move("down")
            if keys[pygame.K_UP]:
                self.paddle2.move("up")
            if keys[pygame.K_DOWN]:
                self.paddle2.move("down")

            self.ball.move()

            if self.ball.rect.colliderect(self.paddle1.rect) and self.ball.speed_x < 0:
                self.ball.speed_x *= -1
            if self.ball.rect.colliderect(self.paddle2.rect) and self.ball.speed_x > 0:
                self.ball.speed_x *= -1

            if self.ball.rect.left < 0:
                if not self.score_counted:  # Проверяем флаг
                    self.player2_score += 1
                    self.score_counted = True  # Устанавливаем флаг, чтобы избежать повторного счета
                    self.ball = Ball(self.width // 2, self.height // 2)
            elif self.ball.rect.right > self.width:
                if not self.score_counted:  # Проверяем флаг
                    self.player1_score += 1
                    self.score_counted = True  # Устанавливаем флаг, чтобы избежать повторного счета
                    self.ball = Ball(self.width // 2, self.height // 2)
            elif 0 < self.ball.rect.centerx < self.width:  # Сбрасываем флаг, когда мяч в игре
                self.score_counted = False

            screen_surface = pygame.Surface((self.width, self.height))
            screen_surface.fill(window_color)
            self.draw_game(screen_surface)
            yield screen_surface  # Use generator to yield the surface

    def draw_game(self, screen_surface):
        self.paddle1.draw(screen_surface, text_color)
        self.paddle2.draw(screen_surface, text_color)
        self.ball.draw(screen_surface, text_color)

        draw_text(screen_surface, str(self.player1_score),
                  self.game_font, text_color, (self.width // 4, 50), 'center')
        draw_text(screen_surface, str(self.player2_score), self.game_font,
                  text_color, (self.width * 3 // 4, 50), 'center')
        pygame.draw.aaline(screen_surface, text_color,
                           (self.width // 2, 0), (self.width // 2, self.height))

    def handle_event(self, event, window_rect):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False

    def stop_running(self):
        self.running = False
# --- END PONG GAME CLASSES ---


GRID_WIDTH = 10
GRID_HEIGHT = 20
BLOCK_SIZE = 30
SIDE_BAR_WIDTH = 200  # Width for score, next shape etc.
GAME_WIDTH = GRID_WIDTH * BLOCK_SIZE + SIDE_BAR_WIDTH
GAME_HEIGHT = GRID_HEIGHT * BLOCK_SIZE

SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1, 1], [0, 0, 1]],  # L
    [[1, 1, 1], [1, 0, 0]],  # J
    [[1, 1], [1, 1]],  # O
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]],  # Z
    [[1, 1, 1], [0, 1, 0]]   # T
]
SHAPE_COLORS = [
    (0, 255, 255),  # Cyan
    (255, 165, 0),  # Orange
    (0, 0, 255),   # Blue
    (255, 255, 0),  # Yellow
    (0, 255, 0),   # Green
    (255, 0, 0),   # Red
    (128, 0, 128)  # Purple
]

# --- FONTS ---
game_font = pygame.font.Font(None, 20)  # Use default font, size 30


class Block:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
        self.color = color

    def draw(self, screen_surface):
        pygame.draw.rect(screen_surface, self.color, self.rect)
        pygame.draw.rect(screen_surface, black, self.rect, 1)  # Draw border


class Shape:
    def __init__(self, shape_type):
        self.shape_type = shape_type
        self.blocks = []
        self.color = SHAPE_COLORS[SHAPES.index(shape_type)]
        self.rotation_index = 0
        # Center shape at the top
        self.x = GRID_WIDTH // 2 - len(shape_type[0]) // 2
        self.y = 0
        self._create_blocks()

    def _create_blocks(self):
        self.blocks = []
        current_shape = self.get_current_rotation()
        for row_index, row in enumerate(current_shape):
            for col_index, cell in enumerate(row):
                if cell == 1:
                    x = (self.x + col_index) * BLOCK_SIZE
                    y = (self.y + row_index) * BLOCK_SIZE
                    self.blocks.append(Block(x, y, self.color))

    def get_current_rotation(self):
        rotated_shape = self.shape_type
        for _ in range(self.rotation_index):
            # Rotate 90 degrees clockwise - standard matrix rotation. Corrected rotation logic!
            rotated_shape = list(zip(*rotated_shape[::-1]))
        return rotated_shape

    def draw(self, screen_surface):
        for block in self.blocks:
            block.draw(screen_surface)

    def move(self, dx, dy, grid):
        if not self.check_collision(dx, dy, grid):
            self.x += dx
            self.y += dy
            self._create_blocks()  # Re-create blocks after moving
            return True
        return False

    def rotate(self, grid):
        original_rotation_index = self.rotation_index
        # Cycle through 4 rotations
        self.rotation_index = (self.rotation_index + 1) % 4
        if self.check_collision(0, 0, grid):
            # Try wall kick - move left or right if rotation causes collision
            if not self._try_wall_kick(grid):
                # Revert rotation if wall kick fails as well
                self.rotation_index = original_rotation_index
        self._create_blocks()  # Re-create blocks after rotation

    def _try_wall_kick(self, grid):
        # Try to move left then right to see if rotation can be valid
        wall_kick_offsets = [-1, 1, -2, 2]  # Example offsets, can be adjusted
        for offset in wall_kick_offsets:
            self.x += offset
            if not self.check_collision(0, 0, grid):
                return True  # Wall kick successful
            self.x -= offset  # Revert offset if kick fails
        return False  # No valid wall kick found

    def check_collision(self, dx, dy, grid):
        temp_x = self.x + dx
        temp_y = self.y + dy
        rotated_shape = self.get_current_rotation()

        for row_index, row in enumerate(rotated_shape):
            for col_index, cell in enumerate(row):
                if cell == 1:
                    grid_x = temp_x + col_index
                    grid_y = temp_y + row_index

                    if grid_x < 0 or grid_x >= GRID_WIDTH or grid_y >= GRID_HEIGHT:
                        return True  # Out of bounds on grid edges
                    # Check for block below
                    # Added grid_y >= 0 check and grid_x range check
                    if 0 <= grid_y < GRID_HEIGHT and 0 <= grid_x < GRID_WIDTH and grid_y >= 0 and grid.grid_cells[grid_y][grid_x] is not None:
                        return True  # Collision with existing block
        return False


class Grid:
    def __init__(self):
        self.grid_cells = [[None for _ in range(
            # Initialize grid with None
            GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

    def draw(self, screen_surface):
        for y_index, row in enumerate(self.grid_cells):
            for x_index, block in enumerate(row):
                if block is not None:
                    block.rect.x = x_index * BLOCK_SIZE
                    block.rect.y = y_index * BLOCK_SIZE
                    block.draw(screen_surface)
                else:  # Draw grid lines for empty cells
                    rect = pygame.Rect(
                        x_index * BLOCK_SIZE, y_index * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                    pygame.draw.rect(screen_surface, light_gray,
                                     rect, 1)  # Light gray grid lines

    def place_shape(self, shape):
        for block in shape.blocks:
            grid_x = block.rect.x // BLOCK_SIZE
            grid_y = block.rect.y // BLOCK_SIZE
            if 0 <= grid_y < GRID_HEIGHT and 0 <= grid_x < GRID_WIDTH:  # Boundary check again for safety
                self.grid_cells[grid_y][grid_x] = block  # Place block in grid

    def clear_lines(self):
        lines_cleared = 0
        full_rows = []
        for y_index, row in enumerate(self.grid_cells):
            if all(cell is not None for cell in row):  # Check if all cells in row are filled
                full_rows.append(y_index)

        if full_rows:
            lines_cleared = len(full_rows)
            for row_index in full_rows:
                del self.grid_cells[row_index]  # Remove full row
                # Add new empty row at the top - Tetris logic
                self.grid_cells.insert(0, [None for _ in range(GRID_WIDTH)])
            # Move blocks above cleared rows down
            self._adjust_blocks_down(full_rows)
        return lines_cleared

    def _adjust_blocks_down(self, cleared_rows):
        # Process cleared rows from bottom to top to avoid index issues
        cleared_rows.sort(reverse=True)
        for cleared_row_index in cleared_rows:
            # Iterate rows above cleared row
            for y_index in range(cleared_row_index - 1, -1, -1):
                for x_index in range(GRID_WIDTH):
                    if self.grid_cells[y_index][x_index] is not None:
                        # Move block down
                        self.grid_cells[y_index +
                                        1][x_index] = self.grid_cells[y_index][x_index]
                        # Clear original position
                        self.grid_cells[y_index][x_index] = None
                        # Update block's rect if moved
                        if self.grid_cells[y_index+1][x_index] is not None:
                            self.grid_cells[y_index +
                                            1][x_index].rect.y += BLOCK_SIZE


class TetrisGameApp:
    def __init__(self):
        self.width = GAME_WIDTH
        self.height = GAME_HEIGHT
        self.grid_offset_x = 50  # Adjusted offset to make more space on the right
        self.grid_offset_y = 0
        self.grid = Grid()
        self.current_shape = self.get_new_shape()
        self.next_shape = self.get_new_shape()
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0
        self.drop_speed = 0.8  # Initial drop speed (seconds per block)
        self.last_drop_time = time.time()
        self.game_over = False
        self.game_font = game_font
        self.running = True

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if not self.game_over:
                        if event.key == pygame.K_LEFT:
                            self.current_shape.move(-1, 0, self.grid)
                        elif event.key == pygame.K_RIGHT:
                            self.current_shape.move(1, 0, self.grid)
                        elif event.key == pygame.K_DOWN:
                            self.current_shape.move(
                                0, 1, self.grid)  # Soft drop
                            # Reset timer for consistent speed after manual drop
                            self.last_drop_time = time.time()
                        elif event.key == pygame.K_UP:
                            self.current_shape.rotate(self.grid)

            if not self.game_over:
                if time.time() - self.last_drop_time >= self.drop_speed:
                    # Automatic block drop
                    # Try to move down, if cannot...
                    if not self.current_shape.move(0, 1, self.grid):
                        # Place shape in grid
                        self.grid.place_shape(self.current_shape)
                        lines_cleared = self.grid.clear_lines()  # Clear any full lines
                        # Update score based on cleared lines
                        self.update_score(lines_cleared)
                        self.current_shape = self.next_shape  # Get next shape
                        self.next_shape = self.get_new_shape()  # Generate a new next shape
                        # Game Over check - if new shape collides immediately at the top
                        if self.current_shape.check_collision(0, 0, self.grid):
                            self.game_over = True
                    self.last_drop_time = time.time()  # Reset drop timer

            screen_surface = pygame.Surface((self.width, self.height))
            screen_surface.fill(window_color)
            self.draw_game(screen_surface)
            yield screen_surface  # Generator to yield the surface for display

    def get_new_shape(self):
        shape_type = random.choice(SHAPES)  # Randomly choose shape type
        return Shape(shape_type)

    def draw_game(self, screen_surface):
        # --- Draw Game Grid ---
        # Transparent surface for the grid
        grid_surface = pygame.Surface(
            (GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE), pygame.SRCALPHA)
        grid_surface.fill((0, 0, 0, 0))  # Transparent background
        self.grid.draw(grid_surface)  # Draw grid on transparent surface
        # Blit grid onto main screen surface with offset
        screen_surface.blit(
            grid_surface, (self.grid_offset_x, self.grid_offset_y))

        # --- Draw Current Shape ---
        for block in self.current_shape.blocks:
            # Create a copy of the block and offset its position for drawing
            block_copy = Block(block.rect.x + self.grid_offset_x, block.rect.y +
                               self.grid_offset_y, block.color)
            block_copy.draw(screen_surface)

        # --- Draw Next Shape Preview ---
        # Transparent surface for next shape area
        next_shape_surface = pygame.Surface(
            (SIDE_BAR_WIDTH, 150), pygame.SRCALPHA)
        next_shape_surface.fill((0, 0, 0, 0))  # Transparent background
        next_shape_x_offset = SIDE_BAR_WIDTH // 2  # Center horizontally in preview area
        next_shape_y_offset = 150 // 2
        for block in self.next_shape.blocks:
            # Scale down and center the next shape preview blocks
            block_copy = Block(block.rect.x // BLOCK_SIZE * 15 + next_shape_x_offset, block.rect.y //
                               BLOCK_SIZE * 15 + next_shape_y_offset - 20, block.color)  # Slightly higher position
            block_copy.rect.size = (15, 15)  # Smaller block size for preview
            block_copy.draw(next_shape_surface)
        # Blit next shape preview on the sidebar area
        screen_surface.blit(next_shape_surface, (GRID_WIDTH * BLOCK_SIZE +
                            self.grid_offset_x, 10))  # Position at top right

        # --- Score and Level Display ---
        score_text_surface = self.game_font.render(
            f"Счет: {self.score}", True, text_color)
        level_text_surface = self.game_font.render(
            f"Уровень: {self.level}", True, text_color)
        lines_text_surface = self.game_font.render(
            f"Линии: {self.lines_cleared_total}", True, text_color)

        text_start_x = GRID_WIDTH * BLOCK_SIZE + \
            self.grid_offset_x + 10  # Position text in sidebar
        text_y_start = 180  # Start position for text vertically
        line_height = 40  # Spacing between lines of text

        screen_surface.blit(score_text_surface, (text_start_x, text_y_start))
        screen_surface.blit(level_text_surface,
                            (text_start_x, text_y_start + line_height))
        screen_surface.blit(lines_text_surface,
                            (text_start_x, text_y_start + 2 * line_height))

        # --- Game Over Display ---
        if self.game_over:
            game_over_text = self.game_font.render("Игра окончена", True, red)
            text_rect = game_over_text.get_rect(
                # Center over grid
                center=(GRID_WIDTH * BLOCK_SIZE // 2 + self.grid_offset_x, self.height // 2))
            screen_surface.blit(game_over_text, text_rect)

    def handle_event(self, event, window_rect):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            if not self.game_over:
                if event.key == pygame.K_LEFT:
                    self.current_shape.move(-1, 0, self.grid)
                elif event.key == pygame.K_RIGHT:
                    self.current_shape.move(1, 0, self.grid)
                elif event.key == pygame.K_DOWN:
                    self.current_shape.move(0, 1, self.grid)
                    self.last_drop_time = time.time()
                elif event.key == pygame.K_UP:
                    self.current_shape.rotate(self.grid)

    def update_score(self, lines_cleared):
        if lines_cleared > 0:
            # Standard Tetris scoring system
            score_increment = [0, 100, 300, 500,
                               800][lines_cleared] * self.level
            self.score += score_increment
            self.lines_cleared_total += lines_cleared
            # Level up every 5 lines (example)
            level_up_threshold = self.level * 5
            if self.lines_cleared_total >= level_up_threshold:
                self.level += 1
                # Increase drop speed by 10% each level (example)
                self.drop_speed *= 0.9

    def stop_running(self):
        self.running = False


pygame.init()
pygame.mixer.init()
pygame.font.init()

screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode(
    (screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("ZOV OS")

blue = (0, 0, 255)
orange = (255, 165, 0)
white = (255, 255, 255)
black = (0, 0, 0)
dark_blue = (0, 0, 100, 128)
red = (255, 0, 0)
yellow = (128, 128, 0)
dark_gray = (30, 30, 30)
light_gray = (150, 150, 150)
bright_red = (255, 0, 0)
green = (0, 200, 0)
transparent_white = (255, 255, 255, 50)
selection_color = (100, 100, 255, 100)
grey_background = (200, 200, 200)
light_blue_grey = (220, 230, 240)

light_theme_window_color = white
light_theme_text_color = black
dark_theme_window_color = dark_gray
dark_theme_text_color = white

window_color = light_theme_window_color
text_color = light_theme_text_color
taskbar_color = white  # Default taskbar color, updated by theme

font_cache = {}


def get_font(font_path, size):
    key = (font_path, size)
    if key not in font_cache:
        try:
            font_cache[key] = pygame.font.Font(font_path, size)
        except FileNotFoundError:
            font_cache[key] = pygame.font.SysFont(None, size)
    return font_cache[key]


font_path = "main_font.otf"
font = get_font(font_path, 200)
file_font = get_font(font_path, 20)
window_font = get_font(font_path, 30)
game_font = get_font(font_path, 30)
console_font = get_font(font_path, 24)
context_menu_font = get_font(font_path, 24)
taskbar_font = get_font(font_path, 20)
description_font = get_font(font_path, 36)
settings_font = get_font(font_path, 20)
browser_font = get_font(font_path, 20)
browser_content_font = get_font(font_path, 24)
widget_font = get_font(font_path, 20)
calculator_font = get_font(font_path, 32)
ztext_font = get_font(font_path, 24)
ztable_cell_font = get_font(font_path, 16)

opening_frames = []
loop_frames = []
try:
    for i in range(10):
        frame_path = os.path.join("images", "opening", f"opening{i}.png")
        if not os.path.exists(frame_path):
            raise FileNotFoundError(
                f"Opening frame image not found: {frame_path}")
        frame = pygame.image.load(frame_path).convert()
        opening_frames.append(pygame.transform.scale(
            frame, (screen_width, screen_height)))
    for i in range(10, 14):
        frame_path = os.path.join("images", "opening", f"opening{i}.png")
        if not os.path.exists(frame_path):
            raise FileNotFoundError(
                f"Loop frame image not found: {frame_path}")
        frame = pygame.image.load(frame_path).convert()
        loop_frames.append(pygame.transform.scale(
            frame, (screen_width, screen_height)))
except FileNotFoundError as e:
    pygame.quit()
    sys.exit()

frame_duration = 0.2
startup_duration = 7
current_frame = 0
current_loop_frame = 0
frame_time = 0
loop_frame_time = 0
show_startup = True
show_loop = False
startup_start_time = 0

try:
    startup_sound = pygame.mixer.Sound(
        os.path.join("Sounds", "startup_sound.mp3"))
    startup_sound.set_volume(0.5)
    sound_loaded = True
except pygame.error as e:
    print(f"Warning: Unable to load startup sound: {e}")
    sound_loaded = False

background_cache = {}


def get_background_image(filename):
    if filename not in background_cache:
        try:
            image = pygame.image.load(
                os.path.join("images", "Wallpapers", filename)).convert()
            background_cache[filename] = pygame.transform.scale(
                image, (screen_width, screen_height))
        except FileNotFoundError:
            surface = pygame.Surface((screen_width, screen_height))
            surface.fill(light_blue_grey)
            background_cache[filename] = surface
    return background_cache[filename]


def init_settings_db():
    conn = sqlite3.connect('system_settings.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            setting_name TEXT PRIMARY KEY,
            setting_value TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS window_states (
            window_title TEXT PRIMARY KEY,
            x INTEGER,
            y INTEGER,
            width INTEGER,
            height INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS desktop_icons (
            icon_name TEXT PRIMARY KEY,
            x INTEGER,
            y INTEGER
        )
    ''')
    conn.commit()
    conn.close()


def is_descendant(folder_to_check, potential_parent):
    if potential_parent is None:
        return False
    if folder_to_check == potential_parent:
        return True
    if isinstance(potential_parent, Folder):  # Ensure potential_parent is a Folder instance
        for file_inside in potential_parent.files_inside:
            if file_inside == folder_to_check:
                return True
            if isinstance(file_inside, Folder):
                if is_descendant(folder_to_check, file_inside):
                    return True
    return False


def get_setting(setting_name, default_value):
    """
    Retrieves a setting value from the database. If the setting does not exist,
    it's created with the default value.
    """
    conn = sqlite3.connect('system_settings.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT setting_value FROM system_settings WHERE setting_name=?", (setting_name,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        update_setting(setting_name, default_value)
        return default_value


def update_setting(setting_name, setting_value):
    """
    Updates or inserts a setting value into the database.
    """
    try:
        # Use 'with' for connection management
        with sqlite3.connect('system_settings.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO system_settings (setting_name, setting_value) VALUES (?, ?)",
                           (setting_name, setting_value))
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Database write error: {
              e}. Please check database file permissions.")


def save_window_state(window):
    """
    Saves the window state (position and size) to the database.
    """
    if window.title:
        try:
            # Use 'with' for connection management
            with sqlite3.connect('system_settings.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO window_states (window_title, x, y, width, height) VALUES (?, ?, ?, ?, ?)",
                               (window.title, window.title_bar.x, window.title_bar.y, window.width, window.height))
                conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Database write error: {
                  e}. Please check database file permissions.")


def load_window_state(window):
    """
    Loads the window state (position and size) from the database.
    """
    if window.title:
        conn = sqlite3.connect('system_settings.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT x, y, width, height FROM window_states WHERE window_title=?", (window.title,))
        result = cursor.fetchone()
        conn.close()
        if result:
            x, y, width, height = result
            window.title_bar.x = x
            window.title_bar.y = y
            window.rect.x = x
            window.rect.y = y + window.title_bar_height
            window.width = width
            window.height = height
            window.rect.width = width
            window.rect.height = height
            window.title_bar.width = width
            window._reposition_window_elements()  # Use encapsulated logic


def save_icon_position(file):
    """
    Saves the desktop icon position to the database.
    """
    try:
        # Use 'with' for connection management
        with sqlite3.connect('system_settings.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO desktop_icons (icon_name, x, y) VALUES (?, ?, ?)",
                           (file.name, file.rect.x, file.rect.y))
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Database write error: {
              e}. Please check database file permissions.")


def load_icon_positions(files):
    """
    Loads desktop icon positions from the database and applies them to the file objects.
    """
    conn = sqlite3.connect('system_settings.db')
    cursor = conn.cursor()
    cursor.execute("SELECT icon_name, x, y FROM desktop_icons")
    results = cursor.fetchall()
    conn.close()
    icon_positions = {name: (x, y) for name, x, y in results}
    for file in files:
        if file.name in icon_positions:
            x, y = icon_positions[file.name]
            file.rect.topleft = (x, y)
            file.name_rect.center = (file.rect.centerx, file.rect.bottom + 20)
            file.update_selection_rect()


init_settings_db()

current_background_setting = get_setting(
    'background_image', 'zovosbg.png')
background_image = get_background_image(current_background_setting)
icon_layout_setting = get_setting(
    'icon_layout', 'grid')
current_theme_setting = get_setting('theme', 'light')
show_clock_widget_setting = get_setting('show_clock_widget', 'true')
show_calendar_widget_setting = get_setting('show_calendar_widget', 'true')
taskbar_icon_size_setting = get_setting('taskbar_icon_size', '40')
taskbar_height_setting = get_setting('taskbar_height', '60')
pinned_apps_setting = get_setting('pinned_apps', '')


def update_theme_colors():
    global window_color, text_color, current_theme_setting, taskbar_color
    current_theme_setting = get_setting('theme', 'light')
    if current_theme_setting == 'dark':
        window_color = dark_theme_window_color
        text_color = dark_theme_text_color
        taskbar_color = dark_gray  # Set taskbar color for dark theme
    else:
        window_color = light_theme_window_color
        text_color = light_theme_text_color
        taskbar_color = white  # Set taskbar color for light theme


update_theme_colors()

show_startup = True
current_letter = 0
last_letter_time = time.time()
show_glow = False
glow_start_time = 0
show_image = False
image_start_time = 0
glow_finished = False
show_description = False
description_start_time = None

clock = pygame.time.Clock()
fps = 60

last_settings_refresh_time = time.time()
settings_refresh_interval = 1

# --- Event for Task Manager Process List Update ---
PROCESS_LIST_UPDATE_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(PROCESS_LIST_UPDATE_EVENT, 1000)  # Update every 1 second
# --- End Event ---


def draw_rect(surface, color, rect, border_width=0, border_radius=0):
    pygame.draw.rect(surface, color, rect, border_width, border_radius)


def draw_text(surface, text, font, color, position, alignment='topleft'):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(**{alignment: position})
    surface.blit(text_surface, text_rect)
    return text_rect


def draw_outlined_text(surface, text, font, color, outline_color, position, alignment='topleft', outline_width=2):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(**{alignment: position})

    text_outline_surface = font.render(text, True, outline_color)

    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            pos = (text_rect.x + dx, text_rect.y + dy)
            surface.blit(text_outline_surface, pos)

    surface.blit(text_surface, text_rect)
    return text_rect


def refresh_settings_from_db(files, windows, widgets, taskbar):
    global current_background_setting, background_image, icon_layout_setting, current_theme_setting, text_color, taskbar_color
    global show_clock_widget_setting, show_calendar_widget_setting, taskbar_icon_size_setting, taskbar_height_setting
    current_background_setting = get_setting(
        'background_image', 'zovosbg.png')
    background_image = get_background_image(current_background_setting)
    icon_layout_setting = get_setting('icon_layout', 'grid')
    current_theme_setting = get_setting('theme', 'light')
    show_clock_widget_setting = get_setting('show_clock_widget', 'true')
    show_calendar_widget_setting = get_setting('show_calendar_widget', 'true')
    taskbar_icon_size_setting = get_setting('taskbar_icon_size', '40')
    taskbar_height_setting = get_setting('taskbar_height', '60')

    update_theme_colors()
    update_widget_visibility(widgets)
    taskbar.update_size_and_color(int(taskbar_height_setting))
    taskbar.update_color()  # Обновляем цвет панели задач и кнопки Пуск
    # Обновляем картинку кнопки Пуск при смене темы
    taskbar.pusk_button.update_image()

    for window in windows:
        window.update_title_surface()
        window.taskbar_icon.update_size(int(taskbar_icon_size_setting))

    if icon_layout_setting == 'grid':
        grid_size = 108 + 20
        for file in files:
            file.rect.topleft = file.get_grid_position(
                grid_size)
            file.name_rect.center = (
                file.rect.centerx, file.rect.bottom + 20)
            file.update_selection_rect()
    elif icon_layout_setting == 'free':
        pass

    for file in files:
        file.update_name_surface()


def update_widget_visibility(widgets):
    global show_clock_widget_setting, show_calendar_widget_setting
    for widget in widgets:
        if isinstance(widget, ClockWidget):
            widget.visible = show_clock_widget_setting == 'true'
            widget.update()  # Ensure widgets update their colors with theme change
        elif isinstance(widget, CalendarWidget):
            widget.visible = show_calendar_widget_setting == 'true'
            widget.update()  # Ensure widgets update their colors with theme change


def draw_description(screen, text, font, color):
    lines = text.strip().split('\n')
    line_height = font.get_linesize()
    text_block_height = len(lines) * line_height
    max_line_width = 0
    rendered_lines = []
    for line in lines:
        text_surface = font.render(line, True, color)
        rendered_lines.append(text_surface)
        max_line_width = max(max_line_width, text_surface.get_width())

    start_y = (screen_height - text_block_height) // 2
    start_x = (screen_width - max_line_width) // 2

    for i, text_surface in enumerate(rendered_lines):
        screen.blit(text_surface, (start_x, start_y + i * line_height))


class SettingsApp:
    def __init__(self):
        self.settings_options_rects = {}
        self.settings_options = []
        self.settings_option_positions = {}
        self.background_previews = {}
        self.load_background_previews()
        self.settings_section_title_font = get_font(
            font_path, 24)
        self.width = 600
        self.height = 600

        self.layout_options_rects = {}
        self.current_layout = get_setting(
            'icon_layout', 'grid')

        self.layout_grid_rect = None
        self.layout_free_rect = None

        self.theme_options_rects = {}
        self.current_theme = get_setting('theme', 'light')

        self.widget_options_rects = {}
        self.show_clock = get_setting('show_clock_widget', 'true') == 'true'
        self.show_calendar = get_setting(
            'show_calendar_widget', 'true') == 'true'

        self.clock_checkbox_rect = None
        self.calendar_checkbox_rect = None
        self.checkbox_size = 20

        self.taskbar_size_slider_rect = None
        self.taskbar_icon_size_slider_rect = None
        self.slider_handle_rect = None
        self.icon_slider_handle_rect = None
        self.is_dragging_slider = False
        self.is_dragging_icon_slider = False
        self.min_taskbar_height = 40
        self.max_taskbar_height = 100
        self.min_icon_size = 20
        self.max_icon_size = 60
        self.current_taskbar_height = int(get_setting('taskbar_height', '60'))
        self.current_taskbar_icon_size = int(
            get_setting('taskbar_icon_size', '40'))

    def load_background_previews(self):
        preview_width = 80
        preview_height = int(preview_width * 9 / 16)
        preview_size = (preview_width, preview_height)

        preview_cache = {}

        def get_preview_surface(filename, size):
            key = (filename, size)
            if key not in preview_cache:
                try:
                    preview_image = pygame.image.load(
                        os.path.join("images", "Wallpapers", filename)).convert()
                    preview_cache[key] = pygame.transform.scale(
                        preview_image, size)
                except FileNotFoundError:
                    surface = pygame.Surface(size)
                    surface.fill(light_blue_grey)
                    preview_cache[key] = surface
            return preview_cache[key]

        wallpapers_dir = os.path.join("images", "Wallpapers")
        if os.path.exists(wallpapers_dir) and os.path.isdir(wallpapers_dir):
            wallpaper_files = [f for f in os.listdir(wallpapers_dir) if os.path.isfile(os.path.join(
                wallpapers_dir, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            for wallpaper_file in wallpaper_files:
                self.background_previews[wallpaper_file] = get_preview_surface(
                    wallpaper_file, preview_size)
                self.settings_options.append(
                    wallpaper_file)
        else:
            print(f"Warning: Wallpaper directory not found or not a directory: {
                  wallpapers_dir}")
            self.background_previews["zovosbg.png"] = get_preview_surface(
                "zovosbg.png", preview_size)
            self.settings_options.append("zovosbg.png")

    def draw(self, screen_surface):
        screen_rect = screen_surface.get_rect()
        section_title_y_offset = 20
        start_x = screen_rect.x + 20
        current_y = screen_rect.y + section_title_y_offset

        draw_text(screen_surface, "Фон", self.settings_section_title_font,
                  text_color, (start_x, current_y), 'topleft')
        section_title_rect = draw_text(
            screen_surface, "Фон", self.settings_section_title_font, text_color, (start_x, current_y), 'topleft')

        current_y += section_title_rect.height + 10
        x_offset_start = start_x
        option_margin_x = 15
        option_margin_y = 20

        background_options = self.settings_options

        for option_key in background_options:
            preview_image = self.background_previews[option_key]
            preview_rect = preview_image.get_rect(
                topleft=(x_offset_start, current_y))
            screen_surface.blit(preview_image, preview_rect)

            option_rect = pygame.Rect(
                preview_rect.x, preview_rect.y, preview_rect.width, preview_rect.height)
            self.settings_options_rects[option_key] = option_rect
            self.settings_option_positions[option_key] = (
                preview_rect.x, preview_rect.y)

            x_offset_start += preview_rect.width + option_margin_x
            if x_offset_start + preview_rect.width + option_margin_x > self.width - 20:
                x_offset_start = start_x
                current_y += preview_rect.height + option_margin_y

        current_y += preview_rect.height + option_margin_y
        draw_text(screen_surface, "Размещение значков", self.settings_section_title_font,
                  text_color, (start_x, current_y), 'topleft')
        layout_title_rect = draw_text(screen_surface, "Размещение значков",
                                      self.settings_section_title_font, text_color, (start_x, current_y), 'topleft')

        current_y += layout_title_rect.height + 10

        layout_option_width = 130
        layout_option_height = 30
        layout_margin_x = 10

        grid_layout_rect = pygame.Rect(
            start_x, current_y, layout_option_width, layout_option_height)
        draw_rect(screen_surface, window_color, grid_layout_rect)
        draw_rect(screen_surface, black, grid_layout_rect, 1)
        draw_text(screen_surface, "По сетке", settings_font,
                  text_color, grid_layout_rect.center, 'center')
        self.layout_grid_rect = grid_layout_rect

        free_layout_rect = pygame.Rect(
            start_x + layout_option_width + layout_margin_x, current_y, layout_option_width, layout_option_height)
        draw_rect(screen_surface, window_color, free_layout_rect)
        draw_rect(screen_surface, black, free_layout_rect, 1)
        draw_text(screen_surface, "Произвольно", settings_font,
                  text_color, free_layout_rect.center, 'center')
        self.layout_free_rect = free_layout_rect

        if self.current_layout == 'grid':
            draw_rect(screen_surface, black, grid_layout_rect, 3)
        elif self.current_layout == 'free':
            draw_rect(screen_surface, black, free_layout_rect, 3)

        current_y += free_layout_rect.height + option_margin_y
        draw_text(screen_surface, "Тема", self.settings_section_title_font,
                  text_color, (start_x, current_y), 'topleft')
        theme_title_rect = draw_text(
            screen_surface, "Тема", self.settings_section_title_font, text_color, (start_x, current_y), 'topleft')

        current_y += theme_title_rect.height + 10

        theme_option_width = 130
        theme_option_height = 30
        theme_margin_x = 10

        light_theme_rect = pygame.Rect(
            start_x, current_y, theme_option_width, theme_option_height)
        draw_rect(screen_surface, window_color, light_theme_rect)
        draw_rect(screen_surface, black, light_theme_rect, 1)
        draw_text(screen_surface, "Светлая", settings_font,
                  text_color, light_theme_rect.center, 'center')
        self.theme_options_rects['light'] = light_theme_rect

        dark_theme_rect = pygame.Rect(
            start_x + theme_option_width + theme_margin_x, current_y, theme_option_width, theme_option_height)
        draw_rect(screen_surface, window_color, dark_theme_rect)
        draw_rect(screen_surface, black, dark_theme_rect, 1)
        draw_text(screen_surface, "Тёмная", settings_font,
                  text_color, dark_theme_rect.center, 'center')
        self.theme_options_rects['dark'] = dark_theme_rect

        if self.current_theme == 'light':
            draw_rect(screen_surface, black, light_theme_rect, 3)
        elif self.current_theme == 'dark':
            draw_rect(screen_surface, black, dark_theme_rect, 3)

        current_y += dark_theme_rect.height + option_margin_y
        draw_text(screen_surface, "Виджеты", self.settings_section_title_font,
                  text_color, (start_x, current_y), 'topleft')
        widgets_title_rect = draw_text(screen_surface, "Виджеты",
                                       self.settings_section_title_font, text_color, (start_x, current_y), 'topleft')

        current_y += widgets_title_rect.height + 10

        widget_option_width = 150
        widget_option_height = 30
        widget_margin_x = 10
        checkbox_margin_x = 10

        clock_label_rect = draw_text(screen_surface, "Часы", settings_font,
                                     text_color, (start_x + checkbox_margin_x + self.checkbox_size + 5, current_y), 'topleft')
        clock_checkbox_rect = pygame.Rect(
            start_x + checkbox_margin_x, current_y, self.checkbox_size, self.checkbox_size)
        draw_rect(screen_surface, window_color, clock_checkbox_rect)
        draw_rect(screen_surface, black, clock_checkbox_rect, 1)
        if self.show_clock:
            pygame.draw.line(
                screen_surface, black, clock_checkbox_rect.topleft, clock_checkbox_rect.bottomright, 3)
            pygame.draw.line(
                screen_surface, black, clock_checkbox_rect.topright, clock_checkbox_rect.bottomleft, 3)
        self.clock_checkbox_rect = clock_checkbox_rect
        current_y += clock_label_rect.height + 5

        calendar_label_rect = draw_text(screen_surface, "Календарь", settings_font,
                                        text_color, (start_x + checkbox_margin_x + self.checkbox_size + 5, current_y), 'topleft')
        calendar_checkbox_rect = pygame.Rect(
            start_x + checkbox_margin_x, current_y, self.checkbox_size, self.checkbox_size)
        draw_rect(screen_surface, window_color, calendar_checkbox_rect)
        draw_rect(screen_surface, black, calendar_checkbox_rect, 1)
        if self.show_calendar:
            pygame.draw.line(screen_surface, black, calendar_checkbox_rect.topleft,
                             calendar_checkbox_rect.bottomright, 3)
            pygame.draw.line(screen_surface, black, calendar_checkbox_rect.topright,
                             calendar_checkbox_rect.bottomleft, 3)
        self.calendar_checkbox_rect = calendar_checkbox_rect

        current_y += calendar_checkbox_rect.height + option_margin_y
        draw_text(screen_surface, "Панель задач", self.settings_section_title_font,
                  text_color, (start_x, current_y), 'topleft')
        taskbar_title_rect = draw_text(screen_surface, "Панель задач",
                                       self.settings_section_title_font, text_color, (start_x, current_y), 'topleft')
        current_y += taskbar_title_rect.height + 10

        slider_y_offset = 10
        slider_height = 10
        slider_handle_size = 20
        slider_margin_y = 20

        taskbar_size_label_rect = draw_text(screen_surface, "Высота панели:", settings_font,
                                            text_color, (start_x, current_y + slider_y_offset), 'topleft')
        taskbar_size_slider_rect = pygame.Rect(start_x + taskbar_size_label_rect.width + 10,
                                               current_y + slider_y_offset + slider_height // 2 - slider_height // 2, 150, slider_height)
        draw_rect(screen_surface, light_gray, taskbar_size_slider_rect)
        slider_handle_pos_x = taskbar_size_slider_rect.left + (taskbar_size_slider_rect.width - slider_handle_size) * (
            self.current_taskbar_height - self.min_taskbar_height) / (self.max_taskbar_height - self.min_taskbar_height)
        slider_handle_rect = pygame.Rect(slider_handle_pos_x, taskbar_size_slider_rect.centery -
                                         slider_handle_size // 2, slider_handle_size, slider_handle_size)
        draw_rect(screen_surface, dark_gray,
                  slider_handle_rect, border_radius=5)
        self.taskbar_size_slider_rect = taskbar_size_slider_rect
        self.slider_handle_rect = slider_handle_rect
        current_y += max(taskbar_size_label_rect.height,
                         slider_handle_size) + slider_margin_y

        taskbar_icon_size_label_rect = draw_text(screen_surface, "Размер значков:", settings_font,
                                                 text_color, (start_x, current_y + slider_y_offset), 'topleft')
        taskbar_icon_size_slider_rect = pygame.Rect(start_x + taskbar_icon_size_label_rect.width + 10,
                                                    current_y + slider_y_offset + slider_height // 2 - slider_height // 2, 150, slider_height)
        draw_rect(screen_surface, light_gray, taskbar_icon_size_slider_rect)
        icon_slider_handle_pos_x = taskbar_icon_size_slider_rect.left + (taskbar_icon_size_slider_rect.width - slider_handle_size) * (
            self.current_taskbar_icon_size - self.min_icon_size) / (self.max_icon_size - self.min_icon_size)
        icon_slider_handle_rect = pygame.Rect(
            icon_slider_handle_pos_x, taskbar_icon_size_slider_rect.centery - slider_handle_size // 2, slider_handle_size, slider_handle_size)
        draw_rect(screen_surface, dark_gray,
                  icon_slider_handle_rect, border_radius=5)

        self.taskbar_icon_size_slider_rect = taskbar_icon_size_slider_rect
        self.icon_slider_handle_rect = icon_slider_handle_rect

    def handle_event(self, mouse_pos, window_rect, event):
        relative_mouse_pos = (mouse_pos[0] - window_rect.x,
                              mouse_pos[1] - window_rect.y)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.slider_handle_rect and self.slider_handle_rect.collidepoint(relative_mouse_pos):
                    self.is_dragging_slider = True
                elif self.icon_slider_handle_rect and self.icon_slider_handle_rect.collidepoint(relative_mouse_pos):
                    self.is_dragging_icon_slider = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging_slider = False
                self.is_dragging_icon_slider = False

                for option_key, option_rect in self.settings_options_rects.items():
                    if option_rect.collidepoint(relative_mouse_pos):
                        update_setting('background_image', option_key)
                        return 'background_change'

                if self.layout_grid_rect and self.layout_grid_rect.collidepoint(relative_mouse_pos):
                    if self.current_layout != 'grid':
                        self.current_layout = 'grid'
                        update_setting('icon_layout', 'grid')
                        return 'layout_change'
                elif self.layout_free_rect and self.layout_free_rect.collidepoint(relative_mouse_pos):
                    if self.current_layout != 'free':
                        self.current_layout = 'free'
                        update_setting('icon_layout', 'free')
                        return 'layout_change'

                if 'light' in self.theme_options_rects and self.theme_options_rects['light'].collidepoint(relative_mouse_pos):
                    if self.current_theme != 'light':
                        self.current_theme = 'light'
                        update_setting('theme', 'light')
                        return 'theme_change'
                elif 'dark' in self.theme_options_rects and self.theme_options_rects['dark'].collidepoint(relative_mouse_pos):
                    if self.current_theme != 'dark':
                        self.current_theme = 'dark'
                        update_setting('theme', 'dark')
                        return 'theme_change'

                if self.clock_checkbox_rect and self.clock_checkbox_rect.collidepoint(relative_mouse_pos):
                    self.show_clock = not self.show_clock
                    update_setting('show_clock_widget',
                                   'true' if self.show_clock else 'false')
                    return 'widget_change'
                elif self.calendar_checkbox_rect and self.calendar_checkbox_rect.collidepoint(relative_mouse_pos):
                    self.show_calendar = not self.show_calendar
                    update_setting('show_calendar_widget',
                                   'true' if self.show_calendar else 'false')
                    return 'widget_change'

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging_slider and self.taskbar_size_slider_rect:
                slider_x = relative_mouse_pos[0] - \
                    self.slider_handle_rect.width // 2
                slider_x = max(self.taskbar_size_slider_rect.left, min(
                    slider_x, self.taskbar_size_slider_rect.right - self.slider_handle_rect.width))
                self.slider_handle_rect.x = slider_x
                slider_pos_ratio = (self.slider_handle_rect.centerx -
                                    self.taskbar_size_slider_rect.left) / self.taskbar_size_slider_rect.width
                self.current_taskbar_height = int(self.min_taskbar_height + (
                    self.max_taskbar_height - self.min_taskbar_height) * slider_pos_ratio)
                self.current_taskbar_height = max(self.min_taskbar_height, min(
                    self.max_taskbar_height, self.current_taskbar_height))
                update_setting('taskbar_height', str(
                    self.current_taskbar_height))
                return 'taskbar_size_change'

            elif self.is_dragging_icon_slider and self.taskbar_icon_size_slider_rect:
                slider_x = relative_mouse_pos[0] - \
                    self.icon_slider_handle_rect.width // 2
                slider_x = max(self.taskbar_icon_size_slider_rect.left, min(
                    slider_x, self.taskbar_icon_size_slider_rect.right - self.icon_slider_handle_rect.width))
                self.icon_slider_handle_rect.x = slider_x
                slider_pos_ratio = (self.icon_slider_handle_rect.centerx -
                                    self.taskbar_icon_size_slider_rect.left) / self.taskbar_icon_size_slider_rect.width
                self.current_taskbar_icon_size = int(
                    self.min_icon_size + (self.max_icon_size - self.min_icon_size) * slider_pos_ratio)
                self.current_taskbar_icon_size = max(self.min_icon_size, min(
                    self.max_icon_size, self.current_taskbar_icon_size))
                update_setting('taskbar_icon_size', str(
                    self.current_taskbar_icon_size))
                return 'taskbar_icon_size_change'

        return None


class TaskManagerApp:
    def __init__(self):
        self.width = 500  # Adjusted width
        self.height = 400  # Adjusted height
        self.task_font = settings_font
        self.processes_data = []
        self.selected_process_index = None
        self.terminate_button_rect = None
        self.header_font = get_font(font_path, 24)  # Slightly larger header
        self.last_update_time = 0
        self.update_interval = 1
        self.process_info_cache = {}
        self.padding = 15  # Padding for elements inside the window
        self.row_height = 35  # Increased row height for better readability
        self.header_height = 50  # Height for the header section
        self.button_height = 50  # Height for the button section
        self.process_list_start_y = self.header_height  # Start position of process list
        self.process_list_rect = pygame.Rect(0, self.process_list_start_y, self.width, self.height -
                                             # Adjusted height calculation
                                             self.process_list_start_y - self.button_height)

        self.update_process_list()

    def update_process_list(self):
        updated_processes_data = []
        for window_index, window in enumerate(windows):
            process_name = window.title
            process_type = "Приложение"  # Simplified type

            if window.file:
                process_type = "Файл"
                process_name = window.file.name
            elif window.folder:
                process_type = "Папка"
                process_name = window.folder.name

            updated_processes_data.append({
                "name": process_name,
                "type": process_type,
                "pid": window_index,  # Still using window index as pseudo PID
                "window": window
            })
        self.processes_data = updated_processes_data

    def draw(self, screen_surface):
        draw_rect(screen_surface, window_color,
                  screen_surface.get_rect(), border_radius=10)
        draw_rect(screen_surface, black,
                  screen_surface.get_rect(), 1, border_radius=10)

        # --- Header Section ---
        header_rect = pygame.Rect(0, 0, self.width, self.header_height)
        draw_rect(screen_surface, light_gray, header_rect, border_radius=10)
        draw_rect(screen_surface, black, header_rect,
                  1, border_radius=10)  # Header border
        header_text_pos = (self.padding, self.padding)
        draw_text(screen_surface, "Диспетчер задач",
                  self.header_font, text_color, header_text_pos, 'topleft')

        # --- Process List ---
        draw_rect(screen_surface, window_color, self.process_list_rect)

        y_offset = self.process_list_start_y + self.padding
        column_width = self.width - 2 * self.padding  # Single column width
        for index, process in enumerate(self.processes_data):
            row_rect = pygame.Rect(
                self.padding, y_offset, column_width, self.row_height)

            if index == self.selected_process_index:
                draw_rect(screen_surface, selection_color,
                          row_rect, border_radius=5)  # Selection highlight

            # Increased padding for text
            process_text_pos = (row_rect.x + 10, row_rect.y + 5)
            draw_text(
                screen_surface, process["name"], self.task_font, text_color, process_text_pos, 'topleft')
            type_text_pos = (row_rect.right - 10, row_rect.y + 5)
            draw_text(
                screen_surface, process["type"], self.task_font, text_color, type_text_pos, 'topright')

            y_offset += self.row_height

        # --- Terminate Button Section ---
        button_section_rect = pygame.Rect(
            0, self.height - self.button_height, self.width, self.button_height)
        draw_rect(screen_surface, light_gray,
                  button_section_rect, border_radius=10)
        draw_rect(screen_surface, black, button_section_rect,
                  1, border_radius=10)  # Button section border

        button_width = 120  # Adjusted button width
        terminate_button_rect = pygame.Rect(
            # Adjusted button position and height
            self.width - button_width - self.padding * 2, self.height - self.button_height + self.padding // 2, button_width, self.button_height - self.padding * 2)
        button_color = red if self.selected_process_index is not None else light_gray
        draw_rect(screen_surface, button_color,
                  terminate_button_rect, border_radius=8)
        draw_rect(screen_surface, black,
                  terminate_button_rect, 1, border_radius=8)
        draw_text(screen_surface, "Завершить процесс", settings_font, white,
                  terminate_button_rect.center, 'center')  # More descriptive button text
        self.terminate_button_rect = terminate_button_rect

    def handle_event(self, event, window_rect):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                relative_mouse_pos = (
                    event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)

                if self.process_list_rect.collidepoint(relative_mouse_pos):
                    process_y_start = self.process_list_start_y + self.padding
                    for index in range(len(self.processes_data)):
                        row_rect = pygame.Rect(
                            self.padding, process_y_start + index * self.row_height, self.width - 2 * self.padding, self.row_height)
                        if row_rect.collidepoint(relative_mouse_pos):
                            self.selected_process_index = index
                            return

                if self.terminate_button_rect and self.terminate_button_rect.collidepoint(relative_mouse_pos) and self.selected_process_index is not None:
                    self.terminate_selected_process()
                    self.selected_process_index = None

    def terminate_selected_process(self):
        if self.selected_process_index is not None:
            process_to_terminate = self.processes_data[self.selected_process_index]
            window_to_close = process_to_terminate["window"]
            if window_to_close:
                window_to_close.is_open = False
                taskbar.remove_icon(window_to_close.taskbar_icon)
                if window_to_close in windows:
                    windows.remove(window_to_close)
                self.update_process_list()  # Refresh process list after termination


class CalculatorApp:
    def __init__(self):
        self.width = 300
        self.height = 440
        self.display_text = "0"
        self.current_number = ""
        self.operator = None
        self.calculation_stack = []
        self.font = calculator_font
        self.button_size = 60
        self.button_margin = 10
        self.buttons = [
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["0", ".", "=", "+"],
            ["C", "+/-"]
        ]
        self.button_rects = []
        self._layout_buttons()
        self.operations = {  # Safer operations mapping
            "+": lambda x, y: x + y,
            "-": lambda x, y: x - y,
            "*": lambda x, y: x * y,
            "/": lambda x, y: x / y if y != 0 else "Error"
        }
        self.button_animations = {}  # To store animation states
        self.animation_duration = 0.1  # Animation duration in seconds

    def _layout_buttons(self):
        start_x = 10
        start_y = 100
        self.button_rects = []
        for row in self.buttons:
            row_rects = []
            x = start_x
            for button_text in row:
                rect = pygame.Rect(
                    x, start_y, self.button_size, self.button_size)
                row_rects.append((rect, button_text))
                x += self.button_size + self.button_margin
            self.button_rects.append(row_rects)
            start_y += self.button_size + self.button_margin

    def draw(self, screen_surface):
        display_rect = pygame.Rect(10, 10, self.width - 20, 80)
        draw_rect(screen_surface, window_color, display_rect, border_radius=5)
        draw_rect(screen_surface, black, display_rect, 1, border_radius=5)
        draw_text(screen_surface, self.display_text, self.font, text_color,
                  (display_rect.right - 20, display_rect.centery), 'midright')

        for row_rects in self.button_rects:
            for rect_button in row_rects:
                rect, button_text = rect_button
                button_color = light_gray if button_text.isdigit(
                ) or button_text == '.' else dark_gray
                # Animation effect
                if button_text in self.button_animations:
                    animation_state = self.button_animations[button_text]
                    if animation_state["animating"]:
                        progress = min(
                            (time.time() - animation_state["start_time"]) / self.animation_duration, 1)
                        scale_factor = 1 - progress * 0.1  # Scale down to 90% at max progress
                        animated_size = (int(rect.width * scale_factor),
                                         int(rect.height * scale_factor))
                        animated_rect = pygame.Rect(0, 0, *animated_size)
                        animated_rect.center = rect.center
                        draw_rect(screen_surface, button_color,
                                  animated_rect, border_radius=10)
                        if progress >= 1:
                            # Animation complete
                            self.button_animations[button_text]["animating"] = False
                    else:
                        draw_rect(screen_surface, button_color,
                                  rect, border_radius=10)  # Normal button
                else:
                    draw_rect(screen_surface, button_color,
                              rect, border_radius=10)  # Normal button

                draw_rect(screen_surface, black, rect, 1, border_radius=10)
                text_color_button = text_color if button_text != "C" else red
                draw_text(screen_surface, button_text, self.font,
                          text_color_button, rect.center, 'center')

    def handle_event(self, event, window_rect):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            relative_mouse_pos = (
                event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
            for row_rects in self.button_rects:
                for rect_button in row_rects:
                    rect, button_text = rect_button
                    if rect.collidepoint(relative_mouse_pos):
                        self.on_button_click(button_text)
                        # Start animation
                        self.button_animations[button_text] = {
                            "animating": True, "start_time": time.time()}
                        return True
        return False

    def on_button_click(self, button_text):
        if button_text.isdigit() or button_text == '.':
            if self.display_text == "0" and button_text != '.':
                self.display_text = button_text
            else:
                self.display_text += button_text
        elif button_text in ["+", "-", "*", "/"]:
            if self.display_text != "":
                try:
                    self.calculation_stack.append(float(self.display_text))
                    self.calculation_stack.append(button_text)
                    self.display_text = ""
                except ValueError:
                    self.display_text = "Error"
                    self.calculation_stack = []
        elif button_text == "=":
            if self.display_text != "":
                try:
                    self.calculation_stack.append(float(self.display_text))
                    result = self._calculate()
                    self.display_text = str(result)
                    self.calculation_stack = []
                except Exception as e:
                    self.display_text = "Error"
                    self.calculation_stack = []
        elif button_text == "C":
            self.display_text = "0"
            self.current_number = ""
            self.operator = None
            self.calculation_stack = []
        elif button_text == "+/-":
            try:
                current_value = float(self.display_text)
                self.display_text = str(current_value * -1)
            except ValueError:
                pass

    def _calculate(self):
        if not self.calculation_stack or len(self.calculation_stack) < 3:
            return self.display_text  # Not enough operands/operators

        result = self.calculation_stack[0]
        i = 1
        while i < len(self.calculation_stack):
            operator = self.calculation_stack[i]
            next_operand = self.calculation_stack[i+1]

            if operator in self.operations:
                operation = self.operations[operator]
                result = operation(result, next_operand)
                if result == "Error":  # Propagate Error from division by zero
                    return "Error"
            else:
                raise Exception("Invalid Operation")
            i += 2
        return result


class Widget:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = True

    def draw(self, screen):
        raise NotImplementedError("Subclasses must implement draw method")

    def update(self):
        pass


class ClockWidget(Widget):
    def __init__(self, x, y):
        super().__init__(x, y, 200, 100)
        self.font = widget_font
        self.time_color = text_color

    def draw(self, screen):
        if self.visible:
            draw_rect(screen, window_color, self.rect)
            draw_rect(screen, black, self.rect, 1)
            current_time = time.strftime("%H:%M:%S")
            draw_text(screen, current_time, self.font,
                      self.time_color, self.rect.center, 'center')

    def update(self):
        self.time_color = text_color


class CalendarWidget(Widget):
    def __init__(self, x, y):
        super().__init__(x, y, 200, 150)
        self.font = widget_font
        self.date_color = text_color

    def draw(self, screen):
        if self.visible:
            draw_rect(screen, window_color, self.rect)
            draw_rect(screen, black, self.rect, 1)
            current_date = time.strftime("%Y-%m-%d")
            draw_text(screen, current_date, self.font,
                      self.date_color, self.rect.center, 'center')
            day_of_week = time.strftime("%A")
            draw_text(screen, day_of_week, self.font, self.date_color,
                      (self.rect.centerx, self.rect.bottom - 30), 'center')

    def update(self):
        self.date_color = text_color


class Window:
    def __init__(self, title, width, height, x, y, file=None, settings_app=None, browser_app=None, calculator_app=None,
                 folder=None, apvia_app=None, properties_text=None, ztext_app=None, ztable_app=None, zdb_app=None, infzov_app=None, calendar_app=None, task_manager_app=None, pong_game_app=None, tetris_game_app=None, snake_game_app=None, minesweeper_app=None):
        self.title = title
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y + 50, width, height)
        self.dragging = False
        self.title_bar_height = 50
        self.title_bar = pygame.Rect(x, y, width, self.title_bar_height)
        self.title_surface = window_font.render(
            self.title, True, text_color)
        self.title_rect = self.title_surface.get_rect(
            center=self.title_bar.center)

        self.close_button_size = 20
        self.close_button_x = self.title_bar.width - \
            self.close_button_size - 10
        self.close_button_y = 15
        self.close_button_rect = pygame.Rect(self.title_bar.x + self.close_button_x,
                                             self.title_bar.y + self.close_button_y, self.close_button_size,
                                             self.close_button_size)
        self.close_cross_surface = pygame.Surface(
            (self.close_button_size, self.close_button_size), pygame.SRCALPHA)
        pygame.draw.line(self.close_cross_surface, red, (0, 0),
                         (self.close_button_size, self.close_button_size), 7)
        pygame.draw.line(self.close_cross_surface, red,
                         (self.close_button_size - 1, 0), (-1, self.close_button_size), 7)

        self.minimize_button_size = 20
        self.minimize_button_x = self.title_bar.width - 2 * \
            (self.minimize_button_size +
             10)
        self.minimize_button_y = 15
        self.minimize_button_rect = pygame.Rect(
            self.title_bar.x + self.minimize_button_x, self.title_bar.y + self.minimize_button_y,
            self.minimize_button_size, self.minimize_button_size)
        self.minimize_line_surface = pygame.Surface(
            (self.minimize_button_size, self.minimize_button_size), pygame.SRCALPHA)
        pygame.draw.line(self.minimize_line_surface, yellow, (3, self.minimize_button_size - 3),
                         (self.minimize_button_size - 3, self.minimize_button_size - 3), 5)

        self.is_open = True
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.file = file
        self.text_input = False
        self.cursor_visible = True
        self.cursor_time = time.time()
        self.cursor_pos = 0
        self.clipboard = ""
        self.selection_start = None
        self.selection_end = None
        self.mail_app = None
        self.app_instance = None
        self.app_thread = None
        self.settings_app = settings_app
        self.browser_app = browser_app
        self.calculator_app = calculator_app
        self.apvia_app = apvia_app
        self.infzov_app = infzov_app
        self.ztext_app = ztext_app
        self.ztable_app = ztable_app
        self.zdb_app = zdb_app
        self.folder = folder
        self.properties_text = properties_text
        self.window_state = "normal"
        self.previous_rect = self.rect.copy()
        self.previous_title_bar = self.title_bar.copy()
        self.calendar_app = calendar_app
        self.task_manager_app = task_manager_app
        self.pong_game_app = pong_game_app
        self.tetris_game_app = tetris_game_app
        self.snake_game_app = snake_game_app
        self.minesweeper_app = minesweeper_app

        self.char_limit_per_line = 70
        self.folder_content_files = []

        self.key_repeat_delay = 0.5
        self.key_repeat_interval = 0.05
        self.key_down_time = 0
        self.held_key = None
        icon_image_path = None
        if self.file:
            icon_image_path = self.file.image_path
        elif self.settings_app:
            icon_image_path = "settings_icon.png"
        elif self.browser_app:
            icon_image_path = "browser_icon.png"
        elif self.calculator_app:
            icon_image_path = "calculator_icon.png"
        elif self.folder:
            icon_image_path = "folder.png"
        elif self.properties_text:
            icon_image_path = "properties_icon.png"
        elif self.ztext_app:
            icon_image_path = "ztext.png"
        elif self.ztable_app:
            icon_image_path = "ztable.png"
        elif self.zdb_app:
            icon_image_path = "zbd.png"
        elif self.infzov_app:
            icon_image_path = "IZ.png"
        elif self.apvia_app:
            icon_image_path = "авпыашка.png"
        elif self.calendar_app:
            icon_image_path = "calendar_icon.png"
        elif self.task_manager_app:
            icon_image_path = "task_manager_icon.png"
        elif self.pong_game_app:
            icon_image_path = "pong_icon.png"
        elif self.tetris_game_app:
            icon_image_path = "tetris_icon.png"
        elif self.snake_game_app:
            icon_image_path = "snake_icon.png"  # Ensure you have snake_icon.png
        elif self.minesweeper_app:
            # Ensure you have minesweeper_icon.png
            icon_image_path = "minesweeper_icon.png"

        self.taskbar_icon = TaskbarIcon(
            self, icon_image_path)

        self.resizing = False
        self.min_width = 200
        self.min_height = 150
        self.initial_mouse_x = 0
        self.initial_mouse_y = 0
        self.initial_width = 0
        self.initial_height = 0
        self.ztext_app = ztext_app
        self.ztable_app = ztable_app
        self.zdb_app = zdb_app
        self.preview_surface = None
        self.calendar_app = calendar_app
        self.task_manager_app = task_manager_app
        self.folder_content_is_dragging = False
        self.folder_content_dragged_file = None

        load_window_state(self)

    def update_title_surface(self):
        self.title_surface = window_font.render(
            self.title, True, text_color)
        self.title_rect = self.title_surface.get_rect(
            center=self.title_bar.center)

    def _reposition_window_elements(self):  # Encapsulated repositioning logic
        """Repositions window elements based on title bar and window rect."""
        self.title_rect.center = self.title_bar.center
        self.close_button_rect.x = self.title_bar.x + \
            self.title_bar.width - self.close_button_size - 10
        self.close_button_rect.y = self.title_bar.y + 15
        self.minimize_button_rect.x = self.title_bar.x + \
            self.title_bar.width - 2 * (self.minimize_button_size + 10)
        self.minimize_button_rect.y = self.title_bar.y + 15

    def draw(self, screen):
        if self.is_open:
            # --- Clip window rect to screen bounds ---
            clipped_rect = self.rect.clip(screen.get_rect())
            clipped_title_bar = self.title_bar.clip(screen.get_rect())

            if clipped_rect.width <= 0 or clipped_rect.height <= 0 or clipped_title_bar.width <= 0 or clipped_title_bar.height <= 0:
                return  # Window is completely off-screen, nothing to draw

            draw_rect(screen, window_color, clipped_title_bar)
            screen.blit(self.title_surface, self.title_rect)

            draw_rect(screen, window_color, self.close_button_rect)
            screen.blit(self.close_cross_surface,
                        self.close_button_rect.topleft)

            draw_rect(screen, window_color, self.minimize_button_rect)
            screen.blit(self.minimize_line_surface,
                        self.minimize_button_rect.topleft)

            draw_rect(screen, light_gray, clipped_rect)
            draw_rect(screen, black, clipped_rect, 1)

            content_surface = screen.subsurface(
                clipped_rect).copy()  # Use clipped rect here
            content_surface.fill(light_gray)

            if self.file and self.file.name.endswith(".txt"):
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                y_offset = 10
                text_content = self.file.content
                lines = []
                current_line = ""
                for char in text_content:
                    if char == '\n':
                        lines.append(current_line)
                        current_line = ""
                    else:
                        current_line += char
                        if len(current_line) > self.char_limit_per_line:
                            lines.append(current_line)
                            current_line = ""
                lines.append(current_line)

                line_surfaces = []
                for line in lines:
                    line_surfaces.append(file_font.render(
                        line, True, text_color))

                for index, line_surface in enumerate(line_surfaces):
                    text_rect = line_surface.get_rect(
                        topleft=(10, y_offset))

                    if self.selection_start is not None and self.selection_end is not None:
                        start_index = 0
                        current_char_index = 0
                        for line_index, current_line_render in enumerate(lines):
                            if line_index < index:
                                start_index += len(current_line_render) + 1
                            else:
                                break

                        end_index = start_index + len(lines[index])

                        selection_start_global = min(
                            self.selection_start, self.selection_end)
                        selection_end_global = max(
                            self.selection_start, self.selection_end)

                        if selection_start_global < end_index and selection_end_global > start_index:
                            selection_start_local = max(
                                0, selection_start_global - start_index)
                            selection_end_local = min(
                                len(lines[index]), selection_end_global - start_index)

                            if selection_start_local < selection_end_local:
                                selected_text = lines[index][selection_start_local:selection_end_local]
                                selected_surface = file_font.render(
                                    selected_text, True, text_color)
                                selected_rect = selected_surface.get_rect(topleft=(
                                    text_rect.x + file_font.size(lines[index][:selection_start_local])[0], text_rect.y))
                                selection_area_rect = pygame.Rect(
                                    selected_rect.x, selected_rect.y, selected_rect.width, selected_rect.height)
                                draw_rect(
                                    content_surface, selection_color, selection_area_rect)

                    content_surface.blit(line_surface, text_rect)
                    y_offset += file_font.get_height() + 5

                if self.text_input:
                    if time.time() - self.cursor_time > 0.5:
                        self.cursor_visible = not self.cursor_visible
                        self.cursor_time = time.time()

                    if self.cursor_visible:
                        lines = text_content.split('\n')
                        line_num = 0
                        char_in_line = 0
                        char_count = 0  # Initialize char_count here
                        for i, line_render in enumerate(lines):
                            if char_count + len(line_render) >= self.cursor_pos:
                                line_num = i
                                char_in_line = self.cursor_pos - char_count
                                break
                            char_count += len(line_render) + 1

                        cursor_x = 10 + \
                            file_font.size(lines[line_num][:char_in_line])[0]
                        cursor_y = 10 + line_num * \
                            (file_font.get_height() + 5)
                        pygame.draw.line(content_surface, text_color, (cursor_x, cursor_y),
                                         (cursor_x, cursor_y + file_font.get_height()), 2)
            elif self.mail_app:
                self.mail_app.draw(content_surface)
            elif self.settings_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                self.settings_app.draw(content_surface)
            elif self.browser_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                self.browser_app.width = self.width
                self.browser_app.height = self.height
                self.browser_app.draw(content_surface)
            elif self.calculator_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                self.calculator_app.width = self.width
                self.calculator_app.height = self.height
                self.calculator_app.draw(content_surface)
            elif self.apvia_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                self.apvia_app.width = self.width
                self.apvia_app.height = self.height
                self.apvia_app.draw(content_surface)
            elif self.infzov_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                self.infzov_app.width = self.width
                self.infzov_app.height = self.height
                self.infzov_app.draw(content_surface, self.rect)
            elif self.folder:
                folder_surface = pygame.Surface(
                    content_surface.get_size(), pygame.SRCALPHA)
                folder_surface.fill(transparent_white)
                content_surface.blit(folder_surface, (0, 0))
                draw_rect(content_surface, window_color,
                          content_surface.get_rect(), 0)
                self.draw_folder_content(
                    content_surface, self.folder.files_inside)
            elif self.properties_text:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                y_offset = 20
                lines = self.properties_text.strip().split('\n')
                for line in lines:
                    text_surface = settings_font.render(line, True, text_color)
                    text_rect = text_surface.get_rect(
                        topleft=(20, y_offset))
                    content_surface.blit(text_surface, text_rect)
                    y_offset += settings_font.get_height() + 5
            elif self.ztext_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                self.ztext_app.width = self.width
                self.ztext_app.height = self.height
                self.ztext_app.draw(content_surface)
            elif self.ztable_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                self.ztable_app.width = self.width
                self.ztable_app.height = self.height
                self.ztable_app.draw(content_surface)
            elif self.zdb_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                self.zdb_app.width = self.width
                self.zdb_app.height = self.height
                self.zdb_app.draw(content_surface)
            elif self.calendar_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                self.calendar_app.width = self.width
                self.calendar_app.height = self.height
                self.calendar_app.draw(content_surface)
            elif self.task_manager_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                self.task_manager_app.width = self.width
                self.task_manager_app.height = self.height
                self.task_manager_app.draw(content_surface)
            elif self.pong_game_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                try:
                    game_surface_generator = self.pong_game_app.run()  # Get the generator
                    # Get the next surface from generator
                    game_surface = next(game_surface_generator)
                    # Blit the game surface
                    content_surface.blit(game_surface, (0, 0))
                except StopIteration:
                    pass  # Generator finished, game likely closed
            elif self.tetris_game_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                try:
                    game_surface_generator = self.tetris_game_app.run()  # Get the generator
                    # Get the next surface from generator
                    game_surface = next(game_surface_generator)
                    # Blit the game surface
                    content_surface.blit(game_surface, (0, 0))
                except StopIteration:
                    pass  # Generator finished, game likely closed
            elif self.snake_game_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                try:
                    game_surface_generator = self.snake_game_app.run()
                    game_surface = next(game_surface_generator)
                    content_surface.blit(game_surface, (0, 0))
                except StopIteration:
                    pass
            elif self.minesweeper_app:
                draw_rect(content_surface, window_color,
                          content_surface.get_rect())
                try:
                    game_surface_generator = self.minesweeper_app.run(
                        pygame.event.get(), content_surface, game_font, window_color, text_color, red, green, black
                    )
                    game_surface = next(game_surface_generator)
                    content_surface.blit(game_surface, (0, 0))
                except StopIteration:
                    pass

            screen.blit(content_surface, clipped_rect)  # Blit clipped rect
            self.preview_surface = pygame.transform.scale(
                content_surface, (content_surface.get_width() // 3, content_surface.get_height() // 3))

    def draw_folder_content(self, screen_surface, folder_files):
        content_rect = screen_surface.get_rect()  # Get the rect of the content surface
        x_start, y_start = 20, 20
        x_offset, y_offset = x_start, y_start
        grid_size = 108 + 20

        for file_obj in folder_files:
            file_obj.rect.topleft = (x_offset, y_offset)
            file_obj.name_rect.center = (
                file_obj.rect.centerx, file_obj.rect.bottom + 20)
            file_obj.update_selection_rect()
            file_obj.draw(screen_surface)
            x_offset += grid_size
            if x_offset + grid_size > content_rect.width - 20:  # Use content_rect.width
                x_offset = x_start
                y_offset += grid_size

    def handle_event(self, event, windows, taskbar, desktop_files, icon_layout_setting, files_in_folder=None):
        global background_image, current_background_setting, dragging_file, is_selecting, dragged_files, file_being_dragged_from_folder, dragged_item_original_folder, cut_file

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.title_bar.collidepoint(event.pos):
                    self.dragging = True
                    self.drag_offset_x = event.pos[0] - self.title_bar.x
                    self.drag_offset_y = event.pos[1] - self.title_bar.y
                if self.close_button_rect.collidepoint(event.pos):
                    self.is_open = False
                    taskbar.remove_icon(self.taskbar_icon)
                    save_window_state(self)
                    if self.app_thread and self.app_thread.is_alive():
                        if self.app_instance and hasattr(self.app_instance, 'stop_running'):
                            self.app_instance.stop_running()
                if self.minimize_button_rect.collidepoint(event.pos):
                    if self.window_state != "minimized":
                        self.window_state = "minimized"
                    else:
                        self.window_state = "normal"

                if self.rect.collidepoint(event.pos) and not self.title_bar.collidepoint(
                        event.pos) and not self.close_button_rect.collidepoint(
                        event.pos) and not self.minimize_button_rect.collidepoint(event.pos):
                    if self.file and self.file.name.endswith(".txt"):
                        self.text_input = True
                        self.cursor_visible = True
                        self.cursor_time = time.time()

                        text_content = self.file.content
                        lines = text_content.split('\n')
                        click_pos_local_x = event.pos[0] - (self.rect.x + 10)
                        click_pos_local_y = event.pos[1] - (self.rect.y + 10)

                        line_height_with_spacing = file_font.get_height() + 5
                        clicked_line_index = min(len(
                            lines) - 1, max(0, click_pos_local_y // line_height_with_spacing))
                        clicked_line_y_start = clicked_line_index * line_height_with_spacing

                        line_text_surface = file_font.render(
                            lines[clicked_line_index], True, black)
                        char_width = line_text_surface.get_width() / max(1,
                                                                         len(lines[clicked_line_index])) if lines[
                            clicked_line_index] else file_font.size(" ")[0]

                        clicked_char_index = min(len(lines[clicked_line_index]), max(
                            0, int(click_pos_local_x // char_width)))

                        char_count = 0  # Initialize char_count here, outside the loop
                        for i, line_render in enumerate(lines):
                            if i < clicked_line_index:  # Count chars only before clicked line index
                                # +1 for newline char
                                char_count += len(line_render) + 1
                            else:
                                break  # Exit loop after processing lines before clicked line

                        self.cursor_pos = char_count + clicked_char_index

                        if not (pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[
                                pygame.K_RSHIFT]):
                            self.selection_start = self.cursor_pos
                            self.selection_end = self.cursor_pos
                        else:
                            if self.selection_start is None:
                                self.selection_start = self.cursor_pos
                                self.selection_end = self.cursor_pos
                            else:
                                self.selection_end = self.cursor_pos
                        self.held_key = None
                    elif self.settings_app:
                        settings_result = self.settings_app.handle_event(
                            event.pos, self.rect, event)
                        if settings_result:
                            if settings_result == 'background_change':
                                current_background_setting = get_setting(
                                    'background_image', 'zovosbg.png')
                                background_image = get_background_image(
                                    current_background_setting)
                            elif settings_result == 'layout_change':
                                refresh_settings_from_db(
                                    desktop_files, windows, widgets, taskbar)
                            elif settings_result == 'theme_change':
                                refresh_settings_from_db(
                                    desktop_files, windows, widgets, taskbar)
                            elif settings_result == 'widget_change':
                                refresh_settings_from_db(
                                    desktop_files, windows, widgets, taskbar)
                            elif settings_result in ['taskbar_size_change', 'taskbar_icon_size_change']:
                                taskbar.update_size_and_color(
                                    int(get_setting('taskbar_height', '60')))
                                for win in windows:
                                    win.taskbar_icon.update_size(
                                        int(get_setting('taskbar_icon_size', '40')))

                    elif self.browser_app:
                        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP,
                                          pygame.MOUSEWHEEL]:
                            if self.rect.collidepoint(event.pos):
                                self.browser_app.handle_event(event, self.rect)
                        elif event.type == pygame.KEYDOWN:
                            self.browser_app.handle_event(event, self.rect)
                    elif self.calculator_app:
                        self.calculator_app.handle_event(event, self.rect)
                    elif self.apvia_app:
                        self.apvia_app.handle_event(event, self.rect)
                    elif self.infzov_app:
                        self.infzov_app.handle_event(event, self.rect)
                    elif self.folder:
                        if self.folder.files_inside:
                            clicked_file_obj = None
                            for file_obj in self.folder.files_inside:
                                if file_obj.selection_rect.collidepoint(
                                        (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)):
                                    clicked_file_obj = file_obj
                                    break

                            if clicked_file_obj:
                                current_time = time.time()
                                if clicked_file_obj.selected and current_time - clicked_file_obj.last_click_time < clicked_file_obj.double_click_interval:
                                    clicked_file_obj.open_file(
                                        desktop_files + self.folder.files_inside, windows, taskbar, self.folder)
                                    for f in self.folder.files_inside:
                                        f.selected = False
                                else:
                                    for f in self.folder.files_inside:
                                        f.selected = False
                                    clicked_file_obj.selected = True
                                    clicked_file_obj.dragging = True
                                    dragging_file = clicked_file_obj
                                    file_being_dragged_from_folder = True
                                    dragged_item_original_folder = self.folder
                                    self.folder_content_is_dragging = True
                                    self.folder_content_dragged_file = clicked_file_obj

                                    dragging_file.drag_offsets = []
                                    initial_drag_pos = pygame.math.Vector2(
                                        dragging_file.rect.center)
                                    for df in dragged_files:
                                        offset = pygame.math.Vector2(
                                            df.rect.center) - initial_drag_pos
                                        dragging_file.drag_offsets.append(
                                            (df, offset))

                                    clicked_file_obj.last_click_time = current_time

                            else:
                                for file_obj in self.folder.files_inside:
                                    file_obj.selected = False
                    elif self.ztext_app:
                        self.ztext_app.handle_event(event, self.rect)
                    elif self.ztable_app:
                        self.ztable_app.handle_event(event, self.rect)
                    elif self.zdb_app:
                        self.zdb_app.handle_event(event, self.rect)
                    elif self.calendar_app:
                        self.calendar_app.handle_event(event, self.rect)
                    elif self.task_manager_app:
                        self.task_manager_app.handle_event(event, self.rect)
                    elif self.pong_game_app:
                        self.pong_game_app.handle_event(event, self.rect)
                    elif self.tetris_game_app:
                        self.tetris_game_app.handle_event(event, self.rect)
                    elif self.snake_game_app:
                        self.snake_game_app.handle_event(event, self.rect)
                    elif self.minesweeper_app:
                        self.minesweeper_app.handle_event(event, self.rect)

                else:
                    self.text_input = False
                    if self.settings_app:
                        pass
                    if self.browser_app:
                        self.browser_app.text_input_active = False
                    if self.calculator_app:
                        pass
                    if self.ztext_app:
                        pass
                    if self.task_manager_app:
                        pass

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                self.resizing = False
                if self.text_input and self.selection_start is not None and self.selection_start == self.selection_end:
                    self.selection_start = None
                if self.folder:
                    self.folder_content_is_dragging = False
                    self.folder_content_dragged_file = None
                    if dragging_file:
                        drop_pos = event.pos
                        drop_rect = pygame.Rect(
                            drop_pos, dragging_file.rect.size)
                        valid_drop_pos = True

                        if self.rect.collidepoint(event.pos):
                            for file_inside in self.folder.files_inside:
                                if file_inside != dragging_file and file_inside.rect.colliderect(drop_rect):
                                    valid_drop_pos = False
                                    break

                            if valid_drop_pos:
                                if file_being_dragged_from_folder and dragged_item_original_folder == self.folder:
                                    dragging_file.dragging = False
                                    dragging_file.selected = False
                                    dragging_file.rect.topleft = (
                                        event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                                    dragging_file.name_rect.center = (
                                        dragging_file.rect.centerx, dragging_file.rect.bottom + 20)
                                    dragging_file.update_selection_rect()
                                else:
                                    if isinstance(dragging_file, Folder) and is_descendant(dragging_file, self.folder):
                                        print("Нельзя переместить папку в себя!")
                                    else:
                                        if dragging_file in desktop_files:
                                            desktop_files.remove(dragging_file)
                                        elif dragging_file.parent_folder:
                                            if dragging_file in dragging_file.parent_folder.files_inside:
                                                dragging_file.parent_folder.files_inside.remove(
                                                    dragging_file)

                                        self.folder.files_inside.append(
                                            dragging_file)
                                        dragging_file.parent_folder = self.folder
                                        dragging_file.dragging = False
                                        dragging_file.selected = False
                                        dragging_file.rect.topleft = (
                                            event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                                        dragging_file.name_rect.center = (
                                            dragging_file.rect.centerx, dragging_file.rect.bottom + 20)
                                        dragging_file.update_selection_rect()

                        else:
                            if dragging_file not in desktop_files and file_being_dragged_from_folder:
                                if isinstance(dragging_file, Folder) and is_descendant(dragging_file, self.folder):
                                    print("Нельзя переместить папку в себя!")
                                else:
                                    if dragging_file in desktop_files:
                                        desktop_files.remove(dragging_file)
                                    elif dragging_file.parent_folder:
                                        if dragging_file in dragging_file.parent_folder.files_inside:
                                            dragging_file.parent_folder.files_inside.remove(
                                                dragging_file)

                                    desktop_files.append(dragging_file)
                                    dragging_file.parent_folder = None
                                    dragging_file.dragging = False
                                    dragging_file.selected = False
                                    dragging_file.rect.topleft = drop_pos
                                    dragging_file.name_rect.center = (
                                        dragging_file.rect.centerx, dragging_file.rect.bottom + 20)
                                    dragging_file.update_selection_rect()
                                    if icon_layout_setting == 'grid':
                                        save_icon_position(dragging_file)

                        dragging_file.dragging = False
                        dragging_file = None
                        dragged_files = []
                        file_being_dragged_from_folder = False
                        dragged_item_original_folder = None

                elif self.ztext_app:
                    self.ztext_app.handle_event(event, self.rect)
                elif self.ztable_app:
                    self.ztable_app.handle_event(event, self.rect)
                elif self.zdb_app:
                    self.zdb_app.handle_event(event, self.rect)
                elif self.calendar_app:
                    self.calendar_app.handle_event(event, self.rect)
                elif self.infzov_app:
                    self.infzov_app.handle_event(event, self.rect)
                elif self.task_manager_app:
                    self.task_manager_app.handle_event(event, self.rect)
                elif self.pong_game_app:
                    self.pong_game_app.handle_event(event, self.rect)
                elif self.tetris_game_app:
                    self.tetris_game_app.handle_event(event, self.rect)
                elif self.snake_game_app:
                    self.snake_game_app.handle_event(event, self.rect)
                elif self.minesweeper_app:
                    self.minesweeper_app.handle_event(event, self.rect)

        elif event.type == pygame.MOUSEWHEEL:
            xmouse, ymouse = pygame.mouse.get_pos()
            if self.browser_app and self.rect.collidepoint((xmouse, ymouse)):
                if event.y > 0:
                    self.browser_app.scroll_y = max(
                        0, self.browser_app.scroll_y - 30)
                elif event.y < 0:
                    self.browser_app.scroll_y = min(
                        self.browser_app.content_height - self.rect.height, self.browser_app.scroll_y + 30)

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                new_x = max(
                    0, min(event.pos[0] - self.drag_offset_x, screen_width - self.width))
                new_y = max(
                    0, min(event.pos[1] - self.drag_offset_y, screen_height - self.height))

                self.title_bar.x = new_x
                self.title_bar.y = new_y

                self.rect.x = self.title_bar.x
                self.rect.y = self.title_bar.y + self.title_bar_height
                self._reposition_window_elements()

            if self.resizing:
                delta_x = event.pos[0] - self.initial_mouse_x
                delta_y = event.pos[1] - self.initial_mouse_y

                new_width = max(self.min_width, self.initial_width + delta_x)
                new_height = max(
                    self.min_height, self.initial_height + delta_y)

                if self.rect.left + new_width > screen_width:
                    new_width = screen_width - self.rect.left
                if self.rect.top + new_height + self.title_bar_height > screen_height:
                    new_height = screen_height - self.title_bar_height - self.rect.top

                self.width = new_width
                self.height = new_height
                self.rect.width = self.width
                self.rect.height = self.height
                self.title_bar.width = self.width
                self._reposition_window_elements()

            if self.folder and dragging_file and dragging_file.dragging and dragging_file.parent_folder == self.folder:
                relative_mouse_x = event.pos[0] - self.rect.x
                relative_mouse_y = event.pos[1] - self.rect.y
                dragging_file.rect.center = (
                    relative_mouse_x, relative_mouse_y)
                dragging_file.name_rect.center = (
                    dragging_file.rect.centerx, dragging_file.rect.bottom + 20)
                dragging_file.update_selection_rect()

                if hasattr(dragging_file, 'drag_offsets'):
                    current_drag_pos = pygame.math.Vector2(
                        dragging_file.rect.center)
                    for file_to_drag, offset in dragging_file.drag_offsets:
                        if file_to_drag != dragging_file:
                            file_to_drag.rect.center = current_drag_pos + offset
                            file_to_drag.name_rect.center = (
                                file_to_drag.rect.centerx, file_to_drag.rect.bottom + 20)
                            file_to_drag.update_selection_rect()

            elif dragging_file and dragging_file.dragging and dragged_files and dragging_file in dragged_files:
                current_drag_pos = pygame.math.Vector2(event.pos)

                if not hasattr(dragging_file, 'drag_offsets'):
                    dragging_file.drag_offsets = []
                    initial_drag_pos = pygame.math.Vector2(
                        dragging_file.rect.center)
                    for df in dragged_files:
                        offset = pygame.math.Vector2(
                            df.rect.center) - initial_drag_pos
                        dragging_file.drag_offsets.append((df, offset))

                for file_to_drag, offset in dragging_file.drag_offsets:
                    if file_to_drag != dragging_file:
                        file_to_drag.rect.center = current_drag_pos + offset
                        file_to_drag.name_rect.center = (
                            file_to_drag.rect.centerx, file_to_drag.rect.bottom + 20)
                        file_to_drag.update_selection_rect()
                dragging_file.rect.center = event.pos

            if self.text_input and self.selection_start is not None and pygame.mouse.get_pressed()[0]:
                if self.rect.collidepoint(event.pos):
                    text_content = self.file.content
                    lines = text_content.split('\n')
                    click_pos_local_x = event.pos[0] - (self.rect.x + 10)
                    click_pos_local_y = event.pos[1] - (self.rect.y + 10)

                    line_height_with_spacing = file_font.get_height() + 5
                    clicked_line_index = min(
                        len(lines) - 1, max(0, click_pos_local_y // line_height_with_spacing))
                    line_text_surface = file_font.render(
                        lines[clicked_line_index], True, black)
                    char_width = line_text_surface.get_width() / max(1,
                                                                     len(lines[clicked_line_index])) if lines[
                        clicked_line_index] else file_font.size(" ")[0]
                    clicked_char_index = min(len(lines[clicked_line_index]), max(
                        0, int(click_pos_local_x // char_width)))

                    char_count = 0
                    for i, line_render in enumerate(lines):
                        if i < clicked_line_index:
                            char_count += len(line_render) + 1
                        else:
                            break

                    self.selection_end = char_count + clicked_char_index

            if self.ztext_app:
                self.ztext_app.handle_event(event, self.rect)
            if self.zdb_app:
                self.zdb_app.handle_event(event, self.rect)
            if self.ztable_app:
                self.ztable_app.handle_event(event, self.rect)
            if self.calendar_app:
                self.calendar_app.handle_event(event, self.rect)
            if self.infzov_app:
                self.infzov_app.handle_event(event, self.rect)
            if self.task_manager_app:
                self.task_manager_app.handle_event(event, self.rect)
            if self.pong_game_app:
                pass  # Pong game handles its own mouse motion if needed
            if self.tetris_game_app:
                pass  # Tetris game handles its own mouse motion if needed
            if self.snake_game_app:
                pass  # Snake game handles its own mouse motion if needed
            if self.minesweeper_app:
                pass  # Minesweeper game handles its own mouse motion if needed

        elif event.type == pygame.KEYDOWN:
            if event.key not in [pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_CAPSLOCK,
                                 pygame.K_NUMLOCK]:
                self.held_key = event.key
                self.key_down_time = time.time()

            if self.file and self.file.name.endswith(".txt") and self.text_input:
                if event.key == pygame.K_LEFT:
                    self.cursor_pos = max(0, self.cursor_pos - 1)
                    self.selection_start = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or
                                                               pygame.key.get_pressed()[
                        pygame.K_RSHIFT]) and self.selection_start is not None else None
                    self.selection_end = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or
                                                             pygame.key.get_pressed()[
                        pygame.K_RSHIFT]) and self.selection_start is not None else None
                elif event.key == pygame.K_RIGHT:
                    self.cursor_pos = min(
                        len(self.file.content), self.cursor_pos + 1)
                    self.selection_start = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or
                                                               pygame.key.get_pressed()[
                        pygame.K_RSHIFT]) and self.selection_start is not None else None
                    self.selection_end = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or
                                                             pygame.key.get_pressed()[
                        pygame.K_RSHIFT]) and self.selection_start is not None else None
                elif event.key == pygame.K_UP:
                    lines = self.file.content.split('\n')
                    current_line_index = 0
                    char_count = 0
                    for i, line in enumerate(lines):
                        if char_count + len(line) >= self.cursor_pos:
                            current_line_index = i
                            break
                        char_count += len(line) + 1

                    if current_line_index > 0:
                        target_line_index = current_line_index - 1
                        chars_above_lines = 0
                        for i in range(target_line_index):
                            chars_above_lines += len(lines[i]) + 1
                        self.cursor_pos = min(chars_above_lines + len(
                            lines[target_line_index]), chars_above_lines + (self.cursor_pos - char_count))
                    else:
                        self.cursor_pos = 0

                    self.selection_start = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or
                                                               pygame.key.get_pressed()[
                        pygame.K_RSHIFT]) and self.selection_start is not None else None
                    self.selection_end = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or
                                                             pygame.key.get_pressed()[
                        pygame.K_RSHIFT]) and self.selection_start is not None else None

                elif event.key == pygame.K_DOWN:
                    lines = self.file.content.split('\n')
                    current_line_index = 0
                    char_count = 0
                    for i, line in enumerate(lines):
                        if char_count + len(line) >= self.cursor_pos:
                            current_line_index = i
                            break
                        char_count += len(line) + 1

                    if current_line_index < len(lines) - 1:
                        target_line_index = current_line_index + 1
                        chars_above_lines = 0
                        for i in range(target_line_index):
                            chars_above_lines += len(lines[i]) + 1
                        self.cursor_pos = min(chars_above_lines + len(
                            lines[target_line_index]), chars_above_lines + (self.cursor_pos - char_count))
                    else:
                        self.cursor_pos = len(self.file.content)

                    self.selection_start = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or
                                                               pygame.key.get_pressed()[
                        pygame.K_RSHIFT]) and self.selection_start is not None else None
                    self.selection_end = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or
                                                             pygame.key.get_pressed()[
                        pygame.K_RSHIFT]) and self.selection_start is not None else None

                elif event.key == pygame.K_BACKSPACE:
                    if self.selection_start is not None and self.selection_start != self.selection_end:
                        start_index = min(
                            self.selection_start, self.selection_end)
                        end_index = max(self.selection_start,
                                        self.selection_end)
                        self.file.content = self.file.content[:start_index] + \
                            self.file.content[end_index:]
                        self.cursor_pos = start_index
                        self.selection_start = None
                        self.selection_end = None
                    elif self.cursor_pos > 0:
                        self.file.content = self.file.content[:self.cursor_pos -
                                                              1] + self.file.content[self.cursor_pos:]
                        self.cursor_pos -= 1
                elif event.key == pygame.K_DELETE:
                    if self.selection_start is not None and self.selection_start != self.selection_end:
                        start_index = min(
                            self.selection_start, self.selection_end)
                        end_index = max(self.selection_start,
                                        self.selection_end)
                        self.file.content = self.file.content[:start_index] + \
                            self.file.content[end_index:]
                        self.cursor_pos = start_index
                        self.selection_start = None
                        self.selection_end = None
                    elif self.cursor_pos < len(self.file.content):
                        self.file.content = self.file.content[:self.cursor_pos] + \
                            self.file.content[self.cursor_pos + 1:]
                elif (event.key == pygame.K_c and (
                        pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL])):
                    if self.selection_start is not None and self.selection_start != self.selection_end:
                        start_index = min(
                            self.selection_start, self.selection_end)
                        end_index = max(self.selection_start,
                                        self.selection_end)
                        self.clipboard = self.file.content[start_index:end_index]
                elif (event.key == pygame.K_x and (
                        pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL])):
                    if self.selection_start is not None and self.selection_start != self.selection_end:
                        start_index = min(
                            self.selection_start, self.selection_end)
                        end_index = max(self.selection_start,
                                        self.selection_end)
                        self.clipboard = self.file.content[start_index:end_index]
                        self.file.content = self.file.content[:start_index] + \
                            self.file.content[end_index:]
                        self.cursor_pos = start_index
                        self.selection_start = None
                        self.selection_end = None
                elif (event.key == pygame.K_v and (
                        pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL])):
                    temp_content = self.file.content[:self.cursor_pos] + \
                        self.clipboard + self.file.content[self.cursor_pos:]
                    lines = temp_content.split('\n')
                    paste_allowed = True
                    for line in lines:
                        if len(line) > self.char_limit_per_line:
                            paste_allowed = False
                            break
                    if paste_allowed:
                        self.file.content = temp_content
                        self.cursor_pos += len(self.clipboard)
                elif event.key == pygame.K_RETURN:
                    self.file.content = self.file.content[:self.cursor_pos] + \
                        '\n' + self.file.content[self.cursor_pos:]
                    self.cursor_pos += 1
                elif event.unicode and file_font.render(self.file.content[:self.cursor_pos] + event.unicode, True,
                                                        black).get_width() < self.rect.width - 20:
                    self.file.content = self.file.content[:self.cursor_pos] + \
                        event.unicode + self.file.content[self.cursor_pos:]
                    self.cursor_pos += 1
            elif self.browser_app and self.browser_app.text_input_active:
                self.browser_app.handle_event(event, self.rect)
            elif self.calculator_app:
                self.calculator_app.handle_event(event, self.rect)
            elif self.apvia_app and (self.apvia_app.current_screen == "game"):
                if event.key == pygame.K_r and (self.apvia_app.game_over or self.apvia_app.game_won):
                    self.apvia_app.start_game()
                    self.apvia_app.money_earning = True
                    return "game_restarted"
                elif event.key == pygame.K_m and (self.apvia_app.game_over or self.apvia_app.game_won):
                    self.apvia_app.current_screen = "main_menu"
                    self.apvia_app.money_earning = True
                    self.apvia_app._layout_buttons()
                    return "back_to_main_menu"
            elif self.ztext_app:
                self.ztext_app.handle_event(event, self.rect)
            elif self.ztable_app:
                self.ztable_app.handle_event(event, self.rect)
            elif self.zdb_app:
                self.zdb_app.handle_event(event, self.rect)
            elif self.task_manager_app:
                self.task_manager_app.handle_event(event, self.rect)
            elif self.pong_game_app:
                self.pong_game_app.handle_event(event, self.rect)
            elif self.tetris_game_app:
                self.tetris_game_app.handle_event(event, self.rect)
            elif self.snake_game_app:
                self.snake_game_app.handle_event(event, self.rect)
            elif self.minesweeper_app:
                self.minesweeper_app.handle_event(event, self.rect)

            self.cursor_visible = True
            self.cursor_time = time.time()
        if self.mail_app:
            self.mail_app.handle_event(event, windows)

    def bring_to_front(self, windows):
        if self in windows:
            windows.remove(self)
            windows.append(self)
            for win in windows:
                if win != self:
                    win.window_state = "normal"
            self.window_state = "normal"


class DesktopFile:
    def __init__(self, name, image_path, x, y, protected=False, file_type="text", app_module=None, app_class=None,
                 is_app=False, parent_folder=None):
        self.name = name
        self.original_name = name
        self.image_path = image_path
        self.original_image = None
        if image_path:
            try:
                self.original_image = pygame.image.load(
                    os.path.join("images", image_path)).convert_alpha()
                self.image = self.original_image
            except FileNotFoundError:
                self.image = self.create_default_txt_icon()
            except Exception as e:  # General error handling for image loading
                print(f"Error loading image {image_path}: {e}")
                self.image = self.create_default_txt_icon()  # Fallback to default icon
        else:
            self.image = self.create_default_txt_icon()

        self.rect = self.image.get_rect(topleft=(x, y))
        self.selected = False
        self.dragging = False
        self.name_surface = file_font.render(
            self.name, True, text_color)
        self.name_rect = self.name_surface.get_rect(
            center=(self.rect.centerx, self.rect.bottom + 20))

        padding_x = self.rect.width * 0.10
        padding_y = self.rect.height * 0.10 + 15

        selection_width = int(self.rect.width + padding_x * 2)
        selection_height = int(self.rect.height + padding_y * 2)

        selection_x = int(self.rect.left - padding_x)
        selection_y = int(self.rect.top - padding_y)

        self.selection_rect = pygame.Rect(
            selection_x, selection_y, selection_width, selection_height)
        self.selection_surface = pygame.Surface(
            (selection_width, selection_height), pygame.SRCALPHA)
        self.selection_surface.fill(dark_blue)

        self.last_click_time = 0
        self.double_click_interval = 0.3
        self.is_in_trash = False
        self.protected = protected
        self.file_type = file_type
        self.app_module = app_module
        self.app_class = app_class
        self.is_app = is_app
        self.parent_folder = parent_folder
        self.drag_offsets = []

        self.content = ""
        self.grid_spacing = 20
        self.icon_size = 108

        self.is_renaming = False
        self.rename_input = ""
        self.rename_cursor_visible = True
        self.rename_cursor_time = time.time()
        self.rename_cursor_position = 0

        loaded_pos = load_icon_position_from_db(self.name)
        if loaded_pos:
            self.rect.topleft = loaded_pos
            self.name_rect.center = (self.rect.centerx, self.rect.bottom + 20)
            self.update_selection_rect()

    def create_default_txt_icon(self):
        image = pygame.Surface((64, 64), pygame.SRCALPHA)
        draw_rect(image, white, (0, 0, 64, 64))
        draw_rect(image, black, (0, 0, 64, 64), 1)
        draw_text(image, ".txt", file_font, black, (32, 32), 'center')
        return image

    def draw(self, screen):
        if not self.is_in_trash:
            if self.selected:
                screen.blit(self.selection_surface, self.selection_rect)
            screen.blit(self.image, self.rect)
            if self.is_renaming:
                input_rect = self.name_rect.copy()
                input_rect.y = self.rect.bottom + 5
                input_rect.height = 25

                draw_rect(screen, window_color, input_rect)
                draw_rect(screen, black, input_rect, 1)

                text_surface = file_font.render(
                    self.rename_input, True, text_color)
                text_render_rect = text_surface.get_rect(
                    center=input_rect.center)
                screen.blit(text_surface, text_render_rect)

                if time.time() - self.rename_cursor_time > 0.5:
                    self.rename_cursor_visible = not self.rename_cursor_visible
                    self.rename_cursor_time = time.time()

                if self.rename_cursor_visible:
                    cursor_x_offset = file_font.size(
                        self.rename_input[:self.rename_cursor_position])[0]
                    cursor_x = input_rect.x + (input_rect.width - text_render_rect.width) // 2 + \
                        cursor_x_offset if self.rename_input else input_rect.centerx
                    cursor_y = input_rect.top + 3
                    pygame.draw.line(screen, text_color, (cursor_x, cursor_y),
                                     (cursor_x, cursor_y + input_rect.height - 6), 2)

            else:
                screen.blit(self.name_surface, self.name_rect)

    def update_name_surface(self):
        self.name_surface = file_font.render(
            self.name, True, text_color)
        self.name_rect = self.name_surface.get_rect(
            center=(self.rect.centerx, self.rect.bottom + 20))

    def update_selection_rect(self):
        padding_x = self.rect.width * 0.05
        padding_y = self.rect.height * 0.05 + 15

        selection_width = int(self.rect.width + padding_x * 2)
        selection_height = int(self.rect.height + padding_y * 2)

        selection_x = int(self.rect.left - padding_x)
        selection_y = int(self.rect.top - padding_y + 10)

        self.selection_rect = pygame.Rect(
            selection_x, selection_y, selection_width, selection_height)

    def get_grid_position(self, grid_size):
        grid_x = round(self.rect.x / grid_size) * grid_size
        grid_y = round(self.rect.y / grid_size) * grid_size
        return grid_x, grid_y

    def handle_event(self, event, files, windows, context_menu, trash, moving_file_to_front, taskbar,
                     icon_layout_setting):
        global dragging_file, is_selecting, dragged_files
        if not self.is_in_trash:
            # --- Added window overlap check ---
            is_overlapped = False
            for window in windows:
                if window.is_open and window.rect.colliderect(self.selection_rect):
                    is_overlapped = True
                    break
            if is_overlapped and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return  # Do nothing if overlapped and left mouse button is pressed

            # --- Original event handling code ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.is_renaming:
                        if not self.name_rect.collidepoint(event.pos):
                            self.name = self.rename_input if self.rename_input else self.original_name
                            self.update_name_surface()
                            self.is_renaming = False
                        return

                    if self.selection_rect.collidepoint(event.pos) and not is_selecting:
                        current_time = time.time()

                        # Check for double click FIRST
                        if current_time - self.last_click_time < self.double_click_interval and self.selected and not self.is_renaming:
                            # Pass parent folder for context
                            self.open_file(
                                files, windows, taskbar, self.parent_folder)
                            for file in files:
                                file.selected = False
                            return  # Early return to prevent drag initiation after double click

                        if not (pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[
                                pygame.K_RCTRL]):
                            for file in files:
                                file.selected = False
                            self.selected = True
                            self.dragging = True
                            dragging_file = self

                            dragged_files = [f for f in files if f.selected]

                            dragging_file.drag_offsets = []
                            initial_drag_pos = pygame.math.Vector2(
                                dragging_file.rect.center)
                            for df in dragged_files:
                                offset = pygame.math.Vector2(
                                    df.rect.center) - initial_drag_pos
                                dragging_file.drag_offsets.append((df, offset))

                            moving_file_to_front(self)

                        self.last_click_time = current_time
                    elif not is_selecting:
                        clicked_on_file = False
                        for file in files:
                            if file.selection_rect.collidepoint(event.pos):
                                clicked_on_file = True
                                break
                        if not clicked_on_file:
                            for file in files:
                                if not (pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[
                                        pygame.K_RCTRL]):
                                    file.selected = False
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.dragging:
                        if trash.rect.colliderect(self.rect):
                            if self.protected:
                                print("Error: Cannot delete protected system file.")
                            else:
                                for dragged_file in dragged_files:
                                    if dragged_file.protected:
                                        print(f"Error: Cannot delete protected system file: {
                                              dragged_file.name}")
                                        continue

                                    dragged_file.is_in_trash = True
                                    if dragged_file in files:
                                        files.remove(dragged_file)
                                    if dragged_file.parent_folder and dragged_file in dragged_file.parent_folder.files_inside:
                                        dragged_file.parent_folder.files_inside.remove(
                                            dragged_file)

                        elif icon_layout_setting == 'grid':
                            grid_size = self.icon_size + self.grid_spacing
                            for dragged_file in dragged_files:
                                dragged_file.rect.topleft = dragged_file.get_grid_position(
                                    grid_size)
                                dragged_file.name_rect.center = (
                                    dragged_file.rect.centerx, dragged_file.rect.bottom + 20)
                                dragged_file.update_selection_rect()
                                save_icon_position(dragged_file)

                        dragging_file = None
                        dragged_files = []
                    self.dragging = False
                    self.drag_offsets = []
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    self.rect.center = event.pos
                    self.name_rect.center = (
                        self.rect.centerx, self.rect.bottom + 20)
                    self.update_selection_rect()

                    if hasattr(self, 'drag_offsets'):
                        current_drag_pos = pygame.math.Vector2(
                            self.rect.center)
                        for file_to_drag, offset in self.drag_offsets:
                            if file_to_drag != self:
                                file_to_drag.rect.center = current_drag_pos + offset
                                file_to_drag.name_rect.center = (
                                    file_to_drag.rect.centerx, file_to_drag.rect.bottom + 20)
                                file_to_drag.update_selection_rect()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if self.file_type == "folder":
                    context_menu_options = [
                        "Открыть", "Переименовать", "Удалить", "Свойства", "Создать .txt", "Создать папку", "Вставить", "Копировать", "Вырезать"]  # Added options
                else:
                    context_menu_options = ["Открыть", "Копировать", "Вырезать",
                                            "Копировать путь", "Создать ярлык", "Переименовать", "Удалить", "Свойства"]

                context_menu = ContextMenu(
                    event.pos[0], event.pos[1], context_menu_options, self, context="file")

            elif event.type == pygame.KEYDOWN:
                if self.is_renaming:
                    if event.key == pygame.K_RETURN:
                        self.name = self.rename_input if self.rename_input else self.original_name
                        self.update_name_surface()
                        self.is_renaming = False
                        save_icon_position(self)
                    elif event.key == pygame.K_ESCAPE:
                        self.rename_input = ""
                        self.is_renaming = False
                    elif event.key == pygame.K_BACKSPACE:
                        self.rename_input = self.rename_input[:-1]
                        self.rename_cursor_position = max(
                            0, self.rename_cursor_position - 1)
                    elif event.key == pygame.K_LEFT:
                        self.rename_cursor_position = max(
                            0, self.rename_cursor_position - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.rename_cursor_position = min(
                            len(self.rename_input), self.rename_cursor_position + 1)
                    elif event.unicode:
                        valid_char = event.unicode.isalnum() or event.unicode == ' ' or event.unicode == '.'
                        if valid_char and file_font.render(self.rename_input + event.unicode, True, black).get_width() <= self.rect.width * 2:
                            self.rename_input += event.unicode
                            self.rename_cursor_position += 1

    # Added current_folder parameter
    def open_file(self, files, windows, taskbar, current_folder=None):
        if self.name.endswith(".txt"):
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 600 > screen_width:
                    new_x = 200
                if new_y + 400 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200

            new_window = Window(self.name, 600, 400, new_x, new_y, file=self)
            windows.append(new_window)
            taskbar.add_icon(new_window.taskbar_icon)
            new_window.bring_to_front(windows)
        elif self.is_app and self.name == "Настройки":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 600 > screen_width:
                    new_x = 200
                if new_y + 600 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200
            settings_app_instance = SettingsApp()
            settings_window = Window("Настройки", settings_app_instance.width,
                                     settings_app_instance.height, new_x, new_y, settings_app=settings_app_instance)
            windows.append(settings_window)
            taskbar.add_icon(settings_window.taskbar_icon)
            settings_window.bring_to_front(windows)
        elif self.is_app and self.name == "Браузер":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 800 > screen_width:
                    new_x = 200
                if new_y + 600 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200
            browser_app_instance = BrowserApp()
            browser_window = Window("Браузер", browser_app_instance.width,
                                    browser_app_instance.height, new_x, new_y, browser_app=browser_app_instance)
            windows.append(browser_window)
            taskbar.add_icon(browser_window.taskbar_icon)
            browser_window.bring_to_front(windows)
        elif self.is_app and self.name == "Калькулятор":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 300 > screen_width:
                    new_x = 200
                if new_y + 400 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200
            calculator_app_instance = CalculatorApp()
            calculator_window = Window("Калькулятор", calculator_app_instance.width,
                                       calculator_app_instance.height, new_x, new_y,
                                       calculator_app=calculator_app_instance)
            windows.append(calculator_window)
            taskbar.add_icon(calculator_window.taskbar_icon)
            calculator_window.bring_to_front(windows)
        elif self.file_type == "folder":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 800 > screen_width:
                    new_x = 200
                if new_y + 600 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200
            folder_window = Window(self.name, 800, 600,
                                   new_x, new_y, folder=self)
            windows.append(folder_window)
            taskbar.add_icon(folder_window.taskbar_icon)
            folder_window.bring_to_front(windows)
        elif self.is_app and self.name == "апвыа":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 300 > screen_width:
                    new_x = 200
                if new_y + 250 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200
                apvia_app_instance = ApviaApp()
                apvia_window = Window("Апвыа", apvia_app_instance.width,
                                      apvia_app_instance.height, new_x,
                                      new_y, apvia_app=apvia_app_instance)
                windows.append(apvia_window)
                taskbar.add_icon(apvia_window.taskbar_icon)
                apvia_window.bring_to_front(windows)
        elif self.is_app and self.name == "ZText":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 600 > screen_width:
                    new_x = 200
                if new_y + 400 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200
            ztext_app_instance = ZTextApp()
            ztext_window = Window("ZText", ztext_app_instance.width,
                                  ztext_app_instance.height, new_x, new_y, ztext_app=ztext_app_instance)
            windows.append(ztext_window)
            taskbar.add_icon(ztext_window.taskbar_icon)
            ztext_window.bring_to_front(windows)
        elif self.is_app and self.name == "ZTable":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 800 > screen_width:
                    new_x = 200
                if new_y + 600 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200
            ztable_app_instance = ZTableApp()
            ztable_window = Window("ZTable", ztable_app_instance.width,
                                   ztable_app_instance.height, new_x, new_y, ztable_app=ztable_app_instance)
            windows.append(ztable_window)
            taskbar.add_icon(ztable_window.taskbar_icon)
            ztable_window.bring_to_front(windows)
        elif self.is_app and self.name == "ZDataBase":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 800 > screen_width:
                    new_x = 200
                if new_y + 600 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200
            zdb_app_instance = ZDBApp()
            zdb_window = Window("ZDataBase", zdb_app_instance.width,
                                zdb_app_instance.height, new_x, new_y, zdb_app=zdb_app_instance)
            windows.append(zdb_window)
            taskbar.add_icon(zdb_window.taskbar_icon)
            zdb_window.bring_to_front(windows)
        elif self.is_app and self.name == "InfZov":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 1280 > screen_width:
                    new_x = 200
                if new_y + 720 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200
            infzov_app_instance = InfZovApp()
            infzov_window = Window("InfZov", infzov_app_instance.width,
                                   infzov_app_instance.height, new_x,
                                   new_y,
                                   infzov_app=infzov_app_instance)
            windows.append(infzov_window)
            taskbar.add_icon(infzov_window.taskbar_icon)
            infzov_window.bring_to_front(windows)
        elif self.is_app and self.name == "Календарь":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 400 > screen_width:
                    new_x = 200
                if new_y + 400 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = screen_width - 450
                new_y = 100

            calendar_app_instance = CalendarApp()
            calendar_window = Window("Календарь", calendar_app_instance.width,
                                     calendar_app_instance.height, new_x, new_y, calendar_app=calendar_app_instance)
            windows.append(calendar_window)
            taskbar.add_icon(calendar_window.taskbar_icon)
            calendar_window.bring_to_front(windows)
        elif self.is_app and self.name == "Диспетчер задач":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 400 > screen_width:
                    new_x = 200
                if new_y + 500 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 300
                new_y = 200

            task_manager_app_instance = TaskManagerApp()
            task_manager_window = Window("Диспетчер задач", task_manager_app_instance.width,
                                         task_manager_app_instance.height, new_x, new_y, task_manager_app=task_manager_app_instance)
            windows.append(task_manager_window)
            taskbar.add_icon(task_manager_window.taskbar_icon)
            task_manager_window.bring_to_front(windows)
        elif self.is_app and self.name == "Pong":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 800 > screen_width:
                    new_x = 200
                if new_y + 600 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200

            pong_game_app_instance = PongGameApp()
            pong_window = Window("Pong", pong_game_app_instance.width,
                                 pong_game_app_instance.height, new_x, new_y, pong_game_app=pong_game_app_instance)
            windows.append(pong_window)
            taskbar.add_icon(pong_window.taskbar_icon)
            pong_window.bring_to_front(windows)
        elif self.is_app and self.name == "Tetris":
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + 800 > screen_width:
                    new_x = 200
                if new_y + 600 + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200

            tetris_game_app_instance = TetrisGameApp()
            tetris_window = Window("Tetris", tetris_game_app_instance.width,
                                   tetris_game_app_instance.height, new_x, new_y, tetris_game_app=tetris_game_app_instance)
            windows.append(tetris_window)
            taskbar.add_icon(tetris_window.taskbar_icon)
            tetris_window.bring_to_front(windows)
        elif self.is_app and self.name == "Snake Game":  # Snake Game integration
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + SnakeGameApp(game_font, window_color, text_color, red, black).width > screen_width:
                    new_x = 200
                if new_y + SnakeGameApp(game_font, window_color, text_color, red, black).height + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200

            snake_game_app_instance = SnakeGameApp(
                game_font, window_color, text_color, red, black)
            snake_window = Window("Snake Game", snake_game_app_instance.width,
                                  snake_game_app_instance.height, new_x, new_y, snake_game_app=snake_game_app_instance)
            windows.append(snake_window)
            taskbar.add_icon(snake_window.taskbar_icon)
            snake_window.bring_to_front(windows)
        elif self.is_app and self.name == "Minesweeper":  # Minesweeper integration
            if windows:
                last_window = windows[-1]
                new_x = last_window.title_bar.x + 30
                new_y = last_window.title_bar.y + 30
                if new_x + MinesweeperApp().width > screen_width:
                    new_x = 200
                if new_y + MinesweeperApp().height + 50 > screen_height:
                    new_y = 200
            else:
                new_x = 200
                new_y = 200

            minesweeper_app_instance = MinesweeperApp()
            minesweeper_window = Window("Minesweeper", minesweeper_app_instance.width,
                                        minesweeper_app_instance.height, new_x, new_y, minesweeper_app=minesweeper_app_instance)
            windows.append(minesweeper_window)
            taskbar.add_icon(minesweeper_window.taskbar_icon)
            minesweeper_window.bring_to_front(windows)

    def show_properties(self):
        """Shows the properties window for this DesktopFile."""
        if windows:
            last_window = windows[-1]
            new_x = last_window.title_bar.x + 30
            new_y = last_window.title_bar.y + 30
            if new_x + 400 > screen_width:
                new_x = 200
            if new_y + 300 + 50 > screen_height:
                new_y = 200
        else:
            new_x = 200
            new_y = 200

        properties_text = f"Имя: {self.name}\n"
        if self.file_type == "folder":
            properties_text += f"Тип: Папка\n"
        elif self.file_type == "text":
            properties_text += f"Тип: Текстовый файл (.txt)\n"
        else:
            properties_text += f"Тип: Приложение\n"  # For apps and others

        properties_window = PropertiesWindow(
            title=f"Свойства: {self.name}",
            width=400, height=300, x=new_x, y=new_y,
            properties_text=properties_text
        )
        windows.append(properties_window)
        taskbar.add_icon(properties_window.taskbar_icon)
        properties_window.bring_to_front(windows)


def load_icon_position_from_db(icon_name):
    conn = sqlite3.connect('system_settings.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT x, y FROM desktop_icons WHERE icon_name=?", (icon_name,))
    result = cursor.fetchone()
    conn.close()
    return (result[0], result[1]) if result else None


class Folder(DesktopFile):
    def __init__(self, name, x, y, parent_folder=None):
        super().__init__(name, "folder.png", x, y, file_type="folder",
                         parent_folder=parent_folder)
        self.files_inside = []

    def handle_event(self, event, files, windows, context_menu, trash, moving_file_to_front, taskbar,
                     icon_layout_setting):
        super().handle_event(event, files, windows, context_menu,
                             trash, moving_file_to_front, taskbar, icon_layout_setting)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            context_menu_options = ["Открыть",
                                    "Переименовать", "Удалить", "Свойства", "Создать .txt", "Создать папку", "Вставить", "Копировать", "Вырезать"]  # Added options
            context_menu = ContextMenu(
                event.pos[0], event.pos[1], context_menu_options, self, context="folder")

    def show_properties(self):
        """Shows the properties window for this Folder."""
        if windows:
            last_window = windows[-1]
            new_x = last_window.title_bar.x + 30
            new_y = last_window.title_bar.y + 30
            if new_x + 400 > screen_width:
                new_x = 200
            if new_y + 300 + 50 > screen_height:
                new_y = 200
        else:
            new_x = 200
            new_y = 200

        properties_text = f"Имя: {self.name}\n"
        properties_text += f"Тип: Папка\n"
        properties_text += f"Содержит: {len(self.files_inside)} объектов\n"

        properties_window = PropertiesWindow(
            title=f"Свойства: {self.name}",
            width=400, height=300, x=new_x, y=new_y,
            properties_text=properties_text
        )
        windows.append(properties_window)
        taskbar.add_icon(properties_window.taskbar_icon)
        properties_window.bring_to_front(windows)


class Trash:
    def __init__(self, x, y):
        try:
            self.original_image = pygame.image.load(
                os.path.join("images", "musor.png")).convert_alpha()
            self.image = self.original_image
        except FileNotFoundError:
            self.original_image = pygame.Surface((64, 64), pygame.SRCALPHA)
            self.original_image.fill(light_gray)
            self.image = self.original_image

        self.rect = self.image.get_rect(topleft=(x, y))
        self.selected = False
        self.dragging = False
        self.name_surface = file_font.render(
            "Корзина", True, text_color)
        self.name_rect = self.name_surface.get_rect(
            center=(self.rect.centerx, self.rect.bottom + 20))

        padding_x = self.rect.width * 0.10
        padding_y = self.rect.height * 0.10 + 15

        selection_width = int(self.rect.width * 2)
        selection_height = int(self.rect.height + padding_y * 2)

        selection_x = int(self.rect.left - padding_x)
        selection_y = int(self.rect.top - padding_y)

        self.selection_rect = pygame.Rect(
            selection_x, selection_y, selection_width, selection_height)
        self.selection_surface = pygame.Surface(
            (selection_width, selection_height), pygame.SRCALPHA)
        self.selection_surface.fill(dark_blue)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        screen.blit(self.name_surface, self.name_rect)

    def handle_event(self, event, files):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                context_menu_options = [
                    "Очистить корзину"]
                context_menu = ContextMenu(
                    event.pos[0], event.pos[1], context_menu_options, None, context="trash")


class PuskMenu:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 200, 200)  # Adjusted initial height
        self.is_open = False
        self.expanded_power_menu = False
        self.options = [
            "Приложения",
            "Настройки",
            "Выключение",
            "Pong",
            "Tetris",
            "Snake Game",
            "Minesweeper",
            "Диспетчер задач"  # Added Task Manager to the text menu
        ]
        self.power_options = ["Выключить", "Перезагрузить", "Спящий режим"]
        self.option_surfaces = [taskbar_font.render(
            opt, True, text_color) for opt in self.options]
        self.power_option_surfaces = [taskbar_font.render(
            opt, True, text_color) for opt in self.power_options]
        self.option_rects = []
        self.power_option_rects = []
        self.option_height = 30  # Consistent option height
        self.padding_x = 10
        self.padding_y = 10
        self.menu_width = self.rect.width  # Fixed menu width
        self.menu_height = (len(self.options) + (len(self.power_options) if self.expanded_power_menu else 0) +
                            1) * self.option_height + 2 * self.padding_y  # Adjust menu height dynamically
        self.rect.height = 0  # Start with zero height for animation

        self.search_rect = pygame.Rect(
            # Search bar size
            x + self.padding_x, y + self.padding_y, self.menu_width - 2 * self.padding_x, 25)
        self.search_text = ""
        self.search_active = False

        self.animation_duration = 0.2
        self.animation_start_time = 0
        self.menu_state = 'closed'
        self.target_height = self.menu_height  # Target height is calculated dynamically
        self.rect.height = 0

    def draw(self, screen):
        if self.menu_state != 'closed':
            if self.menu_state == 'opening':
                elapsed_time = time.time() - self.animation_start_time
                progress = min(elapsed_time / self.animation_duration, 1)
                self.rect.height = int(self.target_height * progress)
                if progress == 1:
                    self.menu_state = 'open'
            elif self.menu_state == 'closing':
                elapsed_time = time.time() - self.animation_start_time
                progress = min(elapsed_time / self.animation_duration, 1)
                self.rect.height = int(self.target_height * (1 - progress))
                if progress == 1:
                    self.menu_state = 'closed'
                    self.is_open = False
                    self.expanded_power_menu = False

            draw_rect(screen, window_color, self.rect)
            draw_rect(screen, light_gray, self.rect, 2)

            draw_rect(screen, white, self.search_rect)
            draw_rect(screen, black, self.search_rect, 1)
            draw_text(screen, self.search_text, taskbar_font, black,
                      (self.search_rect.x + 5, self.search_rect.y + 5), 'topleft')

            self.option_rects = []
            option_y = self.search_rect.bottom + self.padding_y  # Start below search bar

            for i, option_surface in enumerate(self.option_surfaces):
                option_rect = pygame.Rect(
                    self.rect.x + self.padding_x,
                    option_y,
                    self.menu_width - 2 * self.padding_x,
                    self.option_height
                )
                self.option_rects.append(option_rect)

                if option_rect.collidepoint(pygame.mouse.get_pos()):
                    # Highlight on hover
                    draw_rect(screen, light_blue_grey, option_rect)

                draw_text(screen, self.options[i], taskbar_font, text_color,
                          option_rect.center, 'center')
                option_y += self.option_height

            # Power Options Submenu
            if self.expanded_power_menu:
                power_menu_x_offset = self.rect.right
                power_menu_width = 150
                power_menu_rect = pygame.Rect(
                    power_menu_x_offset,
                    # Position relative to last main option
                    self.rect.y + \
                    self.option_rects[-1].bottom + self.padding_y,
                    power_menu_width,
                    len(self.power_options) * \
                    self.option_height + 2 * self.padding_y
                )
                draw_rect(screen, window_color, power_menu_rect)
                draw_rect(screen, light_gray, power_menu_rect, 2)
                self.power_option_rects = []
                power_option_y = power_menu_rect.y + self.padding_y
                for i, power_option_surface in enumerate(self.power_option_surfaces):
                    power_rect = pygame.Rect(
                        power_menu_rect.x + self.padding_x,
                        power_option_y,
                        power_menu_width - 2 * self.padding_x,
                        self.option_height
                    )
                    self.power_option_rects.append(power_rect)
                    if power_rect.collidepoint(pygame.mouse.get_pos()):
                        # Highlight on hover
                        draw_rect(screen, light_blue_grey, power_rect)
                    draw_text(screen, self.power_options[i], taskbar_font, text_color,
                              power_rect.center, 'center')
                    power_option_y += self.option_height

    def handle_event(self, event, files, windows, taskbar):
        if self.menu_state != 'open':
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos) and not (self.expanded_power_menu and pygame.Rect(self.rect.right, self.rect.y + self.option_rects[-1].bottom + self.padding_y, 150, len(self.power_options) * self.option_height + 2 * self.padding_y).collidepoint(event.pos) if self.expanded_power_menu else False):
                self.start_close_animation()
                return True

            if self.search_rect.collidepoint(event.pos):
                self.search_active = True
            else:
                self.search_active = False

            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    option = self.options[i]

                    if option == "Выключение":
                        self.expanded_power_menu = not self.expanded_power_menu
                        self.target_height = self.menu_height = (len(self.options) + (len(self.power_options) if self.expanded_power_menu else 0) + 1) * \
                            self.option_height + 2 * self.padding_y  # recalculate height based on expanded power menu

                    elif option == "Настройки":
                        settings_file = None
                        for f in files:
                            if f.name == "Настройки" and f.is_app:
                                settings_file = f
                                break
                        if settings_file:
                            settings_file.open_file(
                                files, windows, taskbar, None)
                            self.start_close_animation()
                    elif option == "Приложения":
                        browser_file = None  # Replaced "Programs" with "Applications" and updated logic
                        for f in files:
                            if f.name == "Браузер" and f.is_app:  # Assuming "Browser" app for "Applications"
                                browser_file = f
                                break
                        if browser_file:
                            browser_file.open_file(
                                files, windows, taskbar, None)
                            self.start_close_animation()
                    elif option == "Диспетчер задач":
                        task_manager_file = None
                        for f in files:
                            if f.name == "Диспетчер задач" and f.is_app:
                                task_manager_file = f
                                break
                        if task_manager_file:
                            task_manager_file.open_file(
                                files, windows, taskbar, None)
                            self.start_close_animation()
                    elif option == "Pong":
                        pong_file = None
                        for f in files:
                            if f.name == "Pong" and f.is_app:
                                pong_file = f
                                break
                        if pong_file:
                            pong_file.open_file(
                                files, windows, taskbar, None)
                            self.start_close_animation()
                    elif option == "Tetris":
                        tetris_file = None
                        for f in files:
                            if f.name == "Tetris" and f.is_app:
                                tetris_file = f
                                break
                        if tetris_file:
                            tetris_file.open_file(
                                files, windows, taskbar, None)
                            self.start_close_animation()
                    elif option == "Snake Game":
                        snake_file = None
                        for f in files:
                            if f.name == "Snake Game" and f.is_app:
                                snake_file = f
                                break
                        if snake_file:
                            snake_file.open_file(files, windows, taskbar, None)
                            self.start_close_animation()
                    elif option == "Minesweeper":
                        minesweeper_file = None
                        for f in files:
                            if f.name == "Minesweeper" and f.is_app:
                                minesweeper_file = f
                                break
                        if minesweeper_file:
                            minesweeper_file.open_file(
                                files, windows, taskbar, None)
                            self.start_close_animation()

                    return True

            if self.expanded_power_menu:
                for i, power_rect in enumerate(self.power_option_rects):
                    if power_rect.collidepoint(event.pos):
                        power_option = self.power_options[i]
                        if power_option == "Выключить":
                            pygame.quit()
                            sys.exit()
                        elif power_option == "Перезагрузить":
                            os.execl(sys.executable, sys.executable, *sys.argv)
                        elif power_option == "Спящий режим":
                            print("Спящий режим")

                        self.start_close_animation()
                        return True

        elif event.type == pygame.KEYDOWN:
            if self.search_active:
                if event.key == pygame.K_RETURN:
                    self.search_files(files, windows, taskbar)
                elif event.key == pygame.K_BACKSPACE:
                    self.search_text = self.search_text[:-1]
                elif event.unicode:
                    self.search_text += event.unicode

        return False

    def search_files(self, files, windows, taskbar):
        search_query = self.search_text.lower()
        results = [f for f in files if search_query in f.name.lower()]

        if results:
            print("Search Results:")
            for res in results:
                print(f"- {res.name}")

            if results:
                results[0].open_file(files, windows, taskbar, None)
                self.start_close_animation()
        else:
            print("No files found.")

    def start_open_animation(self):
        if self.menu_state == 'closed':
            self.is_open = True
            self.menu_state = 'opening'
            self.animation_start_time = time.time()

    def start_close_animation(self):
        if self.menu_state == 'open':
            self.menu_state = 'closing'
            self.animation_start_time = time.time()
            self.expanded_power_menu = False


class ContextMenu:
    def __init__(self, x, y, options, file=None, context="desktop", folder_window=None):
        self.x = x
        self.y = y
        self.options = options
        self.item_height = 30
        max_width = 0
        self.option_surfaces = []

        for option in options:
            text_surface = context_menu_font.render(
                option, True, text_color)
            self.option_surfaces.append(text_surface)
            width = text_surface.get_width() + 20  # Padding
            if width > max_width:
                max_width = width
        self.width = max_width if max_width > 150 else 150

        self.height = len(options) * self.item_height
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.selected_option = -1
        self.is_open = True
        self.file_name_input = ""
        self.is_typing = False
        self.selected_option_index_for_input = None
        self.creation_requested = False
        self.mouse_x, self.mouse_y = 0, 0
        self.selected_file = file
        self.create_txt_button_visible = "Создать .txt" in options
        self.create_folder_button_visible = "Создать папку" in options
        self.input_rect_width = 200
        self.input_rect_height = 30
        self.input_font = context_menu_font
        self.context = context
        self.folder_window = folder_window
        self.cut_file = cut_file
        self.parent_menu = None  # For submenu support
        self.submenu = None  # To hold a potential submenu instance

    def draw(self, screen):
        if self.is_open:
            # Slightly darker selection color
            light_gray_selection = (200, 200, 200)
            black = (0, 0, 0)
            white = (255, 255, 255)

            draw_rect(screen, window_color, self.rect)
            draw_rect(screen, black, self.rect, 1)

            for i, option_surface in enumerate(self.option_surfaces):
                text_rect = option_surface.get_rect(
                    # Removed icon padding from x
                    topleft=(self.x + 10, self.y + i * self.item_height + 5))

                if i == self.selected_option:
                    draw_rect(screen, light_gray_selection, (self.x, self.y +
                                                             i * self.item_height, self.width, self.item_height))

                screen.blit(option_surface, text_rect)

            if self.is_typing and self.selected_option_index_for_input is not None:
                option_rect = pygame.Rect(
                    self.x, self.y + self.selected_option_index_for_input * self.item_height, self.width,
                    self.item_height)
                input_rect = pygame.Rect(
                    option_rect.right + 5, option_rect.top, self.input_rect_width, self.input_rect_height)
                input_rect.centery = option_rect.centery
                draw_rect(screen, window_color, input_rect)
                draw_rect(screen, black, input_rect, 1)
                draw_text(screen, self.file_name_input, self.input_font,
                          text_color, (input_rect.x + 5, input_rect.y + 5), 'topleft')

            if self.submenu and self.selected_option != -1 and isinstance(self.options[self.selected_option], dict) and 'submenu' in self.options[self.selected_option]:
                self.submenu.draw(screen)

    def handle_event(self, event, files, windows, taskbar, desktop_files, clipboard_file):
        if not self.is_open:
            return

        if self.submenu and self.submenu.is_open:
            self.submenu.handle_event(
                event, files, windows, taskbar, desktop_files, clipboard_file)
            return

        if event.type == pygame.MOUSEMOTION:
            self.selected_option = -1
            for i in range(len(self.options)):
                option_rect = pygame.Rect(
                    self.x, self.y + i * self.item_height, self.width, self.item_height)
                if option_rect.collidepoint(event.pos):
                    self.selected_option = i
                    if isinstance(self.options[i], dict) and 'submenu' in self.options[i]:
                        submenu_options = self.options[i]['submenu']
                        submenu_x = self.x + self.width
                        submenu_y = self.y + i * self.item_height
                        if not self.submenu or not self.submenu.is_open:
                            self.submenu = ContextMenu(
                                submenu_x, submenu_y, submenu_options, file=self.selected_file, context=self.context, folder_window=self.folder_window)
                            self.submenu.parent_menu = self
                            self.submenu.open()
                    else:
                        if self.submenu:
                            self.submenu.close()
                            self.submenu = None
                    break
            else:  # Mouse not over any option in this menu
                if event.pos[0] < self.x or event.pos[0] > self.x + self.width or event.pos[1] < self.y or event.pos[1] > self.y + self.height:
                    if self.submenu and self.submenu.is_open:
                        if not self.submenu.rect.collidepoint(event.pos):
                            self.submenu.close()
                            self.submenu = None

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.selected_option != -1:
                    selected_menu_item = self.options[self.selected_option]

                    if isinstance(selected_menu_item, dict):
                        option = selected_menu_item.get('text')
                        action = selected_menu_item.get('action')
                    else:  # For simple string options
                        option = selected_menu_item
                        action = None

                    if option == "Создать .txt" and self.create_txt_button_visible:
                        self.start_typing("Создать .txt")
                    elif option == "Создать папку" and self.create_folder_button_visible:
                        self.start_typing("Создать папку")
                    elif option == "Переименовать":
                        self.start_typing("Переименовать", initial_text=self.selected_file.name.replace(
                            ".txt", "").replace("/", ""))
                    elif option == "Удалить":
                        self.handle_delete(files, desktop_files)
                    elif option == "Открыть":
                        self.handle_open(files, windows, taskbar)
                    elif option == "Свойства":
                        self.handle_properties()
                    elif option == "Копировать":
                        self.handle_copy(clipboard_file)
                    elif option == "Вырезать":
                        self.handle_cut(clipboard_file)
                    elif option == "Вставить":
                        self.handle_paste(
                            clipboard_file, files, desktop_files, event)
                    elif option == "Копировать путь":
                        self.handle_copy_path()
                    elif option == "Создать ярлык":
                        self.handle_create_shortcut(desktop_files)
                    elif option == "Очистить корзину":
                        self.handle_clear_trash(files)
                    elif option == "Обновить":
                        self.handle_refresh(files, windows, taskbar)
                    elif option == "Вернуть на рабочий стол":
                        self.handle_return_to_desktop(desktop_files)
                    # Custom action associated with menu item (e.g. from submenu)
                    elif action:
                        action(self, files, windows, taskbar,
                               desktop_files, clipboard_file)
                        self.close_all()  # Close all menus after action.

                    else:
                        self.close()
                        self.selected_option = -1

        elif event.type == pygame.KEYDOWN:
            if self.is_typing:
                if event.key == pygame.K_RETURN:
                    self.handle_text_input_enter(files, desktop_files)
                elif event.key == pygame.K_BACKSPACE:
                    self.file_name_input = self.file_name_input[:-1]
                elif event.unicode:
                    self.handle_text_input_unicode(event)
            elif event.key == pygame.K_ESCAPE:  # Added ESC key to close menu
                self.close_all()
            elif event.key == pygame.K_DOWN:
                self.selected_option = (
                    self.selected_option + 1) % len(self.options)
                if self.submenu:
                    self.submenu.close()
                    self.submenu = None
            elif event.key == pygame.K_UP:
                self.selected_option = (
                    self.selected_option - 1) % len(self.options)
                if self.submenu:
                    self.submenu.close()
                    self.submenu = None
            elif event.key == pygame.K_RETURN:
                if self.selected_option != -1:
                    selected_menu_item = self.options[self.selected_option]
                    if isinstance(selected_menu_item, dict):
                        option = selected_menu_item.get('text')
                        action = selected_menu_item.get('action')
                    else:  # For simple string options
                        option = selected_menu_item
                        action = None

                    if option == "Создать .txt" and self.create_txt_button_visible:
                        self.start_typing("Создать .txt")
                    elif option == "Создать папку" and self.create_folder_button_visible:
                        self.start_typing("Создать папку")
                    elif option == "Переименовать":
                        self.start_typing("Переименовать", initial_text=self.selected_file.name.replace(
                            ".txt", "").replace("/", ""))
                    elif option == "Удалить":
                        self.handle_delete(files, desktop_files)
                    elif option == "Открыть":
                        self.handle_open(files, windows, taskbar)
                    elif option == "Свойства":
                        self.handle_properties()
                    elif option == "Копировать":
                        self.handle_copy(clipboard_file)
                    elif option == "Вырезать":
                        self.handle_cut(clipboard_file)
                    elif option == "Вставить":
                        self.handle_paste(
                            clipboard_file, files, desktop_files, event)
                    elif option == "Копировать путь":
                        self.handle_copy_path()
                    elif option == "Создать ярлык":
                        self.handle_create_shortcut(desktop_files)
                    elif option == "Очистить корзину":
                        self.handle_clear_trash(files)
                    elif option == "Обновить":
                        self.handle_refresh(files, windows, taskbar)
                    elif option == "Вернуть на рабочий стол":
                        self.handle_return_to_desktop(desktop_files)
                    # Custom action associated with menu item (e.g. from submenu)
                    elif action:
                        action(self, files, windows, taskbar,
                               desktop_files, clipboard_file)
                        self.close_all()  # Close all menus after action.
                    else:
                        # Just close the menu if no action and not typing.
                        self.close_all()

    def start_typing(self, option_name, initial_text=""):
        self.is_typing = True
        self.selected_option_index_for_input = self.selected_option
        self.file_name_input = initial_text
        self.creation_requested = option_name in [
            "Создать .txt", "Создать папку"]
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.create_txt_button_visible = False
        self.create_folder_button_visible = False

    def handle_text_input_enter(self, files, desktop_files):
        if self.creation_requested:
            if "Создать .txt" in self.options and self.selected_option == 0:
                new_file_name = self.file_name_input + ".txt"
                new_file = DesktopFile(
                    new_file_name, "txtfile.png", self.mouse_x, self.mouse_y, parent_folder=self.folder_window.folder if self.folder_window else None)
                if self.folder_window and self.folder_window.folder:
                    self.folder_window.folder.files_inside.append(new_file)
                else:
                    desktop_files.append(new_file)
                new_file.content = ""
                if icon_layout_setting == 'grid':
                    save_icon_position(new_file)

            elif "Создать папку" in self.options and self.selected_option == 1:
                new_folder_name = self.file_name_input
                new_folder = Folder(
                    new_folder_name, self.mouse_x, self.mouse_y, parent_folder=self.folder_window.folder if self.folder_window else None)
                if self.folder_window and self.folder_window.folder:
                    self.folder_window.folder.files_inside.append(new_folder)
                else:
                    desktop_files.append(new_folder)
                if icon_layout_setting == 'grid':
                    save_icon_position(new_folder)
        else:  # Renaming
            new_file_name = self.file_name_input + \
                (".txt" if self.selected_file.name.endswith(".txt") else "")
            self.selected_file.name = new_file_name
            save_icon_position(self.selected_file)
        self.close()

    def handle_text_input_unicode(self, event):
        valid_char = event.unicode.isalnum() or event.unicode == ' ' or event.unicode == '.'
        if valid_char and self.input_font.render(self.file_name_input + event.unicode, True,
                                                 black).get_width() <= self.input_rect_width - 10:
            self.file_name_input += event.unicode

    def handle_delete(self, files, desktop_files):
        if self.selected_file.protected:
            print("Error: Cannot delete protected system file.")
        else:
            if self.selected_file.file_type == "folder":
                files_to_remove = [self.selected_file]
                files_to_remove.extend(self.selected_file.files_inside)
                for file_to_remove in files_to_remove:
                    if file_to_remove in files:
                        files.remove(file_to_remove)
                    if file_to_remove.parent_folder and file_to_remove in file_to_remove.parent_folder.files_inside:
                        file_to_remove.parent_folder.files_inside.remove(
                            file_to_remove)
            elif self.selected_file in files:
                files.remove(self.selected_file)
            self.close()

    def handle_open(self, files, windows, taskbar):
        if self.selected_file:
            self.selected_file.open_file(
                files, windows, taskbar, self.folder_window.folder if self.folder_window else None)
            self.close()

    def handle_properties(self):
        if self.selected_file:
            self.selected_file.show_properties()
            self.close()

    def handle_copy(self, clipboard_file):
        clipboard_file[0] = self.selected_file
        self.cut_file = None
        self.close()

    def handle_cut(self, clipboard_file):
        clipboard_file[0] = self.selected_file
        self.cut_file = self.selected_file
        self.close()

    def handle_paste(self, clipboard_file, files, desktop_files, event):
        if clipboard_file[0]:
            new_file = clipboard_file[0]
            if self.context == "folder" and self.folder_window and self.folder_window.folder:
                dest_folder = self.folder_window.folder
                if new_file not in dest_folder.files_inside and new_file.parent_folder != dest_folder:
                    if isinstance(new_file, Folder) and is_descendant(new_file, dest_folder):
                        print("Нельзя переместить папку в себя!")
                    else:
                        if self.cut_file == clipboard_file[0]:  # Cut operation
                            if new_file in desktop_files:
                                desktop_files.remove(new_file)
                            elif new_file.parent_folder:
                                if new_file in new_file.parent_folder.files_inside:
                                    new_file.parent_folder.files_inside.remove(
                                        new_file)
                        dest_folder.files_inside.append(new_file)
                        new_file.parent_folder = dest_folder
                        new_file.rect.topleft = (
                            event.pos[0] - self.folder_window.rect.x, event.pos[1] - self.folder_window.rect.y)
                        new_file.name_rect.center = (
                            new_file.rect.centerx, new_file.rect.bottom + 20)
                        new_file.update_selection_rect()
            elif self.context == "desktop_background":
                if new_file not in desktop_files and new_file.parent_folder is not None:
                    if self.cut_file == clipboard_file[0]:  # Cut operation
                        if new_file.parent_folder and new_file in new_file.parent_folder.files_inside:
                            new_file.parent_folder.files_inside.remove(
                                new_file)
                    desktop_files.append(new_file)
                    new_file.parent_folder = None
                    new_file.rect.topleft = (self.mouse_x, self.mouse_y)
                    new_file.name_rect.center = (
                        new_file.rect.centerx, new_file.rect.bottom + 20)
                    new_file.update_selection_rect()

            # Reset cut file after paste in case of cut
            if self.cut_file == clipboard_file[0]:
                clipboard_file[0] = None
                cut_file = None
            self.close()

    def handle_copy_path(self):
        if self.selected_file:
            filepath = os.path.abspath(os.path.join(".", "images", self.selected_file.image_path) if os.path.exists(
                os.path.join("images", self.selected_file.image_path)) else self.selected_file.name)
            # Encode to bytes for scrap.put_text
            pygame.scrap.put_text(filepath.encode('utf-8'))
            self.close()

    def handle_create_shortcut(self, desktop_files):
        if self.selected_file:
            shortcut_file = DesktopFile(
                name=f"{self.selected_file.name} - Ярлык",
                image_path=self.selected_file.image_path,
                x=self.mouse_x + 50, y=self.mouse_y + 50,
                is_app=self.selected_file.is_app,
                file_type=self.selected_file.file_type
            )
            desktop_files.append(shortcut_file)
            self.close()

    def handle_clear_trash(self, files):
        files_to_remove = [f for f in files if f.is_in_trash]
        for file_to_remove in files_to_remove:
            files.remove(file_to_remove)
        self.close()

    def handle_refresh(self, files, windows, taskbar):
        # widgets removed from params as not used in provided code
        refresh_settings_from_db(files, windows, taskbar, None)
        self.close()

    def handle_return_to_desktop(self, desktop_files):
        if self.selected_file and self.selected_file.parent_folder:
            folder = self.selected_file.parent_folder
            if self.selected_file in folder.files_inside:
                folder.files_inside.remove(self.selected_file)
                desktop_files.append(self.selected_file)
                self.selected_file.parent_folder = None
                self.selected_file.rect.topleft = (self.mouse_x, self.mouse_y)
                self.selected_file.name_rect.center = (
                    self.selected_file.rect.centerx, self.selected_file.rect.bottom + 20)
                self.selected_file.update_selection_rect()
        self.close()

    def open(self):
        self.is_open = True
        if self.parent_menu:
            self.parent_menu.close_submenu()  # Close any sibling submenus

    def close(self):
        self.is_open = False
        self.is_typing = False
        self.selected_option_index_for_input = None
        self.creation_requested = False
        self.create_txt_button_visible = True
        self.create_folder_button_visible = True
        if self.submenu:
            self.submenu.close()
            self.submenu = None

    def close_all(self):  # Closes self and all parent menus
        menu = self
        while menu:
            menu.close()
            menu = menu.parent_menu

    def close_submenu(self):  # To close only submenu, not the parent
        if self.submenu:
            self.submenu.close()
            self.submenu = None


class ThemedPuskButton:  # Changed class name to ThemedPuskButton
    def __init__(self, x, y, pusk_menu):
        self.x = x
        self.y = y
        self.pusk_menu = pusk_menu
        self.pusk_button_active = False
        self.update_image()  # Call update_image to set initial image based on theme
        self.rect = self.image.get_rect(topleft=(x, y))

    def update_image(self):  # Added method to update image based on theme
        global current_theme_setting
        if current_theme_setting == 'dark':
            image_path = "puskbutton2.png"  # Use puskbutton2.png for dark theme
        else:
            image_path = "puskbutton1.png"  # Use puskbutton1.png for light theme
        try:
            self.original_image = pygame.image.load(
                os.path.join("images", image_path)).convert_alpha()
            self.image = self.original_image
        except pygame.error as e:
            print(f"Error loading pusk button image: {image_path}, error: {e}")
            self.original_image = pygame.Surface((60, 60))
            self.original_image.fill(light_gray)
            self.image = self.original_image
        except FileNotFoundError:
            print(f"Error: Pusk button image file not found: {image_path}")
            self.original_image = pygame.Surface((60, 60))
            self.original_image.fill(light_gray)
            self.image = self.original_image

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.pusk_menu.menu_state == 'closed':
                    self.pusk_menu.start_open_animation()
                    self.pusk_button_active = True
                elif self.pusk_menu.menu_state == 'open':
                    self.pusk_menu.start_close_animation()
                    self.pusk_button_active = False
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                if self.pusk_menu.menu_state == 'open':
                    self.pusk_menu.start_close_animation()
                    self.pusk_button_active = False


class Taskbar:
    def __init__(self, height):
        self.rect = pygame.Rect(
            0, screen_height - height, screen_width, height)
        self.icons = []
        self.icon_width = int(get_setting('taskbar_icon_size', '40'))
        self.icon_height = int(get_setting('taskbar_icon_size', '40'))
        self.icon_margin = 10
        self.pusk_menu = PuskMenu(10, screen_height - 350 - height)
        self.pusk_button_x = 10
        self.pusk_button_y = screen_height - height + (height - 60) // 2
        self.pusk_button = ThemedPuskButton(  # используем ThemedPuskButton
            self.pusk_button_x, self.pusk_button_y, self.pusk_menu)  # Передаем pusk_menu
        self.taskbar_color = taskbar_color
        self.taskbar_height = height
        self.time_rect = None

    def update_color(self):
        global taskbar_color
        self.taskbar_color = taskbar_color
        self.pusk_button.update_image()  # Обновляем картинку кнопки при смене темы

    def update_size_and_color(self, height):
        self.rect.height = height
        self.rect.y = screen_height - height
        self.taskbar_height = height
        self.pusk_menu.rect.y = screen_height - 350 - height
        self.pusk_button_y = screen_height - height + (height - 60) // 2
        self.pusk_button.rect.y = self.pusk_button_y

    def add_icon(self, icon):
        self.icons.append(icon)

    def remove_icon(self, icon):
        if icon in self.icons:
            self.icons.remove(icon)

    def draw_time(self, screen):
        current_time_str = time.strftime("%H:%M:%S")
        time_surface = taskbar_font.render(current_time_str, True, text_color)
        time_rect = time_surface.get_rect(
            topright=(screen_width - 10, self.rect.centery))
        time_rect.centery = self.rect.centery
        screen.blit(time_surface, time_rect)
        self.time_rect = time_rect

    def draw(self, screen):
        draw_rect(screen, self.taskbar_color, self.rect)
        self.pusk_button.draw(screen)
        icon_x = self.pusk_button_x + self.pusk_button.rect.width + self.icon_margin

        for icon in self.icons:
            icon.draw(screen, icon_x, self.rect.y +
                      (self.rect.height - icon.height) // 2)
            icon_x += icon.width + self.icon_margin

        self.draw_time(screen)

    def handle_event(self, event, windows, files, taskbar):
        if self.pusk_menu.handle_event(event, files, windows, taskbar):
            return

        self.pusk_button.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            icon_x = self.pusk_button_x + self.pusk_button.rect.width + self.icon_margin
            for icon in self.icons:
                icon_rect = pygame.Rect(icon_x, self.rect.y + (
                    self.rect.height - icon.height) // 2, icon.width, icon.height)
                if icon_rect.collidepoint(event.pos):
                    if icon.window.window_state == "minimized":
                        icon.window.window_state = "normal"
                    elif windows and windows[-1] == icon.window:
                        icon.window.window_state = "minimized"
                    else:
                        icon.window.bring_to_front(windows)
                    break
                icon_x += icon.width + self.icon_margin


class TaskbarIcon:
    def __init__(self, window, image_path):
        self.window = window
        self.width = int(get_setting('taskbar_icon_size', '40'))
        self.height = int(get_setting('taskbar_icon_size', '40'))
        self.image_path = image_path
        self.image = None
        self.original_image = None
        if self.image_path:
            try:
                original_image = pygame.image.load(os.path.join(
                    "images", self.image_path)).convert_alpha()
                self.original_image = original_image
                self.update_image_scale()
            except pygame.error as e:
                self.image = None
            except FileNotFoundError as e:  # Handle file not found for taskbar icons too
                print(f"Taskbar Icon File Not Found: {image_path}. Error: {e}")
                self.image = None

    def update_size(self, size):
        self.width = size
        self.height = size
        self.update_image_scale()

    def update_image_scale(self):
        if self.original_image:
            image_ratio = self.original_image.get_width() / self.original_image.get_height()

            if image_ratio > 1:
                scaled_width = self.width
                scaled_height = int(self.width / image_ratio)
            else:
                scaled_height = self.height
                scaled_width = int(self.height * image_ratio)

            self.image = pygame.transform.scale(
                self.original_image, (scaled_width, scaled_height))

    def draw(self, screen, x, y):
        icon_rect = pygame.Rect(x, y, self.width, self.height)
        if self.image:
            image_x = x + (self.width - self.image.get_width()) // 2
            image_y = y + (self.height - self.image.get_height()) // 2
            screen.blit(self.image, (image_x, image_y))
        else:
            draw_text(screen, "Error", taskbar_font,
                      black, icon_rect.center, 'center')

    def get_preview(self):
        if self.window and self.window.preview_surface:
            return self.window.preview_surface
        return None


class PropertiesWindow(Window):
    def __init__(self, title, width, height, x, y, properties_text):
        super().__init__(title, width, height, x, y, properties_text=properties_text)


widgets = []
widgets.append(ClockWidget(10, 10))
widgets.append(CalendarWidget(220, 10))

files = []

files.append(DesktopFile(
    name="Настройки",
    image_path="settings_icon.png",
    x=10, y=150,
    is_app=True,
    protected=True
))

files.append(DesktopFile(
    name="Браузер",
    image_path="browser_icon.png",
    x=10, y=250,
    is_app=True,
    protected=True
))

files.append(DesktopFile(
    name="Калькулятор",
    image_path="calculator_icon.png",
    x=10, y=350,
    is_app=True
))

files.append(Folder(
    name="Новая папка",
    x=200, y=210
))
files.append(DesktopFile(
    name="апвыа",
    image_path="авпыашка.png",
    x=10, y=450,
    is_app=True
))
files.append(DesktopFile(
    name="ZText",
    image_path="ztext.png",
    x=110, y=250,
    is_app=True
))
files.append(DesktopFile(
    name="ZTable",
    image_path="ztable.png",
    x=110, y=350,
    is_app=True
))

files.append(DesktopFile(
    name="ZDataBase",
    image_path="zbd.png",
    x=110, y=450,
    is_app=True
))
files.append(DesktopFile(
    name="Календарь",
    image_path="calendar_icon.png",
    x=110, y=580,
    is_app=True
))
files.append(DesktopFile(
    name="Диспетчер задач",
    image_path="task_manager_icon.png",
    x=10, y=680,
    is_app=True
))
files.append(DesktopFile(  # Pong game application
    name="Pong",
    image_path="pong_icon.png",  # Ensure you have pong_icon.png in images folder
    x=110, y=680,
    is_app=True
))
files.append(DesktopFile(  # Tetris game application
    name="Tetris",
    image_path="tetris_icon.png",  # Ensure you have tetris_icon.png in images folder
    x=210, y=150,
    is_app=True
))
files.append(DesktopFile(  # Snake game application
    name="Snake Game",
    image_path="snake_icon.png",  # Ensure you have snake_icon.png in images folder
    x=210, y=250,
    is_app=True
))
files.append(DesktopFile(  # Minesweeper game application
    name="Minesweeper",
    # Ensure you have minesweeper_icon.png in images folder
    image_path="minesweeper_icon.png",
    x=210, y=350,
    is_app=True
))


trash = Trash(1800, 10)

windows = []
context_menu = None
running = True
selected_file = None
dragging_file = None
dragged_files = []
clipboard_file = [None]
cut_file = None  # Global variable to store cut file

key_repeat_interval = 0.05
key_repeat_timer = 0
held_keys = set()

taskbar_height = int(get_setting('taskbar_height', '60'))
taskbar = Taskbar(taskbar_height)

is_selecting = False
selection_start_pos = None
selection_end_pos = None
hovered_taskbar_icon = None
file_being_dragged_from_folder = False  # Flag to indicate drag from folder
# Store the folder item was dragged from - added for drag fix
dragged_item_original_folder = None


def move_file_to_front(file):
    if file in files:
        files.remove(file)
        files.append(file)


if icon_layout_setting == 'grid':
    grid_size = 108 + 20
    for file in files:
        file.rect.topleft = file.get_grid_position(grid_size)
        file.name_rect.center = (
            file.rect.centerx, file.rect.bottom + 20)
        file.update_selection_rect()

load_icon_positions(files)


while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                if show_startup or show_loop:
                    show_startup = False
                    show_loop = False
                elif show_description:
                    show_description = False
            held_keys.add(event.key)
            key_repeat_timer = time.time()
            if event.key == pygame.K_DELETE:
                files_to_delete = [f for f in files if f.selected]
                for file_to_delete in files_to_delete:
                    if file_to_delete.protected:
                        print("Error: Cannot delete protected system file.")
                        continue
                    file_to_delete.is_in_trash = True
                    if file_to_delete in files:
                        files.remove(file_to_delete)
                    if file_to_delete.parent_folder and file_to_delete in file_to_delete.parent_folder.files_inside:
                        file_to_delete.parent_folder.files_inside.remove(
                            file_to_delete)

        if event.type == pygame.KEYUP:
            held_keys.discard(event.key)
            for window in windows:
                if window.text_input and window.file and window.file.name.endswith(
                        ".txt") and window.held_key == event.key:
                    window.held_key = None

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                selected_file = None
                for file in files:
                    if file.selection_rect.collidepoint(event.pos):
                        selected_file = file
                        break

                folder_window_instance = None
                for window in windows:
                    if window.folder and window.rect.collidepoint(event.pos):
                        folder_window_instance = window
                        break

                if selected_file and not selected_file.protected:
                    if selected_file.parent_folder:
                        context_menu_options = [
                            "Открыть", "Копировать", "Вырезать", "Вернуть на рабочий стол", "Удалить", "Свойства"]
                    else:
                        context_menu_options = [
                            "Открыть", "Копировать", "Вырезать", "Копировать путь", "Создать ярлык", "Переименовать", "Удалить", "Свойства"]

                    context_menu = ContextMenu(
                        event.pos[0], event.pos[1], context_menu_options, selected_file,
                        folder_window=folder_window_instance)
                elif not selected_file:
                    if folder_window_instance:
                        context_menu_options = [
                            "Создать .txt", "Создать папку", "Обновить", "Вставить"]
                        context_menu = ContextMenu(
                            event.pos[0], event.pos[1], context_menu_options, context="folder_background",
                            folder_window=folder_window_instance)
                    else:
                        context_menu_options = [
                            "Создать .txt", "Создать папку", "Обновить", "Вставить"]
                        context_menu = ContextMenu(
                            event.pos[0], event.pos[1], context_menu_options, context="desktop_background",
                            folder_window=folder_window_instance)
                elif trash.selection_rect.collidepoint(event.pos):
                    context_menu_options = ["Очистить корзину"]
                    context_menu = ContextMenu(
                        event.pos[0], event.pos[1], context_menu_options, None, context="trash",
                        folder_window=folder_window_instance)
                else:
                    context_menu = None
            elif event.button == 1:
                if context_menu and context_menu.is_open and not context_menu.rect.collidepoint(event.pos):
                    context_menu.close()
                desktop_clicked = True
                for file in files:
                    if file.selection_rect.collidepoint(event.pos):
                        desktop_clicked = False
                        break
                for window in windows:
                    if window.title_bar.collidepoint(event.pos) or window.rect.collidepoint(event.pos):
                        desktop_clicked = False
                        break
                if desktop_clicked:
                    is_selecting = True
                    selection_start_pos = event.pos
                    selection_end_pos = event.pos
                    for file in files:
                        if not (pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]):
                            file.selected = False

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if is_selecting:
                    is_selecting = False
                    selection_rect = pygame.Rect(selection_start_pos, (
                        selection_end_pos[0] - selection_start_pos[0], selection_end_pos[1] - selection_start_pos[1]))
                    selection_rect.normalize()
                    for file in files:
                        if file.selection_rect.colliderect(selection_rect):
                            file.selected = True
                    selection_start_pos = None
                    selection_end_pos = None
            if taskbar.pusk_button.rect.collidepoint(event.pos):
                taskbar.pusk_button.handle_event(event)
            elif taskbar.pusk_menu.is_open and not taskbar.pusk_menu.rect.collidepoint(event.pos) and not taskbar.pusk_button.rect.collidepoint(event.pos):
                taskbar.pusk_menu.start_close_animation()
                taskbar.pusk_button.pusk_button_active = False

        elif event.type == pygame.MOUSEMOTION:
            if is_selecting:
                selection_end_pos = event.pos

        for window in windows:
            window.handle_event(event, windows, taskbar,
                                files, icon_layout_setting)
            if event.type == pygame.MOUSEBUTTONDOWN and window.is_open and (window.title_bar.collidepoint(event.pos) or window.rect.collidepoint(event.pos)):
                window.bring_to_front(windows)
                break

        if not (context_menu and context_menu.is_open):
            for file in files:
                file.handle_event(event, files, windows,
                                  context_menu, trash, move_file_to_front, taskbar, icon_layout_setting)

        trash.handle_event(event, files)
        if context_menu is not None and context_menu.is_open:
            context_menu.handle_event(
                event, files, windows, taskbar, files, clipboard_file)
        taskbar.handle_event(event, windows, files, taskbar)
        settings_window = next(
            (win for win in windows if win.settings_app), None)
        if settings_window and settings_window.settings_app:
            settings_window.settings_app.handle_event(
                mouse_pos, settings_window.rect, event)

    for window in windows:
        if window.text_input and window.file and window.file.name.endswith(".txt"):
            if window.held_key is not None:
                current_time = time.time()
                if current_time - window.key_down_time >= window.key_repeat_delay:
                    if current_time - window.cursor_time >= window.key_repeat_interval:
                        window.cursor_time = current_time
                        unicode_char = pygame.key.name(window.held_key)
                        key_event = pygame.event.Event(
                            pygame.KEYDOWN, key=window.held_key, unicode=unicode_char)
                        window.handle_event(
                            key_event, windows, taskbar, files, icon_layout_setting)

    if show_startup:
        current_time = time.time()
        if frame_time == 0:
            frame_time = current_time
            startup_start_time = pygame.time.get_ticks()
            if sound_loaded:
                startup_sound.play()

        if current_time - frame_time >= frame_duration:
            current_frame += 1
            frame_time = current_time
            if current_frame >= len(opening_frames):
                current_frame = 0
                show_startup = False
                show_loop = True
                loop_frame_time = current_time

        if current_frame < len(opening_frames):
            screen.blit(opening_frames[current_frame], (0, 0))

        if pygame.time.get_ticks() - startup_start_time >= startup_duration * 1000:
            show_startup = False

    elif show_loop:
        current_time = time.time()
        if current_time - loop_frame_time >= frame_duration:
            current_loop_frame = (current_loop_frame + 1) % len(loop_frames)
            loop_frame_time = current_time

        screen.blit(loop_frames[current_loop_frame], (0, 0))

        if current_time - frame_time >= startup_duration:
            show_loop = False
            show_description = True
            description_start_time = pygame.time.get_ticks()

    else:
        screen.blit(background_image, (0, 0))

        trash.draw(screen)
        taskbar.draw(screen)

        if icon_layout_setting == 'grid':
            grid_size = 108 + 20
            for x in range(0, screen_width, grid_size):
                for y in range(0, screen_height - taskbar_height, grid_size):
                    draw_rect(screen, light_gray, (x, y, 1, 1))

        if is_selecting and selection_start_pos and selection_end_pos:
            selection_rect_draw = pygame.Rect(selection_start_pos, (
                selection_end_pos[0] - selection_start_pos[0], selection_end_pos[1] - selection_start_pos[1]))
            selection_rect_draw.normalize()
            draw_rect(screen, selection_color, selection_rect_draw)

        for widget in widgets:
            if widget.visible:
                widget.draw(screen)
                widget.update()

        delta_time = clock.tick(fps) / 1000.0

        for file in files:
            if file.dragging == False and file.parent_folder is None and not dragging_file == file:
                file.draw(screen)

        for window in windows:
            if window.window_state != "minimized":
                window.draw(screen)

        if dragging_file and dragging_file.dragging:
            # --- Drag and Drop Visual Fix: Draw dragged file only once, at mouse position ---
            dragged_file_render = dragging_file.image  # Get the file image
            dragged_file_rect = dragged_file_render.get_rect(
                center=mouse_pos)  # Position at mouse
            screen.blit(dragged_file_render, dragged_file_rect)  # Draw it
            # --- End Drag and Drop Fix ---

        for window in windows:
            if window.apvia_app and window.apvia_app.current_screen == "game":
                window.apvia_app.update_game(delta_time)
            if window.folder:
                window.draw_folder_content(screen.subsurface(
                    window.rect), window.folder.files_inside)
            if window.pong_game_app and window.pong_game_app.running:
                pass  # Pong game drawing is handled in Window.draw
            if window.tetris_game_app and window.tetris_game_app.running:
                pass  # Tetris game drawing is handled in Window.draw
            if window.snake_game_app and window.snake_game_app.running:
                pass  # Snake game drawing is handled in Window.draw
            if window.minesweeper_app and window.minesweeper_app.running:
                pass  # Minesweeper game drawing is handled in Window.draw

        hovered_taskbar_icon = None
        icon_x = taskbar.pusk_button_x + \
            taskbar.pusk_button.rect.width + taskbar.icon_margin
        for icon in taskbar.icons:
            icon_rect = pygame.Rect(icon_x, taskbar.rect.y + (
                taskbar.rect.height - icon.height) // 2, icon.width, icon.height)
            if icon_rect.collidepoint(mouse_pos):
                hovered_taskbar_icon = icon
                break

        if hovered_taskbar_icon:
            preview_surf = hovered_taskbar_icon.get_preview()
            if preview_surf:
                preview_rect = preview_surf.get_rect(
                    bottomleft=(mouse_pos[0] + 10, taskbar.rect.top))
                screen.blit(preview_surf, preview_rect)
                draw_rect(screen, black, preview_rect, 2)

        if context_menu is not None and context_menu.is_open:
            context_menu.draw(screen)

        taskbar.pusk_menu.draw(screen)

        windows_to_remove = []
        for window in windows:
            if not window.is_open:
                windows_to_remove.append(window)
        for window_to_remove in windows_to_remove:
            if window_to_remove in windows:
                windows.remove(window_to_remove)

        taskbar.icons = [icon for icon in taskbar.icons if icon.window.is_open]

        if time.time() - last_settings_refresh_time >= settings_refresh_interval:
            refresh_settings_from_db(files, windows, widgets, taskbar)
            last_settings_refresh_time = time.time()

        for file in files:
            if file.dragging == False and file.selected == False and icon_layout_setting == 'grid':
                save_icon_position(file)

        for window in windows:
            if window.is_open:
                save_window_state(window)

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
