import os
import sqlite3
import sys
import time
import calendar
from datetime import datetime, timedelta
import random
import psutil
import pygame
pygame.init()
pygame.mixer.init()
pygame.font.init()
screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode(
    (screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("ZOV OS")
lue = (0, 0, 255)
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


calendar_background_color_light = pygame.Color(
    "#f7f7f7")  # Light grey background for light theme
calendar_background_color_dark = dark_gray  # Dark background for dark theme
calendar_border_color_light = light_gray  # Light border for light theme
# Light border for dark theme, to be visible on dark bg
calendar_border_color_dark = light_gray
month_header_color_light = black  # Black header for light theme
month_header_color_dark = white  # White header for dark theme
# Darker day names for light theme
day_name_color_light = pygame.Color("#555555")
# Lighter day names for dark theme
day_name_color_dark = pygame.Color("#999999")
day_number_color_light = black  # Black day numbers for light theme
day_number_color_dark = white  # White day numbers for dark theme
weekend_day_color_light = pygame.Color(
    "#FFD700")  # Gold for weekends in light theme
weekend_day_color_dark = pygame.Color(
    "#FFD700")  # Gold for weekends in dark theme
# Bright blue for current day in light theme
current_day_color_light = pygame.Color("#00BFFF")
# Bright blue for current day in dark theme
current_day_color_dark = pygame.Color("#00BFFF")
button_color_light = white  # White buttons for light theme
button_color_dark = dark_gray  # Dark buttons for dark theme
button_hover_color_light = pygame.Color(
    "#E0E0E0")  # Light grey hover in light theme
button_hover_color_dark = pygame.Color(
    "#555555")  # Darker grey hover in dark theme
button_arrow_color_light = black  # Black arrows in light theme
button_arrow_color_dark = white  # White arrows in dark theme
# Day rect color in light theme
day_rect_color_light = calendar_background_color_light
day_rect_color_dark = calendar_background_color_dark  # Day rect color in dark theme
# Day rect border in light theme
day_rect_border_color_light = calendar_border_color_light
# Day rect border in dark theme
day_rect_border_color_dark = calendar_border_color_dark

tooltip_font = pygame.font.Font(None, 24)


class CalendarApp:
    def __init__(self):
        self.width = 450
        self.height = 420  # Increased height to accommodate better spacing and design
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.font = widget_font
        self.date_color = text_color
        self.current_date = datetime.now()
        self.calendar_surface = None
        self.animating = False
        self.animation_direction = 1
        self.animation_start_time = 0
        self.animation_duration = 0.15
        self.next_calendar_surface = None
        self.animation_surface = pygame.Surface(
            self.rect.size, pygame.SRCALPHA)

        self.month_backward_rect = None
        self.month_forward_rect = None
        self.year_backward_rect = None
        self.year_forward_rect = None
        self.day_rects = []
        self.hovered_day_rect = None
        self.selected_day = None
        self.hovered_day_number = None

        self.theme_colors = {}
        self._update_theme_colors()
        self._render_calendar()

    def _update_theme_colors(self):
        global current_theme_setting
        if current_theme_setting == 'dark':
            self.theme_colors = {
                'calendar_background_color': calendar_background_color_dark,
                'calendar_border_color': calendar_border_color_dark,
                'month_header_color': month_header_color_dark,
                'day_name_color': day_name_color_dark,
                'day_number_color': day_number_color_dark,
                'weekend_day_color': weekend_day_color_dark,
                'current_day_color': current_day_color_dark,
                'button_color': button_color_dark,
                'button_hover_color': button_hover_color_dark,
                'button_arrow_color': button_arrow_color_dark,
                'day_rect_color': day_rect_color_dark,
                'day_rect_border_color': day_rect_border_color_dark
            }
        else:  # light theme or default
            self.theme_colors = {
                'calendar_background_color': calendar_background_color_light,
                'calendar_border_color': calendar_border_color_light,
                'month_header_color': month_header_color_light,
                'day_name_color': day_name_color_light,
                'day_number_color': day_number_color_light,
                'weekend_day_color': weekend_day_color_light,
                'current_day_color': current_day_color_light,
                'button_color': button_color_light,
                'button_hover_color': button_hover_color_light,
                'button_arrow_color': button_arrow_color_light,
                'day_rect_color': day_rect_color_light,
                'day_rect_border_color': day_rect_border_color_light
            }

    def _render_calendar(self):
        self._update_theme_colors()  # Update colors based on current theme before rendering
        self.calendar_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.calendar_surface.fill((0, 0, 0, 0))

        # Background and border for the whole calendar
        draw_rect(self.calendar_surface, self.theme_colors['calendar_background_color'],
                  # Rounded corners for the main calendar
                  pygame.Rect(0, 0, self.width, self.height), border_radius=12)
        draw_rect(self.calendar_surface, self.theme_colors['calendar_border_color'],
                  # Border for the main calendar
                  pygame.Rect(0, 0, self.width, self.height), 2, border_radius=12)

        month_text = self.current_date.strftime("%B %Y").upper()
        month_surface = self.font.render(
            month_text, True, self.theme_colors['month_header_color'])
        month_rect = month_surface.get_rect(
            center=(self.width // 2, 40))  # Slightly lower month header
        self.calendar_surface.blit(month_surface, month_rect)

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_name_x_start = 40
        day_name_y = 70  # Adjusted day names position
        day_name_spacing = (self.width - 2 * day_name_x_start) / 6
        for day_name in day_names:
            day_name_surface = settings_font.render(
                day_name, True, self.theme_colors['day_name_color'])
            day_name_rect = day_name_surface.get_rect(
                center=(day_name_x_start, day_name_y))
            self.calendar_surface.blit(day_name_surface, day_name_rect)
            day_name_x_start += day_name_spacing

        cal = calendar.Calendar()
        month_days = list(cal.monthdayscalendar(
            self.current_date.year, self.current_date.month))
        day_rect_size = 38  # Slightly larger day rects
        day_start_x = 40
        day_start_y = 95  # Adjusted day start position
        day_x = day_start_x
        day_y = day_start_y
        day_count = 0
        self.day_rects = []

        day_spacing_x = day_name_spacing
        day_spacing_y = 48  # Adjusted day spacing

        today = datetime.now().date()
        current_month_date = datetime(
            self.current_date.year, self.current_date.month, 1).date()

        for week in month_days:
            for day in week:
                if day != 0:
                    day_date = datetime(
                        self.current_date.year, self.current_date.month, day).date()
                    day_rect = pygame.Rect(
                        day_x - day_rect_size // 2, day_y, day_rect_size, day_rect_size)
                    draw_rect(self.calendar_surface, self.theme_colors['day_rect_color'],
                              day_rect, border_radius=8)  # Rounded corners for day rects
                    draw_rect(self.calendar_surface, self.theme_colors['day_rect_border_color'],
                              day_rect, 1, border_radius=8)  # Border for day rects

                    day_color_to_use = self.theme_colors['day_number_color']
                    if day_date.weekday() >= 5:
                        day_color_to_use = self.theme_colors['weekend_day_color']
                    if day_date == today and day_date.month == current_month_date.month and day_date.year == current_month_date.year:
                        draw_rect(self.calendar_surface, self.theme_colors['current_day_color'],
                                  day_rect, border_radius=8)  # Highlight for current day
                        day_color_to_use = white  # White text for current day

                    if self.hovered_day_rect == day_rect:
                        draw_rect(self.calendar_surface,
                                  # Hover effect
                                  self.theme_colors['button_hover_color'], day_rect, border_radius=8)
                        # Text color on hover
                        day_color_to_use = self.theme_colors['month_header_color']

                    if self.selected_day and self.selected_day.day == day and self.selected_day.month == self.current_date.month and self.selected_day.year == self.current_date.year:
                        draw_rect(self.calendar_surface, pygame.Color(
                            'forestgreen'), day_rect, border_radius=8)  # Selected day color
                        day_color_to_use = white  # White text for selected day

                    day_surface = settings_font.render(
                        str(day), True, day_color_to_use)
                    day_text_rect = day_surface.get_rect(
                        center=day_rect.center)
                    self.calendar_surface.blit(day_surface, day_text_rect)
                    self.day_rects.append(day_rect)

                day_x += day_spacing_x
                day_count += 1
                if day_count % 7 == 0:
                    day_x = day_start_x
                    day_y += day_spacing_y

        button_size = 34  # Slightly larger buttons
        button_margin_horizontal = 30
        button_margin_vertical = 15

        # Month navigation buttons - More visually distinct arrow design
        month_backward_rect = pygame.Rect(
            button_margin_horizontal, month_rect.centery - button_size // 2, button_size, button_size)
        draw_rect(self.calendar_surface, self.theme_colors['button_color'],
                  month_backward_rect, border_radius=8)  # Rounded buttons
        draw_text(self.calendar_surface, "<", settings_font, self.theme_colors['button_arrow_color'],
                  month_backward_rect.center, 'center')
        self.month_backward_rect = month_backward_rect

        month_forward_rect = pygame.Rect(self.width - button_margin_horizontal -
                                         button_size, month_rect.centery - button_size // 2, button_size, button_size)
        draw_rect(self.calendar_surface, self.theme_colors['button_color'],
                  month_forward_rect, border_radius=8)  # Rounded buttons
        draw_text(self.calendar_surface, ">", settings_font,
                  self.theme_colors['button_arrow_color'], month_forward_rect.center, 'center')
        self.month_forward_rect = month_forward_rect

        # Year navigation buttons - More visually distinct double arrow design
        year_backward_rect = pygame.Rect(
            button_margin_horizontal, month_backward_rect.bottom + button_margin_vertical, button_size, button_size)
        draw_rect(self.calendar_surface, self.theme_colors['button_color'],
                  year_backward_rect, border_radius=8)  # Rounded buttons
        draw_text(self.calendar_surface, "<<", settings_font,
                  self.theme_colors['button_arrow_color'], year_backward_rect.center, 'center')
        self.year_backward_rect = year_backward_rect

        year_forward_rect = pygame.Rect(self.width - button_margin_horizontal - button_size,
                                        month_forward_rect.bottom + button_margin_vertical, button_size, button_size)
        draw_rect(self.calendar_surface, self.theme_colors['button_color'],
                  year_forward_rect, border_radius=8)  # Rounded buttons
        draw_text(self.calendar_surface, ">>", settings_font,
                  self.theme_colors['button_arrow_color'], year_forward_rect.center, 'center')
        self.year_forward_rect = year_forward_rect

        if self.hovered_day_number:
            tooltip_text = datetime(
                self.current_date.year, self.current_date.month, self.hovered_day_number).strftime("%d %B %Y")
            tooltip_surface = tooltip_font.render(
                tooltip_text, True, text_color)
            tooltip_rect = tooltip_surface.get_rect(
                # Adjusted tooltip position - lower
                center=(self.width // 2, self.height - 30))
            draw_rect(self.calendar_surface, self.theme_colors['button_color'], tooltip_rect.inflate(
                10, 5), border_radius=8)  # Rounded tooltip background
            self.calendar_surface.blit(tooltip_surface, tooltip_rect)

    def draw(self, screen_surface):
        if self.animating:
            elapsed_time = time.time() - self.animation_start_time
            progress = min(elapsed_time / self.animation_duration, 1)

            if self.next_calendar_surface:
                self.animation_surface.fill((0, 0, 0, 0))
                if self.animation_direction == 1:
                    next_x = int(self.rect.width * progress)
                    current_x = int(self.rect.width * (progress - 1))

                else:
                    next_x = int(self.rect.width * (progress - 1))
                    current_x = int(self.rect.width * progress)

                self.animation_surface.blit(
                    self.calendar_surface, (current_x, 0))
                self.animation_surface.blit(
                    self.next_calendar_surface, (next_x, 0))
                screen_surface.blit(self.animation_surface,
                                    (self.rect.x, self.rect.y))

            if progress == 1:
                self.animating = False
                self.calendar_surface = self.next_calendar_surface
                self.next_calendar_surface = None

        else:
            screen_surface.blit(self.calendar_surface,
                                (self.rect.x, self.rect.y))

    def _get_day_number_from_rect_index(self, day_index):
        cal = calendar.Calendar()
        month_days = list(cal.monthdayscalendar(
            self.current_date.year, self.current_date.month))
        day_number = 0
        day_count_in_month = 0
        for week in month_days:
            for d in week:
                if d != 0:
                    day_count_in_month += 1
                if day_count_in_month - 1 == day_index:
                    day_number = d
                    break
            if day_number != 0:
                break
        return day_number

    def handle_event(self, event, window_rect):
        if self.animating:
            return

        if event.type == pygame.MOUSEMOTION:
            relative_mouse_pos = (
                event.pos[0] - window_rect.x - self.rect.x, event.pos[1] - window_rect.y - self.rect.y)
            self.hovered_day_rect = None
            self.hovered_day_number = None
            if not self.animating:
                for day_index, day_rect in enumerate(self.day_rects):
                    if day_rect.collidepoint(relative_mouse_pos):
                        self.hovered_day_rect = day_rect
                        day_number = self._get_day_number_from_rect_index(
                            day_index)
                        if day_number != 0:
                            self.hovered_day_number = day_number
                        break
            self._render_calendar()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            relative_mouse_pos = (
                event.pos[0] - window_rect.x - self.rect.x, event.pos[1] - window_rect.y - self.rect.y)
            if self.month_backward_rect and self.month_backward_rect.collidepoint(relative_mouse_pos):
                next_month = self.current_date.month - 1
                next_year = self.current_date.year
                if next_month < 1:
                    next_month = 12
                    next_year -= 1
                self.current_date = datetime(next_year, next_month, 1)
                self._start_animation(-1)
            elif self.month_forward_rect and self.month_forward_rect.collidepoint(relative_mouse_pos):
                next_month = self.current_date.month + 1
                next_year = self.current_date.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                self.current_date = datetime(next_year, next_month, 1)
                self._start_animation(1)
            elif self.year_backward_rect and self.year_backward_rect.collidepoint(relative_mouse_pos):
                self.current_date = datetime(
                    self.current_date.year - 1, self.current_date.month, 1)
                self._start_animation(-1)
            elif self.year_forward_rect and self.year_forward_rect.collidepoint(relative_mouse_pos):
                self.current_date = datetime(
                    self.current_date.year + 1, self.current_date.month, 1)
                self._start_animation(1)
            else:
                for day_index, day_rect in enumerate(self.day_rects):
                    if day_rect.collidepoint(relative_mouse_pos):
                        day_number = self._get_day_number_from_rect_index(
                            day_index)
                        if day_number != 0:
                            self.selected_day = datetime(
                                self.current_date.year, self.current_date.month, day_number)
                            print(f"Selected Date: {
                                  self.selected_day.strftime('%Y-%m-%d')}")
                            self._render_calendar()

    def _start_animation(self, direction):
        self.next_calendar_surface = pygame.Surface(
            self.rect.size, pygame.SRCALPHA)
        self.next_calendar_surface.fill((0, 0, 0, 0))
        temp_calendar_app = CalendarApp()
        temp_calendar_app.rect = self.rect.copy()
        temp_calendar_app.font = self.font
        temp_calendar_app.date_color = self.date_color
        temp_calendar_app.current_date = self.current_date
        temp_calendar_app.selected_day = self.selected_day
        temp_calendar_app._render_calendar()
        self.next_calendar_surface = temp_calendar_app.calendar_surface

        self.animating = True
        self.animation_direction = direction
        self.animation_start_time = time.time()
