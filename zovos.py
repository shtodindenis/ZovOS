import pygame
import time
import sys
import random
import os
import sqlite3
import threading
from browser import BrowserApp

pygame.init()
pygame.font.init()

screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode(
    (screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("ZOV OS Startup")

# --- Colors ---
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
taskbar_color = dark_gray
grey_background = (200, 200, 200)
light_blue_grey = (220, 230, 240)

# Theme Colors
light_theme_window_color = white
light_theme_text_color = black
dark_theme_window_color = dark_gray  # or black
dark_theme_text_color = white

window_color = light_theme_window_color  # Default to light theme
text_color = light_theme_text_color

# --- Fonts ---
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


# --- Startup Animation Frames ---
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

# --- Background Image Caching ---
background_cache = {}


def get_background_image(filename):
    if filename not in background_cache:
        try:
            image = pygame.image.load(
                os.path.join("images", filename)).convert()
            background_cache[filename] = pygame.transform.scale(
                image, (screen_width, screen_height))
        except FileNotFoundError:
            surface = pygame.Surface((screen_width, screen_height))
            surface.fill(light_blue_grey)
            background_cache[filename] = surface
    return background_cache[filename]


# --- Settings Database ---
def init_settings_db():
    conn = sqlite3.connect('system_settings.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            setting_name TEXT PRIMARY KEY,
            setting_value TEXT
        )
    ''')
    conn.commit()
    conn.close()


def get_setting(setting_name, default_value):
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
    conn = sqlite3.connect('system_settings.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO system_settings (setting_name, setting_value) VALUES (?, ?)",
                   (setting_name, setting_value))
    conn.commit()
    conn.close()


init_settings_db()

current_background_setting = get_setting(
    'background_image', 'zovosbg.png')
background_image = get_background_image(current_background_setting)
icon_layout_setting = get_setting(
    'icon_layout', 'grid')
current_theme_setting = get_setting('theme', 'light')


def update_theme_colors():
    global window_color, text_color, current_theme_setting
    current_theme_setting = get_setting('theme', 'light')
    if current_theme_setting == 'dark':
        window_color = dark_theme_window_color
        text_color = dark_theme_text_color
    else:
        window_color = light_theme_window_color
        text_color = light_theme_text_color


update_theme_colors()

# --- Startup Text Animation ---
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


# --- Helper Drawing Functions ---
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


def refresh_settings_from_db(files, windows):
    global current_background_setting, background_image, icon_layout_setting, current_theme_setting, text_color
    current_background_setting = get_setting(
        'background_image', 'zovosbg.png')
    background_image = get_background_image(current_background_setting)
    icon_layout_setting = get_setting('icon_layout', 'grid')
    current_theme_setting = get_setting('theme', 'light')

    update_theme_colors()

    # Update window title text color when theme changes
    for window in windows:
        window.update_title_surface()

    if icon_layout_setting == 'grid':
        grid_size = 108 + 20
        for file in files:
            file.rect.topleft = file.get_grid_position(
                grid_size)
            file.name_rect.center = (
                file.rect.centerx, file.rect.bottom + 20)
            file.update_selection_rect()
    elif icon_layout_setting == 'free':
        pass  # No specific layout update needed for 'free' layout

    # Update text color for all files regardless of layout
    for file in files:
        file.update_name_surface()


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
        self.settings_options = ["Background 1", "Background 2",
                                 "Background 3", "Color", "Light Theme", "Dark Theme"]
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

    def load_background_previews(self):
        preview_width = 100
        preview_height = int(preview_width * 9 / 16)
        preview_size = (preview_width, preview_height)

        preview_cache = {}

        def get_preview_surface(filename, size):
            key = (filename, size)
            if key not in preview_cache:
                try:
                    preview_image = pygame.image.load(
                        os.path.join("images", filename)).convert()
                    preview_cache[key] = pygame.transform.scale(
                        preview_image, size)
                except FileNotFoundError:
                    surface = pygame.Surface(size)
                    surface.fill(light_blue_grey)
                    preview_cache[key] = surface
            return preview_cache[key]

        self.background_previews["zovosbg.png"] = get_preview_surface(
            "zovosbg.png", preview_size)
        self.background_previews["zovosbg2.png"] = get_preview_surface(
            "zovosbg2.png", preview_size)
        self.background_previews["zovosbg3.png"] = get_preview_surface(
            "zovosbg3.png", preview_size)
        self.background_previews["color"] = pygame.Surface(preview_size)
        self.background_previews["color"].fill(
            light_blue_grey)

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
        option_margin_x = 20
        option_margin_y = 30

        background_options = ["zovosbg.png",
                              "zovosbg2.png", "zovosbg3.png", "color"]

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

        draw_text(screen_surface, "Чтобы изменения вступили в силу, перезапустите ОС",
                  settings_font, text_color, (screen_rect.centerx, screen_rect.bottom - 20), 'midbottom')

    def handle_event(self, mouse_pos, window_rect):
        relative_mouse_pos = (mouse_pos[0] - window_rect.x,
                              mouse_pos[1] - window_rect.y)
        for option_key, option_rect in self.settings_options_rects.items():
            if option_rect.collidepoint(relative_mouse_pos):
                if option_key == "zovosbg.png":
                    return "zovosbg.png"
                elif option_key == "zovosbg2.png":
                    return "zovosbg2.png"
                elif option_key == "zovosbg3.png":
                    return "zovosbg3.png"
                elif option_key == "color":
                    return "color"

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

        return None


class CalculatorApp:
    def __init__(self):
        self.width = 300
        self.height = 400
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
            ["C", "+/-"]  # Clear and +/- buttons
        ]
        self.button_rects = []
        self._layout_buttons()

    def _layout_buttons(self):
        start_x = 10
        start_y = 100  # Below the display area
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
        # Display area
        display_rect = pygame.Rect(10, 10, self.width - 20, 80)
        draw_rect(screen_surface, window_color, display_rect)
        draw_rect(screen_surface, black, display_rect, 1)
        draw_text(screen_surface, self.display_text, self.font, text_color,
                  (display_rect.right - 10, display_rect.centery), 'midright')

        # Buttons
        for row_rects in self.button_rects:
            for rect_button in row_rects:
                rect = rect_button[0]  # Get rect from tuple
                button_text = rect_button[1]  # Get button_text from tuple
                button_color = light_gray if button_text.isdigit(
                ) or button_text == '.' else dark_gray
                draw_rect(screen_surface, button_color, rect)
                draw_rect(screen_surface, black, rect, 1)
                text_color_button = text_color if button_text != "C" else red  # Red color for "C"
                draw_text(screen_surface, button_text, self.font,
                          text_color_button, rect.center, 'center')

    def handle_event(self, event, window_rect):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            relative_mouse_pos = (
                event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
            for row_rects in self.button_rects:
                for rect_button in row_rects:
                    rect = rect_button[0]  # Get rect from tuple
                    button_text = rect_button[1]  # Get button_text from tuple
                    if rect.collidepoint(relative_mouse_pos):
                        self.on_button_click(button_text)
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
                self.calculation_stack.append(float(self.display_text))
                self.calculation_stack.append(button_text)
                self.display_text = ""
        elif button_text == "=":
            if self.display_text != "":
                self.calculation_stack.append(float(self.display_text))
                try:
                    result = self._calculate()
                    self.display_text = str(result)
                    self.calculation_stack = []  # Clear stack after calculation
                except Exception as e:
                    self.display_text = "Error"  # Handle errors during calculation
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
                pass  # Ignore if display is error or empty

    def _calculate(self):
        calculation_str = ""
        for item in self.calculation_stack:
            calculation_str += str(item)
        try:
            return eval(calculation_str)  # Using eval for simple calculation
        except (TypeError, ValueError, SyntaxError, ZeroDivisionError):
            raise Exception("Calculation Error")


class Widget:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen):
        raise NotImplementedError("Subclasses must implement draw method")

    def update(self):
        pass  # Optional update method for dynamic widgets


class ClockWidget(Widget):
    def __init__(self, x, y):
        super().__init__(x, y, 200, 100)  # Adjust size as needed
        self.font = widget_font
        self.time_color = text_color

    def draw(self, screen):
        draw_rect(screen, window_color, self.rect)
        draw_rect(screen, black, self.rect, 1)  # Optional border
        current_time = time.strftime("%H:%M:%S")
        draw_text(screen, current_time, self.font,
                  self.time_color, self.rect.center, 'center')

    def update(self):
        self.time_color = text_color  # Update color based on theme change


class CalendarWidget(Widget):
    def __init__(self, x, y):
        super().__init__(x, y, 200, 150)  # Adjust size as needed
        self.font = widget_font
        self.date_color = text_color

    def draw(self, screen):
        draw_rect(screen, window_color, self.rect)
        draw_rect(screen, black, self.rect, 1)  # Optional border
        current_date = time.strftime("%Y-%m-%d")
        draw_text(screen, current_date, self.font,
                  self.date_color, self.rect.center, 'center')
        day_of_week = time.strftime("%A")  # e.g., "Monday"
        draw_text(screen, day_of_week, self.font, self.date_color,
                  (self.rect.centerx, self.rect.bottom - 30), 'center')

    def update(self):
        self.date_color = text_color  # Update color based on theme change


class Window:
    def __init__(self, title, width, height, x, y, file=None, settings_app=None, browser_app=None, calculator_app=None, folder=None, properties_text=None):
        self.title = title
        self.width = width
        self.height = height
        # content rect start below title bar
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
            self.close_button_size - 10  # Relative to title bar width
        self.close_button_y = 15  # Fixed Y inside title bar
        self.close_button_rect = pygame.Rect(self.title_bar.x + self.close_button_x, self.title_bar.y + self.close_button_y, self.close_button_size,
                                             self.close_button_size)
        self.close_cross_surface = pygame.Surface(
            (self.close_button_size, self.close_button_size), pygame.SRCALPHA)
        pygame.draw.line(self.close_cross_surface, red, (0, 0),
                         (self.close_button_size, self.close_button_size), 7)
        pygame.draw.line(self.close_cross_surface, red,
                         (self.close_button_size-1, 0), (-1, self.close_button_size), 7)

        # Minimize Button
        self.minimize_button_size = 20
        self.minimize_button_x = self.title_bar.width - 2 * \
            (self.minimize_button_size +
             10)  # Position before close button, relative to title bar width
        self.minimize_button_y = 15  # Fixed Y inside title bar
        self.minimize_button_rect = pygame.Rect(
            self.title_bar.x + self.minimize_button_x, self.title_bar.y + self.minimize_button_y, self.minimize_button_size, self.minimize_button_size)
        self.minimize_line_surface = pygame.Surface(
            (self.minimize_button_size, self.minimize_button_size), pygame.SRCALPHA)
        pygame.draw.line(self.minimize_line_surface, yellow, (3, self.minimize_button_size - 3),
                         (self.minimize_button_size - 3, self.minimize_button_size - 3), 5)

        # Maximize Button
        self.maximize_button_size = 20
        self.maximize_button_x = self.title_bar.width - 3 * \
            (self.maximize_button_size +
             10)  # Position before minimize button, relative to title bar width
        self.maximize_button_y = 15  # Fixed Y inside title bar
        self.maximize_button_rect = pygame.Rect(
            self.title_bar.x + self.maximize_button_x, self.title_bar.y + self.maximize_button_y, self.maximize_button_size, self.maximize_button_size)
        self.maximize_rect_surface = pygame.Surface(
            (self.maximize_button_size, self.maximize_button_size), pygame.SRCALPHA)
        pygame.draw.rect(self.maximize_rect_surface, green, (3, 3,
                         self.maximize_button_size - 6, self.maximize_button_size - 6), 3)

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
        self.calculator_app = calculator_app  # Add calculator_app
        self.folder = folder
        self.properties_text = properties_text  # For PropertiesWindow
        self.window_state = "normal"  # "normal", "minimized", "maximized"
        self.previous_rect = self.rect.copy()  # Store rect before maximizing
        # Store title bar before maximizing
        self.previous_title_bar = self.title_bar.copy()

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
        elif self.calculator_app:  # Calculator icon
            icon_image_path = "calculator_icon.png"
        elif self.folder:
            icon_image_path = "folder.png"
        elif self.properties_text:  # Properties window icon
            icon_image_path = "properties_icon.png"  # You might want a specific icon

        self.taskbar_icon = TaskbarIcon(
            self, icon_image_path)

        self.resizing = False
        self.resize_handle_size = 10
        self.resize_handle_rect = pygame.Rect(
            0, 0, self.resize_handle_size, self.resize_handle_size)
        self.min_width = 200
        self.min_height = 150
        self.initial_mouse_x = 0
        self.initial_mouse_y = 0
        self.initial_width = 0
        self.initial_height = 0

    def update_title_surface(self):
        """Updates the title surface with the current text color."""
        self.title_surface = window_font.render(
            self.title, True, text_color)
        self.title_rect = self.title_surface.get_rect(
            center=self.title_bar.center)

    def draw(self, screen):
        if self.is_open and self.window_state != "minimized":  # Only draw if open and not minimized
            if self.window_state == "maximized":
                # Maximize to screen, accounting for taskbar
                self.rect.x = 0
                self.rect.y = taskbar_height  # Below taskbar
                self.rect.width = screen_width
                self.rect.height = screen_height - taskbar_height - \
                    self.title_bar_height  # Content area below title bar
                self.title_bar.x = 0
                self.title_bar.y = 0  # Title bar at top of screen
                self.title_bar.width = screen_width
                self.title_rect.center = self.title_bar.center
                self.close_button_rect.x = self.title_bar.x + \
                    self.title_bar.width - self.close_button_size - 10
                self.close_button_rect.y = self.title_bar.y + 15
                self.minimize_button_rect.x = self.title_bar.x + \
                    self.title_bar.width - 2 * (self.minimize_button_size + 10)
                self.minimize_button_rect.y = self.title_bar.y + 15
                self.maximize_button_rect.x = self.title_bar.x + \
                    self.title_bar.width - 3 * (self.maximize_button_size + 10)
                self.maximize_button_rect.y = self.title_bar.y + 15

            # Normal or resizing state - ensure button positions are relative to title_bar's position.
            else:
                self.close_button_rect.topleft = (
                    self.title_bar.x + self.close_button_x, self.title_bar.y + self.close_button_y)
                self.minimize_button_rect.topleft = (
                    self.title_bar.x + self.minimize_button_x, self.title_bar.y + self.minimize_button_y)
                self.maximize_button_rect.topleft = (
                    self.title_bar.x + self.maximize_button_x, self.title_bar.y + self.maximize_button_y)

            draw_rect(screen, window_color, self.title_bar)
            screen.blit(self.title_surface, self.title_rect)

            draw_rect(screen, window_color, self.close_button_rect)
            screen.blit(self.close_cross_surface,
                        self.close_button_rect.topleft)

            draw_rect(screen, window_color, self.minimize_button_rect)
            screen.blit(self.minimize_line_surface,
                        self.minimize_button_rect.topleft)

            draw_rect(screen, window_color, self.maximize_button_rect)
            screen.blit(self.maximize_rect_surface,
                        self.maximize_button_rect.topleft)

            self.resize_handle_rect.bottomright = self.rect.bottomright
            draw_rect(screen, light_gray, self.resize_handle_rect)
            draw_rect(screen, black, self.resize_handle_rect, 1)

            if self.file and self.file.name.endswith(".txt"):
                draw_rect(screen, window_color, self.rect)
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
                        topleft=(self.rect.x + 10, self.rect.y + y_offset))

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
                                    screen, selection_color, selection_area_rect)

                    screen.blit(line_surface, text_rect)
                    y_offset += file_font.get_height() + 5

                if self.text_input:
                    if time.time() - self.cursor_time > 0.5:
                        self.cursor_visible = not self.cursor_visible
                        self.cursor_time = time.time()

                    if self.cursor_visible:
                        lines = text_content.split('\n')
                        line_num = 0
                        char_in_line = 0
                        char_count = 0
                        for i, line_render in enumerate(lines):
                            if char_count + len(line_render) >= self.cursor_pos:
                                line_num = i
                                char_in_line = self.cursor_pos - char_count
                                break
                            char_count += len(line_render) + 1

                        cursor_x = self.rect.x + 10 + \
                            file_font.size(lines[line_num][:char_in_line])[0]
                        cursor_y = self.rect.y + 10 + line_num * \
                            (file_font.get_height() + 5)
                        pygame.draw.line(screen, text_color, (cursor_x, cursor_y),
                                         (cursor_x, cursor_y + file_font.get_height()), 2)
            elif self.mail_app:
                self.mail_app.draw(screen.subsurface(self.rect))
            elif self.settings_app:
                draw_rect(screen, window_color, self.rect)
                self.settings_app.draw(screen.subsurface(self.rect))
            elif self.browser_app:
                draw_rect(screen, window_color, self.rect)
                self.browser_app.width = self.width
                self.browser_app.height = self.height
                self.browser_app.draw(screen.subsurface(self.rect))
            elif self.calculator_app:  # Draw calculator app
                draw_rect(screen, window_color, self.rect)
                self.calculator_app.width = self.width
                self.calculator_app.height = self.height
                self.calculator_app.draw(screen.subsurface(self.rect))
            elif self.folder:
                folder_surface = pygame.Surface(
                    self.rect.size, pygame.SRCALPHA)
                folder_surface.fill(transparent_white)
                screen.blit(folder_surface, self.rect.topleft)
                draw_rect(screen, window_color, self.rect, 0)
                self.draw_folder_content(screen.subsurface(
                    self.rect), self.folder.files_inside)
            elif self.properties_text:  # Draw properties window content
                draw_rect(screen, window_color, self.rect)
                y_offset = 20
                lines = self.properties_text.strip().split('\n')
                for line in lines:
                    text_surface = settings_font.render(line, True, text_color)
                    text_rect = text_surface.get_rect(
                        topleft=(self.rect.x + 20, self.rect.y + y_offset))
                    screen.blit(text_surface, text_rect)
                    y_offset += settings_font.get_height() + 5

    def draw_folder_content(self, screen_surface, folder_files):
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
            if x_offset + grid_size > screen_surface.get_width():
                x_offset = x_start
                y_offset += grid_size

    def handle_event(self, event, windows, taskbar, desktop_files, icon_layout_setting, files_in_folder=None):
        global background_image, current_background_setting, dragging_file, is_selecting, dragged_files

        def is_descendant(folder_to_check, potential_parent):
            if potential_parent is None:
                return False
            if folder_to_check == potential_parent:
                return True
            for file_inside in folder_to_check.files_inside:
                if file_inside == potential_parent:
                    return True
                if isinstance(file_inside, Folder):
                    if is_descendant(file_inside, potential_parent):
                        return True
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.title_bar.collidepoint(event.pos):
                    self.dragging = True
                    self.drag_offset_x = event.pos[0] - self.title_bar.x
                    self.drag_offset_y = event.pos[1] - self.title_bar.y
                if self.close_button_rect.collidepoint(event.pos):
                    self.is_open = False
                    taskbar.remove_icon(self.taskbar_icon)
                    if self.app_thread and self.app_thread.is_alive():
                        if self.app_instance and hasattr(self.app_instance, 'stop_running'):
                            self.app_instance.stop_running()
                if self.minimize_button_rect.collidepoint(event.pos):
                    if self.window_state != "minimized":
                        self.window_state = "minimized"
                    else:  # Restore from minimized
                        self.window_state = "normal"
                if self.maximize_button_rect.collidepoint(event.pos):
                    if self.window_state != "maximized":
                        self.previous_rect = self.rect.copy()  # Save current rect before maximizing
                        self.previous_title_bar = self.title_bar.copy()  # Save title bar rect
                        self.window_state = "maximized"

                    else:  # Restore from maximized
                        self.window_state = "normal"
                        self.rect = self.previous_rect  # Restore previous size and position
                        self.title_bar = self.previous_title_bar.copy()  # Restore title bar rect

                        self.width = self.rect.width  # Ensure width and height are updated
                        self.height = self.rect.height
                        self.title_bar.width = self.width  # Update title bar width

                        self.title_rect.center = self.title_bar.center
                        self.close_button_rect.x = self.title_bar.x + \
                            self.title_bar.width - self.close_button_size - 10
                        self.close_button_rect.y = self.title_bar.y + 15
                        self.minimize_button_rect.x = self.title_bar.x + \
                            self.title_bar.width - 2 * \
                            (self.minimize_button_size + 10)
                        self.minimize_button_rect.y = self.title_bar.y + 15
                        self.maximize_button_rect.x = self.title_bar.x + \
                            self.title_bar.width - 3 * \
                            (self.maximize_button_size + 10)
                        self.maximize_button_rect.y = self.title_bar.y + 15

                if self.resize_handle_rect.collidepoint(event.pos):
                    self.resizing = True
                    self.initial_mouse_x = event.pos[0]
                    self.initial_mouse_y = event.pos[1]
                    self.initial_width = self.width
                    self.initial_height = self.height

                if self.rect.collidepoint(event.pos) and not self.title_bar.collidepoint(event.pos) and not self.close_button_rect.collidepoint(event.pos) and not self.resize_handle_rect.collidepoint(event.pos) and not self.minimize_button_rect.collidepoint(event.pos) and not self.maximize_button_rect.collidepoint(event.pos):
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
                                                                         len(lines[clicked_line_index])) if lines[clicked_line_index] else file_font.size(" ")[0]

                        clicked_char_index = min(len(lines[clicked_line_index]), max(
                            0, int(click_pos_local_x // char_width)))

                        char_count = 0
                        for i in range(clicked_line_index):
                            char_count += len(lines[i]) + 1

                        self.cursor_pos = char_count + clicked_char_index

                        if not (pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[pygame.K_RSHIFT]):
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
                            event.pos, self.rect)
                        if settings_result:
                            if settings_result in ["zovosbg.png", "zovosbg2.png", "zovosbg3.png", "color"]:
                                update_setting(
                                    'background_image', settings_result)
                                global background_image, current_background_setting
                                current_background_setting = settings_result
                                background_image = get_background_image(
                                    current_background_setting)
                            elif settings_result == 'layout_change':
                                refresh_settings_from_db(
                                    desktop_files, windows)  # Pass windows here
                            elif settings_result == 'theme_change':
                                refresh_settings_from_db(
                                    desktop_files, windows)  # Pass windows here
                    elif self.browser_app:
                        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL]:
                            if self.rect.collidepoint(event.pos):
                                self.browser_app.handle_event(event, self.rect)
                        elif event.type == pygame.KEYDOWN:
                            self.browser_app.handle_event(event, self.rect)
                    elif self.calculator_app:  # Handle calculator events
                        self.calculator_app.handle_event(event, self.rect)
                    elif self.folder:
                        if self.folder.files_inside:
                            for file_obj in self.folder.files_inside:
                                if file_obj.selection_rect.collidepoint((event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)):
                                    current_time = time.time()
                                    # Open only if selected and double click
                                    if file_obj.selected and current_time - file_obj.last_click_time < file_obj.double_click_interval:
                                        file_obj.open_file(
                                            desktop_files + self.folder.files_inside, windows, taskbar)
                                        for f in self.folder.files_inside:
                                            f.selected = False
                                    else:
                                        file_obj.selected = True
                                        for f in self.folder.files_inside:
                                            if f != file_obj:
                                                f.selected = False
                                        file_obj.dragging = True
                                        dragging_file = file_obj  # Set dragging_file when dragging from folder
                                    file_obj.last_click_time = current_time
                                    break
                            else:
                                for file_obj in self.folder.files_inside:
                                    file_obj.selected = False

                else:
                    self.text_input = False
                    if self.settings_app:
                        pass
                    if self.browser_app:
                        self.browser_app.text_input_active = False
                    if self.calculator_app:
                        pass

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                self.resizing = False
                if self.text_input and self.selection_start is not None and self.selection_start == self.selection_end:
                    self.selection_start = None
                if self.folder:
                    if dragging_file:
                        if self.rect.collidepoint(event.pos):
                            # Check if not already in folder and not moving within the same folder
                            if dragging_file not in self.folder.files_inside and dragging_file.parent_folder != self.folder:
                                # Prevent moving folder into itself or its descendants
                                if isinstance(dragging_file, Folder) and is_descendant(dragging_file, self.folder):
                                    # Optional: Add visual feedback here
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

                        # Dragging out of folder
                        elif dragging_file.parent_folder == self.folder and not self.rect.collidepoint(event.pos):
                            if dragging_file in self.folder.files_inside:
                                self.folder.files_inside.remove(dragging_file)
                                desktop_files.append(dragging_file)
                                dragging_file.parent_folder = None
                                dragging_file.dragging = False
                                dragging_file.selected = False
                                dragging_file.rect.topleft = event.pos
                                dragging_file.name_rect.center = (
                                    dragging_file.rect.centerx, dragging_file.rect.bottom + 20)
                                dragging_file.update_selection_rect()
                        # Ensure dragging is set to false even if drop is invalid
                        dragging_file.dragging = False
                        dragging_file = None
                        dragged_files = []  # Clear dragged files on mouse up

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
                # Content rect starts below title bar
                self.rect.y = self.title_bar.y + self.title_bar_height

                self.title_rect.center = self.title_bar.center
                self.close_button_rect.x = self.title_bar.x + \
                    self.title_bar.width - self.close_button_size - 10
                self.close_button_rect.y = self.title_bar.y + 15
                self.minimize_button_rect.x = self.title_bar.x + \
                    self.title_bar.width - 2 * (self.minimize_button_size + 10)
                self.minimize_button_rect.y = self.title_bar.y + 15
                self.maximize_button_rect.x = self.title_bar.x + \
                    self.title_bar.width - 3 * (self.maximize_button_size + 10)
                self.maximize_button_rect.y = self.title_bar.y + 15

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
                self.title_rect.center = self.title_bar.center
                self.close_button_rect.x = self.title_bar.x + \
                    self.title_bar.width - self.close_button_size - 10
                self.close_button_rect.y = self.title_bar.y + 15
                self.minimize_button_rect.x = self.title_bar.x + \
                    self.title_bar.width - 2 * (self.minimize_button_size + 10)
                self.minimize_button_rect.y = self.title_bar.y + 15
                self.maximize_button_rect.x = self.title_bar.x + \
                    self.title_bar.width - 3 * (self.maximize_button_size + 10)
                self.maximize_button_rect.y = self.title_bar.y + 15

            if self.folder and dragging_file and dragging_file.dragging and dragging_file.parent_folder == self.folder:  # Dragging within folder
                relative_mouse_x = event.pos[0] - self.rect.x
                relative_mouse_y = event.pos[1] - self.rect.y
                dragging_file.rect.center = (
                    relative_mouse_x, relative_mouse_y)
                dragging_file.name_rect.center = (
                    dragging_file.rect.centerx, dragging_file.rect.bottom + 20)
                dragging_file.update_selection_rect()

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
                                                                     len(lines[clicked_line_index])) if lines[clicked_line_index] else file_font.size(" ")[0]
                    clicked_char_index = min(len(lines[clicked_line_index]), max(
                        0, int(click_pos_local_x // char_width)))

                    char_count = 0
                    for i in range(clicked_line_index):
                        char_count += len(lines[i]) + 1

                    self.selection_end = char_count + clicked_char_index

        elif event.type == pygame.KEYDOWN:
            if event.key not in [pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_CAPSLOCK, pygame.K_NUMLOCK]:
                self.held_key = event.key
                self.key_down_time = time.time()

            if self.file and self.file.name.endswith(".txt") and self.text_input:
                if event.key == pygame.K_LEFT:
                    self.cursor_pos = max(0, self.cursor_pos - 1)
                    self.selection_start = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[
                                                               pygame.K_RSHIFT]) and self.selection_start is not None else None
                    self.selection_end = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[
                                                             pygame.K_RSHIFT]) and self.selection_start is not None else None
                elif event.key == pygame.K_RIGHT:
                    self.cursor_pos = min(
                        len(self.file.content), self.cursor_pos + 1)
                    self.selection_start = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[
                                                               pygame.K_RSHIFT]) and self.selection_start is not None else None
                    self.selection_end = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[
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

                    self.selection_start = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[
                                                               pygame.K_RSHIFT]) and self.selection_start is not None else None
                    self.selection_end = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[
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

                    self.selection_start = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[
                                                               pygame.K_RSHIFT]) and self.selection_start is not None else None
                    self.selection_end = self.cursor_pos if (pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[
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
                            self.file.content[self.cursor_pos+1:]
                elif (event.key == pygame.K_c and (pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL])):
                    if self.selection_start is not None and self.selection_start != self.selection_end:
                        start_index = min(
                            self.selection_start, self.selection_end)
                        end_index = max(self.selection_start,
                                        self.selection_end)
                        self.clipboard = self.file.content[start_index:end_index]
                elif (event.key == pygame.K_v and (pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL])):
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
                elif event.unicode and file_font.render(self.file.content[:self.cursor_pos] + event.unicode, True, black).get_width() < self.rect.width - 20:
                    self.file.content = self.file.content[:self.cursor_pos] + \
                        event.unicode + self.file.content[self.cursor_pos:]
                    self.cursor_pos += 1
            elif self.browser_app and self.browser_app.text_input_active:
                self.browser_app.handle_event(event, self.rect)
            # Pass events to calculator app if active (you might need to add a way to activate calculator text input if needed)
            elif self.calculator_app:
                self.calculator_app.handle_event(event, self.rect)

            self.cursor_visible = True
            self.cursor_time = time.time()
        if self.mail_app:
            self.mail_app.handle_event(event, windows)

    def bring_to_front(self, windows):
        if self in windows:
            windows.remove(self)
            windows.append(self)


class DesktopFile:
    def __init__(self, name, image_path, x, y, protected=False, file_type="text", app_module=None, app_class=None, is_app=False, parent_folder=None):
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

        self.content = ""
        self.grid_spacing = 20
        self.icon_size = 108

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
            screen.blit(self.name_surface, self.name_rect)

    def update_name_surface(self):
        self.name_surface = file_font.render(
            self.name, True, text_color)

    def update_selection_rect(self):
        padding_x = self.rect.width * 0.10
        padding_y = self.rect.height * 0.10 + 15

        selection_width = int(self.rect.width + padding_x * 2)
        selection_height = int(self.rect.height + padding_y * 2)

        selection_x = int(self.rect.left - padding_x)
        selection_y = int(self.rect.top - padding_y)

        self.selection_rect = pygame.Rect(
            selection_x, selection_y, selection_width, selection_height)

    def get_grid_position(self, grid_size):
        grid_x = round(self.rect.x / grid_size) * grid_size
        grid_y = round(self.rect.y / grid_size) * grid_size
        return grid_x, grid_y

    def handle_event(self, event, files, windows, context_menu, trash, moving_file_to_front, taskbar, icon_layout_setting):
        global dragging_file, is_selecting, dragged_files
        if not self.is_in_trash:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.selection_rect.collidepoint(event.pos) and not is_selecting:
                        current_time = time.time()

                        # Open only on double click if selected
                        if current_time - self.last_click_time < self.double_click_interval and self.selected:
                            self.open_file(files, windows, taskbar)
                            for file in files:
                                file.selected = False
                        else:
                            # Check for Ctrl key for multi-select
                            if not (pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]):
                                for file in files:
                                    file.selected = False
                            self.selected = True
                            self.dragging = True
                            dragging_file = self

                            # Initialize dragged_files with all selected files
                            dragged_files = [f for f in files if f.selected]
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
                                # Only unselect if Ctrl is not pressed
                                if not (pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]):
                                    file.selected = False
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.dragging:
                        if trash.rect.colliderect(self.rect):
                            if self.protected:
                                # Error message for protected files
                                print("Error: Cannot delete protected system file.")
                            else:
                                for dragged_file in dragged_files:  # Move all dragged files to trash
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
                            for dragged_file in dragged_files:  # Grid align all dragged files
                                dragged_file.rect.topleft = dragged_file.get_grid_position(
                                    grid_size)
                                dragged_file.name_rect.center = (
                                    dragged_file.rect.centerx, dragged_file.rect.bottom + 20)
                                dragged_file.update_selection_rect()
                        dragging_file = None
                        dragged_files = []  # Clear dragged files after drop
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    for dragged_file in dragged_files:  # Move all dragged files together
                        dragged_file.rect.center = (event.pos[0] + (dragged_files[0].rect.centerx - self.rect.centerx), event.pos[1] + (
                            # Keep relative positions during drag
                            dragged_files[0].rect.centery - self.rect.centery))
                        dragged_file.name_rect.center = (
                            dragged_file.rect.centerx, dragged_file.rect.bottom + 20)
                        dragged_file.update_selection_rect()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                context_menu_options = ["Открыть",
                                        "Копировать", "Удалить", "Свойства"]
                context_menu = ContextMenu(
                    event.pos[0], event.pos[1], context_menu_options, self)

    def open_file(self, files, windows, taskbar):
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
        elif self.is_app and self.name == "Settings":
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
            settings_window = Window("Settings", settings_app_instance.width,
                                     settings_app_instance.height, new_x, new_y, settings_app=settings_app_instance)
            windows.append(settings_window)
            taskbar.add_icon(settings_window.taskbar_icon)
            settings_window.bring_to_front(windows)
        elif self.is_app and self.name == "Browser":
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
            browser_window = Window("Browser", browser_app_instance.width,
                                    browser_app_instance.height, new_x, new_y, browser_app=browser_app_instance)
            windows.append(browser_window)
            taskbar.add_icon(browser_window.taskbar_icon)
            browser_window.bring_to_front(windows)
        elif self.is_app and self.name == "Calculator":  # Open Calculator App
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
            calculator_window = Window("Calculator", calculator_app_instance.width,
                                       calculator_app_instance.height, new_x, new_y, calculator_app=calculator_app_instance)
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

    def show_properties(self):
        properties_text = f"Свойства файла: {self.name}\n"
        if self.file_type == 'folder':
            properties_text += "Тип: Папка\n"
            properties_text += f"Внутри файлов: {len(self.files_inside)}\n"
        elif self.file_type == 'text':
            properties_text += "Тип: Текстовый документ (.txt)\n"
            properties_text += f"Размер: {len(self.content)} символов\n"

        # Open properties in a window instead of print
        properties_window = PropertiesWindow(
            f"Свойства: {self.name}", 400, 300, 300, 300, properties_text=properties_text)
        # Assuming 'windows' list is accessible here. If not, you might need to pass it.
        windows.append(properties_window)
        taskbar.add_icon(properties_window.taskbar_icon)
        properties_window.bring_to_front(windows)


class Folder(DesktopFile):
    def __init__(self, name, x, y, parent_folder=None):
        super().__init__(name, "folder.png", x, y, file_type="folder",
                         parent_folder=parent_folder)
        self.files_inside = []

    def handle_event(self, event, files, windows, context_menu, trash, moving_file_to_front, taskbar, icon_layout_setting):
        super().handle_event(event, files, windows, context_menu,
                             trash, moving_file_to_front, taskbar, icon_layout_setting)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            context_menu_options = ["Открыть",
                                    # Added create options for folder context
                                    "Переименовать", "Удалить", "Свойства", "Создать .txt", "Создать папку"]
            context_menu = ContextMenu(
                event.pos[0], event.pos[1], context_menu_options, self)


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
        if self.selected:
            screen.blit(self.selection_surface, self.selection_rect)

    def handle_event(self, event, files):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.selection_rect.collidepoint(event.pos):
                    self.selected = True
                    for file in files:
                        file.selected = False
                else:
                    self.selected = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                context_menu_options = [
                    "Очистить корзину"]
                context_menu = ContextMenu(
                    event.pos[0], event.pos[1], context_menu_options, None, on_desktop=True)


class PuskMenu:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 200, 300)
        self.is_open = False
        self.options = ["Программы", "Настройки", "Выход"]
        self.option_surfaces = [taskbar_font.render(
            option, True, text_color) for option in self.options]
        self.option_rects = []
        option_y_offset = 30

        for surface in self.option_surfaces:
            rect = surface.get_rect(
                topleft=(self.rect.x + 20, self.rect.y + option_y_offset))
            self.option_rects.append(rect)
            option_y_offset += 40

    def draw(self, screen):
        if self.is_open:
            draw_rect(screen, window_color, self.rect)
            draw_rect(screen, light_gray, self.rect, 2)

            option_y_offset = 30
            for i, option_surface in enumerate(self.option_surfaces):
                rect = option_surface.get_rect(
                    topleft=(self.rect.x + 20, self.rect.y + option_y_offset))
                if self.options[i] == "Настройки":
                    if rect.collidepoint(pygame.mouse.get_pos()):
                        draw_rect(screen, light_blue_grey, rect)
                screen.blit(option_surface, rect)
                option_y_offset += 40

    def handle_event(self, event, files, windows, taskbar):
        if not self.is_open:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                self.is_open = False
                return True

            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    option = self.options[i]
                    if option == "Выход":
                        pygame.quit()
                        sys.exit()
                    elif option == "Настройки":
                        settings_file = None
                        for f in files:
                            if f.name == "Settings" and f.is_app:
                                settings_file = f
                                break
                        if settings_file:
                            settings_file.open_file(files, windows, taskbar)
                    elif option == "Программы":
                        browser_file = None
                        for f in files:
                            if f.name == "Browser" and f.is_app:
                                browser_file = f
                                break
                        if browser_file:
                            browser_file.open_file(files, windows, taskbar)
                    self.is_open = False
                    return True

        return False


class ContextMenu:
    # Added folder_window parameter
    def __init__(self, x, y, options, file=None, on_desktop=False, folder_window=None):
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
            width = text_surface.get_width() + 20
            if width > max_width:
                max_width = width
        self.width = max_width if max_width > 150 else 150

        self.height = len(options) * self.item_height
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.selected_option = -1
        self.is_open = True
        self.file_name_input = ""
        self.is_typing = False  # Input field visibility control
        self.selected_option_index_for_input = None  # Track option needing input
        self.creation_requested = False
        self.mouse_x, self.mouse_y = 0, 0
        self.selected_file = file
        self.create_txt_button_visible = "Создать .txt" in options
        self.create_folder_button_visible = "Создать папку" in options
        self.input_rect_width = 200
        self.input_rect_height = 30
        self.input_font = context_menu_font
        self.on_desktop_menu = on_desktop
        self.folder_window = folder_window  # Store folder window reference

    def draw(self, screen):
        if self.is_open:
            light_gray = (150, 150, 150)
            black = (0, 0, 0)
            white = (255, 255, 255)

            draw_rect(screen, window_color, self.rect)
            draw_rect(screen, black, self.rect, 1)

            for i, option_surface in enumerate(self.option_surfaces):
                text_rect = option_surface.get_rect(
                    topleft=(self.x + 10, self.y + i * self.item_height + 5))

                if i == self.selected_option:
                    draw_rect(screen, light_gray, (self.x, self.y +
                                                   i * self.item_height, self.width, self.item_height))

                screen.blit(option_surface, text_rect)

            if self.is_typing and self.selected_option_index_for_input is not None:  # Conditionally draw input
                option_rect = pygame.Rect(
                    self.x, self.y + self.selected_option_index_for_input * self.item_height, self.width, self.item_height)
                input_rect = pygame.Rect(
                    # Position to the right
                    option_rect.right + 5, option_rect.top, self.input_rect_width, self.input_rect_height)
                input_rect.centery = option_rect.centery  # Vertically align with the option
                draw_rect(screen, window_color, input_rect)
                draw_rect(screen, black, input_rect, 1)
                draw_text(screen, self.file_name_input, self.input_font,
                          text_color, (input_rect.x + 5, input_rect.y + 5), 'topleft')

    # Added desktop_files parameter
    def handle_event(self, event, files, windows, taskbar, desktop_files):
        if not self.is_open:
            return

        if event.type == pygame.MOUSEMOTION:
            self.selected_option = -1
            for i in range(len(self.options)):
                option_rect = pygame.Rect(
                    self.x, self.y + i * self.item_height, self.width, self.item_height)
                if option_rect.collidepoint(event.pos):
                    self.selected_option = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.selected_option != -1:
                    option = self.options[self.selected_option]
                    if option == "Создать .txt" and self.create_txt_button_visible:
                        self.is_typing = True  # Enable input
                        self.selected_option_index_for_input = self.selected_option  # Track for drawing input
                        self.file_name_input = ""
                        self.creation_requested = True
                        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
                        self.create_txt_button_visible = False
                        self.create_folder_button_visible = False
                    elif option == "Создать папку" and self.create_folder_button_visible:
                        self.is_typing = True  # Enable input
                        self.selected_option_index_for_input = self.selected_option  # Track for drawing input
                        self.file_name_input = ""
                        self.creation_requested = True
                        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
                        self.create_txt_button_visible = False
                        self.create_folder_button_visible = False
                    elif option == "Переименовать":
                        self.is_typing = True  # Enable input
                        self.selected_option_index_for_input = self.selected_option  # Track for drawing input
                        self.file_name_input = self.selected_file.name.replace(
                            ".txt", "").replace("/", "")
                        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
                    elif option == "Удалить":
                        if self.selected_file.protected:
                            # Error message for protected files
                            print("Error: Cannot delete protected system file.")
                        else:
                            if self.selected_file.file_type == "folder":
                                files_to_remove = [self.selected_file]
                                files_to_remove.extend(
                                    self.selected_file.files_inside)
                                for file_to_remove in files_to_remove:
                                    if file_to_remove in files:
                                        files.remove(file_to_remove)
                                    if file_to_remove.parent_folder and file_to_remove in file_to_remove.parent_folder.files_inside:
                                        file_to_remove.parent_folder.files_inside.remove(
                                            file_to_remove)
                            elif self.selected_file in files:
                                files.remove(self.selected_file)
                            self.close()  # Close context menu
                    elif option == "Открыть":
                        if self.selected_file:
                            self.selected_file.open_file(
                                files, windows, taskbar)
                            self.close()  # Close context menu
                    elif option == "Свойства":
                        if self.selected_file:
                            self.selected_file.show_properties()
                            self.close()  # Close context menu
                    elif option == "Копировать":
                        print("Функция 'Копировать' еще не реализована.")
                        self.close()  # Close context menu
                    elif option == "Очистить корзину":
                        files_to_remove = [f for f in files if f.is_in_trash]
                        for file_to_remove in files_to_remove:
                            files.remove(file_to_remove)
                        self.close()  # Close context menu
                    elif option == "Обновить":
                        refresh_settings_from_db(
                            files, windows)  # Pass windows here
                        self.close()  # Close context menu
                    elif option == "Вернуть на рабочий стол":  # Handle "Return to Desktop"
                        if self.selected_file and self.selected_file.parent_folder:
                            folder = self.selected_file.parent_folder
                            if self.selected_file in folder.files_inside:
                                folder.files_inside.remove(self.selected_file)
                                # Add to desktop files
                                desktop_files.append(self.selected_file)
                                self.selected_file.parent_folder = None
                                # Place on desktop roughly where clicked
                                self.selected_file.rect.topleft = (
                                    self.mouse_x, self.mouse_y)
                                self.selected_file.name_rect.center = (
                                    self.selected_file.rect.centerx, self.selected_file.rect.bottom + 20)
                                self.selected_file.update_selection_rect()
                        self.close()  # Close context menu
                    elif option == "Сортировать по":
                        # Implement submenu for sorting options if needed, for now just refresh
                        refresh_settings_from_db(files, windows)
                        self.close()

                    else:
                        self.close()  # Close context menu
                        self.selected_option = -1
        elif event.type == pygame.KEYDOWN:
            if self.is_typing:
                if event.key == pygame.K_RETURN:
                    if self.creation_requested:
                        if "Создать .txt" in self.options and self.selected_option == 0:
                            new_file_name = self.file_name_input + ".txt"
                            new_file = DesktopFile(
                                new_file_name, "txtfile.png", self.mouse_x, self.mouse_y)
                            if self.folder_window and self.folder_window.folder:  # if context menu is in folder
                                self.folder_window.folder.files_inside.append(
                                    new_file)  # add to folder content
                                new_file.parent_folder = self.folder_window.folder  # set parent folder
                            else:
                                # Otherwise add to desktop
                                files.append(new_file)
                            new_file.content = ""

                        elif "Создать папку" in self.options and self.selected_option == 1:
                            new_folder_name = self.file_name_input
                            new_folder = Folder(
                                new_folder_name, self.mouse_x, self.mouse_y)
                            if self.folder_window and self.folder_window.folder:  # if context menu is in folder
                                self.folder_window.folder.files_inside.append(
                                    new_folder)  # add to folder content
                                new_folder.parent_folder = self.folder_window.folder  # set parent folder
                            else:
                                # Otherwise add to desktop
                                files.append(new_folder)

                        self.close()  # Close context menu after creation
                    else:  # Rename action
                        new_file_name = self.file_name_input + \
                            (".txt" if self.selected_file.name.endswith(".txt") else "")
                        self.selected_file.name = new_file_name
                        self.close()  # Close context menu after rename

                elif event.key == pygame.K_BACKSPACE:
                    self.file_name_input = self.file_name_input[:-1]
                elif event.unicode:
                    valid_char = event.unicode.isalnum(
                    ) or event.unicode == ' ' or event.unicode == '.'
                    if valid_char and self.input_font.render(self.file_name_input + event.unicode, True, black).get_width() <= self.input_rect_width - 10:
                        self.file_name_input += event.unicode

    def close(self):
        self.is_open = False
        self.is_typing = False  # Disable input when closing
        self.selected_option_index_for_input = None  # Reset input tracking
        self.creation_requested = False
        self.create_txt_button_visible = True
        self.create_folder_button_visible = True


class PuskButton:
    def __init__(self, x, y, image_path, pusk_menu):
        self.image_path = image_path
        try:
            self.original_image = pygame.image.load(
                os.path.join("images", self.image_path)).convert_alpha()
            self.image = self.original_image
        except pygame.error as e:
            self.original_image = pygame.Surface((60, 60))
            self.original_image.fill(light_gray)
            self.image = self.original_image

        self.rect = self.image.get_rect(topleft=(x, y))
        self.pusk_menu = pusk_menu

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pusk_menu.is_open = not self.pusk_menu.is_open


class Taskbar:
    def __init__(self, height):
        self.rect = pygame.Rect(
            0, screen_height - height, screen_width, height)
        self.icons = []
        self.icon_width = 60
        self.icon_height = 40
        self.icon_margin = 10
        self.pusk_menu = PuskMenu(10, screen_height - 300 - height)
        self.pusk_button_x = 10
        self.pusk_button_y = screen_height - height + (height - 60) // 2
        self.pusk_button = PuskButton(
            self.pusk_button_x, self.pusk_button_y, "pusk.png", self.pusk_menu)

    def add_icon(self, icon):
        self.icons.append(icon)

    def remove_icon(self, icon):
        if icon in self.icons:
            self.icons.remove(icon)

    def draw(self, screen):
        draw_rect(screen, taskbar_color, self.rect)
        self.pusk_button.draw(screen)
        self.pusk_menu.draw(screen)
        icon_x = self.pusk_button_x + self.pusk_button.rect.width + self.icon_margin

        for icon in self.icons:
            icon.draw(screen, icon_x, self.rect.y +
                      (self.rect.height - self.icon_height) // 2)
            icon_x += self.icon_width + self.icon_margin

    def handle_event(self, event, windows, files, taskbar):
        if self.pusk_menu.handle_event(event, files, windows, taskbar):
            return

        self.pusk_button.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            icon_x = self.pusk_button_x + self.pusk_button.rect.width + self.icon_margin
            for icon in self.icons:
                icon_rect = pygame.Rect(icon_x, self.rect.y + (
                    self.rect.height - self.icon_height) // 2, self.icon_width, self.icon_height)
                if icon_rect.collidepoint(event.pos):
                    if icon.window.window_state == "minimized":
                        icon.window.window_state = "normal"
                    elif windows and windows[-1] == icon.window:  # Is front window
                        icon.window.window_state = "minimized"
                    else:
                        icon.window.bring_to_front(windows)
                    break
                icon_x += self.icon_width + self.icon_margin


class TaskbarIcon:
    def __init__(self, window, image_path):
        self.window = window
        self.width = 60
        self.height = 40
        self.image_path = image_path
        self.image = None
        if self.image_path:
            try:
                original_image = pygame.image.load(os.path.join(
                    "images", self.image_path)).convert_alpha()
                image_ratio = original_image.get_width() / original_image.get_height()

                if image_ratio > 1:
                    scaled_width = self.width
                    scaled_height = int(self.width / image_ratio)
                else:
                    scaled_height = self.height
                    scaled_width = int(self.height * image_ratio)

                self.image = pygame.transform.scale(
                    original_image, (scaled_width, scaled_height))
            except pygame.error as e:
                self.image = None

    def draw(self, screen, x, y):
        icon_rect = pygame.Rect(x, y, self.width, self.height)
        if self.image:
            image_x = x + (self.width - self.image.get_width()) // 2
            image_y = y + (self.height - self.image.get_height()) // 2
            screen.blit(self.image, (image_x, image_y))
        else:
            draw_text(screen, "Error", taskbar_font,
                      black, icon_rect.center, 'center')


class PropertiesWindow(Window):  # Properties Window class
    def __init__(self, title, width, height, x, y, properties_text):
        super().__init__(title, width, height, x, y, properties_text=properties_text)


# --- Desktop Widgets ---
widgets = []
widgets.append(ClockWidget(10, 10))  # Top left corner
widgets.append(CalendarWidget(220, 10))  # Next to clock

files = []


files.append(DesktopFile(
    name="Settings",
    image_path="settings_icon.png",
    x=10, y=150,
    is_app=True,
    protected=True  # Mark Settings as protected
))

files.append(DesktopFile(
    name="Browser",
    image_path="browser_icon.png",
    x=10, y=250,
    is_app=True,
    protected=True  # Mark Browser as protected
))

files.append(DesktopFile(  # Calculator App Icon
    name="Calculator",
    image_path="calculator_icon.png",
    x=10, y=350,
    is_app=True
))

files.append(Folder(
    name="New Folder",
    x=200, y=100
))


trash = Trash(1800, 10)

windows = []
context_menu = None
running = True
selected_file = None
dragging_file = None
dragged_files = []  # List to store files being dragged together

key_repeat_interval = 0.05
key_repeat_timer = 0
held_keys = set()

taskbar_height = 60
taskbar = Taskbar(taskbar_height)

is_selecting = False
selection_start_pos = None
selection_end_pos = None


def move_file_to_front(file):
    if file in files:
        files.remove(file)
        files.append(file)


while running:
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
            if event.key == pygame.K_DELETE:  # Delete key shortcut
                files_to_delete = [f for f in files if f.selected]
                for file_to_delete in files_to_delete:
                    if file_to_delete.protected:
                        # Error message for protected files
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
                if window.text_input and window.file and window.file.name.endswith(".txt") and window.held_key == event.key:
                    window.held_key = None

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                selected_file = None
                for file in files:
                    if file.selection_rect.collidepoint(event.pos):
                        selected_file = file
                        break

                folder_window_instance = None  # To pass folder window reference to context menu
                for window in windows:
                    if window.folder and window.rect.collidepoint(event.pos):
                        folder_window_instance = window
                        break

                if selected_file and not selected_file.protected:
                    if selected_file.parent_folder:  # File inside folder
                        context_menu_options = [
                            # Added "Return to Desktop"
                            "Открыть", "Копировать", "Вернуть на рабочий стол", "Удалить", "Свойства"]
                    else:  # File on desktop
                        context_menu_options = [
                            # Added "Sort By"
                            "Открыть", "Копировать", "Переименовать", "Удалить", "Свойства", "Сортировать по"]
                        # TODO: Implement sort by submenu

                    context_menu = ContextMenu(
                        event.pos[0], event.pos[1], context_menu_options, selected_file, folder_window=folder_window_instance)
                elif not selected_file:
                    if folder_window_instance:  # Right click in folder window background
                        context_menu_options = ContextMenu(
                            # Create options for folder background
                            event.pos[0], event.pos[1], ["Создать .txt", "Создать папку", "Обновить"], on_desktop=False, folder_window=folder_window_instance)
                    else:  # Right click on desktop background
                        context_menu_options = ContextMenu(
                            event.pos[0], event.pos[1], ["Создать .txt", "Создать папку", "Обновить"], on_desktop=True, folder_window=folder_window_instance)
                elif trash.selection_rect.collidepoint(event.pos):
                    context_menu_options = ContextMenu(
                        event.pos[0], event.pos[1], ["Очистить корзину"], on_desktop=True, folder_window=folder_window_instance)
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
                        # Only unselect if Ctrl is not pressed for box selection
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

        elif event.type == pygame.MOUSEMOTION:
            if is_selecting:
                selection_end_pos = event.pos

        for window in windows:
            window.handle_event(event, windows, taskbar,
                                files, icon_layout_setting)
            if event.type == pygame.MOUSEBUTTONDOWN and window.is_open and window.title_bar.collidepoint(event.pos):
                window.bring_to_front(windows)
                break

        if not (context_menu and context_menu.is_open):
            for file in files:
                file.handle_event(event, files, windows,
                                  context_menu, trash, move_file_to_front, taskbar, icon_layout_setting)

        trash.handle_event(event, files)
        if context_menu is not None and context_menu.is_open:
            # Pass desktop_files to context menu for "Return to Desktop"
            context_menu.handle_event(event, files, windows, taskbar, files)
        taskbar.handle_event(event, windows, files, taskbar)

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
                for y in range(0, screen_height-taskbar_height, grid_size):
                    draw_rect(screen, light_gray, (x, y, 1, 1))

        if is_selecting and selection_start_pos and selection_end_pos:
            selection_rect_draw = pygame.Rect(selection_start_pos, (
                selection_end_pos[0] - selection_start_pos[0], selection_end_pos[1] - selection_start_pos[1]))
            selection_rect_draw.normalize()
            draw_rect(screen, selection_color, selection_rect_draw)

        # Draw Widgets
        for widget in widgets:
            widget.draw(screen)
            widget.update()  # Update widgets (e.g., clock time)

        for file in files:
            if file.dragging == False and file.parent_folder is None:  # Only draw desktop files here
                file.draw(screen)
        for window in windows:
            if window.folder:  # Draw folder content files inside their windows
                window.draw_folder_content(screen.subsurface(
                    window.rect), window.folder.files_inside)

        for file in files:
            if file.dragging == True:
                file.draw(screen)

        for window in windows:
            window.draw(screen)

        if context_menu is not None and context_menu.is_open:
            context_menu.draw(screen)

        windows = [window for window in windows if window.is_open]
        taskbar.icons = [icon for icon in taskbar.icons if icon.window.is_open]

    if time.time() - last_settings_refresh_time >= settings_refresh_interval:
        # Pass windows here to refresh function
        refresh_settings_from_db(files, windows)
        last_settings_refresh_time = time.time()

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
