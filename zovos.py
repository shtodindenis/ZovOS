# main.py
import pygame
import time
import sys
import random
import os
import sqlite3  # Import sqlite3
import threading  # Import threading
from pong_app import MyGameApp
from settings_app import SettingsApp
pygame.init()
pygame.font.init()  # Ensure font module is initialized

screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode(
    (screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("ZOV OS Startup")

blue = (0, 0, 255)
orange = (255, 165, 0)
white = (255, 255, 255)
black = (0, 0, 0)
dark_blue = (0, 0, 100, 128)
red = (255, 0, 0)
dark_gray = (30, 30, 30)
light_gray = (150, 150, 150)
bright_red = (255, 0, 0)
green = (0, 200, 0)
transparent_white = (255, 255, 255, 100)
selection_color = (100, 100, 255, 100)
taskbar_color = dark_gray
grey_background = (200, 200, 200)
light_blue_grey = (220, 230, 240)

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

# Database functions


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


# Initialize database
init_settings_db()

current_background_setting = get_setting(
    'background_image', 'zovosbg.png')  # Load from DB or use default
background_image = get_background_image(current_background_setting)
icon_layout_setting = get_setting(
    'icon_layout', 'grid')  # Load icon layout setting

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

# Settings refresh timer
last_settings_refresh_time = time.time()
settings_refresh_interval = 1  # seconds


def refresh_settings_from_db(files):
    global current_background_setting, background_image, icon_layout_setting
    current_background_setting = get_setting(
        'background_image', 'zovosbg.png')
    background_image = get_background_image(current_background_setting)
    icon_layout_setting = get_setting('icon_layout', 'grid')

    if icon_layout_setting == 'grid':
        grid_size = 128 + 20  # Icon size + spacing
        for file in files:
            file.rect.topleft = file.get_grid_position(
                grid_size)
            file.name_rect.center = (
                file.rect.centerx, file.rect.bottom + 20)
            file.update_selection_rect()
    elif icon_layout_setting == 'free':
        # For free layout, positions are kept as they are, or load positions from DB if implemented
        pass  # Add logic here if you save icon positions in DB


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


def run_app_in_thread(app_instance, subsurface_rect):
    """Runs the ported application in a separate thread."""
    app_instance.run_app(subsurface_rect)  # Call a run_app method in the app


class Window:
    def __init__(self, title, width, height, x, y, file=None, app_instance=None):
        self.title = title
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y + 50, width, height)
        self.dragging = False
        self.title_bar_height = 50
        self.title_bar = pygame.Rect(x, y, width, self.title_bar_height)
        self.title_surface = window_font.render(self.title, True, black)
        self.title_rect = self.title_surface.get_rect(
            center=self.title_bar.center)

        self.close_button_size = 20
        self.close_button_x = x + width - self.close_button_size - 10
        self.close_button_y = y + 15
        self.close_button_rect = pygame.Rect(self.close_button_x, self.close_button_y, self.close_button_size,
                                             self.close_button_size)
        self.close_cross_surface = pygame.Surface(
            (self.close_button_size, self.close_button_size), pygame.SRCALPHA)
        pygame.draw.line(self.close_cross_surface, white, (0, 0),
                         (self.close_button_size, self.close_button_size), 2)
        pygame.draw.line(self.close_cross_surface, white,
                         (self.close_button_size, 0), (0, self.close_button_size), 2)

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
        self.app_instance = app_instance  # Instance of the external Pygame application
        self.app_thread = None  # Thread for ported application

        self.char_limit_per_line = 70

        self.key_repeat_delay = 0.5
        self.key_repeat_interval = 0.05
        self.key_down_time = 0
        self.held_key = None
        icon_image_path = None
        if self.file:
            icon_image_path = self.file.image_path
        self.taskbar_icon = TaskbarIcon(
            self, icon_image_path)

    def draw(self, screen):
        if self.is_open:
            pygame.draw.rect(screen, white, self.title_bar)
            screen.blit(self.title_surface, self.title_rect)
            pygame.draw.rect(screen, red, self.close_button_rect)
            screen.blit(self.close_cross_surface,
                        self.close_button_rect.topleft)
            # Check if app_instance is SettingsApp
            if self.app_instance and isinstance(self.app_instance, SettingsApp):
                pygame.draw.rect(screen, light_blue_grey, self.rect)
                # Delegate drawing to SettingsApp
                self.app_instance.draw(screen.subsurface(self.rect))
                print("Drawing SettingsApp")  # Debug print

            elif self.app_instance:  # Draw for generic app instances
                if hasattr(self.app_instance, 'draw'):  # Check if app has draw method
                    self.app_instance.draw(screen.subsurface(self.rect))
                print(f"Drawing Generic App: {self.title}")  # Debug print

            else:  # Default white window for text files
                pygame.draw.rect(screen, white, self.rect)

            if self.file and self.file.name.endswith(".txt"):
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
                    line_surfaces.append(file_font.render(line, True, black))

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
                                    selected_text, True, black)
                                selected_rect = selected_surface.get_rect(topleft=(
                                    text_rect.x + file_font.size(lines[index][:selection_start_local])[0], text_rect.y))
                                selection_area_rect = pygame.Rect(
                                    selected_rect.x, selected_rect.y, selected_rect.width, selected_rect.height)
                                pygame.draw.rect(
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
                        pygame.draw.line(screen, black, (cursor_x, cursor_y),
                                         (cursor_x, cursor_y + file_font.get_height()), 2)
            elif self.mail_app:
                self.mail_app.draw(screen.subsurface(self.rect))
            # Draw other app instances, but not SettingsApp again

    def handle_event(self, event, windows, taskbar, files, icon_layout_setting):
        # Removed icon_layout_setting from global declaration
        global background_image, current_background_setting
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
                        # You might need a way to gracefully stop the thread
                        # For now, we just let it run until it naturally finishes (if it has a loop that can terminate)
                        # Проверка наличия метода
                        if self.app_instance and hasattr(self.app_instance, 'stop_running'):
                            self.app_instance.stop_running()
                if self.file and self.file.name.endswith(".txt") and self.rect.collidepoint(event.pos):
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

                    if not pygame.key.get_pressed()[pygame.K_LSHIFT] and not pygame.key.get_pressed()[pygame.K_RSHIFT]:
                        self.selection_start = self.cursor_pos
                        self.selection_end = self.cursor_pos
                    else:
                        if self.selection_start is None:
                            self.selection_start = self.cursor_pos
                            self.selection_end = self.cursor_pos
                        else:
                            self.selection_end = self.cursor_pos
                    self.held_key = None
                # Handle settings click events
                elif self.app_instance and isinstance(self.app_instance, SettingsApp) and self.rect.collidepoint(event.pos):
                    setting_action = self.app_instance.handle_event(
                        event.pos, self.rect)
                    if setting_action:  # If SettingsApp returns a setting change action
                        if setting_action in ["zovosbg.png", "zovosbg2.png", "zovosbg3.png", "color"]:
                            current_background_setting = setting_action
                            background_image = get_background_image(
                                current_background_setting)
                            # Update background setting in DB
                            update_setting('background_image',
                                           current_background_setting)
                        elif setting_action == 'layout_change':
                            icon_layout_setting = get_setting(
                                'icon_layout', 'grid')  # Refresh layout setting
                            if icon_layout_setting == 'grid':
                                grid_size = 128 + 20  # Icon size + spacing
                                for file in files:
                                    file.rect.topleft = file.get_grid_position(
                                        grid_size)
                                    file.name_rect.center = (
                                        file.rect.centerx, file.rect.bottom + 20)
                                    file.update_selection_rect()

                elif self.app_instance and not isinstance(self.app_instance, SettingsApp) and self.rect.collidepoint(event.pos):
                    # No need to handle events for threaded apps here in the OS event loop
                    pass

                else:
                    self.text_input = False

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                if self.text_input and self.selection_start is not None and self.selection_start == self.selection_end:
                    self.selection_start = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                new_x = max(
                    0, min(event.pos[0] - self.drag_offset_x, screen_width - self.width))
                new_y = max(
                    0, min(event.pos[1] - self.drag_offset_y, screen_height - self.height - 50))

                self.title_bar.x = new_x
                self.title_bar.y = new_y

                self.rect.x = self.title_bar.x
                self.rect.y = self.title_bar.y + 50

                self.title_rect.center = self.title_bar.center
                self.close_button_rect.x = self.title_bar.x + \
                    self.title_bar.width - self.close_button_size - 10
                self.close_button_rect.y = self.title_bar.y + 15
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

        elif event.type == pygame.KEYDOWN and self.text_input and self.file and self.file.name.endswith(".txt"):
            if event.key not in [pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_CAPSLOCK, pygame.K_NUMLOCK]:
                self.held_key = event.key
                self.key_down_time = time.time()

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
                    start_index = min(self.selection_start, self.selection_end)
                    end_index = max(self.selection_start, self.selection_end)
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
                    start_index = min(self.selection_start, self.selection_end)
                    end_index = max(self.selection_start, self.selection_end)
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
                    start_index = min(self.selection_start, self.selection_end)
                    end_index = max(self.selection_start, self.selection_end)
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

            self.cursor_visible = True
            self.cursor_time = time.time()
        if self.mail_app:
            self.mail_app.handle_event(event, windows)
        # No need to handle events for threaded apps here in the OS event loop

    def bring_to_front(self, windows):
        if self in windows:
            windows.remove(self)
            windows.append(self)


class DesktopFile:
    def __init__(self, name, image_path, x, y, protected=False, file_type="text", app_module=None, app_class=None):
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
                # Default to txt icon if image not found
                self.image = self.create_default_txt_icon()
        else:
            self.image = self.create_default_txt_icon()

        self.rect = self.image.get_rect(topleft=(x, y))
        self.selected = False
        self.dragging = False
        self.name_surface = file_font.render(self.name, True, white)
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
        self.file_type = file_type  # "text", "app" etc.
        self.app_module = app_module  # Module name for app file
        self.app_class = app_class  # Class name within the module

        self.content = ""
        self.grid_spacing = 20  # Spacing between grid cells
        self.icon_size = 128  # Icon size (assuming square 128x128)

    def create_default_txt_icon(self):
        image = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.rect(image, white, (0, 0, 64, 64))
        pygame.draw.rect(image, black, (0, 0, 64, 64), 1)
        text_surface = file_font.render(".txt", True, black)
        text_rect = text_surface.get_rect(center=(32, 32))
        image.blit(text_surface, text_rect)
        return image

    def draw(self, screen):
        if not self.is_in_trash:
            screen.blit(self.image, self.rect)
            if self.name != self.original_name:
                self.name_surface = file_font.render(self.name, True, white)
                self.original_name = self.name

            self.name_rect = self.name_surface.get_rect(
                center=(self.rect.centerx, self.rect.bottom + 20))
            screen.blit(self.name_surface, self.name_rect)

            if self.selected:
                screen.blit(self.selection_surface, self.selection_rect)

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
        if not self.is_in_trash:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.selection_rect.collidepoint(event.pos):
                        current_time = time.time()

                        if current_time - self.last_click_time < self.double_click_interval:
                            self.open_file(files, windows, taskbar)
                            for file in files:
                                file.selected = False
                        else:
                            self.selected = True
                            for file in files:
                                if file != self:
                                    file.selected = False
                            self.dragging = True
                            moving_file_to_front(self)

                        self.last_click_time = current_time
                    else:
                        clicked_on_file = False
                        for file in files:
                            if file.selection_rect.collidepoint(event.pos):
                                clicked_on_file = True
                                break
                        if not clicked_on_file:
                            self.selected = False
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.dragging:
                        if trash.rect.colliderect(self.rect):
                            self.is_in_trash = True
                            files.remove(self)
                        elif icon_layout_setting == 'grid':
                            grid_size = self.icon_size + self.grid_spacing
                            self.rect.topleft = self.get_grid_position(
                                grid_size)
                            self.name_rect.center = (
                                self.rect.centerx, self.rect.bottom + 20)
                            self.update_selection_rect()
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    self.rect.center = event.pos
                    self.name_rect.center = (
                        self.rect.centerx, self.rect.bottom + 20)
                    self.update_selection_rect()

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
        elif self.file_type == "port" and self.app_module and self.app_class:
            try:
                module = __import__(self.app_module)
                app_class = getattr(module, self.app_class)
                app_instance = app_class()
                print(f"Instantiated app: {self.name}, class: {
                      self.app_class}")  # Debug print
                app_width = getattr(app_instance, 'width', 600)
                app_height = getattr(app_instance, 'height', 400)

                if windows:
                    last_window = windows[-1]
                    new_x = last_window.title_bar.x + 30
                    new_y = last_window.title_bar.y + 30
                    if new_x + app_width > screen_width:
                        new_x = 200
                    if new_y + app_height + 50 > screen_height:
                        new_y = 200
                else:
                    new_x = 200
                    new_y = 200

                new_window = Window(self.name, app_width, app_height,
                                    new_x, new_y, file=self, app_instance=app_instance)
                windows.append(new_window)
                taskbar.add_icon(new_window.taskbar_icon)
                new_window.bring_to_front(windows)

                # Start the application in a separate thread
                subsurface_rect = new_window.rect
                new_window.app_thread = threading.Thread(
                    target=run_app_in_thread, args=(app_instance, subsurface_rect))
                new_window.app_thread.start()

            except ImportError as e:
                print(f"Error importing module {self.app_module}: {e}")
            except AttributeError as e:
                print(f"Error accessing class {
                      self.app_class} or methods within module {self.app_module}: {e}")
            except Exception as e:
                print(f"Error launching application {self.name}: {e}")


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
        self.name_surface = file_font.render("Корзина", True, white)
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


class ContextMenu:
    def __init__(self, x, y, options, file=None):
        self.x = x
        self.y = y
        self.options = options
        self.item_height = 30
        max_width = 0
        self.option_surfaces = []
        for option in options:
            text_surface = context_menu_font.render(option, True, black)
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
        self.creation_requested = False
        self.mouse_x, self.mouse_y = 0, 0
        self.selected_file = file
        self.create_txt_button_visible = True
        self.input_rect_width = 200
        self.input_rect_height = 30
        self.input_font = context_menu_font

    def draw(self, screen):
        if self.is_open:
            light_gray = (150, 150, 150)
            black = (0, 0, 0)
            white = (255, 255, 255)

            pygame.draw.rect(screen, white, self.rect)
            pygame.draw.rect(screen, black, self.rect, 1)

            for i, option_surface in enumerate(self.option_surfaces):
                text_rect = option_surface.get_rect(
                    topleft=(self.x + 10, self.y + i * self.item_height + 5))

                if i == self.selected_option:
                    pygame.draw.rect(screen, light_gray, (self.x, self.y +
                                     i * self.item_height, self.width, self.item_height))

                screen.blit(option_surface, text_rect)

            if self.is_typing:
                input_rect = pygame.Rect(
                    self.x, self.y + self.height, self.input_rect_width, self.input_rect_height)
                pygame.draw.rect(screen, white, input_rect)
                pygame.draw.rect(screen, black, input_rect, 1)
                input_surface = self.input_font.render(
                    self.file_name_input, True, black)
                screen.blit(input_surface,
                            (input_rect.x + 5, input_rect.y + 5))

    def handle_event(self, event, files, windows):
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
                        self.file_name_input = ""
                        self.creation_requested = True
                        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
                        self.selected_option = -1
                        self.create_txt_button_visible = False
                    elif option == "Переименовать":
                        self.is_typing = True
                        self.file_name_input = self.selected_file.name.replace(
                            ".txt", "")
                        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
                    elif option == "Удалить":
                        files.remove(self.selected_file)
                        self.is_open = False
                    else:
                        self.is_open = False
                        self.selected_option = -1
        elif event.type == pygame.KEYDOWN:
            if self.is_typing:
                if event.key == pygame.K_RETURN:
                    if self.creation_requested:
                        new_file_name = self.file_name_input + ".txt"
                        new_file = DesktopFile(
                            # Default icon for new txt file
                            new_file_name, "txtfile.png", self.mouse_x, self.mouse_y)
                        files.append(new_file)
                        new_file.content = ""
                        self.is_typing = False
                        self.is_open = False
                        self.creation_requested = False
                        self.selected_option = -1
                    else:
                        new_file_name = self.file_name_input + ".txt"
                        self.selected_file.name = new_file_name
                        self.is_typing = False
                        self.is_open = False

                elif event.key == pygame.K_BACKSPACE:
                    self.file_name_input = self.file_name_input[:-1]
                elif event.unicode:
                    test_name = self.file_name_input + event.unicode
                    text_surface = self.input_font.render(
                        test_name, True, black)
                    if text_surface.get_width() <= self.input_rect_width - 10:
                        self.file_name_input += event.unicode

    def close(self):
        self.is_open = False
        self.is_typing = False
        self.creation_requested = False
        self.create_txt_button_visible = True


class PuskButton:
    def __init__(self, x, y, image_path):
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

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                pass  # Pusk button action can be added here


class Taskbar:
    def __init__(self, height):
        self.rect = pygame.Rect(
            0, screen_height - height, screen_width, height)
        self.icons = []
        self.icon_width = 60
        self.icon_height = 40
        self.icon_margin = 10
        self.pusk_button_x = 10
        self.pusk_button_y = screen_height - height + \
            (height - 60) // 2
        self.pusk_button = PuskButton(  # Correct argument order here
            self.pusk_button_x, self.pusk_button_y, "pusk.png")  # x, y, image_path

    def add_icon(self, icon):
        self.icons.append(icon)

    def remove_icon(self, icon):
        if icon in self.icons:
            self.icons.remove(icon)

    def draw(self, screen):
        pygame.draw.rect(screen, taskbar_color, self.rect)
        self.pusk_button.draw(screen)
        icon_x = self.pusk_button_x + self.pusk_button.rect.width + \
            self.icon_margin

        for icon in self.icons:
            icon.draw(screen, icon_x, self.rect.y +
                      (self.rect.height - self.icon_height) // 2)
            icon_x += self.icon_width + self.icon_margin

    def handle_event(self, event, windows):
        self.pusk_button.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            icon_x = self.pusk_button_x + self.pusk_button.rect.width + self.icon_margin
            for icon in self.icons:
                icon_rect = pygame.Rect(icon_x, self.rect.y + (
                    self.rect.height - self.icon_height) // 2, self.icon_width, self.icon_height)
                if icon_rect.collidepoint(event.pos):
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
            text_surface = taskbar_font.render(
                "Error", True, black)
            text_rect = text_surface.get_rect(center=icon_rect.center)
            screen.blit(text_surface, text_rect)


files = []

# "Настройки" is now a portable app
files.append(DesktopFile(
    name="Настройки",
    image_path="settings.png",  # Make sure you have settings_icon.png in images folder
    x=10, y=10,
    file_type="port",
    app_module="settings_app",  # Module name is the filename without .py
    app_class="SettingsApp"    # Class name inside settings_app.py
))
files.append(DesktopFile(
    name="Pong",
    image_path="zovpong.png",  # Make sure you have settings_icon.png in images folder
    x=110, y=10,
    file_type="port",
    app_module="pong_app",  # Module name is the filename without .py
    app_class="MyGameApp"    # Class name inside settings_app.py
))

trash = Trash(1800, 10)

windows = []
context_menu = None
running = True
selected_file = None
dragging_file = None

key_repeat_interval = 0.05
key_repeat_timer = 0
held_keys = set()

taskbar_height = 60
taskbar = Taskbar(taskbar_height)


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

                if selected_file and not selected_file.protected:
                    context_menu = ContextMenu(
                        event.pos[0], event.pos[1], ["Переименовать", "Удалить"], selected_file)
                elif not selected_file and (not context_menu or context_menu.create_txt_button_visible):
                    context_menu = ContextMenu(
                        event.pos[0], event.pos[1], ["Создать .txt"])
                else:
                    context_menu = None
            elif event.button == 1:
                if context_menu and context_menu.is_open and not context_menu.rect.collidepoint(event.pos):
                    context_menu.close()
        if not (context_menu and context_menu.is_open):
            for file in files:
                file.handle_event(event, files, windows,
                                  context_menu, trash, move_file_to_front, taskbar, icon_layout_setting)

        for window in windows:
            window.handle_event(event, windows, taskbar,
                                files, icon_layout_setting)
        trash.handle_event(event, files)
        if context_menu is not None and context_menu.is_open:
            context_menu.handle_event(event, files, windows)
        taskbar.handle_event(event, windows)

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

        # Grid drawing for debugging (optional)
        if icon_layout_setting == 'grid':
            grid_size = 128 + 20
            for x in range(0, screen_width, grid_size):
                for y in range(0, screen_height-taskbar_height, grid_size):
                    # Draw grid points
                    pygame.draw.rect(screen, light_gray, (x, y, 1, 1))

        for file in files:
            if file.dragging == False:
                file.draw(screen)

        for file in files:
            if file.dragging == True:
                file.draw(screen)

        for window in windows:
            # Draw window frame, title bar, close button, and delegate app drawing
            window.draw(screen)

        if context_menu is not None and context_menu.is_open:
            context_menu.draw(screen)

        windows = [window for window in windows if window.is_open]
        taskbar.icons = [icon for icon in taskbar.icons if icon.window.is_open]

    # Refresh settings every 5 seconds
    if time.time() - last_settings_refresh_time >= settings_refresh_interval:
        refresh_settings_from_db(files)
        last_settings_refresh_time = time.time()

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
