import math
import random

import pygame

pygame.font.init()


class ApviaApp:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.menu_options = ["Основной режим", "Бесконечный режим", "Кастомизация"]
        self.difficulty_options = ["Очень легко", "Легко", "Нормально", "Тяжело", "Безумно", "Невозможно"]
        self.button_rects = []
        self.difficulty_button_rects = []
        self.customization_button_rects = []
        self.back_button_rect = None
        self.money_earning = True

        self.window_color = (255, 255, 255)
        self.button_color = (128, 0, 0)
        self.button_border_color = (255, 36, 0)
        self.text_color = (255, 255, 255)
        self.black = (0, 0, 0)
        self.light_gray = (200, 200, 200)
        self.green_color = (0, 255, 0)
        self.red_color = (255, 0, 0)
        self.blue_color = (0, 0, 255)
        self.purple_color = (128, 0, 128)
        self.orange_color = (255, 165, 0)
        self.white_color = (255, 255, 255)

        self.font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 42)
        self.score_font = pygame.font.SysFont(None, 32)
        self.timer_font = pygame.font.SysFont(None, 32)
        self.restart_font = pygame.font.SysFont(None, 32)
        self.menu_font = pygame.font.SysFont(None, 32)

        self.current_screen = "main_menu"
        self.current_game_mode = None  # 'main_game', 'infinite_game', None

        self.backgrounds = {
            'bg2': pygame.image.load('images/апвыа/background_textures/bg2.png'),
            'bg4': pygame.image.load('images/апвыа/background_textures/bg4.png'),
            'bg1': pygame.image.load('images/апвыа/background_textures/bg1.png'),
            'bg3': pygame.image.load('images/апвыа/background_textures/bg3.png'),
            'bg5': pygame.image.load('images/апвыа/background_textures/bg5.png'),
            'bg6': pygame.image.load('images/апвыа/background_textures/bg6.png'),
            'bg7': pygame.image.load('images/апвыа/background_textures/bg7.png'),
        }
        self.select_sprite = pygame.image.load('images/апвыа/background_textures/select.png')
        self.bg2_sprite = pygame.image.load('images/апвыа/background_textures/bg2_sprite.png')
        self.bg4_sprite = pygame.image.load('images/апвыа/background_textures/bg4_sprite.png')
        self.bg1_sprite = pygame.image.load('images/апвыа/background_textures/bg1_sprite.png')
        self.bg3_sprite = pygame.image.load('images/апвыа/background_textures/bg3_sprite.png')
        self.bg5_sprite = pygame.image.load('images/апвыа/background_textures/bg5_sprite.png')
        self.bg6_sprite = pygame.image.load('images/апвыа/background_textures/bg6_sprite.png')
        self.bg7_sprite = pygame.image.load('images/апвыа/background_textures/bg7_sprite.png')
        self.bg4_lock_sprite = pygame.image.load('images/апвыа/background_textures/bg4_lock.png')
        self.bg1_lock_sprite = pygame.image.load('images/апвыа/background_textures/bg1_lock.png')
        self.bg3_lock_sprite = pygame.image.load('images/апвыа/background_textures/bg3_lock.png')
        self.bg5_lock_sprite = pygame.image.load('images/апвыа/background_textures/bg5_lock.png')
        self.bg6_lock_sprite = pygame.image.load('images/апвыа/background_textures/bg6_lock.png')
        self.bg7_lock_sprite = pygame.image.load('images/апвыа/background_textures/bg7_lock.png')
        self.text_bg_sprite = pygame.image.load('images/апвыа/background_textures/text_bg.png')

        self.blue_point_texture = pygame.image.load('images/апвыа/sprites/blue.png')
        self.orange_point_texture = pygame.image.load('images/апвыа/sprites/orange.png')
        self.purple_point_texture = pygame.image.load('images/апвыа/sprites/purple.png')
        self.black_point_texture = pygame.image.load('images/апвыа/sprites/black.png')
        self.green_point_texture = pygame.image.load('images/апвыа/sprites/green.png') # already loaded, no need to load again for money display

        self.selected_background = 'bg2'
        self.progress = []
        self.load_progress()
        self.load_background()

        self.ball_radius = 20
        self.green_point_radius = 10
        self.ball_upper = 1.5
        self.scor = 24

        self.current_difficulty_name = 'Очень легко'

        self.red_ball_x = self.width // 2
        self.red_ball_y = self.height // 2
        self.blue_ball_x = 100
        self.blue_ball_y = 100

        self.red_ball_speed = 400
        self.temp_speed_boost = 0
        self.speed_boost_time = 0
        self.speed_boost_duration = 5000

        self.blue_ball_speed = 240
        self.blue_ball_freeze_time = 0

        self.game_over = False
        self.game_won = False
        self.game_saved = False

        self.collected_points = 0
        self.required_points = 30

        self.green_points = []
        self.special_points = []
        self.special_respawn_time = 0
        self.black_point_taken = False
        self.start_time = 0
        self.last_time = 0

        self.money = 0
        self.load_money()

        self._layout_buttons()

    def _layout_buttons(self):
        button_width = 300
        button_height = 80
        start_y = self.height // 2 - (len(self.menu_options) * button_height + (
                len(self.menu_options) - 1) * 10) // 2 + button_height // 2
        margin = 10
        center_x = self.width // 2

        self.button_rects = []
        for option in self.menu_options:
            rect = pygame.Rect(0, 0, button_width, button_height)
            rect.center = (center_x, start_y)
            self.button_rects.append((rect, option))
            start_y += button_height + margin
        self.difficulty_button_rects = []
        self.customization_button_rects = []
        self.back_button_rect = None

    def _layout_difficulty_buttons(self):
        button_width = 300
        button_height = 60
        start_y = self.height // 2 - (len(self.difficulty_options) * button_height + (
                len(self.difficulty_options) - 1) * 10) // 2 + button_height // 2
        margin = 10
        center_x = self.width // 2

        self.difficulty_button_rects = []
        for option in self.difficulty_options:
            rect = pygame.Rect(0, 0, button_width, button_height)
            rect.center = (center_x, start_y)
            self.difficulty_button_rects.append((rect, option))
            start_y += button_height + margin

        back_button_width = 150
        back_button_height = 50
        back_button_rect = pygame.Rect(10, 10, back_button_width, back_button_height)
        self.back_button_rect = (back_button_rect, "Назад")

    def _layout_customization_buttons(self):
        self.customization_button_rects = []

        button_width = 100
        button_height = 100
        start_x = self.width // 2 - (4 * button_width + 3 * 40) // 2 + button_width // 2 - 115
        start_y = self.height // 2 - button_height // 2 + 70
        margin_x = 30
        row_margin_y = 15

        bg_options = ['bg2', 'bg4', 'bg1', 'bg3', 'bg6', 'bg5', 'bg7']
        bg_sprites = [self.bg2_sprite, self.bg4_sprite, self.bg1_sprite, self.bg3_sprite, self.bg6_sprite, self.bg5_sprite, self.bg7_sprite]
        bg_lock_sprites = [None, self.bg4_lock_sprite, self.bg1_lock_sprite, self.bg3_lock_sprite, self.bg6_lock_sprite, self.bg5_lock_sprite, self.bg7_lock_sprite]
        unlock_difficulties = [None, "Очень легко", "Легко", "Нормально", "Тяжело", "Безумно", "Невозможно"]
        is_unlocked = [True] + [False] * (len(bg_options) - 1) # bg2 is always unlocked

        for i in range(1, len(bg_options)): # Check unlock status for bg4, bg1, bg3, bg6, bg5, bg7
            if unlock_difficulties[i] in self.progress:
                is_unlocked[i] = True

        for i in range(len(bg_options)):
            rect = pygame.Rect(0, 0, button_width, button_height)
            rect.center = (start_x, start_y)
            sprite_to_use = bg_sprites[i] if is_unlocked[i] else bg_lock_sprites[i]
            self.customization_button_rects.append((rect, bg_options[i], sprite_to_use, is_unlocked[i]))
            start_x += button_width + margin_x
            if start_x > 780: # move to next row
                start_x = self.width // 2 - (4 * button_width + 3 * 40) // 2 + button_width // 2 - 115
                start_y += button_height + row_margin_y # move start_y to next row


        back_button_width = 150
        back_button_height = 50
        back_button_rect = pygame.Rect(10, 10, back_button_width, back_button_height)
        self.back_button_rect = (back_button_rect, "Назад")

    def draw(self, screen_surface):
        screen_rect = screen_surface.get_rect()
        screen_surface.blit(self.backgrounds[self.selected_background], (0, 0))

        if self.current_screen == "main_menu":
            for rect_button in self.button_rects:
                rect = rect_button[0]
                button_text = rect_button[1]
                self.draw_rect(screen_surface, self.button_color, rect)
                self.draw_rect(screen_surface, self.button_border_color, rect, 3)
                if button_text == "Бесконечный режим":
                    self.draw_text(screen_surface, button_text, self.small_font, self.text_color, rect.center, 'center')
                else:
                    self.draw_text(screen_surface, button_text, self.font, self.text_color, rect.center, 'center')
                self.draw_rect(screen_surface, self.black, rect, 1)
            self.draw_money_display(screen_surface) # Display money in main menu
        elif self.current_screen == "difficulty_menu":
            for rect_button in self.difficulty_button_rects:
                rect = rect_button[0]
                button_text = rect_button[1]
                self.draw_rect(screen_surface, self.button_color, rect)
                self.draw_rect(screen_surface, self.button_border_color, rect, 3)
                self.draw_text(screen_surface, button_text, self.small_font, self.text_color, rect.center, 'center')
                self.draw_rect(screen_surface, self.black, rect, 1)
            if self.back_button_rect:
                rect, button_text = self.back_button_rect
                self.draw_rect(screen_surface, self.button_color, rect)
                self.draw_rect(screen_surface, self.button_border_color, rect, 3)
                self.draw_text(screen_surface, button_text, self.small_font, self.text_color, rect.center, 'center')
                self.draw_rect(screen_surface, self.black, rect, 1)
        elif self.current_screen == "customization_menu":
            screen_surface.blit(self.text_bg_sprite, (5, 70))
            for rect_button in self.customization_button_rects:
                rect = rect_button[0]
                bg_name = rect_button[1]
                bg_sprite = rect_button[2]
                is_unlocked = rect_button[3]
                screen_surface.blit(bg_sprite, rect.topleft)
                if self.selected_background == bg_name and is_unlocked:
                    screen_surface.blit(self.select_sprite, rect.topleft)

            if self.back_button_rect:
                rect, button_text = self.back_button_rect
                self.draw_rect(screen_surface, self.button_color, rect)
                self.draw_rect(screen_surface, self.button_border_color, rect, 3)
                self.draw_text(screen_surface, button_text, self.small_font, self.text_color, rect.center, 'center')
                self.draw_rect(screen_surface, self.black, rect, 1)
            self.draw_money_display(screen_surface) # Display money in customization menu
        elif self.current_screen == "game" or self.current_screen == "infinite_game":
            if not self.game_over and not self.game_won:
                self.draw_elements(screen_surface)
            self.draw_text_game(screen_surface)
            if self.game_over or self.game_won:
                self.draw_game_over_or_won(screen_surface)

    def handle_event(self, event, window_rect):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            relative_mouse_pos = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)

            if self.current_screen == "main_menu":
                for rect_button in self.button_rects:
                    rect = rect_button[0]
                    button_text = rect_button[1]
                    if rect.collidepoint(relative_mouse_pos):
                        if button_text == "Основной режим":
                            self.current_game_mode = "main_game"
                            self.current_screen = "difficulty_menu"
                            self._layout_difficulty_buttons()
                            return "main_mode_selected"
                        elif button_text == "Бесконечный режим":
                            self.current_game_mode = "infinite_game"
                            self.start_infinite_game()
                            return "infinite_mode_selected"
                        elif button_text == "Кастомизация":
                            self.current_screen = "customization_menu"
                            self._layout_customization_buttons()
                            return "customization_selected"
                        return None
            elif self.current_screen == "difficulty_menu":
                for rect_button in self.difficulty_button_rects:
                    rect = rect_button[0]
                    button_text = rect_button[1]
                    if rect.collidepoint(relative_mouse_pos):
                        self.set_difficulty(button_text)
                        if self.current_game_mode == "main_game":
                            self.start_game()
                        return "difficulty_set"
                if self.back_button_rect:
                    rect, button_text = self.back_button_rect
                    if rect.collidepoint(relative_mouse_pos):
                        self.current_screen = "main_menu"
                        self._layout_buttons()
                        return "back_to_main_menu"
            elif self.current_screen == "customization_menu":
                for rect_button in self.customization_button_rects:
                    rect = rect_button[0]
                    bg_name = rect_button[1]
                    is_unlocked = rect_button[3]
                    if rect.collidepoint(relative_mouse_pos) and is_unlocked:
                        self.select_background(bg_name)
                        return "background_selected"
                if self.back_button_rect:
                    rect, button_text = self.back_button_rect
                    if rect.collidepoint(relative_mouse_pos):
                        self.current_screen = "main_menu"
                        self._layout_buttons()
                        return "back_to_main_menu"
            elif self.current_screen == "game" or self.current_screen == "infinite_game":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and (self.game_over or self.game_won):  # Game won removed from condition
                        print('restarting game')
                        if self.current_game_mode == "main_game":
                            self.start_game()
                        elif self.current_game_mode == "infinite_game":
                            self.start_infinite_game()
                        return "game_restarted"
                    elif event.key == pygame.K_m and (
                            self.game_over or self.game_won):  # Game won removed from condition
                        print('going to menu')
                        self.current_screen = "main_menu"
                        self._layout_buttons()
                        self.current_game_mode = None
                        return "back_to_main_menu"
        return None

    def update_game(self, delta_time):
        if not self.game_over and self.current_screen in ["game", "infinite_game"]:  # Added infinite_game screen
            current_time = pygame.time.get_ticks()

            if self.ball_radius > self.scor:
                self.ball_upper = round(self.ball_upper - 0.1, 2)
                self.scor += 3

            self.spawn_special_points(current_time)

            self.update_red_ball(delta_time)
            self.update_blue_ball(delta_time)

            self.reset_speed_boost(current_time)

            self.check_collisions_with_green_points()
            self.check_collisions_with_special_points(current_time)

            self.check_game_over()
            self.check_game_won()

    def set_difficulty(self, difficulty_name):
        self.current_difficulty_name = difficulty_name
        if difficulty_name == 'Очень легко':
            self.blue_ball_speed = 240
            self.required_points = 15
            self.ball_upper = 1.5
        elif difficulty_name == 'Легко':
            self.blue_ball_speed = 280
            self.required_points = 15
            self.ball_upper = 2
        elif difficulty_name == 'Нормально':
            self.blue_ball_speed = 300
            self.required_points = 20
            self.ball_upper = 1.5
        elif difficulty_name == 'Тяжело':
            self.blue_ball_speed = 340
            self.required_points = 20
            self.ball_upper = 1.25
        elif difficulty_name == 'Безумно':
            self.blue_ball_speed = 360
            self.required_points = 25
            self.ball_upper = 1.1
        elif difficulty_name == 'Невозможно':
            self.blue_ball_speed = 399
            self.required_points = 30
            self.ball_upper = 1

    def select_background(self, bg_name):
        if bg_name in self.backgrounds:
            self.selected_background = bg_name
            self.save_background()

    def start_game(self):
        self._start_new_game("game")

    def start_infinite_game(self):
        self._start_new_game("game") # Using "game" screen for infinite too, logic will differ in win/lose conditions
        self.required_points = float('inf')
        self.ball_upper = 1.25
        self.blue_ball_speed = 360

    def _start_new_game(self, game_screen):
        self.current_screen = game_screen
        self.game_over = False
        self.game_won = False  # Reset game_won always
        self.game_saved = False
        self.special_respawn_time = 0
        self.red_ball_x = self.width // 2
        self.red_ball_y = self.height // 2
        self.blue_ball_x = 100
        self.blue_ball_y = 100
        self.collected_points = 0
        self.green_points = [(random.randint(30, self.width - 30), random.randint(30, self.height - 30))]
        self.special_points = []
        self.ball_radius = 20
        self.temp_speed_boost = 0
        self.speed_boost_time = 0
        self.blue_ball_freeze_time = 0
        self.black_point_taken = False
        self.start_time = pygame.time.get_ticks()
        self.last_time = pygame.time.get_ticks()

        if self.current_difficulty_name == 'Очень легко':
            self.ball_upper = 1.5
        elif self.current_difficulty_name == 'Легко':
            self.ball_upper = 2
        elif self.current_difficulty_name == 'Нормально':
            self.ball_upper = 1.5
        elif self.current_difficulty_name == 'Тяжело':
            self.ball_upper = 1.25
        elif self.current_difficulty_name == 'Безумно':
            self.ball_upper = 1.1
        elif self.current_difficulty_name == 'Невозможно':
            self.ball_upper = 1

    def load_progress(self):
        try:
            with open('progress.txt', 'r') as file:
                self.progress = [line.strip() for line in file.readlines()] # Read each line and strip whitespace
        except FileNotFoundError:
            self.progress = []

    def save_progress(self):
        with open('progress.txt', 'w') as file:
            file.write('\n'.join(self.progress))

    def save_background(self):
        with open('saving_session.txt', 'w') as file:
            file.write(self.selected_background)

    def load_background(self):
        try:
            with open('saving_session.txt', 'r') as file:
                self.selected_background = file.read().strip()
        except FileNotFoundError:
            self.selected_background = 'bg2'

    def load_money(self):
        try:
            with open('money.txt', 'r') as file:
                self.money = int(file.read().strip())
        except FileNotFoundError:
            self.money = 0
        except ValueError: # Handle cases where money.txt is empty or has invalid content
            self.money = 0

    def save_money(self):
        with open('money.txt', 'w') as file:
            file.write(str(self.money))

    def get_difficulty_bonus(self):
        difficulty_bonuses = {
            "Очень легко": 0,
            "Легко": 5,
            "Нормально": 10,
            "Тяжело": 15,
            "Безумно": 20,
            "Невозможно": 30
        }
        return difficulty_bonuses.get(self.current_difficulty_name, 0) # Default to 0 if difficulty is not found

    def update_red_ball(self, delta_time):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.red_ball_y -= (self.red_ball_speed + self.temp_speed_boost) * delta_time
        if keys[pygame.K_DOWN]:
            self.red_ball_y += (self.red_ball_speed + self.temp_speed_boost) * delta_time
        if keys[pygame.K_LEFT]:
            self.red_ball_x -= (self.red_ball_speed + self.temp_speed_boost) * delta_time
        if keys[pygame.K_RIGHT]:
            self.red_ball_x += (self.red_ball_speed + self.temp_speed_boost) * delta_time

        if self.red_ball_x - self.ball_radius < 0:
            self.red_ball_x = self.ball_radius
        elif self.red_ball_x + self.ball_radius > self.width:
            self.red_ball_x = self.width - self.ball_radius
        if self.red_ball_y - self.ball_radius < 0:
            self.red_ball_y = self.ball_radius
        elif self.red_ball_y + self.ball_radius > self.height:
            self.red_ball_y = self.height - self.ball_radius

    def update_blue_ball(self, delta_time):
        if self.blue_ball_freeze_time > 0:
            self.blue_ball_freeze_time -= delta_time * 1000
            return

        dx = self.red_ball_x - self.blue_ball_x
        dy = self.red_ball_y - self.blue_ball_y
        distance = math.hypot(dx, dy)
        if distance > 0:
            dx /= distance
            dy /= distance
            self.blue_ball_x += dx * self.blue_ball_speed * delta_time
            self.blue_ball_y += dy * self.blue_ball_speed * delta_time

    def check_collisions_with_green_points(self):
        for point in self.green_points[:]:
            dx = self.red_ball_x - point[0]
            dy = self.red_ball_y - point[1]
            distance = math.hypot(dx, dy)
            if distance < self.ball_radius + self.green_point_radius:
                self.green_points.remove(point)
                self.collected_points += 1
                self.ball_radius = round(self.ball_radius + self.ball_upper, 2)
                if self.collected_points < self.required_points and self.current_screen == "game":  # Only generate new point in main mode until win
                    new_point = self.generate_safe_point()
                    self.green_points.append(new_point)

    def check_collisions_with_special_points(self, current_time):
        for point in self.special_points[:]:
            point_x, point_y, point_texture = point

            hitbox_width = 15
            hitbox_height = 39

            if (point_x <= self.red_ball_x + self.ball_radius and
                    point_x + hitbox_width >= self.red_ball_x - self.ball_radius and
                    point_y <= self.red_ball_y + self.ball_radius and
                    point_y + hitbox_height >= self.red_ball_y - self.ball_radius):
                self.special_points.remove(point)
                if point_texture == self.blue_point_texture:
                    self.blue_ball_freeze_time = 2500
                elif point_texture == self.orange_point_texture:
                    self.ball_radius -= 3 * self.ball_upper
                    if self.ball_radius < 5:
                        self.ball_radius = 5
                elif point_texture == self.purple_point_texture:
                    self.temp_speed_boost = self.red_ball_speed * 0.25
                    self.speed_boost_time = current_time
                elif point_texture == self.black_point_texture and not self.black_point_taken:
                    self.black_point_taken = True

    def generate_safe_point(self):
        while True:
            x = random.randint(30, self.width - 30)
            y = random.randint(30, self.height - 30)
            if not self.is_point_in_stats_area(x, y):
                return (x, y)

    def is_point_in_stats_area(self, x, y):
        stats_area_x = 0
        stats_area_y = 0
        stats_area_width = 200
        stats_area_height = 50

        if (x >= stats_area_x and x <= stats_area_x + stats_area_width and
                y >= stats_area_y and y <= stats_area_y + stats_area_height):
            return True
        return False

    def reset_speed_boost(self, current_time):
        if self.temp_speed_boost > 0 and current_time - self.speed_boost_time > self.speed_boost_duration:
            self.temp_speed_boost = 0

    def check_game_over(self):
        if math.hypot(self.red_ball_x - self.blue_ball_x,
                      self.red_ball_y - self.blue_ball_y) < 2 * self.ball_radius and not self.black_point_taken:
            self.game_over = True
            if self.current_game_mode == "infinite_game": # Award money on game over in infinite mode
                money_earned = self.collected_points
                self.money += money_earned
                self.save_money()
        elif math.hypot(self.red_ball_x - self.blue_ball_x,
                        self.red_ball_y - self.blue_ball_y) < 2 * self.ball_radius and self.black_point_taken:
            self.black_point_taken = False
            self.blue_ball_x = 10
            self.blue_ball_y = 10

    def check_game_won(self):
        if self.collected_points >= self.required_points and self.current_game_mode == "main_game":  # Only check win in main game
            self.game_won = True
            self.progress.append(self.current_difficulty_name)
            if not self.game_saved:
                self.save_progress()
                self.game_saved = True
            if self.money_earning:
                money_earned = self.collected_points + self.get_difficulty_bonus() # Award money on win in main mode
                self.money += money_earned
                self.save_money()
                self.money_earning = False

    def spawn_special_points(self, current_time):
        if self.special_respawn_time == 0:
            self.special_respawn_time = current_time + 15000
        elif current_time > self.special_respawn_time:
            roll = random.random()
            if roll < 0.4:
                self.special_points.append(self.generate_safe_point() + (self.purple_point_texture,))
            elif roll < 0.75:
                self.special_points.append(self.generate_safe_point() + (self.blue_point_texture,))
            elif roll < 0.95:
                self.special_points.append(self.generate_safe_point() + (self.orange_point_texture,))
            else:
                if self.black_point_taken:
                    self.spawn_special_points(current_time)
                else:
                    self.special_points.append(self.generate_safe_point() + (self.black_point_texture,))
            self.special_respawn_time = current_time + 15000

    def draw_elements(self, surface):
        for point in self.green_points:
            surface.blit(self.green_point_texture, point)

        for point in self.special_points:
            surface.blit(point[2], (point[0], point[1]))

        pygame.draw.circle(surface, self.red_color, (int(self.red_ball_x), int(self.red_ball_y)), int(self.ball_radius))
        pygame.draw.circle(surface, self.blue_color, (int(self.blue_ball_x), int(self.blue_ball_y)),
                           int(self.ball_radius))

    def draw_text_game(self, surface):
        if self.current_game_mode == "infinite_game":
            score_text = self.score_font.render(f"Собрано: {self.collected_points}", True,
                                                self.green_color)
        else:
            score_text = self.score_font.render(f"Собрано: {self.collected_points}/{self.required_points}", True,
                                                self.green_color)
        score_rect = score_text.get_rect(topleft=(10, 10))
        surface.blit(score_text, score_rect)

        elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        timer_text = self.timer_font.render(f"Время: {minutes:02d}:{seconds:02d}", True, self.red_color)
        timer_rect = timer_text.get_rect(topright=(self.width - 10, 10))
        surface.blit(timer_text, timer_rect)

    def draw_game_over_or_won(self, surface):
        if self.game_won:
            text = self.font.render("Хорош!", True, self.green_color)
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 30))  # Adjusted position
            surface.blit(text, text_rect)
            restart_text = self.restart_font.render("Нажмите 'R' для рестарта", True, self.green_color)
            restart_rect = restart_text.get_rect(center=(self.width // 2, self.height // 2 + 20))  # Adjusted position
            surface.blit(restart_text, restart_rect)
            menu_text = self.menu_font.render("Нажмите 'M' для выхода в меню", True,
                                              self.green_color)  # Added menu text
            menu_rect = menu_text.get_rect(center=(self.width // 2, self.height // 2 + 70))  # Added menu text position
            surface.blit(menu_text, menu_rect)  # Added menu text blit
        elif self.game_over:
            text = self.font.render("Ты лох", True, self.red_color)
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 30))  # Adjusted position
            surface.blit(text, text_rect)
            restart_text = self.restart_font.render("Нажмите 'R' для рестарта", True, self.red_color)
            restart_rect = restart_text.get_rect(center=(self.width // 2, self.height // 2 + 20))  # Adjusted position
            surface.blit(restart_text, restart_rect)
            menu_text = self.menu_font.render("Нажмите 'M' для выхода в меню", True, self.red_color)  # Added menu text
            menu_rect = menu_text.get_rect(center=(self.width // 2, self.height // 2 + 70))  # Added menu text position
            surface.blit(menu_text, menu_rect)  # Added menu text blit

    def draw_money_display(self, surface):
        money_text_surface = self.score_font.render(str(self.money), True, self.green_color)
        money_text_rect = money_text_surface.get_rect(topright=(self.width - 40, 10)) # Position text to the left of sprite
        surface.blit(money_text_surface, money_text_rect)
        money_sprite_rect = self.green_point_texture.get_rect(topright=(self.width - 10, 15)) # Position sprite to the right of text
        surface.blit(self.green_point_texture, money_sprite_rect)


    @property
    def app_width(self):
        return self.width

    @property
    def app_height(self):
        return self.height

    def draw_rect(self, surface, color, rect, border_width=0, border_radius=0):
        pygame.draw.rect(surface, color, rect, border_width, border_radius)

    def draw_text(self, surface, text, font, color, position, alignment='topleft'):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(**{alignment: position})
        surface.blit(text_surface, text_rect)
        return text_rect