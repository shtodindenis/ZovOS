import math
import random
import sqlite3
import sys

import pygame


class InfZovApp:
    def __init__(self):
        self.width = 1280
        self.height = 720
        pygame.init()
        self.screen = pygame.Surface((self.width, self.height))
        self.font0 = pygame.font.Font('sb.ttf', 20)
        self.font = pygame.font.Font('sb.ttf', 28)
        self.fontx = pygame.font.Font('sb.ttf', 48)
        self.title_font = pygame.font.Font('sb.ttf', 58)
        self.white = (255, 255, 255)
        self.red = (255, 0, 0)
        self.green = (0, 255, 0)
        self.gray = (100, 100, 100)
        self.tank_width = 100
        self.tank_height = 41
        self.ammo_width = 50
        self.ammo_height = 41
        self.explosion_width = 50
        self.explosion_height = 50
        self.shell_radius = 80
        self.rlo_width = 80
        self.rlo_height = 44
        self.rlos = []
        self.tanks = []
        self.selected_rocket = "фаб500"
        self.selected_radii = "Маленький"
        self.game_time_limit = 60
        self.difficulty = "Нормально"
        self.score = 0
        self.ammo_count = 10
        self.explosions = []
        self.shells = []
        self.ammos_ingame = []
        self.crosshair = Crosshair(self)
        self.last_ammo_spawn_time = 0
        self.start_time = 0
        self.paused = False
        self.money_per_tank = 0

        self.tank_speeds = {
            "Легко": 2,
            "Нормально": 4,
            "Тяжело": 8
        }

        self.tank_counts = {
            "Легко": 15,
            "Нормально": 10,
            "Тяжело": 4
        }
        self.money_per_tank_levels = {
            "Легко": 1,
            "Нормально": 2,
            "Тяжело": 3
        }

        self.ammo_spawn_rates = {
            "Легко": 0.1,
            "Нормально": 0.05,
            "Тяжело": 0.03
        }
        self.rlo_counts = {
            "Легко": 0,
            "Нормально": 2,
            "Тяжело": 3
        }

        self.rocket_prices = {
            "фаб500": 250,
            "офаб500": 250,
            "офзаб500": 250,
            "фаб500м62": 700,
            "кмгу": 700,
            "каб500л": 700,
            "каб500кр": 1500,
            "фаб3000": 1500,
            "каб1500": 1500,
            "рдс1": 5000
        }

        self.explosion_radii_prices = {
            "Маленький": {"price": 100, "radius": 100},
            "Средний": {"price": 2000, "radius": 200},
            "Большой": {"price": 6000, "radius": 300},
            "Огромный": {"price": 15000, "radius": 400}
        }

        self.rocket_sprites = {
            "фаб500": pygame.image.load('images/IZ/rocket_sprites/фаб500.png').convert_alpha(),
            "офаб500": pygame.image.load('images/IZ/rocket_sprites/офаб500.png').convert_alpha(),
            "офзаб500": pygame.image.load('images/IZ/rocket_sprites/офзаб500.png').convert_alpha(),
            "фаб500м62": pygame.image.load('images/IZ/rocket_sprites/фаб500м62.png').convert_alpha(),
            "кмгу": pygame.image.load('images/IZ/rocket_sprites/кмгу.png').convert_alpha(),
            "каб500л": pygame.image.load('images/IZ/rocket_sprites/каб500л.png').convert_alpha(),
            "каб500кр": pygame.image.load('images/IZ/rocket_sprites/каб500кр.png').convert_alpha(),
            "фаб3000": pygame.image.load('images/IZ/rocket_sprites/фаб3000.png').convert_alpha(),
            "каб1500": pygame.image.load('images/IZ/rocket_sprites/каб1500.png').convert_alpha(),
            "рдс1": pygame.image.load('images/IZ/rocket_sprites/рдс1.png').convert_alpha()
        }

        self.rocket_shop_sprites = {
            "фаб500": pygame.image.load('images/IZ/rocket_sprites/фаб500_маг.png').convert_alpha(),
            "офаб500": pygame.image.load('images/IZ/rocket_sprites/офаб500_маг.png').convert_alpha(),
            "офзаб500": pygame.image.load('images/IZ/rocket_sprites/офзаб500_маг.png').convert_alpha(),
            "фаб500м62": pygame.image.load('images/IZ/rocket_sprites/фаб500м62_маг.png').convert_alpha(),
            "кмгу": pygame.image.load('images/IZ/rocket_sprites/кмгу_маг.png').convert_alpha(),
            "каб500л": pygame.image.load('images/IZ/rocket_sprites/каб500л_маг.png').convert_alpha(),
            "каб500кр": pygame.image.load('images/IZ/rocket_sprites/каб500кр_маг.png').convert_alpha(),
            "фаб3000": pygame.image.load('images/IZ/rocket_sprites/фаб3000_маг.png').convert_alpha(),
            "каб1500": pygame.image.load('images/IZ/rocket_sprites/каб1500_маг.png').convert_alpha(),
            "рдс1": pygame.image.load('images/IZ/rocket_sprites/рдс1_маг.png').convert_alpha()
        }
        self.explosion_shop_sprites = {
            "Маленький": pygame.image.load('images/IZ/explosion_sprites/маленький_маг.png').convert_alpha(),
            "Средний": pygame.image.load('images/IZ/explosion_sprites/средний_маг.png').convert_alpha(),
            "Большой": pygame.image.load('images/IZ/explosion_sprites/большой_маг.png').convert_alpha(),
            "Огромный": pygame.image.load('images/IZ/explosion_sprites/огромный_маг.png').convert_alpha()
        }
        self.money_icon = pygame.image.load('images/IZ/ui/счёт.png').convert_alpha()
        self.money_icon = pygame.transform.scale(self.money_icon, (40, 40))
        self.score_icon = pygame.image.load('images/IZ/ui/счёт.png').convert_alpha()
        self.score_icon = pygame.transform.scale(self.score_icon, (40, 40))
        self.ammo_icon_ui = pygame.image.load('images/IZ/ui/боек.png').convert_alpha()
        self.ammo_icon_ui = pygame.transform.scale(self.ammo_icon_ui, (40, 40))
        self.time_icon = pygame.image.load('images/IZ/ui/time_icon.png').convert_alpha()
        self.kursk_icon = pygame.image.load('images/IZ/ui/kursk_icon.png').convert_alpha()

        self.background_image = pygame.image.load('images/IZ/bgs/donec.jpg').convert()
        self.background_image = pygame.transform.scale(self.background_image, (self.width, self.height))
        self.kal_bg = pygame.image.load('images/IZ/bgs/kal.jpg').convert()
        self.kal_bg = pygame.transform.scale(self.kal_bg, (self.width, self.height))

        self.current_background_index = 0
        self.background_alpha = 0
        self.background_images = [
            pygame.image.load('images/IZ/bgs/sv1.png').convert_alpha(),
            pygame.image.load('images/IZ/bgs/sv2.png').convert_alpha(),
            pygame.image.load('images/IZ/bgs/donec.jpg').convert_alpha(),
            pygame.image.load('images/IZ/bgs/sv3.png').convert_alpha()
        ]

        self.menu_options = ["Играть", "Магазин", "Выход"]
        self.button_rects = []
        self._layout_buttons()

        self.shop_options = ["Скины для ракет", "Радиус взрыва", "Назад"]
        self.shop_button_rects = []
        self._layout_shop_buttons()

        self.rejim_options = ["60 секунд", "Оборона Курска", "Назад"]
        self.rejim_button_rects = []
        self._layout_rejim_buttons()

        self.difficulty_options = ["Легко", "Нормально", "Тяжело", "Назад"]
        self.difficulty_button_rects = []
        self._layout_difficulty_buttons()

        self.rank_options = ["Играть снова", "Назад в меню"]
        self.rank_button_rects = []
        self._layout_rank_buttons()

        self.current_screen = "main_menu"

        # Slider attributes moved from CustomSlider
        self.slider_rect = pygame.Rect(self.width // 3, self.height - 160,
                                       self.width - self.width // 3 * 2, 40)
        self.slider_background_image = pygame.image.load('images/IZ/ui/sl.png').convert_alpha()
        self.slider_background_image = pygame.transform.scale(self.slider_background_image,
                                                              (self.slider_rect.width, self.slider_rect.height))
        self.slider_handle_image = pygame.image.load('images/IZ/ui/slider.png').convert_alpha()
        self.slider_handle_image = pygame.transform.scale(self.slider_handle_image, (37, 38))
        self.slider_handle_rect = self.slider_handle_image.get_rect(
            center=(self.slider_rect.x, self.slider_rect.y + self.slider_rect.height // 2))
        self.slider_handle_rect.x = self.slider_rect.x
        self.slider_min_value = 0
        self.slider_max_value = 100
        self.slider_value = 0
        self.slider_is_dragging = False

        self.create_db()
        self.create_rockets_table()
        self.create_explosion_radii_table()
        self.load_buyed_rockets()
        self.load_buyed_explosion_radii()

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

    def _layout_shop_buttons(self):
        button_width = 360
        button_height = 80
        start_y = self.height // 2 - (len(self.shop_options) * button_height + (
                len(self.shop_options) - 1) * 10) // 2 + button_height // 2
        margin = 10
        center_x = self.width // 2

        self.shop_button_rects = []
        for option in self.shop_options:
            rect = pygame.Rect(0, 0, button_width, button_height)
            rect.center = (center_x, start_y)
            self.shop_button_rects.append((rect, option))
            start_y += button_height + margin

    def _layout_rejim_buttons(self):
        button_width = 360
        button_height = 80
        start_y = self.height // 2 - (len(self.rejim_options) * button_height + (
                len(self.rejim_options) - 1) * 10) // 2 + button_height // 2
        margin = 10
        center_x = self.width // 2

        self.rejim_button_rects = []
        for option in self.rejim_options:
            rect = pygame.Rect(0, 0, button_width, button_height)
            rect.center = (center_x, start_y)
            self.rejim_button_rects.append((rect, option))
            start_y += button_height + margin

    def _layout_difficulty_buttons(self):
        button_width = 300
        button_height = 50
        start_y = self.height // 2 - (len(self.difficulty_options) * button_height + (
                len(self.difficulty_options) - 1) * 10) // 2 + button_height // 2
        margin = 25
        center_x = self.width // 2

        self.difficulty_button_rects = []
        for option in self.difficulty_options:
            rect = pygame.Rect(0, 0, button_width, button_height)
            rect.center = (center_x, start_y)
            self.difficulty_button_rects.append((rect, option))
            start_y += button_height + margin

    def _layout_rank_buttons(self):
        button_width = 240
        button_height = 40
        start_y = self.height // 2 + 55  # Starting Y position for buttons in rank screen
        margin = 50
        center_x = self.width // 2

        self.rank_button_rects = []
        for option in self.rank_options:
            rect = pygame.Rect(0, 0, button_width, button_height)
            rect.center = (center_x, start_y)
            self.rank_button_rects.append((rect, option))
            start_y += button_height + margin

    def draw(self, screen_surface, window_rect):
        screen_rect = screen_surface.get_rect()
        if self.current_screen == "main_menu":
            self.draw_main_menu(screen_surface, window_rect)
        elif self.current_screen == "shop_menu":
            self.draw_shop_menu(screen_surface, window_rect)
        elif self.current_screen == "rocket_shop":
            self.draw_rocket_shop(screen_surface, window_rect, window_rect)
        elif self.current_screen == "explosion_shop":
            self.draw_explosion_shop(screen_surface, window_rect, window_rect)
        elif self.current_screen == "rejim_menu":
            self.draw_rejim_menu(screen_surface, window_rect)
        elif self.current_screen == "difficulty_menu":
            self.draw_difficulty_menu(screen_surface, window_rect)
        elif self.current_screen == "main_game":
            self.draw_main_game(screen_surface)
        elif self.current_screen == "rank_screen":
            self.draw_rank_screen(screen_surface, window_rect)

    def draw_rank_screen(self, screen_surface, window_rect):
        screen_surface.blit(self.background_image, (0, 0))

        score_text = self.font.render(f"Заработано за сессию: {self.score}", True, self.white)
        score_text_rect = score_text.get_rect(center=(self.width // 2, self.height // 2 - 150))
        screen_surface.blit(score_text, score_text_rect)
        screen_surface.blit(self.score_icon, (score_text_rect.right + 10, score_text_rect.top))

        relative_mouse_pos = (pygame.mouse.get_pos()[0] - window_rect.x, pygame.mouse.get_pos()[1] - window_rect.y)

        for rect_button in self.rank_button_rects:
            rect = rect_button[0]
            button_text = rect_button[1]

            pygame.draw.rect(screen_surface,
                             (200, 70, 70) if rect.collidepoint(relative_mouse_pos) else self.red,
                             rect)

            button_text_render = self.font.render(button_text, True, self.white)
            button_text_rect = button_text_render.get_rect(center=rect.center)
            screen_surface.blit(button_text_render, button_text_rect)

    def draw_difficulty_menu(self, screen_surface, window_rect):
        screen_surface.blit(self.background_image, (0, 0))

        title_text = self.title_font.render("Выберите сложность", True, self.white)
        title_rect = title_text.get_rect(center=(self.width // 2, 50))
        screen_surface.blit(title_text, title_rect)
        relative_mouse_pos = (pygame.mouse.get_pos()[0] - window_rect.x, pygame.mouse.get_pos()[1] - window_rect.y)

        for rect_button in self.difficulty_button_rects:
            rect = rect_button[0]
            button_text = rect_button[1]

            pygame.draw.rect(screen_surface,
                             (200, 70, 70) if rect.collidepoint(relative_mouse_pos) else self.red,
                             rect)

            button_text_render = self.font.render(button_text, True, self.white)
            button_text_rect = button_text_render.get_rect(center=rect.center)
            screen_surface.blit(button_text_render, button_text_rect)

    def draw_rejim_menu(self, screen_surface, window_rect):
        screen_surface.blit(self.background_image, (0, 0))

        title_text = self.title_font.render("Выбор режима", True, self.white)
        title_rect = title_text.get_rect(center=(self.width // 2, 50))
        screen_surface.blit(title_text, title_rect)
        relative_mouse_pos = (pygame.mouse.get_pos()[0] - window_rect.x, pygame.mouse.get_pos()[1] - window_rect.y)

        for i, rect_button in enumerate(self.rejim_button_rects):
            rect = rect_button[0]
            button_text = rect_button[1]
            color = (200, 70, 70) if rect.collidepoint(relative_mouse_pos) else self.red
            if button_text == "Оборона Курска":
                color = self.gray  # Make "Оборона Курска" button inactive
            pygame.draw.rect(screen_surface,
                             color,
                             rect)

            button_text_render = self.font.render(button_text, True, self.white)
            button_text_rect = button_text_render.get_rect(center=rect.center)
            screen_surface.blit(button_text_render, button_text_rect)

            if button_text == "60 секунд":
                screen_surface.blit(pygame.transform.scale(self.time_icon, (30, 30)),
                                    (rect.left + 10, rect.centery - 15))
            elif button_text == "Оборона Курска":
                screen_surface.blit(pygame.transform.scale(self.kursk_icon, (30, 30)),
                                    (rect.left + 10, rect.centery - 15))

    def draw_main_menu(self, screen_surface, window_rect):
        current_background_image = self.background_images[self.current_background_index]
        next_background_image_index = (self.current_background_index + 1) % len(self.background_images)
        next_background_image = self.background_images[next_background_image_index]

        screen_surface.blit(current_background_image, (0, 0))

        s = pygame.Surface((self.width, self.height))
        s.set_alpha(min(255, self.background_alpha))
        s.blit(next_background_image, (0, 0))

        screen_surface.blit(s, (0, 0))

        if self.background_alpha < 555:
            self.background_alpha += 1
        else:
            self.current_background_index = next_background_image_index
            self.background_alpha = 0

        title_text = self.title_font.render("Infinity ZOV", True, self.white)
        title_rect = title_text.get_rect(center=(self.width // 2, self.height // 2 - 200))
        screen_surface.blit(title_text, title_rect)
        relative_mouse_pos = (pygame.mouse.get_pos()[0] - window_rect.x, pygame.mouse.get_pos()[1] - window_rect.y)

        for rect_button in self.button_rects:
            rect = rect_button[0]
            button_text = rect_button[1]

            pygame.draw.rect(screen_surface,
                             (200, 70, 70) if rect.collidepoint(relative_mouse_pos) else self.red,
                             rect)

            button_text_render = self.font.render(button_text, True, self.white)
            button_text_rect = button_text_render.get_rect(center=rect.center)
            screen_surface.blit(button_text_render, button_text_rect)

    def draw_shop_menu(self, screen_surface, window_rect):
        screen_surface.blit(self.background_image, (0, 0))

        title_text = self.title_font.render("Магазин", True, self.white)
        title_rect = title_text.get_rect(center=(self.width // 2, 50))
        screen_surface.blit(title_text, title_rect)

        current_money = self.get_player_money()
        money_text = self.font.render(f"{current_money}", True, self.white)
        money_text_rect = money_text.get_rect(center=(self.width // 2 - 25, 120))
        screen_surface.blit(money_text, money_text_rect)
        screen_surface.blit(self.money_icon, (money_text_rect.right + 10, money_text_rect.top))

        relative_mouse_pos = (pygame.mouse.get_pos()[0] - window_rect.x, pygame.mouse.get_pos()[1] - window_rect.y)

        for rect_button in self.shop_button_rects:
            rect = rect_button[0]
            button_text = rect_button[1]

            pygame.draw.rect(screen_surface,
                             (200, 70, 70) if rect.collidepoint(relative_mouse_pos) else self.red,
                             rect)

            button_text_render = self.font.render(button_text, True, self.white)
            button_text_rect = button_text_render.get_rect(center=rect.center)
            screen_surface.blit(button_text_render, button_text_rect)

    def draw_rocket_shop(self, screen_surface, window_rect, game_window_rect):
        screen_surface.blit(self.background_image, (0, 0))

        title_text = self.title_font.render("Магазин", True, self.white)
        title_rect = title_text.get_rect(center=(self.width // 2, 50))
        screen_surface.blit(title_text, title_rect)

        current_money = self.get_player_money()
        money_text = self.font.render(f"{current_money}", True, self.white)
        money_text_rect = money_text.get_rect(center=(self.width // 2 - 25, 120))
        screen_surface.blit(money_text, money_text_rect)
        screen_surface.blit(self.money_icon, (money_text_rect.right + 10, money_text_rect.top))

        back_button_rect = pygame.Rect(self.width // 2 - 120, self.height - 100, 240, 40)
        pygame.draw.rect(screen_surface,
                         (200, 70, 70) if back_button_rect.collidepoint(pygame.mouse.get_pos()) else self.red,
                         back_button_rect)
        back_button_text = self.font.render("Назад", True, self.white)
        back_button_text_rect = back_button_text.get_rect(center=back_button_rect.center)
        screen_surface.blit(back_button_text, back_button_text_rect)

        rocket_card_width = 162
        rocket_card_height = 208
        spacing = 15
        total_cards_width = len(self.rocket_sprites) * (rocket_card_width + spacing)
        initial_offset = (self.width - total_cards_width) // 2 + 200

        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()
        c.execute("SELECT name, price FROM rockets")
        rockets_data = c.fetchall()
        conn.close()
        last_used, buyed_rockets = self.load_buyed_rockets()
        self.selected_rocket = last_used

        for i, (rocket_name, price) in enumerate(rockets_data):
            x = initial_offset + i * (rocket_card_width + spacing) - int(
                self.get_rocket_shop_slider_value() / 30 * (rocket_card_width + spacing)) + 100
            y = self.height // 2 - rocket_card_height // 2 - 50
            rocket_button_rect = pygame.Rect(x, y, rocket_card_width, rocket_card_height)
            buy_button_rect = pygame.Rect(x, y + rocket_card_height + 40, rocket_card_width, 40)

            if x + rocket_card_width > 0 and x < self.width:
                screen_surface.blit(pygame.transform.scale(self.rocket_shop_sprites[rocket_name],
                                                           (rocket_card_width, rocket_card_height)), (x, y))
                if rocket_name not in buyed_rockets:
                    color = (200, 70, 70) if buy_button_rect.collidepoint(pygame.mouse.get_pos()) else self.red
                    buy_text = self.font.render("Купить", True, self.white)
                elif rocket_name in buyed_rockets and rocket_name != self.selected_rocket:
                    color = (100, 100, 100) if buy_button_rect.collidepoint(pygame.mouse.get_pos()) else (150, 150, 150)
                    buy_text = self.font.render("Выбрать", True, self.white)
                else:
                    color = (150, 150, 150)
                    buy_text = self.font.render("Выбрано", True, self.white)

                pygame.draw.rect(screen_surface, color, buy_button_rect)
                buy_text_rect = buy_text.get_rect(center=buy_button_rect.center)
                screen_surface.blit(buy_text, buy_text_rect)

                if rocket_name not in buyed_rockets:
                    price_text = self.font.render(str(price), True, self.white)
                    price_rect = price_text.get_rect(center=(buy_button_rect.centerx - 20, buy_button_rect.top - 25))
                    screen_surface.blit(self.money_icon, (price_rect.right + 10, price_rect.top))
                    screen_surface.blit(price_text, price_rect)

        self.draw_rocket_shop_slider(screen_surface)

    def draw_explosion_shop(self, screen_surface, window_rect, game_window_rect):
        screen_surface.blit(self.background_image, (0, 0))

        title_text = self.title_font.render("Магазин", True, self.white)
        title_rect = title_text.get_rect(center=(self.width // 2, 50))
        screen_surface.blit(title_text, title_rect)

        current_money = self.get_player_money()
        money_text = self.font.render(f"{current_money}", True, self.white)
        money_text_rect = money_text.get_rect(center=(self.width // 2 - 25, 120))
        screen_surface.blit(money_text, money_text_rect)
        screen_surface.blit(self.money_icon, (money_text_rect.right + 10, money_text_rect.top))

        back_button_rect = pygame.Rect(self.width // 2 - 120, self.height - 100, 240, 40)
        pygame.draw.rect(screen_surface,
                         (200, 70, 70) if back_button_rect.collidepoint(pygame.mouse.get_pos()) else self.red,
                         back_button_rect)
        back_button_text = self.font.render("Назад", True, self.white)
        back_button_text_rect = back_button_text.get_rect(center=back_button_rect.center)
        screen_surface.blit(back_button_text, back_button_text_rect)

        rocket_card_width = 162
        rocket_card_height = 208
        spacing = 15
        total_cards_width = len(self.explosion_shop_sprites) * (rocket_card_width + spacing)
        initial_offset = (self.width - total_cards_width) // 2

        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()
        c.execute("SELECT name, price FROM explosion_radii")
        rockets_data = c.fetchall()
        conn.close()
        last_used, buyed_rockets = self.load_buyed_explosion_radii()
        self.selected_radii = last_used

        for i, (rocket_name, price) in enumerate(rockets_data):
            x = initial_offset + i * (rocket_card_width + spacing) + 100
            y = self.height // 2 - rocket_card_height // 2 - 50
            rocket_button_rect = pygame.Rect(x, y, rocket_card_width, rocket_card_height)
            buy_button_rect = pygame.Rect(x, y + rocket_card_height + 40, rocket_card_width, 40)

            if x + rocket_card_width > 0 and x < self.width:
                screen_surface.blit(pygame.transform.scale(self.explosion_shop_sprites[rocket_name],
                                                           (rocket_card_width, rocket_card_height)), (x, y))
                if rocket_name not in buyed_rockets:
                    color = (200, 70, 70) if buy_button_rect.collidepoint(pygame.mouse.get_pos()) else self.red
                    buy_text = self.font.render("Купить", True, self.white)
                elif rocket_name in buyed_rockets and rocket_name != self.selected_radii:
                    color = (100, 100, 100) if buy_button_rect.collidepoint(pygame.mouse.get_pos()) else (150, 150, 150)
                    buy_text = self.font.render("Выбрать", True, self.white)
                else:
                    color = (150, 150, 150)
                    buy_text = self.font.render("Выбрано", True, self.white)

                pygame.draw.rect(screen_surface, color, buy_button_rect)
                buy_text_rect = buy_text.get_rect(center=buy_button_rect.center)
                screen_surface.blit(buy_text, buy_text_rect)

                if rocket_name not in buyed_rockets:
                    price_text = self.font.render(str(price), True, self.white)
                    price_rect = price_text.get_rect(center=(buy_button_rect.centerx - 20, buy_button_rect.top - 25))
                    screen_surface.blit(self.money_icon, (price_rect.right + 10, price_rect.top))
                    screen_surface.blit(price_text, price_rect)

    def draw_main_game(self, screen_surface):
        screen_surface.blit(self.kal_bg, (0, 0))

        for tank in self.tanks:
            tank.update()
            tank.draw(screen_surface)

        crosshair_color = self.white
        for rlo in self.rlos[:]:
            rlo.update()
            rlo.draw(screen_surface)

            distance_to_rlo = math.hypot(rlo.rect.centerx - self.crosshair.x,
                                         rlo.rect.centery - self.crosshair.y)

            if not rlo.is_destroyed and self.crosshair.x is not None and self.crosshair.y is not None:
                distance_to_rlo = math.hypot(rlo.rect.centerx - self.crosshair.x,
                                             rlo.rect.centery - self.crosshair.y)
                if distance_to_rlo < 200 and rlo.is_defending:
                    crosshair_color = self.red
        self.crosshair.draw(screen_surface, crosshair_color)

        for ammo in self.ammos_ingame:
            ammo.draw(screen_surface)

        for explosion in self.explosions[:]:
            if not explosion.update():
                self.explosions.remove(explosion)
            explosion.draw(screen_surface)

        for shell in self.shells[:]:
            shell.draw(screen_surface)
            current_time = pygame.time.get_ticks()
            if current_time - shell.timer < 800:
                shell.scale_factor -= 0.06
                if shell.scale_factor < 0:
                    shell.scale_factor = 0
                shell.image = pygame.transform.scale(shell.original_image,
                                                     (int(shell.original_image.get_width() * shell.scale_factor),
                                                      int(shell.original_image.get_height() * shell.scale_factor)))
                if shell.scale_factor < 0.3:
                    for tank in self.tanks[:]:
                        distance_to_tank = math.hypot(tank.rect.centerx - shell.x,
                                                      tank.rect.centery - shell.y)
                        if not tank.is_destroyed:
                            distance_to_tank = math.hypot(tank.rect.centerx - shell.x,
                                                          tank.rect.centery - shell.y)
                        if distance_to_tank <= self.shell_radius * (1 - shell.scale_factor):
                            self.explosions.append(Explosion(self, tank.rect.centerx, tank.rect.centery))
                            tank.destroy()
                            current_money = self.get_player_money()
                            self.update_player_money(current_money + self.money_per_tank)
                            self.score += self.money_per_tank
                    for rlo in self.rlos[:]:
                        if not rlo.is_destroyed:
                            distance_to_rlo = math.hypot(rlo.rect.centerx - shell.x,
                                                         rlo.rect.centery - shell.y)
                        if distance_to_rlo <= self.shell_radius * (1 - shell.scale_factor):
                            self.explosions.append(Explosion(self, rlo.rect.centerx, rlo.rect.centery))
                            rlo.destroy()
                            current_money = self.get_player_money()
                            self.update_player_money(current_money + self.money_per_tank)
                            self.score += self.money_per_tank
            else:
                self.shells.remove(shell)

        score_text = self.font.render(f"{self.score}", True, self.white)
        screen_surface.blit(score_text, (10, 15))
        screen_surface.blit(self.score_icon, (score_text.get_width() + 20, 10))

        ammo_text = self.font.render(f"{self.ammo_count}", True, self.white)
        screen_surface.blit(ammo_text, (10, 55))
        screen_surface.blit(self.ammo_icon_ui, (ammo_text.get_width() + 20, 55))

        time_text = self.fontx.render(f"{self.game_time_limit - (pygame.time.get_ticks() - self.start_time) // 1000}",
                                      True, (255, 255, 255))
        screen_surface.blit(time_text, (self.width // 2 - 40, 10))

    def handle_event(self, event, window_rect):
        if self.current_screen == "main_menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                relative_mouse_pos = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                for rect_button in self.button_rects:
                    rect = rect_button[0]
                    button_text = rect_button[1]
                    if rect.collidepoint(relative_mouse_pos):
                        if button_text == "Играть":
                            self.current_screen = "rejim_menu"
                            return "rejim_menu_selected"
                        elif button_text == "Магазин":
                            self.current_screen = "shop_menu"
                            return "shop_selected"
                        elif button_text == "Выход":
                            return "exit_selected"
        elif self.current_screen == "shop_menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                relative_mouse_pos = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                for rect_button in self.shop_button_rects:
                    rect = rect_button[0]
                    button_text = rect_button[1]
                    if rect.collidepoint(relative_mouse_pos):
                        if button_text == "Скины для ракет":
                            self.current_screen = "rocket_shop"
                            return "rocket_shop_selected"
                        elif button_text == "Радиус взрыва":
                            self.current_screen = "explosion_shop"
                            return "explosion_shop_selected"
                        elif button_text == "Назад":
                            self.current_screen = "main_menu"
                            return "back_to_main_menu"
        elif self.current_screen == "rocket_shop":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                relative_mouse_pos = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                back_button_rect = pygame.Rect(self.width // 2 - 120, self.height - 100, 240, 40)
                if self.slider_rect.collidepoint(relative_mouse_pos):
                    self.slider_is_dragging = True
                elif back_button_rect.collidepoint(relative_mouse_pos):
                    self.current_screen = "shop_menu"
                    return "back_to_shop_menu"

                rocket_card_width = 162
                rocket_card_height = 208
                spacing = 15
                initial_offset = (self.width - len(self.rocket_sprites) * (rocket_card_width + spacing)) // 2 + 200
                conn = sqlite3.connect('player_data.db')
                c = conn.cursor()
                c.execute("SELECT name, price FROM rockets")
                rockets_data = c.fetchall()
                conn.close()
                last_used, buyed_rockets = self.load_buyed_rockets()
                self.selected_rocket = last_used

                for i, (rocket_name, price) in enumerate(rockets_data):
                    x = initial_offset + i * (rocket_card_width + spacing) - int(
                        self.get_rocket_shop_slider_value() / 30 * (rocket_card_width + spacing)) + 100
                    y = self.height // 2 - rocket_card_height // 2 - 50
                    buy_button_rect = pygame.Rect(x, y + rocket_card_height + 40, rocket_card_width, 40)

                    if buy_button_rect.collidepoint(relative_mouse_pos):
                        if rocket_name not in buyed_rockets:
                            current_money = self.get_player_money()
                            if current_money >= price:
                                buyed_rockets.append(rocket_name)
                                self.save_buyed_rockets(rocket_name, buyed_rockets)
                                self.update_player_money(current_money - price)
                        else:
                            self.selected_rocket = rocket_name
                            self.save_buyed_rockets(self.selected_rocket, buyed_rockets)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.slider_is_dragging = False
            elif event.type == pygame.MOUSEMOTION and self.slider_is_dragging:
                relative_mouse_pos = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                self.move_rocket_shop_slider(relative_mouse_pos)

        elif self.current_screen == "explosion_shop":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                relative_mouse_pos = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                back_button_rect = pygame.Rect(self.width // 2 - 120, self.height - 100, 240, 40)
                if back_button_rect.collidepoint(relative_mouse_pos):
                    self.current_screen = "shop_menu"
                    return "back_to_shop_menu"

                rocket_card_width = 162
                rocket_card_height = 208
                spacing = 15
                initial_offset = (self.width - len(self.explosion_shop_sprites) * (rocket_card_width + spacing)) // 2

                conn = sqlite3.connect('player_data.db')
                c = conn.cursor()
                c.execute("SELECT name, price FROM explosion_radii")
                rockets_data = c.fetchall()
                conn.close()
                last_used, buyed_radii = self.load_buyed_explosion_radii()
                buyed_rockets = buyed_radii
                self.selected_radii = last_used

                for i, (rocket_name, price) in enumerate(rockets_data):
                    x = initial_offset + i * (rocket_card_width + spacing) + 100
                    y = self.height // 2 - rocket_card_height // 2 - 50
                    buy_button_rect = pygame.Rect(x, y + rocket_card_height + 40, rocket_card_width, 40)

                    if buy_button_rect.collidepoint(relative_mouse_pos):
                        if rocket_name not in buyed_rockets:
                            current_money = self.get_player_money()
                            if current_money >= price:
                                buyed_rockets.append(rocket_name)
                                self.save_buyed_explosion_radii(rocket_name, buyed_rockets)
                                self.update_player_money(current_money - price)
                        else:
                            self.selected_radii = rocket_name
                            self.save_buyed_explosion_radii(self.selected_radii, buyed_rockets)
        elif self.current_screen == "rejim_menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                relative_mouse_pos = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                for i, rect_button in enumerate(self.rejim_button_rects):
                    rect = rect_button[0]
                    button_text = rect_button[1]
                    if rect.collidepoint(relative_mouse_pos):
                        if button_text == "60 секунд":
                            self.current_screen = "difficulty_menu"
                            return "difficulty_menu_selected"
                        elif button_text == "Назад":
                            self.current_screen = "main_menu"
                            return "back_to_main_menu"
        elif self.current_screen == "difficulty_menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                relative_mouse_pos = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                for i, rect_button in enumerate(self.difficulty_button_rects):
                    rect = rect_button[0]
                    button_text = rect_button[1]
                    if rect.collidepoint(relative_mouse_pos):
                        if button_text in ["Легко", "Нормально", "Тяжело"]:
                            self.difficulty = button_text
                            self.start_main_game(button_text)
                            self.current_screen = "main_game"
                            return "start_main_game"
                        elif button_text == "Назад":
                            self.current_screen = "rejim_menu"
                            return "back_to_rejim_menu"
        elif self.current_screen == "main_game":
            if not self.paused:
                if event.type == pygame.MOUSEMOTION:
                    self.crosshair.x, self.crosshair.y = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.ammo_count > 0:
                    relative_mouse_pos = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                    rlo_in_range = False
                    for rlo in self.rlos:
                        if not rlo.is_destroyed:
                            distance_to_rlo = math.hypot(rlo.rect.centerx - self.crosshair.x,
                                                         rlo.rect.centery - self.crosshair.y)
                            if distance_to_rlo < 200 and rlo.is_defending:
                                rlo_in_range = True
                                break
                    if not rlo_in_range:
                        self.shells.append(Shell(self, self.crosshair.x, self.crosshair.y))
                        self.ammo_count -= 1
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
        elif self.current_screen == "rank_screen":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                relative_mouse_pos = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                for rect_button in self.rank_button_rects:
                    rect = rect_button[0]
                    button_text = rect_button[1]
                    if rect.collidepoint(relative_mouse_pos):
                        if button_text == "Играть снова":
                            self.start_main_game(self.difficulty) # restart game with same difficulty
                            self.current_screen = "main_game"
                            return "restart_main_game"
                        elif button_text == "Назад в меню":
                            self.current_screen = "main_menu"
                            return "back_to_main_menu_from_rank"

        return None

    def start_main_game(self, difficulty):
        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()
        c.execute("SELECT radius FROM explosion_radii WHERE is_selected = 1")
        selected_explosion_radius = c.fetchone()
        self.shell_radius = selected_explosion_radius[
            0] if selected_explosion_radius else 100  # Default radius if none selected

        self.difficulty = difficulty
        self.money_per_tank = self.money_per_tank_levels[difficulty]
        self.tanks = [Tank(self, self.tank_speeds[difficulty]) for _ in range(self.tank_counts[difficulty])]
        self.rlos = [RLO(self) for _ in range(self.rlo_counts[difficulty])]
        self.ammos_ingame = []
        self.explosions = []
        self.shells = []
        self.score = 0
        self.ammo_count = 10
        self.last_ammo_spawn_time = pygame.time.get_ticks()
        self.start_time = pygame.time.get_ticks()
        self.paused = False
        pygame.mouse.set_visible(False)
        self.crosshair = Crosshair(self)

    def update_main_game(self):
        if not self.paused:
            current_time = pygame.time.get_ticks()
            if len(self.tanks) < self.tank_counts[self.difficulty]:
                self.tanks.append(Tank(self, self.tank_speeds[self.difficulty]))

            for ammo in self.ammos_ingame[:]:
                if ammo.rect.collidepoint(self.crosshair.x, self.crosshair.y):
                    self.ammos_ingame.remove(ammo)
                    self.ammo_count += 7

            for tank in self.tanks[:]:
                if tank.is_destroyed and pygame.time.get_ticks() - tank.destroy_time > 7000:
                    self.tanks.remove(tank)
            for rlo in self.rlos[:]:
                if rlo.is_destroyed and pygame.time.get_ticks() - rlo.destroy_time > 7000:
                    self.rlos.remove(rlo)

            if current_time - self.last_ammo_spawn_time > 1000:
                if random.random() < self.ammo_spawn_rates[self.difficulty]:
                    self.ammos_ingame.append(Ammo(self))
                self.last_ammo_spawn_time = current_time

            if self.game_time_limit - (current_time - self.start_time) // 1000 <= 0:
                pygame.mouse.set_visible(True)
                self.current_screen = "rank_screen"

    # Integrated Slider methods from CustomSlider
    def draw_rocket_shop_slider(self, screen):
        screen.blit(self.slider_background_image, (self.slider_rect.x - 5, self.slider_rect.y + 2))
        screen.blit(self.slider_handle_image, (self.slider_handle_rect.x, self.slider_handle_rect.y))

    def move_rocket_shop_slider(self, mouse_pos):
        if self.slider_is_dragging:
            self.slider_handle_rect.x = mouse_pos[0] - self.slider_handle_image.get_width() // 2
            self.slider_handle_rect.x = max(self.slider_rect.left,
                                            min(self.slider_handle_rect.x,
                                                self.slider_rect.right - self.slider_handle_image.get_width()))
            self.slider_value = (self.slider_handle_rect.x - self.slider_rect.left) / (
                        self.slider_rect.width - self.slider_handle_image.get_width()) * (
                                        self.slider_max_value - self.slider_min_value) + self.slider_min_value

    def get_rocket_shop_slider_value(self):
        return self.slider_value

    def create_db(self):
        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS player
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     money INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()

    def create_rockets_table(self):
        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()
        listOfTables = c.execute(
            """SELECT name FROM sqlite_master WHERE type='table'
            AND name='rockets'; """).fetchall()

        if listOfTables == []:
            c.execute('''CREATE TABLE IF NOT EXISTS rockets
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT,
                         price INTEGER,
                         is_bought INTEGER DEFAULT 0,
                         is_selected INTEGER DEFAULT 0)''')
            conn.commit()
            conn.close()
            conn = sqlite3.connect('player_data.db')
            c = conn.cursor()

            rocket_prices = self.rocket_prices

            for rocket, price in rocket_prices.items():
                c.execute("INSERT OR IGNORE INTO rockets (name, price) VALUES (?, ?)", (rocket, price))

            c.execute("UPDATE rockets SET is_selected = 1 WHERE name = 'фаб500'")
            c.execute("UPDATE rockets SET is_bought = 1 WHERE name = 'фаб500'")

            conn.commit()
            conn.close()
        else:
            print('Table found!')

    def create_explosion_radii_table(self):
        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()
        listOfTables = c.execute(
            """SELECT name FROM sqlite_master WHERE type='table'
            AND name='explosion_radii'; """).fetchall()

        if listOfTables == []:
            c.execute('''CREATE TABLE IF NOT EXISTS explosion_radii
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT,
                         price INTEGER,
                         radius INTEGER,
                         is_bought INTEGER DEFAULT 0,
                         is_selected INTEGER DEFAULT 0)''')
            conn.commit()
            conn.close()
            conn = sqlite3.connect('player_data.db')
            c = conn.cursor()

            explosion_radii_prices = self.explosion_radii_prices

            for name, details in explosion_radii_prices.items():
                c.execute("INSERT OR IGNORE INTO explosion_radii (name, price, radius) VALUES (?, ?, ?)",
                          (name, details['price'], details['radius']))

            c.execute("UPDATE explosion_radii SET is_selected = 1 WHERE name = 'Маленький'")
            c.execute("UPDATE explosion_radii SET is_bought = 1 WHERE name = 'Маленький'")

            conn.commit()
            conn.close()
        else:
            print('Table found!')

    def load_buyed_explosion_radii(self):
        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()
        c.execute("SELECT name FROM explosion_radii WHERE is_bought = 1")
        bought_explosion_radii = [row[0] for row in c.fetchall()]

        c.execute("SELECT name FROM explosion_radii WHERE is_selected = 1")
        selected_explosion_radius = c.fetchone()

        if selected_explosion_radius is None:
            last_used = "Маленький"
        else:
            last_used = selected_explosion_radius[0]

        conn.close()

        self.selected_radii = last_used  # Set the class attribute
        return last_used, bought_explosion_radii

    def save_buyed_explosion_radii(self, last_used, all_buyed_explosion_radii):
        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()

        c.execute("UPDATE explosion_radii SET is_bought = 0")
        for radius in all_buyed_explosion_radii:
            c.execute("UPDATE explosion_radii SET is_bought = 1 WHERE name = ?", (radius,))

        c.execute("UPDATE explosion_radii SET is_selected = 0")
        c.execute("UPDATE explosion_radii SET is_selected = 1 WHERE name = ?", (last_used,))

        conn.commit()
        conn.close()

    def get_player_money(self):
        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()
        c.execute("SELECT money FROM player WHERE id=1")
        money = c.fetchone()
        if money is None:
            return 0
        else:
            return money[0]

    def update_player_money(self, money):
        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()
        c.execute("SELECT * FROM player WHERE id=1")
        if c.fetchone() is None:
            c.execute("INSERT INTO player (money) VALUES (?)", (money,))
        else:
            c.execute("UPDATE player SET money=? WHERE id=1", (money,))

        conn.commit()
        conn.close()

    def load_buyed_rockets(self):
        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()
        c.execute("SELECT name FROM rockets WHERE is_bought = 1")
        bought_rockets = [row[0] for row in c.fetchall()]
        c.execute("SELECT name FROM rockets WHERE is_selected = 1")
        selected_rocket = c.fetchone()

        if selected_rocket is None:
            last_used = "фаб500"
        else:
            last_used = selected_rocket[0]

        conn.close()

        self.selected_rocket = last_used  # Set the class attribute
        return last_used, bought_rockets

    def save_buyed_rockets(self, last_used, all_buyed_rockets):
        conn = sqlite3.connect('player_data.db')
        c = conn.cursor()

        c.execute("UPDATE rockets SET is_bought = 0")
        for rocket in all_buyed_rockets:
            c.execute("UPDATE rockets SET is_bought = 1 WHERE name = ?", (rocket,))

        c.execute("UPDATE rockets SET is_selected = 0")
        c.execute("UPDATE rockets SET is_selected = 1 WHERE name = ?", (last_used,))

        conn.commit()
        conn.close()


class RLO:
    def __init__(self, game):  # Pass game instance
        self.game = game  # Store game instance
        self.image = pygame.image.load('images/IZ/units/РСЗО.png').convert_alpha()
        self.image = pygame.transform.scale(self.image,
                                            (self.game.rlo_width, self.game.rlo_height))  # Use game attributes
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, self.game.width - self.game.rlo_width)  # Use game attributes
        self.rect.y = random.randint(0, self.game.height - self.game.rlo_height)  # Use game attributes
        self.speed = 6
        self.angle = random.uniform(0, 2 * math.pi)
        self.is_destroyed = False
        self.destroy_time = 0
        self.cycle_time = pygame.time.get_ticks()
        self.is_defending = False
        self.angular_velocity = 0

    def draw(self, screen):
        self.image2 = pygame.transform.rotate(self.image, math.degrees(self.angle))
        self.rect2 = self.image2.get_rect(center=self.rect.center)
        if self.is_destroyed:
            current_time = pygame.time.get_ticks()
            if current_time - self.destroy_time < 5000:
                screen.blit(self.image2, self.rect2)
            elif current_time - self.destroy_time < 7000:
                alpha = int(255 * (1 - (current_time - self.destroy_time - 5000) / 2000))
                s = pygame.Surface((self.game.rlo_width * 3, self.game.rlo_height * 3),
                                   pygame.SRCALPHA)  # Use game attributes
                s.blit(self.image2, (0, 0))
                s.set_alpha(alpha)
                screen.blit(s, self.rect2)
        else:
            screen.blit(self.image2, self.rect2)

    def update(self):
        if not self.is_destroyed:
            current_time = pygame.time.get_ticks()
            if current_time - self.cycle_time < 10000:
                if current_time - self.cycle_time < 5000:
                    self.is_defending = False
                    self.angle += self.angular_velocity
                    self.angular_velocity *= 0.80
                    if abs(self.angular_velocity) < 0.01:
                        self.angular_velocity = 0
                    self.speed_x = self.speed * math.cos(self.angle)
                    self.speed_y = -self.speed * math.sin(self.angle)

                    self.rect.x += self.speed_x
                    self.rect.y += self.speed_y

                    if self.rect.left < 0 or self.rect.right > self.game.width:  # Use game attributes
                        self.angle = math.pi - self.angle
                        if self.rect.left < 0:
                            self.rect.left = 0
                        elif self.rect.right > self.game.width:  # Use game attributes
                            self.rect.right = self.game.width  # Use game attributes
                    if self.rect.top < 0 or self.rect.bottom > self.game.height:  # Use game attributes
                        self.angle = -self.angle
                        if self.rect.top < 0:
                            self.rect.top = 0
                        elif self.rect.bottom > self.game.height:  # Use game attributes
                            self.rect.bottom = self.game.height  # Use game attributes

                    for tank in self.game.tanks:  # Use game attributes
                        if tank != self and not tank.is_destroyed and not self.is_destroyed:
                            distance_to_tank = math.hypot(tank.rect.centerx - self.rect.centerx,
                                                          tank.rect.centery - self.rect.centery)
                            if distance_to_tank < (
                                    self.game.tank_width + self.game.tank_height) / 2:  # Use game attributes
                                dx = tank.rect.centerx - self.rect.centerx
                                dy = tank.rect.centery - self.rect.centery
                                angle = math.atan2(dy, dx)

                                overlap = (
                                                      self.game.tank_width + self.game.tank_height) / 2 - distance_to_tank  # Use game attributes
                                self.rect.x -= dx / math.hypot(dx, dy) * overlap / 4
                                self.rect.y -= dy / math.hypot(dx, dy) * overlap / 4
                                tank.rect.x += dx / math.hypot(dx, dy) * overlap / 4
                                tank.rect.y += dy / math.hypot(dx, dy) * overlap / 4

                                self.angular_velocity += angle / 80
                                tank.angular_velocity -= angle / 80

                        elif tank != self and tank.is_destroyed:
                            distance_to_destroyed_tank = math.hypot(tank.rect.centerx - self.rect.centerx,
                                                                    tank.rect.centery - self.rect.centery)
                            if distance_to_destroyed_tank < (
                                    self.game.tank_width + self.game.tank_height) / 2:  # Use game attributes
                                dx = tank.rect.centerx - self.rect.centerx
                                dy = tank.rect.centery - self.rect.centery
                                angle = math.atan2(dy, dx)

                                overlap = (
                                                      self.game.tank_width + self.game.tank_height) / 2 - distance_to_destroyed_tank  # Use game attributes
                                self.rect.x -= dx / math.hypot(dx, dy) * overlap / 4
                                self.rect.y -= dy / math.hypot(dx, dy) * overlap / 4
                                tank.rect.x += dx / math.hypot(dx, dy) * overlap / 4
                                tank.rect.y += dy / math.hypot(dx, dy) * overlap / 4

                                self.angular_velocity += angle / 80
                    for tank in self.game.rlos:  # Use game attributes
                        if tank != self:
                            distance_to_tank = math.hypot(tank.rect.centerx - self.rect.centerx,
                                                          tank.rect.centery - self.rect.centery)
                            if distance_to_tank < (
                                    self.game.tank_width + self.game.tank_height) / 2:  # Use game attributes
                                dx = tank.rect.centerx - self.rect.centerx
                                dy = tank.rect.centery - self.rect.centery
                                angle = math.atan2(dy, dx)

                                overlap = (
                                                      self.game.tank_width + self.game.tank_height) / 2 - distance_to_tank  # Use game attributes
                                self.rect.x -= dx / math.hypot(dx, dy) * overlap / 4
                                self.rect.y -= dy / math.hypot(dx, dy) * overlap / 4
                                tank.rect.x += dx / math.hypot(dx, dy) * overlap / 4
                                tank.rect.y += dy / math.hypot(dx, dy) * overlap / 4

                                self.angular_velocity += angle / 80
                                if not tank.is_defending or tank.is_destroyed:
                                    tank.angular_velocity -= angle / 80
                else:
                    self.is_defending = True

            else:
                self.cycle_time = current_time

    def destroy(self):
        self.is_destroyed = True
        self.destroy_time = pygame.time.get_ticks()
        self.image = pygame.image.load('images/IZ/units/РСЗО2.png').convert_alpha()
        self.image = pygame.transform.scale(self.image,
                                            (self.game.rlo_width, self.game.rlo_height))  # Use game attributes


class Building:
    def __init__(self, game, type, hp):  # Pass game instance
        self.game = game  # Store game instance
        self.image = pygame.image.load('images/IZ/units/build.png').convert_alpha()
        self.rect = self.image.get_rect(center=(self.game.width - 150, self.game.height // 2))  # Use game attributes
        self.hp = hp
        self.type = type

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        hp_bar_width = 100
        hp_bar_height = 15
        hp_bar_x = self.rect.centerx - hp_bar_width // 2
        hp_bar_y = self.rect.top - hp_bar_height - 10
        pygame.draw.rect(screen, self.game.red,
                         (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height))  # Use game attributes
        current_hp = int(hp_bar_width * (self.hp / 100))
        pygame.draw.rect(screen, self.game.green,
                         (hp_bar_x, hp_bar_y, current_hp, hp_bar_height))  # Use game attributes

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0


class Tank:
    def __init__(self, game, speed):  # Pass game instance
        self.game = game  # Store game instance
        self.image = pygame.image.load('images/IZ/units/ТАНКВСУ.png').convert_alpha()
        self.image = pygame.transform.scale(self.image,
                                            (self.game.tank_width, self.game.tank_height))  # Use game attributes
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, self.game.width - self.game.tank_width)  # Use game attributes
        self.rect.y = random.randint(0, self.game.height - self.game.tank_height)  # Use game attributes
        self.speed = speed
        self.angle = random.uniform(0, 2 * math.pi)
        self.is_destroyed = False
        self.destroy_time = 0
        self.angular_velocity = 0

    def draw(self, screen):
        self.image2 = pygame.transform.rotate(self.image, math.degrees(self.angle))
        self.rect2 = self.image2.get_rect(center=self.rect.center)
        if self.is_destroyed:
            current_time = pygame.time.get_ticks()
            if current_time - self.destroy_time < 5000:
                screen.blit(self.image2, self.rect2)
            elif current_time - self.destroy_time < 7000:
                alpha = int(255 * (1 - (current_time - self.destroy_time - 5000) / 2000))
                s = pygame.Surface((self.game.tank_width * 3, self.game.tank_height * 3),
                                   pygame.SRCALPHA)  # Use game attributes
                s.blit(self.image2, (0, 0))
                s.set_alpha(alpha)
                screen.blit(s, self.rect2)
        else:
            screen.blit(self.image2, self.rect2)

    def update(self):
        if not self.is_destroyed:
            self.speed_x = self.speed * math.cos(self.angle)
            self.speed_y = -self.speed * math.sin(self.angle)
            self.angle += self.angular_velocity
            self.angular_velocity *= 0.80
            if abs(self.angular_velocity) < 0.01:
                self.angular_velocity = 0
            self.angle += math.pi / 820
            self.rect.x += self.speed_x
            self.rect.y += self.speed_y

            if self.rect.left < 0:
                self.angle = math.pi - self.angle
                self.rect.x = 0
            elif self.rect.right > self.game.width:  # Use game attributes
                self.angle = math.pi - self.angle
                self.rect.right = self.game.width  # Use game attributes
            if self.rect.top < 0:
                self.angle = -self.angle
                self.rect.y = 0
            elif self.rect.bottom > self.game.height:  # Use game attributes
                self.rect.bottom = self.game.height  # Use game attributes
                self.angle = -self.angle

            for tank in self.game.tanks:  # Use game attributes
                if tank != self and not tank.is_destroyed and not self.is_destroyed:
                    distance_to_tank = math.hypot(tank.rect.centerx - self.rect.centerx,
                                                  tank.rect.centery - self.rect.centery)
                    if distance_to_tank < (self.game.tank_width + self.game.tank_height) / 2:  # Use game attributes
                        dx = tank.rect.centerx - self.rect.centerx
                        dy = tank.rect.centery - self.rect.centery
                        angle = math.atan2(dy, dx)

                        overlap = (
                                              self.game.tank_width + self.game.tank_height) / 2 - distance_to_tank  # Use game attributes
                        self.rect.x -= dx / math.hypot(dx, dy) * overlap / 4
                        self.rect.y -= dy / math.hypot(dx, dy) * overlap / 4
                        tank.rect.x += dx / math.hypot(dx, dy) * overlap / 4
                        tank.rect.y += dy / math.hypot(dx, dy) * overlap / 4

                        self.angular_velocity += angle / 80
                        tank.angular_velocity -= angle / 80

                elif tank != self and tank.is_destroyed:
                    distance_to_destroyed_tank = math.hypot(tank.rect.centerx - self.rect.centerx,
                                                            tank.rect.centery - self.rect.centery)
                    if distance_to_destroyed_tank < (
                            self.game.tank_width + self.game.tank_height) / 2:  # Use game attributes
                        dx = tank.rect.centerx - self.rect.centerx
                        dy = tank.rect.centery - self.rect.centery
                        angle = math.atan2(dy, dx)

                        overlap = (
                                              self.game.tank_width + self.game.tank_height) / 2 - distance_to_destroyed_tank  # Use game attributes
                        self.rect.x -= dx / math.hypot(dx, dy) * overlap / 4
                        self.rect.y -= dy / math.hypot(dx, dy) * overlap / 4
                        tank.rect.x += dx / math.hypot(dx, dy) * overlap / 4
                        tank.rect.y += dy / math.hypot(dx, dy) * overlap / 4

                        self.angular_velocity += angle / 80
            for tank in self.game.rlos:  # Use game attributes
                if tank != self:
                    distance_to_tank = math.hypot(tank.rect.centerx - self.rect.centerx,
                                                  tank.rect.centery - self.rect.centery)
                    if distance_to_tank < (self.game.tank_width + self.game.tank_height) / 2:  # Use game attributes
                        dx = tank.rect.centerx - self.rect.centerx
                        dy = tank.rect.centery - self.rect.centery
                        angle = math.atan2(dy, dx)

                        overlap = (
                                              self.game.tank_width + self.game.tank_height) / 2 - distance_to_tank  # Use game attributes
                        self.rect.x -= dx / math.hypot(dx, dy) * overlap / 4
                        self.rect.y -= dy / math.hypot(dx, dy) * overlap / 4
                        tank.rect.x += dx / math.hypot(dx, dy) * overlap / 4
                        tank.rect.y += dy / math.hypot(dx, dy) * overlap / 4

                        self.angular_velocity += angle / 80
                        if not tank.is_defending or tank.is_destroyed:
                            tank.angular_velocity -= angle / 80

    def destroy(self):
        self.is_destroyed = True
        self.destroy_time = pygame.time.get_ticks()
        self.image = pygame.image.load('images/IZ/units/ТАНКВСУ2.png').convert_alpha()
        self.image = pygame.transform.scale(self.image,
                                            (self.game.tank_width, self.game.tank_height))  # Use game attributes


class Crosshair:
    def __init__(self, game):  # Pass game instance
        self.game = game  # Store game instance
        self.x = self.game.width // 2  # Use game attributes
        self.y = self.game.height // 2  # Use game attributes

    def draw(self, screen, color=None):
        if color is None:
            color = self.game.white  # Use game attributes
        pygame.draw.line(screen, color, (self.x - 12, self.y), (self.x + 12, self.y), 2)
        pygame.draw.line(screen, color, (self.x, self.y - 12), (self.x, self.y + 12), 2)


class Ammo:
    def __init__(self, game):  # Pass game instance
        self.game = game  # Store game instance
        self.image = pygame.image.load('images/IZ/units/boepripasi.png').convert_alpha()
        self.image = pygame.transform.scale(self.image,
                                            (self.game.ammo_width, self.game.ammo_height))  # Use game attributes
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, self.game.width - self.game.ammo_width)  # Use game attributes
        self.rect.y = random.randint(0, self.game.height - self.game.ammo_height)  # Use game attributes

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Shell:
    def __init__(self, game, x, y):  # Pass game instance
        self.game = game  # Store game instance
        self.original_image = self.game.rocket_sprites[self.game.selected_rocket]  # Use game attributes
        self.image = self.original_image.copy()
        self.x = x
        self.y = y
        self.timer = pygame.time.get_ticks()
        self.scale_factor = 1.0

    def draw(self, screen):
        screen.blit(self.image, (self.x - self.image.get_width() // 2,
                                 self.y - self.image.get_height() // 2))


class Explosion:
    def __init__(self, game, x, y):  # Pass game instance
        self.game = game  # Store game instance
        self.image = pygame.image.load('images/IZ/units/сво.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (
        self.game.explosion_width, self.game.explosion_height))  # Use game attributes
        self.rect = self.image.get_rect(center=(x, y))
        self.timer = pygame.time.get_ticks()
        self.scale_factor = 1.0
        self.alpha = 255

    def draw(self, screen):
        scaled_image = pygame.transform.scale(self.image, (int(self.image.get_width() * self.scale_factor),
                                                           int(self.image.get_height() * self.scale_factor)))
        s = pygame.Surface((scaled_image.get_width(), scaled_image.get_height()), pygame.SRCALPHA)
        s.blit(scaled_image, (0, 0))
        s.set_alpha(self.alpha)
        screen.blit(s, (self.rect.centerx - scaled_image.get_width() // 2,
                        self.rect.centery - scaled_image.get_height() // 2))

    def update(self):
        current_time = pygame.time.get_ticks()

        if current_time - self.timer < 1000:
            self.scale_factor = min(1 + (current_time - self.timer) / 1000 * 0.5,
                                    1.5)

        elif current_time - self.timer < 2000:
            self.alpha = max(0, 255 - (current_time - self.timer - 1000) / 1000 * 255)

        else:
            return False

        return True
