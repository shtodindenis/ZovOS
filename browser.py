import pygame
import time
import sys
import random
import os
import sqlite3
import threading

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


def refresh_settings_from_db(files):
    global current_background_setting, background_image, icon_layout_setting, current_theme_setting, text_color
    current_background_setting = get_setting(
        'background_image', 'zovosbg.png')
    background_image = get_background_image(current_background_setting)
    icon_layout_setting = get_setting('icon_layout', 'grid')
    current_theme_setting = get_setting('theme', 'light')

    update_theme_colors()

    if icon_layout_setting == 'grid':
        grid_size = 108 + 20
        for file in files:
            file.rect.topleft = file.get_grid_position(
                grid_size)
            file.name_rect.center = (
                file.rect.centerx, file.rect.bottom + 20)
            file.update_selection_rect()
            file.update_name_surface()
    elif icon_layout_setting == 'free':
        pass


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


class BrowserApp:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.address_bar_rect = pygame.Rect(10, 10, self.width - 20, 30)
        self.address_bar_text = "zov://"
        self.content_rect = pygame.Rect(
            10, 50, self.width - 20, self.height - 60)
        self.text_input_active = False
        self.cursor_visible = True
        self.cursor_time = pygame.time.get_ticks()
        self.cursor_pos = 0
        self.site_content = None
        self.functions = {}
        self.button_elements = []
        self.scroll_y = 0
        self.content_height = 0
        self.image_cache = {}
        self.site_variables = {}
        self.background_color = light_blue_grey
        self.startup_function_code = None

    def parse_site_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return ["Не удалось загрузить сайт."], {}

        parsed_content = []
        lines = content.splitlines()
        tags_section = False
        functions = {}
        function_name = None
        function_code_lines = []
        parsing_function = False
        self.background_color = light_blue_grey
        startup_code_lines = []
        parsing_startup_function = False

        for line in lines:
            line = line.strip()
            if not line or line.startswith("&&"):
                continue

            if line.startswith("@") and line.endswith("{"):
                function_name = line[1:-1].strip()
                function_code_lines = []
                parsing_function = True
                parsing_startup_function = False
                continue
            elif line == "}":
                if parsing_function and function_name:
                    functions[function_name] = "\n".join(function_code_lines)
                    parsing_function = False
                    function_name = None
                elif parsing_startup_function:
                    self.startup_function_code = "\n".join(startup_code_lines)
                    parsing_startup_function = False
                continue
            elif parsing_function:
                function_code_lines.append(line)
                continue
            elif line.startswith("%start") and line.endswith("{"):
                startup_code_lines = []
                parsing_startup_function = True
                continue
            elif parsing_startup_function:
                startup_code_lines.append(line)
                continue

            if line == "[TAGS]":
                tags_section = True
                continue
            elif line == "[/TAGS]":
                tags_section = False
                continue
            elif line.startswith("[TEXT") and line.endswith("]"):
                tag_content_start = line.find("]") + 1
                tag_content_end = line.rfind("[/TEXT]")
                if tag_content_end == -1:
                    tag_content = line[tag_content_start:]
                else:
                    tag_content = line[tag_content_start:tag_content_end].strip(
                    )

                attrs_str = line[line.find(
                    "(")+1:line.find(")")] if "(" in line and ")" in line else ""
                attrs = {}
                for attr_pair in attrs_str.split(";"):
                    if "=" in attr_pair:
                        parts = attr_pair.split("=")
                        if len(parts) == 2:
                            key, value = parts
                            attrs[key.strip()] = value.strip()

                parsed_content.append(
                    {'tag': 'TEXT', 'text': tag_content, 'attrs': attrs})
                continue
            elif line == "[/TEXT]":
                continue
            elif line.startswith("[IMG") and line.endswith("[/IMG]"):
                attrs_str = line[line.find(
                    "(")+1:line.find(")")] if "(" in line and ")" in line else ""
                attrs = {}
                for attr_pair in attrs_str.split(";"):
                    if "=" in attr_pair:
                        parts = attr_pair.split("=")
                        if len(parts) == 2:
                            key, value = parts
                            attrs[key.strip()] = value.strip().strip(
                                "'").strip('"')

                link = attrs.get('link')
                if link:
                    parsed_content.append(
                        {'tag': 'IMG', 'link': link, 'attrs': attrs})
                continue
            elif line == "[/IMG]":
                continue
            elif line.startswith("[BUTTON") and line.endswith("[/BUTTON]"):
                tag_content_start = line.find("]") + 1
                tag_content_end = line.rfind("[/BUTTON]")
                if tag_content_end == -1:
                    button_text = line[tag_content_start:]
                else:
                    button_text = line[tag_content_start:tag_content_end].strip(
                    )

                attrs_str = line[line.find(
                    "(")+1:line.find(")")] if "(" in line and ")" in line else ""
                attrs = {}
                for attr_pair in attrs_str.split(";"):
                    if "=" in attr_pair:
                        parts = attr_pair.split("=")
                        if len(parts) == 2:
                            key, value = parts
                            attrs[key.strip()] = value.strip().strip(
                                "'").strip('"')

                parsed_content.append(
                    {'tag': 'BUTTON', 'text': button_text, 'attrs': attrs})
                continue
            elif line == "[/BUTTON]":
                continue

            if tags_section:
                if "=" in line:
                    key, value_comment = line.split("=", 1)
                    value = value_comment.split(
                        "&&")[0].strip().strip("'").strip()
                    key_strip = key.strip()
                    if key_strip == "$name":
                        parsed_content.insert(
                            0, {'tag': 'NAME', 'text': value})
                    elif key_strip == "$color":
                        self.background_color = self.parse_color(
                            value)

        return parsed_content, functions

    def parse_color(self, color_str):
        color_str = color_str.lower()
        if color_str == "red":
            return red
        elif color_str == "blue":
            return blue
        elif color_str == "green":
            return green
        elif color_str == "yellow":
            return yellow
        elif color_str == "white":
            return white
        elif color_str == "black":
            return black
        elif color_str == "orange":
            return orange
        elif color_str.startswith("#"):
            try:
                return pygame.Color(color_str)
            except ValueError:
                return light_blue_grey
        elif "," in color_str:
            try:
                rgb = [int(c.strip()) for c in color_str.split(",")]
                if len(rgb) == 3 and all(0 <= x <= 255 for x in rgb):
                    return tuple(rgb)
                else:
                    return light_blue_grey
            except ValueError:
                return light_blue_grey
        else:
            return light_blue_grey

    def render_site_content(self, content, screen_surface, scroll_y):
        y_offset = 10 - scroll_y
        line_spacing = 5
        content_width = screen_surface.get_width() - 20
        content_height_limit = screen_surface.get_height() - 20
        x_margin = 10
        total_height = 0
        button_elements = []

        for item in content:
            if item['tag'] == 'NAME':
                draw_text(screen_surface, item['text'], browser_font, text_color, (screen_surface.get_width(
                ) // 2, y_offset + browser_font.get_height() // 2), 'center')
                name_surface = browser_font.render(
                    item['text'], True, text_color)
                y_offset += name_surface.get_height() + line_spacing + 10
                total_height += name_surface.get_height() + line_spacing + 10
            elif item['tag'] == 'TEXT':
                text = item['text']
                attrs = item['attrs']
                element_id = attrs.get('id')
                color = attrs.get('color', 'black')
                align = attrs.get('align', 'left')
                font_size = int(attrs.get('size', 24))
                font_name = attrs.get('font', font_path)
                hidden = attrs.get('hidden', 'false').lower() == 'true'

                if hidden:
                    continue

                text_color_final = text_color
                if color == 'red':
                    text_color_final = red
                elif color == 'blue':
                    text_color_final = blue
                elif color == 'green':
                    text_color_final = green
                elif color == 'yellow':
                    text_color_final = yellow
                elif color == 'white':
                    text_color_final = white
                elif color == 'black':
                    text_color_final = black

                current_font = get_font(font_name, font_size)

                words = text.split(' ')
                lines = []
                current_line = ""

                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    text_surface = current_font.render(
                        test_line, True, text_color_final)
                    if text_surface.get_width() <= content_width:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                lines.append(current_line)

                for line in lines:
                    text_surface = current_font.render(
                        line, True, text_color_final)
                    text_rect = text_surface.get_rect(
                        topleft=(x_margin, y_offset))
                    if align == 'center':
                        text_rect.centerx = screen_surface.get_width() // 2
                    elif align == 'right':
                        text_rect.right = screen_surface.get_width() - x_margin
                    screen_surface.blit(text_surface, text_rect)
                    y_offset += text_surface.get_height() + line_spacing
                    total_height += text_surface.get_height() + line_spacing
            elif item['tag'] == 'IMG':
                link = item['link']
                attrs = item['attrs']
                align = attrs.get('align', 'left')
                width_percent_str = attrs.get('width')
                height_percent_str = attrs.get('height')
                hidden = attrs.get('hidden', 'false').lower() == 'true'

                if hidden:
                    continue

                try:
                    if link not in self.image_cache:
                        image = pygame.image.load(
                            os.path.join("images", link)).convert_alpha()
                        self.image_cache[link] = image
                    image = self.image_cache[link]
                    original_image_size = image.get_size()
                    image_rect = image.get_rect()

                    if width_percent_str and width_percent_str.endswith('%'):
                        try:
                            width_percent = int(width_percent_str[:-1])
                            image_width = int(
                                content_width * (width_percent / 100.0))
                            if height_percent_str and height_percent_str.lower() == 'auto':
                                image_height = int(
                                    image_width * (original_image_size[1] / original_image_size[0]))
                            elif height_percent_str and height_percent_str.endswith('%'):
                                try:
                                    height_percent = int(
                                        height_percent_str[:-1])
                                    image_height = int(
                                        content_height_limit * (height_percent / 100.0))
                                except ValueError:
                                    image_height = original_image_size[1]
                            else:
                                image_height = original_image_size[1]
                            image = pygame.transform.scale(
                                image, (image_width, image_height))
                            image_rect = image.get_rect()

                        except ValueError:
                            pass

                    image_rect.topleft = (x_margin, y_offset)

                    if align == 'center':
                        image_rect.centerx = screen_surface.get_width() // 2
                    elif align == 'right':
                        image_rect.right = screen_surface.get_width() - x_margin

                    screen_surface.blit(image, image_rect)
                    y_offset += image_rect.height + line_spacing
                    total_height += image_rect.height + line_spacing
                except FileNotFoundError:
                    error_surface = browser_content_font.render(
                        f"Error loading image: {link}", True, red)
                    error_rect = error_surface.get_rect(
                        topleft=(x_margin, y_offset))
                    screen_surface.blit(error_surface, error_rect)
                    y_offset += error_rect.height + line_spacing
                    total_height += error_rect.height + line_spacing
            elif item['tag'] == 'BUTTON':
                button_text = item['text']
                attrs = item['attrs']
                button_width = int(attrs.get('width', '100'))
                button_height = int(attrs.get('height', '30'))
                font_name = attrs.get('font', font_path)
                font_size = int(attrs.get('size', '20'))
                border_radius = int(attrs.get('radius', '0'))
                border_width = int(attrs.get('border', '1'))
                hidden = attrs.get('hidden', 'false').lower() == 'true'
                align = attrs.get('align', 'left')
                button_text_color_str = attrs.get(
                    'color', 'black')

                if hidden:
                    continue

                button_rect = pygame.Rect(
                    x_margin, y_offset, button_width, button_height)

                if align == 'center':
                    button_rect.centerx = content_width // 2 + x_margin
                elif align == 'right':
                    button_rect.right = content_width + x_margin

                draw_rect(screen_surface, window_color,
                          button_rect, border_radius=border_radius)
                draw_rect(screen_surface, black, button_rect,
                          border_width, border_radius=border_radius)

                current_font = get_font(font_name, font_size)

                button_text_color = text_color
                if button_text_color_str == 'white':
                    button_text_color = white
                elif button_text_color_str == 'black':
                    button_text_color = black

                draw_text(screen_surface, button_text, current_font,
                          button_text_color, button_rect.center, 'center')

                command_name = attrs.get('command')

                button_element_info = {
                    'rect': button_rect,
                    'command': command_name if command_name else None,
                    'attrs': attrs
                }
                button_elements.append(button_element_info)

                y_offset += button_height + line_spacing
                total_height += button_height + line_spacing

        return total_height, button_elements

    def setattribute(self, element_id, attribute, value):
        if self.site_content:
            for item in self.site_content:
                if 'attrs' in item and 'id' in item['attrs'] and item['attrs']['id'] == element_id:
                    item['attrs'][attribute] = value
                    if item['tag'] == 'TEXT':
                        item['text'] = value
                    elif item['tag'] == 'BUTTON':
                        item['text'] = value
                    return

    def setvariable(self, var_name, var_value):
        self.site_variables[var_name] = var_value

    def getvariable(self, var_name):
        return self.site_variables.get(var_name)

    def execute_startup_function(self):
        if self.startup_function_code:
            try:
                local_vars = {
                    'setattribute': self.setattribute,
                    'setvariable': self.setvariable,
                    'getvariable': self.getvariable
                }
                exec(self.startup_function_code, globals(), local_vars)
            except Exception as e:
                print(f"Error executing startup function: {e}")

    def draw(self, screen_surface):
        self.address_bar_rect.width = screen_surface.get_width() - 20
        self.content_rect.width = screen_surface.get_width() - 20
        self.content_rect.height = screen_surface.get_height() - 60

        draw_rect(screen_surface, window_color, self.address_bar_rect)
        draw_rect(screen_surface, black, self.address_bar_rect, 1)
        draw_text(screen_surface, self.address_bar_text, browser_font, text_color,
                  (self.address_bar_rect.x + 5, self.address_bar_rect.y + 5), 'topleft')

        draw_rect(screen_surface, self.background_color, self.content_rect)
        draw_rect(screen_surface, black, self.content_rect, 1)

        content_surface = pygame.Surface(
            self.content_rect.size, pygame.SRCALPHA)
        content_surface.fill(self.background_color)

        if self.site_content:
            self.content_height, self.button_elements = self.render_site_content(
                self.site_content, content_surface, self.scroll_y)
            screen_surface.blit(content_surface, self.content_rect.topleft)

        if self.text_input_active:
            if pygame.time.get_ticks() - self.cursor_time > 500:
                self.cursor_visible = not self.cursor_visible
                self.cursor_time = pygame.time.get_ticks()

            if self.cursor_visible:
                cursor_x = self.address_bar_rect.x + 5 + \
                    browser_font.size(
                        self.address_bar_text[:self.cursor_pos])[0]
                cursor_y = self.address_bar_rect.y + 5
                pygame.draw.line(screen_surface, text_color, (cursor_x, cursor_y),
                                 (cursor_x, cursor_y + browser_font.get_height()), 2)

    def handle_event(self, event, window_rect):
        if event.type == pygame.MOUSEBUTTONDOWN:
            relative_mouse_pos = (
                event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
            if event.button == 1:
                if self.address_bar_rect.collidepoint(relative_mouse_pos):
                    self.text_input_active = True
                    self.cursor_visible = True
                    self.cursor_time = pygame.time.get_ticks()
                    click_pos_local_x = relative_mouse_pos[0] - (
                        self.address_bar_rect.x + 5)
                    char_width = browser_font.size(
                        " ")[0]
                    if char_width > 0:
                        self.cursor_pos = max(
                            0, int(click_pos_local_x / char_width))
                    else:
                        self.cursor_pos = len(self.address_bar_text)
                else:
                    self.text_input_active = False
                if self.site_content:
                    content_surface_offset = self.content_rect.topleft
                    relative_mouse_pos_in_content = (
                        relative_mouse_pos[0] - content_surface_offset[0], relative_mouse_pos[1] - content_surface_offset[1] + self.scroll_y)
                    if self.button_elements:
                        for button_element in self.button_elements:
                            if button_element['rect'].collidepoint(relative_mouse_pos_in_content):
                                command_name = button_element['command']
                                if command_name and command_name in self.functions:
                                    function_code = self.functions[command_name]
                                    try:
                                        local_vars = {
                                            'attrs': button_element['attrs'],
                                            'setattribute': self.setattribute,
                                            'setvariable': self.setvariable,
                                            'getvariable': self.getvariable
                                        }
                                        exec(function_code,
                                             globals(), local_vars)
                                    except Exception as e:
                                        pass
                                break
            elif event.button == 4:
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.button == 5:
                self.scroll_y = min(
                    self.content_height - self.content_rect.height, self.scroll_y + 30)
        elif event.type == pygame.KEYDOWN and self.text_input_active:
            if event.key == pygame.K_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)
            elif event.key == pygame.K_RIGHT:
                self.cursor_pos = min(
                    len(self.address_bar_text), self.cursor_pos + 1)
            elif event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    self.address_bar_text = self.address_bar_text[:self.cursor_pos -
                                                                  1] + self.address_bar_text[self.cursor_pos:]
                    self.cursor_pos -= 1
            elif event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.address_bar_text):
                    self.address_bar_text = self.address_bar_text[:self.cursor_pos] + \
                        self.address_bar_text[self.cursor_pos+1:]
            elif event.key == pygame.K_RETURN:
                url = self.address_bar_text.lower()
                if url.startswith("zov://"):
                    site_name = url[6:]
                    site_path = os.path.join("sites", site_name)
                    if os.path.exists(site_path):
                        self.site_variables = {}
                        self.site_content, self.functions = self.parse_site_file(
                            site_path)
                        self.scroll_y = 0

                        if self.site_content:
                            self.execute_startup_function()

                    else:
                        self.site_content = ["Сайт не найден."], {}
                        self.scroll_y = 0
                else:
                    self.site_content = ["Неверный адрес."], {}
                    self.scroll_y = 0
                self.text_input_active = False
            elif event.unicode:
                self.address_bar_text = self.address_bar_text[:self.cursor_pos] + \
                    event.unicode + self.address_bar_text[self.cursor_pos:]
                self.cursor_pos += 1

            self.cursor_visible = True
            self.cursor_time = pygame.time.get_ticks()
