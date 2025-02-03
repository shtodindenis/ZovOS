import os
import sqlite3
import sys
import time
import calendar
from datetime import datetime, timedelta

import pygame

from apvia import ApviaApp
from browser import BrowserApp
from ZOffice import ZTextApp, ZDBApp, ZTableApp
from IZ import InfZovApp

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
    startup_sound = pygame.mixer.Sound(os.path.join("Sounds", "startup_sound.mp3"))
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
                os.path.join("images", filename)).convert()
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
    conn.commit()
    conn.close()
def is_descendant(folder_to_check, potential_parent):
    """
    Checks if 'folder_to_check' is a descendant of 'potential_parent'.
    This prevents moving a folder into itself or its subfolders.

    Args:
        folder_to_check (Folder): The folder to check if it is a descendant.
        potential_parent (Folder): The potential parent folder.

    Returns:
        bool: True if 'folder_to_check' is a descendant of 'potential_parent', False otherwise.
    """
    if potential_parent is None:
        return False
    if folder_to_check == potential_parent:
        return True
    for file_inside in potential_parent.files_inside:
        if file_inside == folder_to_check:
            return True
        if isinstance(file_inside, Folder):
            if is_descendant(file_inside, file_inside):  # Corrected recursive call
                return True
    return False

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
        taskbar_color = dark_gray
    else:
        window_color = light_theme_window_color
        text_color = light_theme_text_color
        taskbar_color = white


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
    taskbar.update_color()

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
        elif isinstance(widget, CalendarWidget):
            widget.visible = show_calendar_widget_setting == 'true'

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

        self.widget_options_rects = {}
        self.show_clock = get_setting('show_clock_widget', 'true') == 'true'
        self.show_calendar = get_setting('show_calendar_widget', 'true') == 'true'

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
        self.current_taskbar_icon_size = int(get_setting('taskbar_icon_size', '40'))

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
        clock_checkbox_rect = pygame.Rect(start_x + checkbox_margin_x, current_y, self.checkbox_size, self.checkbox_size)
        draw_rect(screen_surface, window_color, clock_checkbox_rect)
        draw_rect(screen_surface, black, clock_checkbox_rect, 1)
        if self.show_clock:
            pygame.draw.line(screen_surface, black, clock_checkbox_rect.topleft, clock_checkbox_rect.bottomright, 3)
            pygame.draw.line(screen_surface, black, clock_checkbox_rect.topright, clock_checkbox_rect.bottomleft, 3)
        self.clock_checkbox_rect = clock_checkbox_rect
        current_y += clock_label_rect.height + 5

        calendar_label_rect = draw_text(screen_surface, "Календарь", settings_font,
                  text_color, (start_x + checkbox_margin_x + self.checkbox_size + 5, current_y), 'topleft')
        calendar_checkbox_rect = pygame.Rect(start_x + checkbox_margin_x, current_y, self.checkbox_size, self.checkbox_size)
        draw_rect(screen_surface, window_color, calendar_checkbox_rect)
        draw_rect(screen_surface, black, calendar_checkbox_rect, 1)
        if self.show_calendar:
            pygame.draw.line(screen_surface, black, calendar_checkbox_rect.topleft, calendar_checkbox_rect.bottomright, 3)
            pygame.draw.line(screen_surface, black, calendar_checkbox_rect.topright, calendar_checkbox_rect.bottomleft, 3)
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
        taskbar_size_slider_rect = pygame.Rect(start_x + taskbar_size_label_rect.width + 10, current_y + slider_y_offset + slider_height // 2 - slider_height // 2, 150, slider_height)
        draw_rect(screen_surface, light_gray, taskbar_size_slider_rect)
        slider_handle_pos_x = taskbar_size_slider_rect.left + (taskbar_size_slider_rect.width - slider_handle_size) * (self.current_taskbar_height - self.min_taskbar_height) / (self.max_taskbar_height - self.min_taskbar_height)
        slider_handle_rect = pygame.Rect(slider_handle_pos_x, taskbar_size_slider_rect.centery - slider_handle_size // 2, slider_handle_size, slider_handle_size)
        draw_rect(screen_surface, dark_gray, slider_handle_rect, border_radius=5)
        self.taskbar_size_slider_rect = taskbar_size_slider_rect
        self.slider_handle_rect = slider_handle_rect
        current_y += max(taskbar_size_label_rect.height, slider_handle_size) + slider_margin_y

        taskbar_icon_size_label_rect = draw_text(screen_surface, "Размер значков:", settings_font,
                  text_color, (start_x, current_y + slider_y_offset), 'topleft')
        taskbar_icon_size_slider_rect = pygame.Rect(start_x + taskbar_icon_size_label_rect.width + 10, current_y + slider_y_offset + slider_height // 2 - slider_height // 2, 150, slider_height)
        draw_rect(screen_surface, light_gray, taskbar_icon_size_slider_rect)
        icon_slider_handle_pos_x = taskbar_icon_size_slider_rect.left + (taskbar_icon_size_slider_rect.width - slider_handle_size) * (self.current_taskbar_icon_size - self.min_icon_size) / (self.max_icon_size - self.min_icon_size)
        icon_slider_handle_rect = pygame.Rect(icon_slider_handle_pos_x, taskbar_icon_size_slider_rect.centery - slider_handle_size // 2, slider_handle_size, slider_handle_size)
        draw_rect(screen_surface, dark_gray, icon_slider_handle_rect, border_radius=5)

        self.taskbar_icon_size_slider_rect = taskbar_icon_size_slider_rect
        self.icon_slider_handle_rect = icon_slider_handle_rect

        # Removed "To apply changes restart OS" text

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

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging_slider and self.taskbar_size_slider_rect:
                slider_x = relative_mouse_pos[0] - self.slider_handle_rect.width // 2
                slider_x = max(self.taskbar_size_slider_rect.left, min(slider_x, self.taskbar_size_slider_rect.right - self.slider_handle_rect.width))
                self.slider_handle_rect.x = slider_x
                slider_pos_ratio = (self.slider_handle_rect.centerx - self.taskbar_size_slider_rect.left) / self.taskbar_size_slider_rect.width
                self.current_taskbar_height = int(self.min_taskbar_height + (self.max_taskbar_height - self.min_taskbar_height) * slider_pos_ratio)
                self.current_taskbar_height = max(self.min_taskbar_height, min(self.max_taskbar_height, self.current_taskbar_height))
                update_setting('taskbar_height', str(self.current_taskbar_height))
                return 'taskbar_size_change'

            elif self.is_dragging_icon_slider and self.taskbar_icon_size_slider_rect:
                slider_x = relative_mouse_pos[0] - self.icon_slider_handle_rect.width // 2
                slider_x = max(self.taskbar_icon_size_slider_rect.left, min(slider_x, self.taskbar_icon_size_slider_rect.right - self.icon_slider_handle_rect.width))
                self.icon_slider_handle_rect.x = slider_x
                slider_pos_ratio = (self.icon_slider_handle_rect.centerx - self.taskbar_icon_size_slider_rect.left) / self.taskbar_icon_size_slider_rect.width
                self.current_taskbar_icon_size = int(self.min_icon_size + (self.max_icon_size - self.min_icon_size) * slider_pos_ratio)
                self.current_taskbar_icon_size = max(self.min_icon_size, min(self.max_icon_size, self.current_taskbar_icon_size))
                update_setting('taskbar_icon_size', str(self.current_taskbar_icon_size))
                return 'taskbar_icon_size_change'


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

        if self.clock_checkbox_rect and self.clock_checkbox_rect.collidepoint(relative_mouse_pos):
            self.show_clock = not self.show_clock
            update_setting('show_clock_widget', 'true' if self.show_clock else 'false')
            return 'widget_change'
        elif self.calendar_checkbox_rect and self.calendar_checkbox_rect.collidepoint(relative_mouse_pos):
            self.show_calendar = not self.show_calendar
            update_setting('show_calendar_widget', 'true' if self.show_calendar else 'false')
            return 'widget_change'

        return None


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
        draw_rect(screen_surface, window_color, display_rect)
        draw_rect(screen_surface, black, display_rect, 1)
        draw_text(screen_surface, self.display_text, self.font, text_color,
                  (display_rect.right - 10, display_rect.centery), 'midright')

        for row_rects in self.button_rects:
            for rect_button in row_rects:
                rect = rect_button[0]
                button_text = rect_button[1]
                button_color = light_gray if button_text.isdigit(
                ) or button_text == '.' else dark_gray
                draw_rect(screen_surface, button_color, rect)
                draw_rect(screen_surface, black, rect, 1)
                text_color_button = text_color if button_text != "C" else red
                draw_text(screen_surface, button_text, self.font,
                          text_color_button, rect.center, 'center')

    def handle_event(self, event, window_rect):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            relative_mouse_pos = (
                event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
            for row_rects in self.button_rects:
                for rect_button in row_rects:
                    rect = rect_button[0]
                    button_text = rect_button[1]
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
        calculation_str = ""
        for item in self.calculation_stack:
            calculation_str += str(item)
        try:
            return eval(calculation_str)
        except (TypeError, ValueError, SyntaxError, ZeroDivisionError):
            raise Exception("Calculation Error")


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

calendar_background_color = pygame.Color("#F0F0F0") # Light gray background
calendar_border_color = black
month_header_color = text_color
day_name_color = pygame.Color("#707070") # Slightly darker day names
day_number_color = text_color
weekend_day_color = pygame.Color("#FFD700") # Gold for weekends
current_day_color = pygame.Color("#00BFFF") # Deep Sky Blue for current day
button_color = window_color
button_hover_color = pygame.Color("#E0E0E0") # Lighter gray on hover
button_arrow_color = text_color
day_rect_color = calendar_background_color
day_rect_border_color = black
tooltip_font = pygame.font.Font(None, 24)

class CalendarApp:
    def __init__(self):
        self.width = 450  # Увеличена ширина на 50px
        self.height = 400 # Increased height to accommodate redesign and tooltip
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.font = widget_font
        self.date_color = text_color
        self.current_date = datetime.now()
        self.calendar_surface = None
        self.animating = False
        self.animation_direction = 1
        self.animation_start_time = 0
        self.animation_duration = 0.15  # Reduced animation duration for smoother transition
        self.next_calendar_surface = None
        self.animation_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA) # Surface for animation

        self.month_backward_rect = None
        self.month_forward_rect = None
        self.year_backward_rect = None
        self.year_forward_rect = None
        self.day_rects = [] # Store day rects for alignment
        self.hovered_day_rect = None # To track hovered day for visual feedback
        self.selected_day = None # Track selected day
        self.hovered_day_number = None # Track day number when hovered for tooltip

        self._render_calendar()


    def _render_calendar(self):
        self.calendar_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.calendar_surface.fill((0, 0, 0, 0))

        # Month and Year Header
        month_text = self.current_date.strftime("%B %Y").upper() # Uppercase for header
        month_surface = self.font.render(month_text, True, month_header_color) # Use header color
        month_rect = month_surface.get_rect(center=(self.width // 2, 30))
        self.calendar_surface.blit(month_surface, month_rect)

        # Day Names
        day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        day_name_x_start = 40 # Adjusted start position for day names
        day_name_y = 60
        day_name_spacing = (self.width - 2 * day_name_x_start) / 6
        for day_name in day_names:
            day_name_surface = settings_font.render(day_name, True, day_name_color) # Use day name color
            day_name_rect = day_name_surface.get_rect(center=(day_name_x_start, day_name_y))
            self.calendar_surface.blit(day_name_surface, day_name_rect)
            day_name_x_start += day_name_spacing

        # Calendar Days Grid
        cal = calendar.Calendar()
        month_days = list(cal.monthdayscalendar(self.current_date.year, self.current_date.month)) # Исправлена ошибка здесь!
        day_rect_size = 36 # Slightly smaller day rects
        day_start_x = 40
        day_start_y = 80 # Adjusted day grid position
        day_x = day_start_x
        day_y = day_start_y
        day_count = 0
        self.day_rects = [] # Clear day rects for new render

        day_spacing_x = day_name_spacing
        day_spacing_y = 45 # Adjusted vertical spacing

        today = datetime.now().date()
        current_month_date = datetime(self.current_date.year, self.current_date.month, 1).date()

        for week in month_days: # Iterate through weeks
            for day in week: # Iterate through days in week
                if day != 0:
                    day_date = datetime(self.current_date.year, self.current_date.month, day).date()
                    day_rect = pygame.Rect(day_x - day_rect_size // 2, day_y, day_rect_size, day_rect_size)
                    draw_rect(self.calendar_surface, day_rect_color, day_rect, border_radius=6) # Rounded day rects
                    draw_rect(self.calendar_surface, day_rect_border_color, day_rect, 1, border_radius=6) # Border

                    day_color_to_use = day_number_color
                    if day_date.weekday() >= 5: # Weekend highlighting
                        day_color_to_use = weekend_day_color
                    if day_date == today and day_date.month == current_month_date.month and day_date.year == current_month_date.year: # Current day highlighting
                        draw_rect(self.calendar_surface, current_day_color, day_rect, border_radius=6) # Highlight current day
                        day_color_to_use = pygame.Color('white') # White text on highlighted day

                    if self.hovered_day_rect == day_rect: # Hover effect
                        draw_rect(self.calendar_surface, button_hover_color, day_rect, border_radius=6) # Highlight hovered day
                        day_color_to_use = text_color # Keep text visible on hover

                    if self.selected_day and self.selected_day.day == day and self.selected_day.month == self.current_date.month and self.selected_day.year == self.current_date.year: # Selected day highlighting
                        draw_rect(self.calendar_surface, pygame.Color('forestgreen'), day_rect, border_radius=6) # Highlight selected day
                        day_color_to_use = pygame.Color('white') # White text on highlighted day


                    day_surface = settings_font.render(str(day), True, day_color_to_use)
                    day_text_rect = day_surface.get_rect(center=day_rect.center)
                    self.calendar_surface.blit(day_surface, day_text_rect)
                    self.day_rects.append(day_rect)

                day_x += day_spacing_x
                day_count += 1
                if day_count % 7 == 0:
                    day_x = day_start_x
                    day_y += day_spacing_y

        # Navigation Buttons - Redesigned and repositioned
        button_size = 28 # Slightly larger buttons
        button_margin_horizontal = 20 # More horizontal margin
        button_margin_vertical = 15 # Vertical margin

        month_backward_rect = pygame.Rect(button_margin_horizontal, month_rect.centery - button_size // 2, button_size, button_size)
        draw_rect(self.calendar_surface, button_color, month_backward_rect, border_radius=6) # Rounded buttons
        draw_text(self.calendar_surface, "<", settings_font, button_arrow_color, month_backward_rect.center, 'center') # Arrow symbols
        self.month_backward_rect = month_backward_rect

        month_forward_rect = pygame.Rect(self.width - button_margin_horizontal - button_size, month_rect.centery - button_size // 2, button_size, button_size)
        draw_rect(self.calendar_surface, button_color, month_forward_rect, border_radius=6)
        draw_text(self.calendar_surface, ">", settings_font, button_arrow_color, month_forward_rect.center, 'center')
        self.month_forward_rect = month_forward_rect

        year_backward_rect = pygame.Rect(button_margin_horizontal, month_backward_rect.bottom + button_margin_vertical, button_size, button_size)
        draw_rect(self.calendar_surface, button_color, year_backward_rect, border_radius=6)
        draw_text(self.calendar_surface, "<<", settings_font, button_arrow_color, year_backward_rect.center, 'center')
        self.year_backward_rect = year_backward_rect

        year_forward_rect = pygame.Rect(self.width - button_margin_horizontal - button_size, month_forward_rect.bottom + button_margin_vertical, button_size, button_size)
        draw_rect(self.calendar_surface, button_color, year_forward_rect, border_radius=6)
        draw_text(self.calendar_surface, ">>", settings_font, button_arrow_color, year_forward_rect.center, 'center')
        self.year_forward_rect = year_forward_rect

        # Tooltip for hovered day
        if self.hovered_day_number:
            tooltip_text = datetime(self.current_date.year, self.current_date.month, self.hovered_day_number).strftime("%d %B %Y")
            tooltip_surface = tooltip_font.render(tooltip_text, True, text_color)
            tooltip_rect = tooltip_surface.get_rect(center=(self.width // 2, self.height - 20)) # Position tooltip at the bottom
            draw_rect(self.calendar_surface, button_color, tooltip_rect.inflate(10, 5), border_radius=5) # Background for tooltip
            self.calendar_surface.blit(tooltip_surface, tooltip_rect)


    def draw(self, screen_surface):
        draw_rect(screen_surface, calendar_background_color, self.rect, border_radius=10) # Rounded calendar container
        draw_rect(screen_surface, calendar_border_color, self.rect, 2, border_radius=10) # Thicker border for container

        if self.animating:
            elapsed_time = time.time() - self.animation_start_time
            progress = min(elapsed_time / self.animation_duration, 1)

            if self.next_calendar_surface:
                self.animation_surface.fill((0,0,0,0)) # Clear animation surface
                if self.animation_direction == 1: # Forward animation - slide in from right
                    next_x = int(self.rect.width * progress)
                    current_x = int(self.rect.width * (progress - 1)) # Start off screen to the left

                else: # Backward animation - slide in from left
                    next_x = int(self.rect.width * (progress - 1)) # Start off screen to the right
                    current_x = int(self.rect.width * progress)

                self.animation_surface.blit(self.calendar_surface, (current_x, 0))
                self.animation_surface.blit(self.next_calendar_surface, (next_x, 0))
                screen_surface.blit(self.animation_surface, (self.rect.x, self.rect.y)) # Blit animation surface with offset

            if progress == 1:
                self.animating = False
                self.calendar_surface = self.next_calendar_surface
                self.next_calendar_surface = None

        else:
            screen_surface.blit(self.calendar_surface, (self.rect.x, self.rect.y)) # Blit with offset


    def handle_event(self, event, window_rect):
        if self.animating:
            return

        if event.type == pygame.MOUSEMOTION: # Hover detection
            relative_mouse_pos = (event.pos[0] - window_rect.x - self.rect.x, event.pos[1] - window_rect.y - self.rect.y)
            self.hovered_day_rect = None # Reset hover
            self.hovered_day_number = None # Reset hovered day number
            if not self.animating: # Avoid hover effect during animation
                for day_index, day_rect in enumerate(self.day_rects):
                    if day_rect.collidepoint(relative_mouse_pos):
                        self.hovered_day_rect = day_rect
                        cal = calendar.Calendar()
                        month_days = list(cal.monthdayscalendar(self.current_date.year, self.current_date.month))
                        day_number = 0
                        day_count_in_month = 0
                        for week in month_days:
                            for d in week:
                                if d != 0:
                                    day_count_in_month += 1
                                if day_count_in_month -1 == day_index: # day_index is 0-based, day_count is 1-based
                                    day_number = d
                                    break
                            if day_number != 0:
                                break
                        if day_number != 0:
                            self.hovered_day_number = day_number
                        break
            self._render_calendar() # Re-render to update hover effect


        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            relative_mouse_pos = (
                event.pos[0] - window_rect.x - self.rect.x, event.pos[1] - window_rect.y - self.rect.y) # Adjusted mouse pos for calendar rect
            if self.month_backward_rect and self.month_backward_rect.collidepoint(relative_mouse_pos):
                self.current_date = self.current_date - timedelta(days=35)
                self._start_animation(-1)
            elif self.month_forward_rect and self.month_forward_rect.collidepoint(relative_mouse_pos):
                self.current_date = self.current_date + timedelta(days=35)
                self._start_animation(1)
            elif self.year_backward_rect and self.year_backward_rect.collidepoint(relative_mouse_pos):
                self.current_date = datetime(self.current_date.year - 1, self.current_date.month, 1)
                self._start_animation(-1)
            elif self.year_forward_rect and self.year_forward_rect.collidepoint(relative_mouse_pos):
                self.current_date = datetime(self.current_date.year + 1, self.current_date.month, 1)
                self._start_animation(1)
            else: # Day click detection
                for day_rect in self.day_rects:
                    if day_rect.collidepoint(relative_mouse_pos):
                        day_index = self.day_rects.index(day_rect)
                        cal = calendar.Calendar()
                        month_days = list(cal.monthdayscalendar(self.current_date.year, self.current_date.month))
                        day_number = 0
                        day_count_in_month = 0
                        for week in month_days:
                            for d in week:
                                if d != 0:
                                    day_count_in_month += 1
                                if day_count_in_month -1 == day_index: # day_index is 0-based, day_count is 1-based
                                    day_number = d
                                    break
                            if day_number != 0:
                                break

                        if day_number != 0:
                            self.selected_day = datetime(self.current_date.year, self.current_date.month, day_number) # Store selected date
                            print(f"Selected Date: {self.selected_day.strftime('%Y-%m-%d')}") # Example action - print selected date
                            self._render_calendar() # Re-render to show selection


    def _start_animation(self, direction):
        self.next_calendar_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.next_calendar_surface.fill((0, 0, 0, 0))
        temp_calendar_app = CalendarApp()
        temp_calendar_app.rect = self.rect.copy()
        temp_calendar_app.font = self.font
        temp_calendar_app.date_color = self.date_color
        temp_calendar_app.current_date = self.current_date
        temp_calendar_app.selected_day = self.selected_day # Keep selected day during animation
        temp_calendar_app._render_calendar()
        self.next_calendar_surface = temp_calendar_app.calendar_surface

        self.animating = True
        self.animation_direction = direction
        self.animation_start_time = time.time()


class TaskbarCalendar(CalendarApp):
    def __init__(self):
        super().__init__()
        self.width = 300 # Reduced width for taskbar calendar
        self.height = 280 # Reduced height
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.is_visible = False
        self.animation_duration = 0.15 # Reduced animation duration for taskbar calendar too


    def draw(self, screen_surface, taskbar_rect):
        if self.is_visible:
            self.rect.bottomright = (taskbar_rect.right - 10, taskbar_rect.top)
            super().draw(screen_surface) # Call superclass draw - no need to redraw background here, CalendarApp draw does it

    def handle_event(self, event, taskbar_rect):
        if self.is_visible:
            relative_mouse_pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
            if self.rect.collidepoint(event.pos):
                return super().handle_event(event, self.rect) # Pass self.rect as window_rect for TaskbarCalendar
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.rect.collidepoint(event.pos) and not taskbar_rect.collidepoint(event.pos):
                self.is_visible = False
                return True
        return False

    def toggle_visibility(self):
        self.is_visible = not self.is_visible


class Window:
    def __init__(self, title, width, height, x, y, file=None, settings_app=None, browser_app=None, calculator_app=None,
                 folder=None, apvia_app=None, properties_text=None, ztext_app=None, ztable_app=None, zdb_app=None, infzov_app=None, calendar_app=None):
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
        self.preview_surface = None  # For window preview
        self.calendar_app = calendar_app

    def update_title_surface(self):
        self.title_surface = window_font.render(
            self.title, True, text_color)
        self.title_rect = self.title_surface.get_rect(
            center=self.title_bar.center)

    def draw(self, screen):
        if self.is_open:
            draw_rect(screen, window_color, self.title_bar)
            screen.blit(self.title_surface, self.title_rect)

            draw_rect(screen, window_color, self.close_button_rect)
            screen.blit(self.close_cross_surface,
                        self.close_button_rect.topleft)

            draw_rect(screen, window_color, self.minimize_button_rect)
            screen.blit(self.minimize_line_surface,
                        self.minimize_button_rect.topleft)

            draw_rect(screen, light_gray, self.rect)
            draw_rect(screen, black, self.rect, 1)

            content_surface = screen.subsurface(self.rect).copy()
            content_surface.fill(light_gray)

            if self.file and self.file.name.endswith(".txt"):
                draw_rect(content_surface, window_color, content_surface.get_rect())
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
                        char_count = 0
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
                draw_rect(content_surface, window_color, content_surface.get_rect())
                self.settings_app.draw(content_surface)
            elif self.browser_app:
                draw_rect(content_surface, window_color, content_surface.get_rect())
                self.browser_app.width = self.width
                self.browser_app.height = self.height
                self.browser_app.draw(content_surface)
            elif self.calculator_app:
                draw_rect(content_surface, window_color, content_surface.get_rect())
                self.calculator_app.width = self.width
                self.calculator_app.height = self.height
                self.calculator_app.draw(content_surface)
            elif self.apvia_app:
                draw_rect(content_surface, window_color, content_surface.get_rect())
                self.apvia_app.width = self.width
                self.apvia_app.height = self.height
                self.apvia_app.draw(content_surface)
            elif self.infzov_app:
                draw_rect(content_surface, window_color, content_surface.get_rect())
                self.infzov_app.width = self.width
                self.infzov_app.height = self.height
                self.infzov_app.draw(content_surface, self.rect)
            elif self.folder:
                folder_surface = pygame.Surface(
                    content_surface.get_size(), pygame.SRCALPHA)
                folder_surface.fill(transparent_white)
                content_surface.blit(folder_surface, (0, 0))
                draw_rect(content_surface, window_color, content_surface.get_rect(), 0)
                self.draw_folder_content(content_surface, self.folder.files_inside)
            elif self.properties_text:
                draw_rect(content_surface, window_color, content_surface.get_rect())
                y_offset = 20
                lines = self.properties_text.strip().split('\n')
                for line in lines:
                    text_surface = settings_font.render(line, True, text_color)
                    text_rect = text_surface.get_rect(
                        topleft=(20, y_offset))
                    content_surface.blit(text_surface, text_rect)
                    y_offset += settings_font.get_height() + 5
            elif self.ztext_app:
                draw_rect(content_surface, window_color, content_surface.get_rect())
                self.ztext_app.width = self.width
                self.ztext_app.height = self.height
                self.ztext_app.draw(content_surface)
            elif self.ztable_app:
                draw_rect(content_surface, window_color, content_surface.get_rect())
                self.ztable_app.width = self.width
                self.ztable_app.height = self.height
                self.ztable_app.draw(content_surface)
            elif self.zdb_app:
                draw_rect(content_surface, window_color, content_surface.get_rect())
                self.zdb_app.width = self.width
                self.zdb_app.height = self.height
                self.zdb_app.draw(content_surface)
            elif self.calendar_app:
                draw_rect(content_surface, window_color, content_surface.get_rect())
                self.calendar_app.width = self.width
                self.calendar_app.height = self.height
                self.calendar_app.draw(content_surface)

            screen.blit(content_surface, self.rect)
            self.preview_surface = pygame.transform.scale(content_surface, (content_surface.get_width() // 3, content_surface.get_height() // 3))


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
                            event.pos, self.rect, event)
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
                                    desktop_files, windows, widgets, taskbar)
                            elif settings_result == 'theme_change':
                                refresh_settings_from_db(
                                    desktop_files, windows, widgets, taskbar)
                            elif settings_result == 'widget_change':
                                refresh_settings_from_db(
                                    desktop_files, windows, widgets, taskbar)
                            elif settings_result in ['taskbar_size_change', 'taskbar_icon_size_change']:
                                taskbar.update_size_and_color(int(get_setting('taskbar_height', '60')))
                                for win in windows:
                                    win.taskbar_icon.update_size(int(get_setting('taskbar_icon_size', '40')))

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
                            for file_obj in self.folder.files_inside:
                                if file_obj.selection_rect.collidepoint(
                                        (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)):
                                    current_time = time.time()
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
                                        dragging_file = file_obj

                                        dragging_file.drag_offsets = []
                                        initial_drag_pos = pygame.math.Vector2(dragging_file.rect.center)
                                        for df in dragged_files:
                                            offset = pygame.math.Vector2(df.rect.center) - initial_drag_pos
                                            dragging_file.drag_offsets.append((df, offset))

                                    file_obj.last_click_time = current_time
                                    break
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

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                self.resizing = False
                if self.text_input and self.selection_start is not None and self.selection_start == self.selection_end:
                    self.selection_start = None
                if self.folder:
                    if dragging_file:
                        drop_pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                        drop_rect = pygame.Rect(drop_pos, dragging_file.rect.size)
                        valid_drop_pos = True
                        for file_in_folder in self.folder.files_inside:
                            if file_in_folder != dragging_file and drop_rect.colliderect(file_in_folder.rect):
                                valid_drop_pos = False
                                break

                        if self.rect.collidepoint(event.pos) and valid_drop_pos:
                            if dragging_file not in self.folder.files_inside and dragging_file.parent_folder != self.folder:
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
                                    dragging_file.rect.topleft = drop_pos
                                    dragging_file.name_rect.center = (
                                        dragging_file.rect.centerx, dragging_file.rect.bottom + 20)
                                    dragging_file.update_selection_rect()

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
                        dragging_file.dragging = False
                        dragging_file = None
                        dragged_files = []
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

                self.title_rect.center = self.title_bar.center
                self.close_button_rect.x = self.title_bar.x + \
                                           self.title_bar.width - self.close_button_size - 10
                self.close_button_rect.y = self.title_bar.y + 15
                self.minimize_button_rect.x = self.title_bar.x + \
                                              self.title_bar.width - 2 * (self.minimize_button_size + 10)
                self.minimize_button_rect.y = self.title_bar.y + 15

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

            if self.folder and dragging_file and dragging_file.dragging and dragging_file.parent_folder == self.folder:
                relative_mouse_x = event.pos[0] - self.rect.x
                relative_mouse_y = event.pos[1] - self.rect.y
                dragging_file.rect.center = (
                    relative_mouse_x, relative_mouse_y)
                dragging_file.name_rect.center = (
                    dragging_file.rect.centerx, dragging_file.rect.bottom + 20)
                dragging_file.update_selection_rect()

                if hasattr(dragging_file, 'drag_offsets'):
                    current_drag_pos = pygame.math.Vector2(dragging_file.rect.center)
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
                    initial_drag_pos = pygame.math.Vector2(dragging_file.rect.center)
                    for df in dragged_files:
                        offset = pygame.math.Vector2(df.rect.center) - initial_drag_pos
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
                        self.file.content = self.file.content[:start_index] + self.file.content[end_index:]
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
                print('fimozik ne tyanul')
                if event.key == pygame.K_r and (self.apvia_app.game_over or self.apvia_app.game_won):
                    print('fimozik potyanul')
                    self.apvia_app.start_game()
                    self.apvia_app.money_earning = True
                    return "game_restarted"
                elif event.key == pygame.K_m and (self.apvia_app.game_over or self.apvia_app.game_won):
                    print('dima penis')
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

            self.cursor_visible = True
            self.cursor_time = time.time()
        if self.mail_app:
            self.mail_app.handle_event(event, windows)

    def bring_to_front(self, windows):
        if self in windows:
            windows.remove(self)
            windows.append(self)


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

                text_surface = file_font.render(self.rename_input, True, text_color)
                text_render_rect = text_surface.get_rect(center=input_rect.center)
                screen.blit(text_surface, text_render_rect)

                if time.time() - self.rename_cursor_time > 0.5:
                    self.rename_cursor_visible = not self.rename_cursor_visible
                    self.rename_cursor_time = time.time()

                if self.rename_cursor_visible:
                    cursor_x_offset = file_font.size(self.rename_input[:self.rename_cursor_position])[0]
                    cursor_x = input_rect.x + (input_rect.width - text_render_rect.width) // 2 + cursor_x_offset if self.rename_input else input_rect.centerx
                    cursor_y = input_rect.top + 3
                    pygame.draw.line(screen, text_color, (cursor_x, cursor_y), (cursor_x, cursor_y + input_rect.height - 6), 2)


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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.is_renaming:
                        if not self.name_rect.collidepoint(event.pos):
                            self.name = self.rename_input if self.rename_input else self.original_name
                            self.update_name_surface()
                            self.is_renaming = False
                        return

                    if self.name_rect.collidepoint(event.pos):
                        current_time = time.time()
                        if current_time - self.last_click_time < self.double_click_interval and not self.is_renaming:
                            self.is_renaming = True
                            self.rename_input = self.name.replace(".txt", "").replace("/", "")
                            self.rename_cursor_visible = True
                            self.rename_cursor_time = time.time()
                            self.rename_cursor_position = len(self.rename_input)
                            return
                        self.last_click_time = current_time
                    elif self.selection_rect.collidepoint(event.pos) and not is_selecting:
                        current_time = time.time()

                        if current_time - self.last_click_time < self.double_click_interval and self.selected and not self.is_renaming:
                            self.open_file(files, windows, taskbar)
                            for file in files:
                                file.selected = False
                        else:
                            if not (pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[
                                pygame.K_RCTRL]):
                                for file in files:
                                    file.selected = False
                            self.selected = True
                            self.dragging = True
                            dragging_file = self

                            dragged_files = [f for f in files if f.selected]

                            dragging_file.drag_offsets = []
                            initial_drag_pos = pygame.math.Vector2(dragging_file.rect.center)
                            for df in dragged_files:
                                offset = pygame.math.Vector2(df.rect.center) - initial_drag_pos
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
                                        print(f"Error: Cannot delete protected system file: {dragged_file.name}")
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
                        current_drag_pos = pygame.math.Vector2(self.rect.center)
                        for file_to_drag, offset in self.drag_offsets:
                            if file_to_drag != self:
                                file_to_drag.rect.center = current_drag_pos + offset
                                file_to_drag.name_rect.center = (
                                    file_to_drag.rect.centerx, file_to_drag.rect.bottom + 20)
                                file_to_drag.update_selection_rect()


            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if self.file_type == "folder":
                    context_menu_options = ["Открыть", "Переименовать", "Удалить", "Свойства", "Вставить"]
                else:
                    context_menu_options = ["Открыть", "Копировать", "Вырезать", "Копировать путь", "Создать ярлык", "Переименовать", "Удалить", "Свойства"]

                context_menu = ContextMenu(
                    event.pos[0], event.pos[1], context_menu_options, self, context="file")

            elif event.type == pygame.KEYDOWN:
                if self.is_renaming:
                    if event.key == pygame.K_RETURN:
                        self.name = self.rename_input if self.rename_input else self.original_name
                        self.update_name_surface()
                        self.is_renaming = False
                    elif event.key == pygame.K_ESCAPE:
                        self.rename_input = ""
                        self.is_renaming = False
                    elif event.key == pygame.K_BACKSPACE:
                        self.rename_input = self.rename_input[:-1]
                        self.rename_cursor_position = max(0, self.rename_cursor_position - 1)
                    elif event.key == pygame.K_LEFT:
                        self.rename_cursor_position = max(0, self.rename_cursor_position - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.rename_cursor_position = min(len(self.rename_input), self.rename_cursor_position + 1)
                    elif event.unicode:
                        valid_char = event.unicode.isalnum() or event.unicode == ' ' or event.unicode == '.'
                        if valid_char and file_font.render(self.rename_input + event.unicode, True, black).get_width() <= self.rect.width * 2:
                            self.rename_input += event.unicode
                            self.rename_cursor_position += 1


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
        elif self.is_app and self.name == "Calculator":
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
        elif self.is_app and self.name == "Calendar":
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
            calendar_window = Window("Calendar", calendar_app_instance.width,
                                     calendar_app_instance.height, new_x, new_y, calendar_app=calendar_app_instance)
            windows.append(calendar_window)
            taskbar.add_icon(calendar_window.taskbar_icon)
            calendar_window.bring_to_front(windows)


    def show_properties(self):
        file_size = len(self.content)
        creation_time = time.ctime(os.path.getctime(os.path.join(".", "images", self.image_path) if os.path.exists(os.path.join("images", self.image_path)) else "."))
        modification_time = time.ctime(os.path.getmtime(os.path.join(".", "images", self.image_path) if os.path.exists(os.path.join("images", self.image_path)) else "."))
        file_type_desc = "Папка с файлами" if self.file_type == 'folder' else "Текстовый документ (.txt)" if self.file_type == 'text' else "Приложение"

        properties_text = f"Свойства файла: {self.name}\n"
        properties_text += f"Тип: {file_type_desc}\n"
        properties_text += f"Размер: {file_size} байт\n"
        properties_text += f"Создан: {creation_time}\n"
        properties_text += f"Изменен: {modification_time}\n"

        properties_window = PropertiesWindow(
            f"Свойства: {self.name}", 400, 300, 300, 300, properties_text=properties_text)
        windows.append(properties_window)
        taskbar.add_icon(properties_window.taskbar_icon)
        properties_window.bring_to_front(windows)


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
                                    "Переименовать", "Удалить", "Свойства", "Создать .txt", "Создать папку", "Вставить"]
            context_menu = ContextMenu(
                event.pos[0], event.pos[1], context_menu_options, self, context="folder")


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
        self.rect = pygame.Rect(x, y, 200, 350)
        self.is_open = False
        self.options = ["Программы", "Настройки", "Выключение"]
        self.power_options = ["Выключить", "Перезагрузить", "Спящий режим"]
        self.option_surfaces = []
        self.power_option_surfaces = [taskbar_font.render(opt, True, text_color) for opt in self.power_options]
        self.option_rects = []
        self.power_option_rects = []
        option_y_offset = 70

        self.search_rect = pygame.Rect(x + 10, y + 10, 180, 25)
        self.search_text = ""
        self.search_active = False

        self.option_icons = {}
        try:
            self.option_icons["Программы"] = pygame.transform.scale(pygame.image.load(os.path.join("images", "programs_icon.png")).convert_alpha(), (24, 24))
            self.option_icons["Настройки"] = pygame.transform.scale(pygame.image.load(os.path.join("images", "settings_icon_small.png")).convert_alpha(), (24, 24))
            self.option_icons["Выключение"] = pygame.transform.scale(pygame.image.load(os.path.join("images", "power_icon.png")).convert_alpha(), (24, 24))
            self.option_icons["Выключить"] = pygame.transform.scale(pygame.image.load(os.path.join("images", "shutdown_icon.png")).convert_alpha(), (20, 20))
            self.option_icons["Перезагрузить"] = pygame.transform.scale(pygame.image.load(os.path.join("images", "reboot_icon.png")).convert_alpha(), (20, 20))
            self.option_icons["Спящий режим"] = pygame.transform.scale(pygame.image.load(os.path.join("images", "sleep_icon.png")).convert_alpha(), (20, 20))
        except FileNotFoundError:
            print("Error: Could not load Pusk Menu icons. Using text only.")
            self.option_icons = {}

        self.animation_duration = 0.2
        self.animation_start_time = 0
        self.menu_state = 'closed'
        self.target_height = self.rect.height
        self.rect.height = 0
        self.expanded_power_menu = False


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
            draw_text(screen, self.search_text, taskbar_font, black, (self.search_rect.x + 5, self.search_rect.y + 5), 'topleft')

            self.option_surfaces = [taskbar_font.render(
                option, True, text_color) for option in self.options]

            self.option_rects = []
            option_y_offset = 70
            for i, option_surface in enumerate(self.option_surfaces):
                rect = option_surface.get_rect(
                    topleft=(self.rect.x + 35, self.rect.y + option_y_offset))
                self.option_rects.append(rect)

                if self.options[i] in self.option_icons:
                    icon = self.option_icons[self.options[i]]
                    icon_rect = icon.get_rect(midleft=(self.rect.x + 15, rect.centery))
                    screen.blit(icon, icon_rect)

                screen.blit(option_surface, rect)
                option_y_offset += 40

            if self.options[i] == "Выключение" and rect.collidepoint(pygame.mouse.get_pos()):
                draw_rect(screen, light_blue_grey, rect)

            if self.expanded_power_menu:
                power_menu_x_offset = self.rect.right
                power_menu_width = 150
                power_menu_rect = pygame.Rect(power_menu_x_offset, self.rect.y + self.option_rects[-1].bottom + 10, power_menu_width, len(self.power_options) * 30 + 20)
                draw_rect(screen, window_color, power_menu_rect)
                draw_rect(screen, light_gray, power_menu_rect, 2)
                self.power_option_rects = []
                power_option_y = power_menu_rect.y + 10
                for i, power_option_surface in enumerate(self.power_option_surfaces):
                    power_rect = power_option_surface.get_rect(topleft=(power_menu_rect.x + 30, power_option_y))
                    self.power_option_rects.append(power_rect)
                    if self.power_options[i] in self.option_icons:
                        icon = self.option_icons[self.power_options[i]]
                        icon_rect = icon.get_rect(midleft=(power_menu_rect.x + 10, power_rect.centery))
                        screen.blit(icon, icon_rect)
                    screen.blit(power_option_surface, power_rect)
                    power_option_y += 30


    def handle_event(self, event, files, windows, taskbar):
        if self.menu_state != 'open':
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos) and not (self.expanded_power_menu and pygame.Rect(self.rect.right, self.rect.y + self.option_rects[-1].bottom + 10, 150, len(self.power_options) * 30 + 20).collidepoint(event.pos) if self.expanded_power_menu else False):
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
                    elif option == "Настройки":
                        settings_file = None
                        for f in files:
                            if f.name == "Settings" and f.is_app:
                                settings_file = f
                                break
                        if settings_file:
                            settings_file.open_file(files, windows, taskbar)
                            self.start_close_animation()
                    elif option == "Программы":
                        browser_file = None
                        for f in files:
                            if f.name == "Browser" and f.is_app:
                                browser_file = f
                                break
                        if browser_file:
                            browser_file.open_file(files, windows, taskbar)
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
                results[0].open_file(files, windows, taskbar)
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
            width = text_surface.get_width() + 20
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
        self.cut_file = None


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

    def handle_event(self, event, files, windows, taskbar, desktop_files, clipboard_file):
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
                        self.is_typing = True
                        self.selected_option_index_for_input = self.selected_option
                        self.file_name_input = ""
                        self.creation_requested = True
                        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
                        self.create_txt_button_visible = False
                        self.create_folder_button_visible = False
                    elif option == "Создать папку" and self.create_folder_button_visible:
                        self.is_typing = True
                        self.selected_option_index_for_input = self.selected_option
                        self.file_name_input = ""
                        self.creation_requested = True
                        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
                        self.create_txt_button_visible = False
                        self.create_folder_button_visible = False
                    elif option == "Переименовать":
                        self.is_typing = True
                        self.selected_option_index_for_input = self.selected_option
                        self.file_name_input = self.selected_file.name.replace(
                            ".txt", "").replace("/", "")
                        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
                    elif option == "Удалить":
                        if self.selected_file.protected:
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
                            self.close()
                    elif option == "Открыть":
                        if self.selected_file:
                            self.selected_file.open_file(
                                files, windows, taskbar)
                            self.close()
                    elif option == "Свойства":
                        if self.selected_file:
                            self.selected_file.show_properties()
                            self.close()
                    elif option == "Копировать":
                        clipboard_file[0] = self.selected_file
                        self.cut_file = None
                        self.close()
                    elif option == "Вырезать":
                        clipboard_file[0] = self.selected_file
                        self.cut_file = self.selected_file
                        self.close()
                    elif option == "Вставить":
                        if clipboard_file[0]:
                            new_file = clipboard_file[0]
                            if self.context == "folder" and self.selected_file.file_type == "folder":
                                if new_file not in self.selected_file.files_inside and new_file.parent_folder != self.selected_file:
                                    if isinstance(new_file, Folder) and is_descendant(new_file, self.selected_file):
                                        print("Нельзя переместить папку в себя!")
                                    else:
                                        if new_file in desktop_files:
                                            desktop_files.remove(new_file)
                                        elif new_file.parent_folder:
                                            if new_file in new_file.parent_folder.files_inside:
                                                new_file.parent_folder.files_inside.remove(new_file)
                                        self.selected_file.files_inside.append(new_file)
                                        new_file.parent_folder = self.selected_file
                                        new_file.rect.topleft = (self.mouse_x, self.mouse_y)
                                        new_file.name_rect.center = (new_file.rect.centerx, new_file.rect.bottom + 20)
                                        new_file.update_selection_rect()
                            elif self.context == "desktop_background":
                                if new_file not in desktop_files and new_file.parent_folder is not None:
                                    if new_file.parent_folder and new_file in new_file.parent_folder.files_inside:
                                        new_file.parent_folder.files_inside.remove(new_file)
                                    desktop_files.append(new_file)
                                    new_file.parent_folder = None
                                    new_file.rect.topleft = (self.mouse_x, self.mouse_y)
                                    new_file.name_rect.center = (new_file.rect.centerx, new_file.rect.bottom + 20)
                                    new_file.update_selection_rect()
                            if self.cut_file == clipboard_file[0]:
                                clipboard_file[0] = None
                                self.cut_file = None
                            self.close()
                    elif option == "Копировать путь":
                        if self.selected_file:
                            filepath = os.path.abspath(os.path.join(".", "images", self.selected_file.image_path) if os.path.exists(os.path.join("images", self.selected_file.image_path)) else self.selected_file.name)
                            pygame.scrap.put_text(filepath)
                            self.close()
                    elif option == "Создать ярлык":
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


                    elif option == "Очистить корзину":
                        files_to_remove = [f for f in files if f.is_in_trash]
                        for file_to_remove in files_to_remove:
                            files.remove(file_to_remove)
                        self.close()
                    elif option == "Обновить":
                        refresh_settings_from_db(
                            files, windows, widgets, taskbar)
                        self.close()
                    elif option == "Вернуть на рабочий стол":
                        if self.selected_file and self.selected_file.parent_folder:
                            folder = self.selected_file.parent_folder
                            if self.selected_file in folder.files_inside:
                                folder.files_inside.remove(self.selected_file)
                                desktop_files.append(self.selected_file)
                                self.selected_file.parent_folder = None
                                self.selected_file.rect.topleft = (
                                    self.mouse_x, self.mouse_y)
                                self.selected_file.name_rect.center = (
                                    self.selected_file.rect.centerx, self.selected_file.rect.bottom + 20)
                                self.selected_file.update_selection_rect()
                        self.close()


                    else:
                        self.close()
                        self.selected_option = -1
        elif event.type == pygame.KEYDOWN:
            if self.is_typing:
                if event.key == pygame.K_RETURN:
                    if self.creation_requested:
                        if "Создать .txt" in self.options and self.selected_option == 0:
                            new_file_name = self.file_name_input + ".txt"
                            new_file = DesktopFile(
                                new_file_name, "txtfile.png", self.mouse_x, self.mouse_y)
                            if self.folder_window and self.folder_window.folder:
                                self.folder_window.folder.files_inside.append(
                                    new_file)
                                new_file.parent_folder = self.folder_window.folder
                            else:
                                desktop_files.append(new_file)
                            new_file.content = ""

                        elif "Создать папку" in self.options and self.selected_option == 1:
                            new_folder_name = self.file_name_input
                            new_folder = Folder(
                                new_folder_name, self.mouse_x, self.mouse_y)
                            if self.folder_window and self.folder_window.folder:
                                self.folder_window.folder.files_inside.append(
                                    new_folder)
                                new_folder.parent_folder = self.folder_window.folder
                            else:
                                desktop_files.append(new_folder)

                        self.close()
                    else:
                        new_file_name = self.file_name_input + \
                                        (".txt" if self.selected_file.name.endswith(".txt") else "")
                        self.selected_file.name = new_file_name
                        self.close()

                elif event.key == pygame.K_BACKSPACE:
                    self.file_name_input = self.file_name_input[:-1]
                elif event.unicode:
                    valid_char = event.unicode.isalnum(
                    ) or event.unicode == ' ' or event.unicode == '.'
                    if valid_char and self.input_font.render(self.file_name_input + event.unicode, True,
                                                             black).get_width() <= self.input_rect_width - 10:
                        self.file_name_input += event.unicode


    def close(self):
        self.is_open = False
        self.is_typing = False
        self.selected_option_index_for_input = None
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
        self.pusk_button_active = False
        self.pusk_menu = pusk_menu

    def draw(self, screen):
        if self.pusk_button_active:
            draw_rect(screen, light_gray, self.rect)
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
        self.pusk_button = PuskButton(
            self.pusk_button_x, self.pusk_button_y, "pusk.png", self.pusk_menu)
        self.taskbar_color = taskbar_color
        self.taskbar_height = height
        self.time_rect = None
        self.taskbar_calendar = TaskbarCalendar()

    def update_color(self):
        global taskbar_color
        self.taskbar_color = taskbar_color

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
        time_rect = time_surface.get_rect(topright=(screen_width - 10, self.rect.centery))
        time_rect.centery = self.rect.centery
        screen.blit(time_surface, time_rect)
        self.time_rect = time_rect

    def draw(self, screen):
        draw_rect(screen, self.taskbar_color, self.rect)
        self.pusk_button.draw(screen)
        self.pusk_menu.draw(screen)
        icon_x = self.pusk_button_x + self.pusk_button.rect.width + self.icon_margin

        for icon in self.icons:
            icon.draw(screen, icon_x, self.rect.y +
                      (self.rect.height - icon.height) // 2)
            icon_x += icon.width + self.icon_margin

        self.draw_time(screen)
        self.taskbar_calendar.draw(screen, self.rect)

    def handle_event(self, event, windows, files, taskbar):
        if self.pusk_menu.handle_event(event, files, windows, taskbar):
            return

        self.pusk_button.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.time_rect and self.time_rect.collidepoint(event.pos):
                self.taskbar_calendar.toggle_visibility()
            else:
                self.taskbar_calendar.is_visible = False

            self.taskbar_calendar.handle_event(event, self.rect)
            if self.taskbar_calendar.is_visible and self.taskbar_calendar.rect.collidepoint(event.pos):
                return

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
        elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEMOTION:
            self.taskbar_calendar.handle_event(event, self.rect)


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
    name="Settings",
    image_path="settings_icon.png",
    x=10, y=150,
    is_app=True,
    protected=True
))

files.append(DesktopFile(
    name="Browser",
    image_path="browser_icon.png",
    x=10, y=250,
    is_app=True,
    protected=True
))

files.append(DesktopFile(
    name="Calculator",
    image_path="calculator_icon.png",
    x=10, y=350,
    is_app=True
))

files.append(Folder(
    name="New Folder",
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
    name="InfZov",
    image_path="IZ.png",
    x=10, y=580,
    is_app=True
))
files.append(DesktopFile(
    name="Calendar",
    image_path="calendar_icon.png",
    x=110, y=580,
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

key_repeat_interval = 0.05
key_repeat_timer = 0
held_keys = set()

taskbar_height = int(get_setting('taskbar_height', '60'))
taskbar = Taskbar(taskbar_height)

is_selecting = False
selection_start_pos = None
selection_end_pos = None
hovered_taskbar_icon = None


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
                        context_menu_options = ["Создать .txt", "Создать папку", "Обновить", "Вставить"]
                        context_menu = ContextMenu(
                            event.pos[0], event.pos[1], context_menu_options, context="folder_background",
                            folder_window=folder_window_instance)
                    else:
                        context_menu_options = ["Создать .txt", "Создать папку", "Обновить", "Вставить"]
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
            context_menu.handle_event(event, files, windows, taskbar, files, clipboard_file)
        taskbar.handle_event(event, windows, files, taskbar)
        settings_window = next((win for win in windows if win.settings_app), None)
        if settings_window and settings_window.settings_app:
            settings_window.settings_app.handle_event(mouse_pos, settings_window.rect, event)

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
            window.draw(screen)

        if dragging_file and dragging_file.dragging:
            dragging_file.draw(screen)

        for window in windows:
            if window.apvia_app and window.apvia_app.current_screen == "game":
                window.apvia_app.update_game(delta_time)
            if window.folder:
                window.draw_folder_content(screen.subsurface(
                    window.rect), window.folder.files_inside)

        hovered_taskbar_icon = None
        icon_x = taskbar.pusk_button_x + taskbar.pusk_button.rect.width + taskbar.icon_margin
        for icon in taskbar.icons:
            icon_rect = pygame.Rect(icon_x, taskbar.rect.y + (
                        taskbar.rect.height - icon.height) // 2, icon.width, icon.height)
            if icon_rect.collidepoint(mouse_pos):
                hovered_taskbar_icon = icon
                break

        if hovered_taskbar_icon:
            preview_surf = hovered_taskbar_icon.get_preview()
            if preview_surf:
                preview_rect = preview_surf.get_rect(bottomleft=(mouse_pos[0] + 10, taskbar.rect.top))
                screen.blit(preview_surf, preview_rect)
                draw_rect(screen, black, preview_rect, 2)

        if context_menu is not None and context_menu.is_open:
            context_menu.draw(screen)

        windows = [window for window in windows if window.is_open]
        taskbar.icons = [icon for icon in taskbar.icons if icon.window.is_open]

        if time.time() - last_settings_refresh_time >= settings_refresh_interval:
            refresh_settings_from_db(files, windows, widgets, taskbar)
            last_settings_refresh_time = time.time()

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()