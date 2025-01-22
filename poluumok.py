import pygame
import time
import sys
import random
import math


# Инициализация Pygame
pygame.init()

# Размеры экрана (Full HD)
screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("ZOV OS Startup")

# Цвета
blue = (0, 0, 255)
orange = (255, 165, 0)
white = (255, 255, 255)
black = (0, 0, 0)
dark_blue = (0, 0, 100, 128)  # Темно-синий с прозрачностью
red = (255, 0, 0)
dark_gray = (30, 30, 30)
light_gray = (150, 150, 150)
bright_red = (255, 0, 0)
green = (0, 200, 0)
transparent_white = (255, 255, 255, 100)

# Шрифт
font = pygame.font.Font(None, 200)
file_font = pygame.font.Font(None, 30)  # Шрифт для названия файла
window_font = pygame.font.Font(None, 30)

# Заставка
startup_text = "ZOV OS"
text_colors = [blue, blue, blue, blue, orange, orange]
text_surfaces = []
for i, char in enumerate(startup_text):
    text_surface = font.render(char, True, text_colors[i])
    text_surfaces.append(text_surface)

text_positions = [
    (screen_width // 2 - text_surfaces[0].get_width() * 2.5 + text_surfaces[0].get_width() * -1,
     screen_height // 2 - text_surfaces[0].get_height() // 2),
    (screen_width // 2 - text_surfaces[0].get_width() * 2.5 + text_surfaces[0].get_width() * 0,
     screen_height // 2 - text_surfaces[0].get_height() // 2),
    (screen_width // 2 - text_surfaces[0].get_width() * 2.5 + text_surfaces[0].get_width() * 1 + 25,
     screen_height // 2 - text_surfaces[0].get_height() // 2),
    (screen_width // 2 - text_surfaces[0].get_width() * 2.5 + text_surfaces[0].get_width() * 2,
     screen_height // 2 - text_surfaces[0].get_height() // 2),
    (screen_width // 2 - text_surfaces[0].get_width() * 2.5 + text_surfaces[0].get_width() * 3,
     screen_height // 2 - text_surfaces[0].get_height() // 2),
    (screen_width // 2 - text_surfaces[0].get_width() * 2.5 + text_surfaces[0].get_width() * 4,
     screen_height // 2 - text_surfaces[0].get_height() // 2),
]
text_alphas = [0, 0, 0, 0, 0, 0]
text_alpha_speed = 20

blue_glow_image = pygame.image.load("blglow.png").convert_alpha()
orange_glow_image = pygame.image.load("orglow.png").convert_alpha()

glow_surfaces = []
for i, surface in enumerate(text_surfaces):
    if text_colors[i] == blue:
        if blue_glow_image:
            glow = pygame.transform.scale(blue_glow_image, (surface.get_width() * 2, surface.get_height() * 2))
            glow_surfaces.append(glow)
        else:
            glow_surfaces.append(None)
    elif text_colors[i] == orange:
        if orange_glow_image:
            glow = pygame.transform.scale(orange_glow_image, (surface.get_width() * 2, surface.get_height() * 2))
            glow_surfaces.append(glow)
        else:
            glow_surfaces.append(None)
    else:
        glow_surfaces.append(None)

glow_alphas = [0, 0, 0, 0, 0, 0]
glow_alpha_speed = 10

background_image = pygame.image.load("zovosbg.png").convert()
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

show_startup = True
current_letter = 0
last_letter_time = time.time()
show_glow = False
glow_start_time = 0
show_image = False
image_start_time = 0
glow_finished = False

clock = pygame.time.Clock()
fps = 30

# Шрифты для мини-игры
try:
    font_path = "font.otf"
    font_size = 30
    game_font = pygame.font.Font(font_path, font_size)
    console_font = pygame.font.Font(font_path, 24)
except:
    print("ERROR: Roboto font not found.")
    game_font = pygame.font.SysFont(None, 30)
    console_font = pygame.font.SysFont(None, 24)
    print("Using default system font.")

# Иконки для мини-игры (заглушки)
play_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.polygon(play_icon, light_gray, [(5, 5), (25, 15), (5, 25)])
pause_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.rect(pause_icon, light_gray, (5, 5, 8, 20))
pygame.draw.rect(pause_icon, light_gray, (17, 5, 8, 20))
stop_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.rect(stop_icon, light_gray, (5, 5, 20, 20))

# Функция для отрисовки текста на экране мини-игры
def draw_text(text, color, rect, surface, aa=True, bkg=None, text_font=game_font):
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

# Функция генерации ошибок для мини-игры
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
        "ERROR: NullPointerException"
    ]
    return random.choice(errors)

# Функция для создания эффекта глитча для мини-игры
def draw_glitch(surface, intensity=5):
    for _ in range(intensity):
        x = random.randint(0, surface.get_width())
        y = random.randint(0, surface.get_height())
        w = random.randint(10, 100)
        h = random.randint(5, 20)
        color = random.choice([red, bright_red, black])
        pygame.draw.rect(surface, color, (x, y, w, h))

# Функция для создания звукового глитч-эффекта для мини-игры
def play_error_sound():
    global error_sound, error_sound_timer
    error_sound = True
    error_sound_timer = time.time()

# Функция для создания элементов ремонта для мини-игры
def create_repair_items(width, height):
    repair_items = []
    target_positions = {}

    # Надпись "ВЯЧПЛЕЕР"
    text = "ВЯЧПЛЕЕР"
    text_surface = game_font.render(text, True, white)
    text_rect = text_surface.get_rect(topleft=(10, 10))
    for i, char in enumerate(text):
        char_surface = game_font.render(char, True, white)
        char_rect = char_surface.get_rect(topleft=(random.randint(50, width - 50), random.randint(50, height - 100)))
        repair_items.append((char_surface, char_rect, "char", i, False))  # type, index, is_repaired
        target_positions[(char_surface, "char", i)] = text_rect.topleft[0] + text_surface.get_rect(x=0, y=0, width=0, height=0).width/len(text) * i, 10

    # Иконки плеера
    controls_y = height - 80
    play_button_rect = pygame.Rect(width // 2 - 15, controls_y + 15, 30, 30)
    stop_button_rect = pygame.Rect(width // 2 - 65, controls_y + 15, 30, 30)
    rewind_button_rect = pygame.Rect(width // 2 - 115, controls_y + 15, 30, 30)
    forward_button_rect = pygame.Rect(width // 2 + 35, controls_y + 15, 30, 30)
    volume_rect = pygame.Rect(width - 150, controls_y + 15, 100, 30)
    timeline_rect = pygame.Rect(50, controls_y - 15, width - 100, 10)

    icons = [(play_icon, play_button_rect.center, "play_icon"),
            (stop_icon, stop_button_rect.center, "stop_icon"),
            (pygame.Surface((30,30), pygame.SRCALPHA), rewind_button_rect.center, "rewind_icon"),
            (pygame.Surface((30,30), pygame.SRCALPHA), forward_button_rect.center, "forward_icon"),
            (pygame.Surface((100, 30), pygame.SRCALPHA), volume_rect.center, "volume_icon"),
             (pygame.Surface((width - 100, 10), pygame.SRCALPHA), timeline_rect.center, "timeline_icon")
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
        elif type == "timeline_icon":
            pygame.draw.rect(icon, light_gray, (0, 0, width-100, 10))
        icon_rect = icon.get_rect(center=(random.randint(50, width - 50), random.randint(50, height - 100)))
        repair_items.append((icon, icon_rect, type, i, False))  # type, index, is_repaired
        target_positions[(icon, type, i)] = pos[0], pos[1]
    return repair_items, target_positions

def draw_target_indicator(surface, pos, size):
    """Рисует переливающийся квадрат-индикатор."""
    x, y = pos
    w, h = size
    center_x = x
    center_y = y

    time_now = pygame.time.get_ticks()
    phase = (math.sin(time_now / 200.0) + 1) / 2  # Изменение от 0 до 1

    color = (int(transparent_white[0] * phase),
             int(transparent_white[1] * phase),
             int(transparent_white[2] * phase),
             transparent_white[3])

    indicator_surface = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(indicator_surface, color, (0, 0, w, h), border_radius=5)

    surface.blit(indicator_surface, (center_x - w // 2, center_y - h // 2))


# Класс мини-игры
class Minigame:
    def __init__(self, rect):
        self.rect = rect
        self.playing = False
        self.show_console = False
        self.console_width = 350
        self.console_messages = []
        self.last_error_time = 0
        self.glitch_effect = False
        self.glitch_start_time = 0
        self.ending_text_index = 0
        self.ending_text_timer = 0
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

        # Текст для "концовки" мини-игры
        self.ending_text = [
            "ERROR: Critical failure.",
            "AudioPlayerError: This app written by Vyachka siska, so obviously that won't working lol",
            "ERROR: Reality breakdown imminent.",
            "WARNING: You shouldn't have done that.",
            "...",
            "ERROR: The void is coming.",
            "SYSTEM: Initiating Self-Destruct",
            "SYSTEM: User data lost. No recovery possible.",
            "...",
            "ERROR: Goodbye",
            "YOU SHOULDN'T HAVE DONE THAT",
            "HA HA HA HA HA HA",
            "I'M COMING FOR YOU",
            "YOU CAN'T HIDE",
            "...",
            "GAME OVER!"
        ]

        self.controls_y = self.rect.height - 80
        self.play_button_rect = pygame.Rect(self.rect.width // 2 - 15, self.controls_y + 15, 30, 30)
        self.stop_button_rect = pygame.Rect(self.rect.width // 2 - 65, self.controls_y + 15, 30, 30)
        self.rewind_button_rect = pygame.Rect(self.rect.width // 2 - 115, self.controls_y + 15, 30, 30)
        self.forward_button_rect = pygame.Rect(self.rect.width // 2 + 35, self.controls_y + 15, 30, 30)
        self.volume_rect = pygame.Rect(self.rect.width - 150, self.controls_y + 15, 100, 30)
        self.timeline_rect = pygame.Rect(50, self.controls_y - 15, self.rect.width - 100, 10)

    def draw(self, surface):
        # Отрисовка фона
        pygame.draw.rect(surface, dark_gray, (0, 0, self.rect.width, self.rect.height))
        #  Надпись в левом верхнем углу
        if not self.repair_mode:
            draw_text("ВЯЧПЛЕЕР", white, pygame.Rect(10, 10, 200, 50), surface, text_font=game_font)

        # Отрисовка элементов управления
        if not self.repair_mode:
            controls_y = self.rect.height - 80
            self.play_button_rect = pygame.Rect(self.rect.width // 2 - 15, controls_y + 15, 30, 30)
            self.stop_button_rect = pygame.Rect(self.rect.width // 2 - 65, controls_y + 15, 30, 30)
            self.rewind_button_rect = pygame.Rect(self.rect.width // 2 - 115, controls_y + 15, 30, 30)
            self.forward_button_rect = pygame.Rect(self.rect.width // 2 + 35, controls_y + 15, 30, 30)
            self.volume_rect = pygame.Rect(self.rect.width - 150, controls_y + 15, 100, 30)
            self.timeline_rect = pygame.Rect(50, controls_y - 15, self.rect.width - 100, 10)

            pygame.draw.rect(surface, black, (0, controls_y, self.rect.width, 60))

            # Отрисовка полосы прогресса
            progress_bar_width = self.timeline_rect.width * self.timeline_progress

            pygame.draw.rect(surface, light_gray, self.timeline_rect)
            progress_bar_rect = pygame.Rect(self.timeline_rect.x, self.timeline_rect.y, int(progress_bar_width),
                                            self.timeline_rect.height)
            pygame.draw.rect(surface, green, progress_bar_rect)

            surface.blit(play_icon if not self.playing else pause_icon, self.play_button_rect)
            surface.blit(stop_icon, self.stop_button_rect)
            pygame.draw.polygon(surface, light_gray,
                                [(self.rewind_button_rect.centerx - 10, self.rewind_button_rect.centery - 8),
                                 (self.rewind_button_rect.centerx - 10, self.rewind_button_rect.centery + 8),
                                 (self.rewind_button_rect.centerx - 18, self.rewind_button_rect.centery)])
            pygame.draw.polygon(surface, light_gray,
                                [(self.rewind_button_rect.centerx - 1, self.rewind_button_rect.centery - 8),
                                 (self.rewind_button_rect.centerx - 1, self.rewind_button_rect.centery + 8),
                                 (self.rewind_button_rect.centerx - 9, self.rewind_button_rect.centery)])
            pygame.draw.polygon(surface, light_gray,
                                [(self.forward_button_rect.centerx + 10, self.forward_button_rect.centery - 8),
                                 (self.forward_button_rect.centerx + 10, self.forward_button_rect.centery + 8),
                                 (self.forward_button_rect.centerx + 18, self.forward_button_rect.centery)])
            pygame.draw.polygon(surface, light_gray,
                                [(self.forward_button_rect.centerx + 1, self.forward_button_rect.centery - 8),
                                 (self.forward_button_rect.centerx + 1, self.forward_button_rect.centery + 8),
                                 (self.forward_button_rect.centerx + 9, self.forward_button_rect.centery)])
            pygame.draw.rect(surface, light_gray, self.volume_rect)
            draw_text("VOL", light_gray, pygame.Rect(self.volume_rect.x - 45, self.volume_rect.y, 45, 30), surface,
                      text_font=game_font)

        # Отрисовка консоли
        if self.show_console:
            console_rect = pygame.Rect(self.rect.width - self.console_width, 0, self.console_width, self.rect.height)
            if not self.repair_mode:
                pygame.draw.rect(surface, (20, 20, 20), console_rect)

            if not self.game_started:
                current_time = time.time()
                if current_time - self.last_error_time > random.uniform(1, 2):
                    self.console_messages.append(generate_error())
                    self.last_error_time = current_time

                if len(self.console_messages) > 15:
                    self.game_started = True
                    self.repair_mode = True
                    self.repair_items, self.target_positions = create_repair_items(self.rect.width, self.rect.height)
                    self.console_messages = ["SYSTEM: Repair mode activated.",
                                             "SYSTEM: Fix the audio player to proceed."
                                             ]

                text_rect = pygame.Rect(console_rect.x + 10, console_rect.y + 10, self.console_width - 20,
                                        self.rect.height - 20)
                # Calculate the available height for text in the console
                available_height = text_rect.height
                line_height = console_font.get_linesize()
                max_lines_in_console = available_height // line_height

                # Get only the last messages to fit in the console area
                lines_to_draw = self.console_messages[-max_lines_in_console:]

                # Draw the text
                text_y = text_rect.y
                for line in lines_to_draw:
                    draw_text(line, red, pygame.Rect(text_rect.x, text_y, text_rect.width, line_height), surface,
                              text_font=console_font)
                    text_y += line_height

            elif self.game_started and not self.repair_mode:  # Вывод "концовки"
                if self.ending_text_index > 0:
                    self.ending_text_timer += 1
                    text_y = console_rect.y + 20
                    for i in range(self.ending_text_index):
                        if i < len(self.ending_text) - 1:
                            color = red
                        else:
                            color = bright_red
                        draw_text(self.ending_text[i], color,
                                  pygame.Rect(console_rect.x + 10, text_y, self.console_width - 20, self.rect.height),
                                  surface, text_font=console_font)
                        text_y += console_font.get_height() + 5
                else:
                    self.console_messages = ["SYSTEM: Repair complete.",
                                             "SYSTEM: Audio player is stable.",
                                             "...",
                                             "SYSTEM: The void is gone for now."]
                    text_rect = pygame.Rect(console_rect.x + 10, console_rect.y + 10, self.console_width - 20,
                                            self.rect.height - 20)

                    # Calculate the available height for text in the console
                    available_height = text_rect.height
                    line_height = console_font.get_linesize()
                    max_lines_in_console = available_height // line_height

                    # Get only the last messages to fit in the console area
                    lines_to_draw = self.console_messages[-max_lines_in_console:]

                    # Draw the text
                    text_y = text_rect.y
                    for line in lines_to_draw:
                        draw_text(line, green, pygame.Rect(text_rect.x, text_y, text_rect.width, line_height), surface,
                                  text_font=console_font)
                        text_y += line_height

            if self.glitch_effect:
                draw_glitch(surface, intensity=25)
                if time.time() - self.glitch_start_time > 0.3:
                    self.glitch_effect = False

        # Отрисовка элементов ремонта
        if self.repair_mode:
            for item, rect, type, index, is_repaired in self.repair_items:
                surface.blit(item, rect)
                if self.dragging_item and self.dragging_item == (
                item, rect, type, index, self.repair_items.index((item, rect, type, index, is_repaired))):
                    target_x, target_y = self.target_positions[(item, type, index)]
                    # Создаем rect для целевого положения
                    target_item_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2,
                                                   item.get_width(), item.get_height())
                    draw_target_indicator(surface, target_item_rect.center,
                                          (item.get_width() + 10, item.get_height() + 10))
                if is_repaired:
                    target_x, target_y = self.target_positions[(item, type, index)]
                    target_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2,
                                              item.get_width(), item.get_height())
                    surface.blit(item, target_rect)

        if self.error_sound:
            draw_glitch(surface, intensity=25)
            if time.time() - self.error_sound_timer > 0.1:
                self.error_sound = False
        if self.playing and not self.game_started and not self.repair_mode:
            self.timeline_progress += 0.0001
        if self.timeline_progress >= 1:
            self.timeline_progress = 0

    def handle_event(self, event, windows):

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)  # Корректируем координаты

                if not self.game_started and self.play_button_rect.collidepoint(pos):
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
                if self.show_console and not self.repair_mode:
                    console_rect = pygame.Rect(self.rect.width - self.console_width, 0, self.console_width,
                                               self.rect.height)
                    if console_rect.collidepoint(pos):
                        if self.game_started:
                            if self.ending_text_index < len(self.ending_text):
                                self.ending_text_index += 1
                                self.glitch_effect = True
                                self.glitch_start_time = time.time()
                                play_error_sound()
                            else:
                                for window in windows:
                                    if window.minigame == self:
                                        window.is_open = False

                if self.repair_mode:
                    for i, (item, rect, type, index, is_repaired) in enumerate(self.repair_items):
                        if rect.collidepoint(pos) and not is_repaired:
                            self.dragging_item = (item, rect, type, index, i)
                            self.offset_x = rect.x - pos[0]
                            self.offset_y = rect.y - pos[1]
                            break


        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.dragging_item:
                    item, rect, type, index, item_index = self.dragging_item
                    target_x, target_y = self.target_positions[(item, type, index)]
                    target_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2,
                                              item.get_width(), item.get_height())
                    if rect.colliderect(target_rect):
                        self.repair_items[item_index] = (item, target_rect, type, index, True)
                        self.repaired_items += 1
                    self.dragging_item = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_item:
                item, rect, type, index, item_index = self.dragging_item
                pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                rect.x = pos[0] + self.offset_x
                rect.y = pos[1] + self.offset_y

        if self.repair_mode and self.repaired_items >= len(self.target_positions):
            self.repair_mode = False
            self.game_started = False
            self.show_console = True
            self.repaired_items = 0
            self.ending_text_index = 0
            controls_y = self.rect.height - 80
            self.play_button_rect = pygame.Rect(self.rect.width // 2 - 15, controls_y + 15, 30, 30)
            self.stop_button_rect = pygame.Rect(self.rect.width // 2 - 65, controls_y + 15, 30, 30)
            self.rewind_button_rect = pygame.Rect(self.rect.width // 2 - 115, controls_y + 15, 30, 30)
            self.forward_button_rect = pygame.Rect(self.rect.width // 2 + 35, controls_y + 15, 30, 30)
            self.volume_rect = pygame.Rect(self.rect.width - 150, controls_y + 15, 100, 30)
            self.timeline_rect = pygame.Rect(50, controls_y - 15, self.rect.width - 100, 10)


# Класс окна
class Window:
    def __init__(self, title, width, height, x, y):
        self.title = title
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y + 50, width, height)
        self.dragging = False
        self.title_bar_height = 50
        self.title_bar = pygame.Rect(x, y, width, self.title_bar_height)
        self.title_surface = window_font.render(self.title, True, black)
        self.title_rect = self.title_surface.get_rect(center=self.title_bar.center)

        self.close_button_size = 20
        self.close_button_x = x + width - self.close_button_size - 10
        self.close_button_y = y + 15
        self.close_button_rect = pygame.Rect(self.close_button_x, self.close_button_y, self.close_button_size,
                                             self.close_button_size)

        self.is_open = True
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.minigame = None  # Добавляем ссылку на мини-игру

    def draw(self, screen):
        if self.is_open:
            pygame.draw.rect(screen, white, self.title_bar)  # белая плашка
            screen.blit(self.title_surface, self.title_rect)  # название
            pygame.draw.rect(screen, red, self.close_button_rect)  # красный крест
            pygame.draw.rect(screen, white, self.rect)  # Окно

            if self.minigame:
                self.minigame.draw(screen.subsurface(self.rect))

    def handle_event(self, event, windows):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                if self.title_bar.collidepoint(event.pos):
                    self.dragging = True
                    self.drag_offset_x = event.pos[0] - self.title_bar.x
                    self.drag_offset_y = event.pos[1] - self.title_bar.y
                if self.close_button_rect.collidepoint(event.pos):
                    self.is_open = False

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.title_bar.x = event.pos[0] - self.drag_offset_x
                self.title_bar.y = event.pos[1] - self.drag_offset_y

                self.rect.x = self.title_bar.x
                self.rect.y = self.title_bar.y + 50

                self.title_rect.center = self.title_bar.center
                self.close_button_rect.x = self.title_bar.x + self.title_bar.width - self.close_button_size - 10
                self.close_button_rect.y = self.title_bar.y + 15
        if self.minigame:
            self.minigame.handle_event(event, windows)


# Класс файла рабочего стола
class DesktopFile:
    def __init__(self, name, image_path, x, y):
        self.name = name
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.selected = False
        self.dragging = False
        self.name_surface = file_font.render(self.name, True, white)
        self.name_rect = self.name_surface.get_rect(center=(self.rect.centerx, self.rect.bottom + 20))

        # Рассчитываем размер рамки выделения
        padding_x = self.rect.width * 0.10
        padding_y = self.rect.height * 0.10 + 15

        selection_width = int(self.rect.width + padding_x * 2)
        selection_height = int(self.rect.height + padding_y * 2)

        selection_x = int(self.rect.left - padding_x)
        selection_y = int(self.rect.top - padding_y)

        self.selection_rect = pygame.Rect(selection_x, selection_y, selection_width, selection_height)
        self.selection_surface = pygame.Surface((selection_width, selection_height), pygame.SRCALPHA)
        self.selection_surface.fill(dark_blue)

        self.last_click_time = 0
        self.double_click_interval = 0.3

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        screen.blit(self.name_surface, self.name_rect)
        if self.selected:
            pygame.draw.rect(self.selection_surface, dark_blue, self.selection_surface.get_rect(), border_radius=5)
            pygame.draw.rect(self.selection_surface, white, self.selection_surface.get_rect(), 1, border_radius=5)
            screen.blit(self.selection_surface, self.selection_rect)

    def handle_event(self, event, files):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                if self.selection_rect.collidepoint(event.pos):
                    current_time = time.time()

                    if current_time - self.last_click_time < self.double_click_interval:
                        self.open_file(files, windows)
                    else:

                        self.selected = not self.selected
                        for file in files:
                            if file != self:
                                file.selected = False
                        self.dragging = True

                    self.last_click_time = current_time
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.center = event.pos
                self.name_rect.center = (self.rect.centerx, self.rect.bottom + 20)

                # Обновляем позицию рамки выделения
                padding_x = self.rect.width * 0.10
                padding_y = self.rect.height * 0.10

                selection_x = int(self.rect.left - padding_x)
                selection_y = int(self.rect.top - padding_y)

                self.selection_rect.topleft = (selection_x, selection_y)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DELETE and self.selected:
                files.remove(self)

    def open_file(self, files, windows):
        print(f"Открываю файл: {self.name}")
        if self.name == "ВЯЧ.py":
            new_window = Window(self.name, 800, 600, 200, 200)
            new_window.minigame = Minigame(new_window.rect)
            windows.append(new_window)

# Создание тестового файла
files = [DesktopFile("ВЯЧ.py", "py.png", 100, 100),
         DesktopFile("Корзина", "musor.png", 1800, 10),
         DesktopFile("Настройки", "nastoiku.png", 1800, 200)
         ]

windows = []
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

        if show_image:
            for file in files:
                file.handle_event(event, files)
            for window in windows:
                window.handle_event(event, windows)

    screen.fill(black)

    if show_startup:
        if current_letter < len(text_surfaces):
            text_alphas[current_letter] = min(255, text_alphas[current_letter] + text_alpha_speed)
            if text_alphas[current_letter] == 255 and time.time() - last_letter_time > 0.5:
                last_letter_time = time.time()
                current_letter += 1

        if current_letter == len(text_surfaces):
            if not show_glow:
                show_glow = True
                show_startup = False
                glow_start_time = time.time()

        for i in range(current_letter):
            text_surfaces[i].set_alpha(text_alphas[i])
            screen.blit(text_surfaces[i], text_positions[i])

    elif show_glow:
        if time.time() - glow_start_time < 0.5:
            for i, glow in enumerate(glow_surfaces):
                if glow is not None:
                    glow_alphas[i] = min(100, glow_alphas[i] + glow_alpha_speed)
                    glow.set_alpha(glow_alphas[i])
                    poses = text_positions[i]
                    glow_rect = glow.get_rect(center=(poses[0] + 40, poses[1] + 40))
                    screen.blit(glow, glow_rect)
            for i in range(len(text_surfaces)):
                text_surfaces[i].set_alpha(255)
                screen.blit(text_surfaces[i], text_positions[i])
        else:
            show_glow = False
            image_start_time = time.time()
            glow_alphas = [0, 0, 0, 0, 0, 0]

    elif time.time() - image_start_time > 0.5:
        show_image = True

    if show_image:
        if background_image:
            screen.blit(background_image, (0, 0))
        for file in files:
            file.draw(screen)
        for window in windows:
            window.draw(screen)
        windows = [window for window in windows if window.is_open]  # удаление закрытых окон
    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
