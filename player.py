import pygame
import random
import time
import math
import sqlite3
import os  # Import the os module

white = (255, 255, 255)
black = (0, 0, 0)
dark_gray = (30, 30, 30)
light_gray = (150, 150, 150)
bright_red = (255, 0, 0)
red = (255, 0, 0)
green = (0, 200, 0)
transparent_white = (255, 255, 255, 100)

play_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.polygon(play_icon, light_gray, [(5, 5), (25, 15), (5, 25)])
pause_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.rect(pause_icon, light_gray, (5, 5, 8, 20))
pygame.draw.rect(pause_icon, light_gray, (17, 5, 8, 20))
stop_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.rect(stop_icon, light_gray, (5, 5, 20, 20))


def draw_text(text, color, rect, surface, text_font, aa=True, bkg=None):
    y = rect.top
    line_spacing = -2

    font_height = text_font.size("Tg")[1]

    while text:
        i = 1
        if y + font_height > rect.bottom:
            break
        while text_font.size(text[:i])[0] < rect.width and i < len(text):
            i += 1
        if i < len(text):
            i = text.rfind(" ", 0, i) + 1
        if bkg:
            image = text_font.render(text[:i], 1, color, bkg)
            image.set_colorkey(bkg)
        else:
            image = text_font.render(text[:i], aa, color)

        surface.blit(image, (rect.left, y))
        y += font_height + line_spacing
        text = text[i:]


def generate_error():
    errors = [
        "ERROR: File not found",
        "ERROR: Invalid audio format",
        "ERROR: Memory access violation",
        "ERROR: System instability detected",
        "WARNING: Unknown entity encountered",
        "FATAL ERROR: Core meltdown imminent",
        "ERROR: Temporal anomaly detected",
        "ERROR: 404 Universe Not Found",
        "ERROR: Divide By Cucumber Error. Please Reinstall Universe And Reboot",
        "ERROR: Segmentation fault (core dumped)",
        "ERROR: OutOfCheeseError: Redo from start",
        "ERROR: [REDACTED]",
        "ERROR: 🤪",
        "ERROR: Please insert your soul into USB port.",
        "ERROR: Not enough mana",
        "ERROR: NullPointerException",
        "ERROR: Blue Screen of Death",
        "ERROR: Your computer has run into a problem and needs to restart.",
        "ERROR: Unexpected error occurred",
        "ERROR: Failed to load resource",
        "ERROR: Connection to server lost",
    ]
    return random.choice(errors)


def draw_glitch(surface, intensity=5):
    for _ in range(intensity):
        x = random.randint(0, surface.get_width())
        y = random.randint(0, surface.get_height())
        w = random.randint(10, 100)
        h = random.randint(5, 20)
        color = random.choice([red, bright_red, black, (0, 255, 0)])
        pygame.draw.rect(surface, color, (x, y, w, h))


def play_error_sound():
    global error_sound, error_sound_timer
    error_sound = True
    error_sound_timer = time.time()


def create_repair_items(width, height, game_font, repair_stage):
    repair_items = []
    target_positions = {}
    base_velocity = 2
    if repair_stage == 1:
        velocity_multiplier = 0.75
    elif repair_stage == 2:
        velocity_multiplier = 1.5
    elif repair_stage == 3:
        velocity_multiplier = 3
    else:
        velocity_multiplier = 1

    text = "ВЯЧПЛЕЕР"
    text_surface = game_font.render(text, True, white)
    text_rect = text_surface.get_rect(
        topleft=(40, 40))
    for i, char in enumerate(text):
        char_surface = game_font.render(char, True, white)
        char_rect = char_surface.get_rect(topleft=(random.randint(
            50, width - 50), random.randint(50, height - 100)))
        target_x = text_rect.left + text_surface.get_rect().width / len(text) * i
        target_y = text_rect.top
        velocity_x = random.uniform(-base_velocity * velocity_multiplier,
                                    base_velocity * velocity_multiplier)
        velocity_y = random.uniform(-base_velocity * velocity_multiplier,
                                    base_velocity * velocity_multiplier)
        repair_items.append(
            (char_surface, char_rect, "char", i, False, target_x, target_y, velocity_x, velocity_y))
        target_positions[(char_surface, "char", i)] = target_x, target_y

    controls_y = height - 80
    play_button_rect = pygame.Rect(width // 2 - 15, controls_y + 15, 30, 30)
    stop_button_rect = pygame.Rect(width // 2 - 65, controls_y + 15, 30, 30)
    rewind_button_rect = pygame.Rect(width // 2 - 115, controls_y + 15, 30, 30)
    forward_button_rect = pygame.Rect(width // 2 + 35, controls_y + 15, 30, 30)
    volume_rect = pygame.Rect(width - 150, controls_y + 15, 100, 30)
    timeline_rect = pygame.Rect(50, controls_y - 15, width - 100, 10)

    icons = [(play_icon, play_button_rect.center, "play_icon"),
             (stop_icon, stop_button_rect.center, "stop_icon"),
             (pygame.Surface((30, 30), pygame.SRCALPHA),
              rewind_button_rect.center, "rewind_icon"),
             (pygame.Surface((30, 30), pygame.SRCALPHA),
              forward_button_rect.center, "forward_icon"),
             (pygame.Surface((100, 30), pygame.SRCALPHA),
              volume_rect.center, "volume_icon"),
             (pygame.Surface((width - 100, 10), pygame.SRCALPHA),
              timeline_rect.center, "timeline_icon")
             ]
    for i, (icon, pos, type) in enumerate(icons):
        if type == "rewind_icon":
            pygame.draw.polygon(icon, light_gray, [(15, 15 - 8),
                                                   (15, 15 + 8),
                                                   (15 - 8, 15)])
            pygame.draw.polygon(icon, light_gray, [(15 + 9, 15 - 8),
                                                   (15 + 9, 15 + 8),
                                                   (15, 15)])

        if type == "forward_icon":
            pygame.draw.polygon(icon, light_gray, [(15, 15 - 8),
                                                   (15, 15 + 8),
                                                   (15 + 8, 15)])
            pygame.draw.polygon(icon, light_gray, [(15 - 9, 15 - 8),
                                                   (15 - 9, 15 + 8),
                                                   (15, 15)])
        elif type == "volume_icon":
            pygame.draw.rect(icon, light_gray, (0, 0, 100, 30))
            pygame.draw.circle(icon, green, (30, 15), 7)

        elif type == "timeline_icon":
            pygame.draw.rect(icon, light_gray, (0, 0, width - 100, 10))
        icon_rect = icon.get_rect(center=(random.randint(
            50, width - 50), random.randint(50, height - 100)))
        velocity_x = random.uniform(-base_velocity * velocity_multiplier,
                                    base_velocity * velocity_multiplier)
        velocity_y = random.uniform(-base_velocity * velocity_multiplier,
                                    base_velocity * velocity_multiplier)
        repair_items.append((icon, icon_rect, type, i, False,
                            pos[0], pos[1], velocity_x, velocity_y))
        target_positions[(icon, type, i)] = pos[0], pos[1]
    return repair_items, target_positions


def draw_target_indicator(surface, pos, size):
    x, y = pos
    w, h = size
    center_x = x
    center_y = y

    time_now = pygame.time.get_ticks()
    phase = (math.sin(time_now / 200.0) + 1) / 2

    color = (int(transparent_white[0] * phase),
             int(transparent_white[1] * phase),
             int(transparent_white[2] * phase),
             transparent_white[3])

    indicator_surface = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(indicator_surface, color, (0, 0, w, h), border_radius=5)

    surface.blit(indicator_surface, (center_x - w // 2, center_y - h // 2))


class Minigame:
    def __init__(self, rect, game_font, console_font):
        self.rect = rect
        self.game_font = game_font
        self.console_font = console_font
        self.playing = False
        self.show_console = False
        self.console_width = 350
        self.console_messages = []
        self.last_error_time = 0
        self.glitch_effect = False
        self.glitch_start_time = 0
        self.error_sound = False
        self.error_sound_timer = 0
        self.game_started = False
        self.repair_mode = False
        self.repair_items = []
        self.repaired_items = 0
        self.target_positions = {}
        self.dragging_item = None
        self.offset_x = 0
        self.offset_y = 0
        self.repair_complete = False
        self.timeline_progress = 0
        self.music_track_length = 120
        self.first_repair_complete = False
        self.vyacheslav_message = False
        self.vyacheslav_message_start_time = 0
        self.second_repair_complete = False
        self.third_repair_complete = False
        self.second_repair_message = False
        self.second_repair_message_start_time = 0
        self.post_second_repair_message = False

        self.hand_smash = False
        self.hand_smash_start_time = 0
        self.hand_smash_image = pygame.image.load(os.path.join(
            "images", "hand_smash.png"))  # Load from images folder
        self.hand_smash_initial_image = self.hand_smash_image.copy()
        self.hand_smash_image = pygame.transform.scale(
            self.hand_smash_image, (150, 150))
        self.hand_smash_center = None
        self.hand_smash_anim_duration = 1.5

        self.hand_enlarge_anim = False
        self.redden_anim = False
        self.explosion_anim = False
        self.anim_start_time = 0
        self.hand_initial_size = (150, 150)
        self.hand_target_size = (
            int(150 * 1.5), int(150 * 1.5))
        self.boom_image = pygame.image.load(os.path.join(
            "images", "boom.png")).convert_alpha()  # Load from images folder
        self.boom_scale = 0
        self.boom_alpha = 255
        self.explosion_duration = 0.5

        self.item_scatter_velocities = {}

        self.post_repair_time = 0
        self.post_repair_duration = 3

        self.controls_y = self.rect.height - 80
        self.play_button_rect = pygame.Rect(
            self.rect.width // 2 - 15, self.controls_y + 15, 30, 30)
        self.stop_button_rect = pygame.Rect(
            self.rect.width // 2 - 65, self.controls_y + 15, 30, 30)
        self.rewind_button_rect = pygame.Rect(
            self.rect.width // 2 - 115, self.controls_y + 15, 30, 30)
        self.forward_button_rect = pygame.Rect(
            self.rect.width // 2 + 35, self.controls_y + 15, 30, 30)
        self.volume_rect = pygame.Rect(
            self.rect.width - 150, self.controls_y + 15, 100, 30)
        self.timeline_rect = pygame.Rect(
            50, self.controls_y - 15, self.rect.width - 100, 10)

        self.repair_stage = 1

        self.db_conn = sqlite3.connect('minigame_progress.db')
        self.db_cursor = self.db_conn.cursor()
        self.create_tables()
        self.load_game_state()
        # Glitch effect on minigame start
        self.glitch_effect = True
        self.glitch_start_time = time.time()

    def create_tables(self):
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_started BOOLEAN,
                repair_mode BOOLEAN,
                first_repair_complete BOOLEAN,
                second_repair_complete BOOLEAN,
                third_repair_complete BOOLEAN,
                repaired_items INTEGER,
                timeline_progress REAL,
                show_console BOOLEAN,
                playing BOOLEAN,
                repair_stage INTEGER,
                second_repair_message BOOLEAN,
                post_second_repair_message BOOLEAN
            )
        ''')
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS repair_item_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_state_id INTEGER,
                item_type TEXT,
                item_index INTEGER,
                is_repaired BOOLEAN,
                FOREIGN KEY (game_state_id) REFERENCES game_state(id)
            )
        ''')
        self.db_conn.commit()

    def save_game_state(self):
        self.db_cursor.execute("DELETE FROM game_state")
        self.db_cursor.execute("DELETE FROM repair_item_state")

        self.db_cursor.execute('''
            INSERT INTO game_state (game_started, repair_mode, first_repair_complete, second_repair_complete, third_repair_complete,
                                    repaired_items, timeline_progress, show_console, playing, repair_stage, second_repair_message, post_second_repair_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.game_started, self.repair_mode, self.first_repair_complete, self.second_repair_complete, self.third_repair_complete,
              self.repaired_items, self.timeline_progress, self.show_console, self.playing, self.repair_stage, self.second_repair_message, self.post_second_repair_message))
        game_state_id = self.db_cursor.lastrowid

        for item, rect, type, index, is_repaired, target_x, target_y, _, _ in self.repair_items:
            self.db_cursor.execute('''
                INSERT INTO repair_item_state (game_state_id, item_type, item_index, is_repaired)
                VALUES (?, ?, ?, ?)
            ''', (game_state_id, type, index, is_repaired))
        self.db_conn.commit()

    def load_game_state(self):
        self.db_cursor.execute(
            "SELECT * FROM game_state ORDER BY id DESC LIMIT 1")
        game_state_data = self.db_cursor.fetchone()

        if game_state_data:
            (state_id, self.game_started, self.repair_mode, self.first_repair_complete,
             self.second_repair_complete, self.third_repair_complete, self.repaired_items, self.timeline_progress,
             self.show_console, self.playing, self.repair_stage, self.second_repair_message, self.post_second_repair_message) = game_state_data

            if self.repair_mode or self.first_repair_complete or self.second_repair_complete or self.third_repair_complete:
                self.repair_items, self.target_positions = create_repair_items(
                    self.rect.width, self.rect.height, self.game_font, self.repair_stage)

                self.db_cursor.execute(
                    "SELECT * FROM repair_item_state WHERE game_state_id = ?", (state_id,))
                repair_item_data = self.db_cursor.fetchall()
                repaired_items_dict = {}
                for item_state in repair_item_data:
                    _, _, item_type, item_index, is_repaired = item_state
                    repaired_items_dict[(item_type, item_index)] = is_repaired

                updated_repair_items = []
                for item, rect, type, index, _, target_x, target_y, vx, vy in self.repair_items:
                    is_repaired = repaired_items_dict.get(
                        (type, index), False)
                    updated_repair_items.append(
                        (item, rect, type, index, is_repaired, target_x, target_y, vx, vy))
                self.repair_items = updated_repair_items
                self.repaired_items = sum(
                    1 for item in self.repair_items if item[4])
            if self.show_console:
                self.play_button_rect.x -= self.console_width // 2
                self.stop_button_rect.x -= self.console_width // 2
                self.rewind_button_rect.x -= self.console_width // 2
                self.forward_button_rect.x -= self.console_width // 2
                self.volume_rect.x -= self.console_width // 2
                self.timeline_rect.x -= self.console_width // 2

    def draw(self, surface):
        surface_color = dark_gray
        if self.redden_anim:
            redden_progress = min(
                1, (time.time() - self.anim_start_time) / 1.0)
            surface_color = (dark_gray[0] + int((255 - dark_gray[0]) * redden_progress), dark_gray[1] - int(
                dark_gray[1] * redden_progress), dark_gray[2] - int(dark_gray[2] * redden_progress))
            surface_color = tuple(max(0, min(255, int(c)))
                                  for c in surface_color)
        pygame.draw.rect(surface, surface_color,
                         (0, 0, self.rect.width, self.rect.height))

        if not self.repair_mode and not self.first_repair_complete and not self.post_repair_time and not self.second_repair_message and not self.post_second_repair_message:
            text_color = white
            if self.redden_anim:
                redden_progress = min(
                    1, (time.time() - self.anim_start_time) / 1.0)
                text_color = (white[0] + int((255 - white[0]) * redden_progress), white[1] - int(
                    white[1] * redden_progress), white[2] - int(white[2] * redden_progress))
                text_color = tuple(max(0, min(255, int(c)))
                                   for c in text_color)

            draw_text("ВЯЧПЛЕЕР", text_color, pygame.Rect(
                40, 40, 200, 50), surface, text_font=self.game_font)

        if not self.repair_mode and not self.first_repair_complete and not self.post_repair_time and not self.second_repair_message and not self.post_second_repair_message:
            controls_y = self.rect.height - 80
            self.play_button_rect = pygame.Rect(
                self.rect.width // 2 - 15, controls_y + 15, 30, 30)
            self.stop_button_rect = pygame.Rect(
                self.rect.width // 2 - 65, controls_y + 15, 30, 30)
            self.rewind_button_rect = pygame.Rect(
                self.rect.width // 2 - 115, controls_y + 15, 30, 30)
            self.forward_button_rect = pygame.Rect(
                self.rect.width // 2 + 35, controls_y + 15, 30, 30)
            self.volume_rect = pygame.Rect(
                self.rect.width - 150, controls_y + 15, 100, 30)
            self.timeline_rect = pygame.Rect(
                50, controls_y - 15, self.rect.width - 100, 10)

            controls_color = black
            if self.redden_anim:
                redden_progress = min(
                    1, (time.time() - self.anim_start_time) / 1.0)
                controls_color = (black[0] + int((255 - black[0]) * redden_progress), black[1] - int(
                    black[1] * redden_progress), black[2] - int(black[2] * redden_progress))
                controls_color = tuple(max(0, min(255, int(c)))
                                       for c in controls_color)

            pygame.draw.rect(
                surface, controls_color, (0, controls_y, self.rect.width, 60))

            progress_bar_width = self.timeline_rect.width * self.timeline_progress

            timeline_color = light_gray
            progress_color = green
            if self.redden_anim:
                redden_progress = min(
                    1, (time.time() - self.anim_start_time) / 1.0)
                timeline_color = (light_gray[0] + int((255 - light_gray[0]) * redden_progress), light_gray[1] - int(
                    light_gray[1] * redden_progress), light_gray[2] - int(light_gray[2] * redden_progress))
                progress_color = (green[0] + int((255 - green[0]) * redden_progress), green[1] - int(
                    green[1] * redden_progress), green[2] - int(green[2] * redden_progress))
                timeline_color = tuple(max(0, min(255, int(c)))
                                       for c in timeline_color)
                progress_color = tuple(max(0, min(255, int(c)))
                                       for c in progress_color)

            pygame.draw.rect(surface, timeline_color, self.timeline_rect)
            progress_bar_rect = pygame.Rect(self.timeline_rect.x, self.timeline_rect.y, int(progress_bar_width),
                                            self.timeline_rect.height)
            pygame.draw.rect(surface, progress_color, progress_bar_rect)

            icon_color = light_gray
            volume_slider_color = green
            if self.redden_anim:
                redden_progress = min(
                    1, (time.time() - self.anim_start_time) / 1.0)
                icon_color = (light_gray[0] + int((255 - light_gray[0]) * redden_progress), light_gray[1] - int(
                    light_gray[1] * redden_progress), light_gray[2] - int(light_gray[2] * redden_progress))
                volume_slider_color = (green[0] + int((255 - green[0]) * redden_progress), green[1] - int(
                    green[1] * redden_progress), green[2] - int(green[2] * redden_progress))
                icon_color = tuple(max(0, min(255, int(c)))
                                   for c in icon_color)
                volume_slider_color = tuple(
                    max(0, min(255, int(c))) for c in volume_slider_color)

            surface.blit(
                play_icon if not self.playing else pause_icon, self.play_button_rect)
            surface.blit(stop_icon, self.stop_button_rect)
            pygame.draw.polygon(surface, icon_color,
                                [(self.rewind_button_rect.centerx - 10, self.rewind_button_rect.centery - 8),
                                 (self.rewind_button_rect.centerx - 10,
                                  self.rewind_button_rect.centery + 8),
                                 (self.rewind_button_rect.centerx - 18, self.rewind_button_rect.centery)])
            pygame.draw.polygon(surface, icon_color,
                                [(self.rewind_button_rect.centerx - 1, self.rewind_button_rect.centery - 8),
                                 (self.rewind_button_rect.centerx - 1,
                                  self.rewind_button_rect.centery + 8),
                                 (self.rewind_button_rect.centerx - 9, self.rewind_button_rect.centery)])
            pygame.draw.polygon(surface, icon_color,
                                [(self.forward_button_rect.centerx + 10, self.forward_button_rect.centery - 8),
                                 (self.forward_button_rect.centerx + 10,
                                  self.forward_button_rect.centery + 8),
                                 (self.forward_button_rect.centerx + 18, self.forward_button_rect.centery)])
            pygame.draw.polygon(surface, icon_color,
                                [(self.forward_button_rect.centerx + 1, self.forward_button_rect.centery - 8),
                                 (self.forward_button_rect.centerx + 1,
                                  self.forward_button_rect.centery + 8),
                                 (self.forward_button_rect.centerx + 9, self.forward_button_rect.centery)])
            pygame.draw.rect(surface, icon_color, self.volume_rect)
            pygame.draw.circle(surface, volume_slider_color, (self.volume_rect.x +
                               30, self.volume_rect.centery), 7)
            text_vol_color = light_gray
            if self.redden_anim:
                redden_progress = min(
                    1, (time.time() - self.anim_start_time) / 1.0)
                text_vol_color = (light_gray[0] + int((255 - light_gray[0]) * redden_progress), light_gray[1] - int(
                    light_gray[1] * redden_progress), light_gray[2] - int(light_gray[2] * redden_progress))
                text_vol_color = tuple(max(0, min(255, int(c)))
                                       for c in text_vol_color)
            draw_text("VOL", text_vol_color, pygame.Rect(self.volume_rect.x - 45, self.volume_rect.y, 45, 30), surface,
                      text_font=self.game_font)

        if self.show_console and not self.first_repair_complete and not self.second_repair_message and not self.post_second_repair_message:
            console_rect = pygame.Rect(
                self.rect.width - self.console_width, 0, self.console_width, self.rect.height)
            if not self.repair_mode:
                console_bg_color = (20, 20, 20)
                if self.redden_anim:
                    redden_progress = min(
                        1, (time.time() - self.anim_start_time) / 1.0)
                    console_bg_color = (console_bg_color[0] + int((255 - console_bg_color[0]) * redden_progress), console_bg_color[1] - int(
                        console_bg_color[1] * redden_progress), console_bg_color[2] - int(console_bg_color[2] * redden_progress))
                    console_bg_color = tuple(
                        max(0, min(255, int(c))) for c in console_bg_color)
                pygame.draw.rect(surface, console_bg_color, console_rect)

            if not self.game_started:
                current_time = time.time()
                if current_time - self.last_error_time > random.uniform(1, 2):
                    self.console_messages.append(generate_error())
                    self.last_error_time = current_time

                if len(self.console_messages) > 15:
                    self.game_started = True
                    self.repair_mode = True
                    self.repair_items, self.target_positions = create_repair_items(
                        self.rect.width, self.rect.height, self.game_font, self.repair_stage)
                    self.console_messages = ["SYSTEM: Repair mode activated.",
                                             "SYSTEM: Fix the audio player to proceed."
                                             ]
                    self.save_game_state()

                text_rect = pygame.Rect(console_rect.x + 10, console_rect.y + 10, self.console_width - 20,
                                        self.rect.height - 20)
                available_height = text_rect.height
                line_height = self.console_font.get_linesize()
                max_lines_in_console = available_height // line_height

                lines_to_draw = self.console_messages[-max_lines_in_console:]

                text_y = text_rect.y
                for line in lines_to_draw:
                    text_console_color = red
                    if self.redden_anim:
                        redden_progress = min(
                            1, (time.time() - self.anim_start_time) / 1.0)
                        text_console_color = (red[0] + int((255 - red[0]) * redden_progress), red[1] - int(
                            red[1] * redden_progress), red[2] - int(red[2] * redden_progress))
                        text_console_color = tuple(
                            max(0, min(255, int(c))) for c in text_console_color)
                    draw_text(line, text_console_color, pygame.Rect(text_rect.x, text_y, text_rect.width, line_height), surface,
                              text_font=self.console_font)
                    text_y += line_height

        if self.repair_mode and not self.hand_smash and not self.explosion_anim:
            for i, (item, rect, type, index, is_repaired, target_x, target_y, velocity_x, velocity_y) in enumerate(self.repair_items):
                if not is_repaired:
                    rect.x += velocity_x
                    rect.y += velocity_y

                    if rect.left < 0 or rect.right > self.rect.width:
                        velocity_x *= -1
                    if rect.top < 0 or rect.bottom > self.rect.height:
                        velocity_y *= -1
                    self.repair_items[i] = (
                        item, rect, type, index, is_repaired, target_x, target_y, velocity_x, velocity_y)

        if self.repair_mode:
            for item, rect, type, index, is_repaired, target_x, target_y, _, _ in self.repair_items:
                if not is_repaired:
                    item_surface = item
                    if self.redden_anim:
                        item_surface = item.copy()
                        red_tint = pygame.Surface(
                            item_surface.get_size(), pygame.SRCALPHA)
                        redden_progress = min(
                            1, (time.time() - self.anim_start_time) / 1.0)
                        red_color = (int(255 * redden_progress), 0,
                                     0, int(255 * redden_progress))
                        red_tint.fill(red_color)
                        item_surface.blit(red_tint, (0, 0),
                                          special_flags=pygame.BLEND_RGBA_MULT)
                    surface.blit(item_surface, rect)

                if self.dragging_item and self.dragging_item[2] == type and self.dragging_item[3] == index:
                    target_item_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2,
                                                   item.get_width(), item.get_height())
                    draw_target_indicator(surface, target_item_rect.center,
                                          (item.get_width() + 10, item.get_height() + 10))

                if is_repaired:
                    target_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2,
                                              item.get_width(), item.get_height())
                    item_surface = item
                    if self.redden_anim:
                        item_surface = item.copy()
                        red_tint = pygame.Surface(
                            item_surface.get_size(), pygame.SRCALPHA)
                        redden_progress = min(
                            1, (time.time() - self.anim_start_time) / 1.0)
                        red_color = (int(255 * redden_progress), 0,
                                     0, int(255 * redden_progress))
                        red_tint.fill(red_color)
                        item_surface.blit(red_tint, (0, 0),
                                          special_flags=pygame.BLEND_RGBA_MULT)
                    surface.blit(item_surface, target_rect)

        if self.post_repair_time > 0:
            current_time = time.time()
            if current_time - self.post_repair_time < self.post_repair_duration:
                for item, rect, type, index, is_repaired, target_x, target_y, _, _ in self.repair_items:
                    target_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2,
                                              item.get_width(), item.get_height())
                    surface.blit(item, target_rect)
            else:
                self.post_repair_time = 0
                if self.repair_stage == 1:
                    self.repair_stage = 2
                elif self.repair_stage == 2:
                    self.repair_stage = 3
                else:
                    self.third_repair_complete = True

                if not self.third_repair_complete:
                    self.repair_items, self.target_positions = create_repair_items(
                        self.rect.width, self.rect.height, self.game_font, self.repair_stage)
                    self.repaired_items = 0
                    for i, (item, rect, type, index, is_repaired, target_x, target_y, _, _) in enumerate(self.repair_items):
                        rect.x = random.randint(50, self.rect.width - 50)
                        rect.y = random.randint(50, self.rect.height - 100)
                        velocity_x = random.uniform(-5, 5)
                        velocity_y = random.uniform(-5, 5)
                        self.repair_items[i] = (
                            item, rect, type, index, False, target_x, target_y, velocity_x, velocity_y)

                    self.repair_mode = True
                    self.save_game_state()
                else:
                    self.repair_mode = False
                    self.game_started = False
                    self.show_console = False
                    print("All repairs complete!")

        if self.vyacheslav_message:
            text_rect = pygame.Rect(
                self.rect.width//2-250, self.rect.height//2-20, 500, 40)
            text_vyach_color = red
            if self.redden_anim:
                redden_progress = min(
                    1, (time.time() - self.anim_start_time) / 1.0)
                text_vyach_color = (red[0] + int((255 - red[0]) * redden_progress), red[1] - int(
                    red[1] * redden_progress), red[2] - int(red[2] * redden_progress))
                text_vyach_color = tuple(max(0, min(255, int(c)))
                                         for c in text_vyach_color)

            draw_text("НЕТ, ЭТО ВСЁ ВАШИ ФАНТАЗИИ", text_vyach_color,
                      text_rect, surface, self.game_font)
            if time.time() - self.vyacheslav_message_start_time > 1.5 and not self.hand_enlarge_anim and not self.second_repair_message:
                self.vyacheslav_message = False
                self.hand_enlarge_anim = True
                self.redden_anim = True
                self.anim_start_time = time.time()
                self.hand_smash_center = (
                    self.rect.width // 2, self.rect.height // 2)
                self.item_scatter_velocities = {}

        if self.second_repair_message:
            text_rect = pygame.Rect(
                self.rect.width//2-350, self.rect.height//2-20, 700, 40)
            text_second_repair_color = red
            if self.redden_anim:
                redden_progress = min(
                    1, (time.time() - self.anim_start_time) / 1.0)
                text_second_repair_color = (red[0] + int((255 - red[0]) * redden_progress), red[1] - int(
                    red[1] * redden_progress), red[2] - int(red[2] * redden_progress))
                text_second_repair_color = tuple(max(0, min(255, int(c)))
                                                 for c in text_second_repair_color)

            draw_text("ЧТО ЗА РЕЗИСТОР ТЫ СДЕЛАЛ???", text_second_repair_color,
                      text_rect, surface, self.game_font)
            if time.time() - self.second_repair_message_start_time > 1.5 and not self.post_second_repair_message:
                self.second_repair_message = False
                self.post_second_repair_message = True

        if self.post_second_repair_message and not self.hand_enlarge_anim and not self.hand_smash and not self.explosion_anim:
            self.hand_enlarge_anim = True
            self.redden_anim = True
            self.anim_start_time = time.time()
            self.hand_smash_center = (
                self.rect.width // 2, self.rect.height // 2)
            self.item_scatter_velocities = {}
            self.post_second_repair_message = False

        if self.hand_enlarge_anim:
            anim_progress = min(1, (time.time() - self.anim_start_time) / 1.0)
            current_hand_size = (int(self.hand_initial_size[0] + (self.hand_target_size[0] - self.hand_initial_size[0]) * anim_progress),
                                 int(self.hand_initial_size[1] + (self.hand_target_size[1] - self.hand_initial_size[1]) * anim_progress))
            self.hand_smash_image = pygame.transform.scale(
                self.hand_smash_initial_image, current_hand_size)
            hand_smash_rect = self.hand_smash_image.get_rect(
                center=self.hand_smash_center)
            surface.blit(self.hand_smash_image, hand_smash_rect)

            if anim_progress >= 1:
                self.hand_enlarge_anim = False
                self.redden_anim = False
                self.explosion_anim = True
                self.anim_start_time = time.time()
                self.boom_scale = 0
                self.boom_alpha = 255
        if self.explosion_anim and not self.third_repair_complete:
            explosion_progress = min(
                1, (time.time() - self.anim_start_time) / self.explosion_duration)
            self.boom_scale = 2 * explosion_progress
            self.boom_alpha = 255 - int(255 * explosion_progress)

            boom_current_size = (int(self.boom_image.get_width(
            ) * self.boom_scale), int(self.boom_image.get_height() * self.boom_scale))
            boom_image_scaled = pygame.transform.scale(
                self.boom_image, boom_current_size)
            boom_image_scaled.set_alpha(self.boom_alpha)
            boom_rect = boom_image_scaled.get_rect(
                center=self.hand_smash_center)
            surface.blit(boom_image_scaled, boom_rect)

            if explosion_progress >= 1:
                self.explosion_anim = False
                self.hand_smash = True
                self.hand_smash_start_time = time.time()

                for i, (item, rect, type, index, is_repaired, target_x, target_y, _, _) in enumerate(self.repair_items):
                    if not is_repaired:
                        item_center = rect.center
                        direction = pygame.math.Vector2(
                            item_center[0] - self.hand_smash_center[0], item_center[1] - self.hand_smash_center[1])
                        if direction.length() == 0:
                            direction = pygame.math.Vector2(
                                random.uniform(-1, 1), random.uniform(-1, 1))
                        direction = direction.normalize()
                        scatter_speed = random.uniform(
                            10, 20)
                        self.item_scatter_velocities[i] = direction * \
                            scatter_speed
        else:
            self.explosion_anim = False

        if self.hand_smash:
            current_hand_smash_time = time.time() - self.hand_smash_start_time
            if current_hand_smash_time < self.hand_smash_anim_duration and not self.third_repair_complete:
                hand_smash_rect = self.hand_smash_image.get_rect(
                    center=self.hand_smash_center)
                surface.blit(self.hand_smash_image, hand_smash_rect)

                for i, (item, rect, type, index, is_repaired, target_x, target_y, _, _) in enumerate(self.repair_items):
                    if not is_repaired and i in self.item_scatter_velocities:
                        velocity = self.item_scatter_velocities[i]
                        rect.x += velocity.x
                        rect.y += velocity.y
                        self.item_scatter_velocities[i] *= 0.95

            else:
                self.hand_smash = False
                self.repair_items, self.target_positions = create_repair_items(
                    self.rect.width, self.rect.height, self.game_font, self.repair_stage)
                self.repaired_items = 0
                self.save_game_state()
                self.item_scatter_velocities = {}

        if self.error_sound:
            draw_glitch(surface, intensity=25)
            if time.time() - self.error_sound_timer > 0.1:
                self.error_sound = False
        if self.playing and not self.game_started and not self.repair_mode and not self.first_repair_complete and not self.post_repair_time and not self.second_repair_message and not self.post_second_repair_message:
            self.timeline_progress += 0.1/self.music_track_length / \
                60
        if self.timeline_progress >= 1:
            self.timeline_progress = 0

        if self.glitch_effect:
            glitch_surface = pygame.Surface(
                (self.rect.width, self.rect.height), pygame.SRCALPHA)
            draw_glitch(glitch_surface, intensity=25)
            surface.blit(glitch_surface, (0, 0))
            if time.time() - self.glitch_start_time > 0.3:
                self.glitch_effect = False

        if self.third_repair_complete and self.repair_stage == 3:
            text_color = white
            draw_text("ВЯЧПЛЕЕР", text_color, pygame.Rect(
                40, 40, 200, 50), surface, text_font=self.game_font)

            controls_y = self.rect.height - 80
            self.play_button_rect = pygame.Rect(
                self.rect.width // 2 - 15, controls_y + 15, 30, 30)
            self.stop_button_rect = pygame.Rect(
                self.rect.width // 2 - 65, controls_y + 15, 30, 30)
            self.rewind_button_rect = pygame.Rect(
                self.rect.width // 2 - 115, controls_y + 15, 30, 30)
            self.forward_button_rect = pygame.Rect(
                self.rect.width // 2 + 35, controls_y + 15, 30, 30)
            self.volume_rect = pygame.Rect(
                self.rect.width - 150, controls_y + 15, 100, 30)
            self.timeline_rect = pygame.Rect(
                50, controls_y - 15, self.rect.width - 100, 10)

            controls_color = black
            pygame.draw.rect(
                surface, controls_color, (0, controls_y, self.rect.width, 60))

            progress_bar_width = self.timeline_rect.width * self.timeline_progress
            timeline_color = light_gray
            progress_color = green

            pygame.draw.rect(surface, timeline_color, self.timeline_rect)
            progress_bar_rect = pygame.Rect(self.timeline_rect.x, self.timeline_rect.y, int(progress_bar_width),
                                            self.timeline_rect.height)
            pygame.draw.rect(surface, progress_color, progress_bar_rect)

            icon_color = light_gray
            volume_slider_color = green

            surface.blit(
                play_icon if not self.playing else pause_icon, self.play_button_rect)
            surface.blit(stop_icon, self.stop_button_rect)
            pygame.draw.polygon(surface, icon_color,
                                [(self.rewind_button_rect.centerx - 10, self.rewind_button_rect.centery - 8),
                                 (self.rewind_button_rect.centerx - 10,
                                  self.rewind_button_rect.centery + 8),
                                 (self.rewind_button_rect.centerx - 18, self.rewind_button_rect.centery)])
            pygame.draw.polygon(surface, icon_color,
                                [(self.rewind_button_rect.centerx - 1, self.rewind_button_rect.centery - 8),
                                 (self.rewind_button_rect.centerx - 1,
                                  self.rewind_button_rect.centery + 8),
                                 (self.rewind_button_rect.centerx - 9, self.rewind_button_rect.centery)])
            pygame.draw.polygon(surface, icon_color,
                                [(self.forward_button_rect.centerx + 10, self.forward_button_rect.centery - 8),
                                 (self.forward_button_rect.centerx + 10,
                                  self.forward_button_rect.centery + 8),
                                 (self.forward_button_rect.centerx + 18, self.forward_button_rect.centery)])
            pygame.draw.polygon(surface, icon_color,
                                [(self.forward_button_rect.centerx + 1, self.forward_button_rect.centery - 8),
                                 (self.forward_button_rect.centerx + 1,
                                  self.forward_button_rect.centery + 8),
                                 (self.forward_button_rect.centerx + 9, self.forward_button_rect.centery)])
            pygame.draw.rect(surface, icon_color, self.volume_rect)
            pygame.draw.circle(surface, volume_slider_color, (self.volume_rect.x +
                                                              30, self.volume_rect.centery), 7)
            text_vol_color = light_gray
            draw_text("VOL", text_vol_color, pygame.Rect(self.volume_rect.x - 45, self.volume_rect.y, 45, 30), surface,
                      text_font=self.game_font)

    def handle_event(self, event, windows):

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)

                if not self.game_started and self.play_button_rect.collidepoint(pos) and not self.first_repair_complete and not self.second_repair_message and not self.post_second_repair_message:
                    self.playing = not self.playing
                    if not self.playing:
                        play_error_sound()
                        self.show_console = True
                        self.play_button_rect.x -= self.console_width // 2
                        self.stop_button_rect.x -= self.console_width // 2
                        self.rewind_button_rect.x -= self.console_width // 2
                        self.forward_button_rect.x -= self.console_width // 2
                        self.volume_rect.x -= self.console_width // 2
                        self.timeline_rect.x -= self.console_width // 2
                        self.save_game_state()
                if self.show_console and not self.repair_mode and not self.first_repair_complete and not self.second_repair_message and not self.post_second_repair_message:
                    console_rect = pygame.Rect(self.rect.width - self.console_width, 0, self.console_width,
                                               self.rect.height)
                    if console_rect.collidepoint(pos):
                        if self.game_started:
                            for window in windows:
                                if window.minigame == self:
                                    window.is_open = False

                if self.repair_mode and not self.explosion_anim and not self.hand_enlarge_anim:
                    for i, (item, rect, type, index, is_repaired, target_x, target_y, _, _) in enumerate(self.repair_items):
                        if rect.collidepoint(pos) and not is_repaired:
                            self.dragging_item = (
                                item, rect, type, index, i, target_x, target_y)
                            self.offset_x = rect.x - pos[0]
                            self.offset_y = rect.y - pos[1]
                            break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.dragging_item and not self.explosion_anim and not self.hand_enlarge_anim:
                    item, rect, type, index, item_index, target_x, target_y = self.dragging_item
                    target_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2,
                                              item.get_width(), item.get_height())
                    if rect.colliderect(target_rect):
                        self.repair_items[item_index] = (
                            item, target_rect, type, index, True, target_x, target_y, 0, 0)
                        self.repaired_items += 1
                        # Trigger glitch effect after successful repair
                        self.glitch_effect = True
                        self.glitch_start_time = time.time()
                        self.save_game_state()
                    self.dragging_item = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_item and not self.explosion_anim and not self.hand_enlarge_anim:
                item, rect, type, index, item_index, target_x, target_y = self.dragging_item
                pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                rect.x = pos[0] + self.offset_x
                rect.y = pos[1] + self.offset_y

        if self.repair_mode and self.repaired_items >= len(self.target_positions) and not self.explosion_anim and not self.hand_enlarge_anim:
            if not self.first_repair_complete:
                self.vyacheslav_message = True
                self.vyacheslav_message_start_time = time.time()
                self.first_repair_complete = True
                self.repair_mode = False
                self.game_started = False
                self.show_console = False
                self.post_repair_time = time.time()
                self.save_game_state()
            elif not self.second_repair_complete and self.repair_stage == 2:
                self.second_repair_complete = True
                self.repair_mode = False
                self.game_started = False
                self.show_console = False
                self.second_repair_message = True
                self.second_repair_message_start_time = time.time()
                self.post_repair_time = time.time()
                self.save_game_state()
            elif not self.third_repair_complete and self.repair_stage == 3:
                self.third_repair_complete = True
                self.repair_mode = False
                self.game_started = False
                self.show_console = False
                self.vyacheslav_message = True
                self.vyacheslav_message_start_time = time.time()
                self.post_repair_time = time.time()
                self.save_game_state()
