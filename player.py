import pygame
import random
import time
import math

# Цвета
white = (255, 255, 255)
black = (0, 0, 0)
dark_gray = (30, 30, 30)
light_gray = (150, 150, 150)
bright_red = (255, 0, 0)
red = (255, 0, 0)
green = (0, 200, 0)
transparent_white = (255, 255, 255, 100)

# Иконки для мини-игры
play_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.polygon(play_icon, light_gray, [(5, 5), (25, 15), (5, 25)])
pause_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.rect(pause_icon, light_gray, (5, 5, 8, 20))
pygame.draw.rect(pause_icon, light_gray, (17, 5, 8, 20))
stop_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.rect(stop_icon, light_gray, (5, 5, 20, 20))

# Функция для отрисовки текста на экране мини-игры


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
        "ERROR: NullPointerException",
        "ERROR: Blue Screen of Death",
        "ERROR: Your computer has run into a problem and needs to restart.",
        "ERROR: Unexpected error occurred",
        "ERROR: Failed to load resource",
        "ERROR: Connection to server lost",
    ]
    return random.choice(errors)

# Функция для создания эффекта глитча для мини-игры


def draw_glitch(surface, intensity=5):
    for _ in range(intensity):
        x = random.randint(0, surface.get_width())
        y = random.randint(0, surface.get_height())
        w = random.randint(10, 100)
        h = random.randint(5, 20)
        color = random.choice([red, bright_red, black, (0, 255, 0)])
        pygame.draw.rect(surface, color, (x, y, w, h))

# Функция для создания звукового глитч-эффекта для мини-игры


def play_error_sound():
    global error_sound, error_sound_timer
    error_sound = True
    error_sound_timer = time.time()

# Функция для создания элементов ремонта для мини-игры


def create_repair_items(width, height, game_font):
    repair_items = []
    target_positions = {}

    # Надпись "ВЯЧПЛЕЕР" (смещена)
    text = "ВЯЧПЛЕЕР"
    text_surface = game_font.render(text, True, white)
    text_rect = text_surface.get_rect(
        topleft=(40, 40))  # Смещено вниз и вправо
    for i, char in enumerate(text):
        char_surface = game_font.render(char, True, white)
        char_rect = char_surface.get_rect(topleft=(random.randint(
            50, width - 50), random.randint(50, height - 100)))
        # type, index, is_repaired, target_x, target_y, velocity_x, velocity_y
        target_x = text_rect.left + text_surface.get_rect().width / len(text) * i
        target_y = text_rect.top
        velocity_x = random.uniform(-5, 5)
        velocity_y = random.uniform(-5, 5)
        repair_items.append(
            (char_surface, char_rect, "char", i, False, target_x, target_y, velocity_x, velocity_y))
        target_positions[(char_surface, "char", i)] = target_x, target_y

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
            # Улучшенная иконка перемотки назад
            pygame.draw.polygon(icon, light_gray, [(15, 15 - 8),
                                                   (15, 15 + 8),
                                                   (15 - 8, 15)])
            pygame.draw.polygon(icon, light_gray, [(15 + 9, 15 - 8),
                                                   (15 + 9, 15 + 8),
                                                   (15, 15)])

        if type == "forward_icon":
            # Улучшенная иконка перемотки вперед
            pygame.draw.polygon(icon, light_gray, [(15, 15 - 8),
                                                   (15, 15 + 8),
                                                   (15 + 8, 15)])
            pygame.draw.polygon(icon, light_gray, [(15 - 9, 15 - 8),
                                                   (15 - 9, 15 + 8),
                                                   (15, 15)])
        elif type == "volume_icon":
            # Иконка громкости с ползунком
            pygame.draw.rect(icon, light_gray, (0, 0, 100, 30))
            pygame.draw.circle(icon, green, (30, 15), 7)  # Кружок-ползунок

        elif type == "timeline_icon":
            pygame.draw.rect(icon, light_gray, (0, 0, width - 100, 10))
        icon_rect = icon.get_rect(center=(random.randint(
            50, width - 50), random.randint(50, height - 100)))
        # type, index, is_repaired, target_x, target_y, velocity_x, velocity_y
        velocity_x = random.uniform(-5, 5)
        velocity_y = random.uniform(-5, 5)
        repair_items.append((icon, icon_rect, type, i, False,
                            pos[0], pos[1], velocity_x, velocity_y))
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
        self.music_track_length = 120  # Длина трека в секундах
        self.first_repair_complete = False
        self.vyacheslav_message = False
        self.vyacheslav_message_start_time = 0
        self.hand_smash = False
        self.hand_smash_start_time = 0
        self.hand_smash_image = pygame.image.load("hand_smash.png")
        self.hand_smash_image = pygame.transform.scale(
            self.hand_smash_image, (150, 150))

        self.post_repair_time = 0  # Время после завершения ремонта
        self.post_repair_duration = 3  # Длительность показа собранного плеера

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

        self.second_repair_complete = False  # Флаг для отслеживания второго ремонта

    def draw(self, surface):
        # Отрисовка фона
        pygame.draw.rect(surface, dark_gray,
                         (0, 0, self.rect.width, self.rect.height))
        #  Надпись в левом верхнем углу (смещена)
        if not self.repair_mode and not self.first_repair_complete and not self.post_repair_time:
            draw_text("ВЯЧПЛЕЕР", white, pygame.Rect(
                40, 40, 200, 50), surface, text_font=self.game_font)  # Смещено вниз и вправо

        # Отрисовка элементов управления
        if not self.repair_mode and not self.first_repair_complete and not self.post_repair_time:
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

            pygame.draw.rect(
                surface, black, (0, controls_y, self.rect.width, 60))

            # Отрисовка полосы прогресса
            progress_bar_width = self.timeline_rect.width * self.timeline_progress

            pygame.draw.rect(surface, light_gray, self.timeline_rect)
            progress_bar_rect = pygame.Rect(self.timeline_rect.x, self.timeline_rect.y, int(progress_bar_width),
                                            self.timeline_rect.height)
            pygame.draw.rect(surface, green, progress_bar_rect)

            surface.blit(
                play_icon if not self.playing else pause_icon, self.play_button_rect)
            surface.blit(stop_icon, self.stop_button_rect)
            pygame.draw.polygon(surface, light_gray,
                                [(self.rewind_button_rect.centerx - 10, self.rewind_button_rect.centery - 8),
                                 (self.rewind_button_rect.centerx - 10,
                                  self.rewind_button_rect.centery + 8),
                                 (self.rewind_button_rect.centerx - 18, self.rewind_button_rect.centery)])
            pygame.draw.polygon(surface, light_gray,
                                [(self.rewind_button_rect.centerx - 1, self.rewind_button_rect.centery - 8),
                                 (self.rewind_button_rect.centerx - 1,
                                  self.rewind_button_rect.centery + 8),
                                 (self.rewind_button_rect.centerx - 9, self.rewind_button_rect.centery)])
            pygame.draw.polygon(surface, light_gray,
                                [(self.forward_button_rect.centerx + 10, self.forward_button_rect.centery - 8),
                                 (self.forward_button_rect.centerx + 10,
                                  self.forward_button_rect.centery + 8),
                                 (self.forward_button_rect.centerx + 18, self.forward_button_rect.centery)])
            pygame.draw.polygon(surface, light_gray,
                                [(self.forward_button_rect.centerx + 1, self.forward_button_rect.centery - 8),
                                 (self.forward_button_rect.centerx + 1,
                                  self.forward_button_rect.centery + 8),
                                 (self.forward_button_rect.centerx + 9, self.forward_button_rect.centery)])
            pygame.draw.rect(surface, light_gray, self.volume_rect)
            pygame.draw.circle(surface, green, (self.volume_rect.x +
                               30, self.volume_rect.centery), 7)  # Кружок-ползунок
            draw_text("VOL", light_gray, pygame.Rect(self.volume_rect.x - 45, self.volume_rect.y, 45, 30), surface,
                      text_font=self.game_font)

        # Отрисовка консоли
        if self.show_console and not self.first_repair_complete:
            console_rect = pygame.Rect(
                self.rect.width - self.console_width, 0, self.console_width, self.rect.height)
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
                    self.repair_items, self.target_positions = create_repair_items(
                        self.rect.width, self.rect.height, self.game_font)
                    self.console_messages = ["SYSTEM: Repair mode activated.",
                                             "SYSTEM: Fix the audio player to proceed."
                                             ]

                text_rect = pygame.Rect(console_rect.x + 10, console_rect.y + 10, self.console_width - 20,
                                        self.rect.height - 20)
                # Calculate the available height for text in the console
                available_height = text_rect.height
                line_height = self.console_font.get_linesize()
                max_lines_in_console = available_height // line_height

                # Get only the last messages to fit in the console area
                lines_to_draw = self.console_messages[-max_lines_in_console:]

                # Draw the text
                text_y = text_rect.y
                for line in lines_to_draw:
                    draw_text(line, red, pygame.Rect(text_rect.x, text_y, text_rect.width, line_height), surface,
                              text_font=self.console_font)
                    text_y += line_height

        # Отрисовка элементов ремонта
        if self.repair_mode:
            for item, rect, type, index, is_repaired, target_x, target_y, _, _ in self.repair_items:
                if not is_repaired:  # Рисуем только неисправленные элементы
                    surface.blit(item, rect)

                if self.dragging_item and self.dragging_item[2] == type and self.dragging_item[3] == index:
                    # Отображение индикатора цели для перетаскиваемого элемента
                    target_item_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2,
                                                   item.get_width(), item.get_height())
                    draw_target_indicator(surface, target_item_rect.center,
                                          (item.get_width() + 10, item.get_height() + 10))

                if is_repaired:
                    # Рисуем исправленные элементы на их целевых позициях
                    target_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2,
                                              item.get_width(), item.get_height())
                    surface.blit(item, target_rect)

        if self.post_repair_time > 0:
            current_time = time.time()
            if current_time - self.post_repair_time < self.post_repair_duration:
                for item, rect, type, index, is_repaired, target_x, target_y, _, _ in self.repair_items:
                    target_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2,
                                              item.get_width(), item.get_height())
                    surface.blit(item, target_rect)
            else:
                self.post_repair_time = 0
                self.repair_items, self.target_positions = create_repair_items(
                    self.rect.width, self.rect.height, self.game_font)
                self.repaired_items = 0
                for i, (item, rect, type, index, is_repaired, target_x, target_y, _, _) in enumerate(self.repair_items):
                    rect.x = random.randint(50, self.rect.width - 50)
                    rect.y = random.randint(50, self.rect.height - 100)
                    velocity_x = random.uniform(-5, 5)
                    velocity_y = random.uniform(-5, 5)
                    self.repair_items[i] = (
                        item, rect, type, index, False, target_x, target_y, velocity_x, velocity_y)

                self.repair_mode = True  # Запускаем повторный ремонт

        if self.vyacheslav_message:
            text_rect = pygame.Rect(
                self.rect.width//2-150, self.rect.height//2-20, 300, 40)
            draw_text("НЕТ, ЭТО ВСЁ ВАШИ ФАНТАЗИИ", red,
                      text_rect, surface, self.game_font)
            if time.time() - self.vyacheslav_message_start_time > 1.5:
                self.vyacheslav_message = False
                self.hand_smash = True
                self.hand_smash_start_time = time.time()

        if self.hand_smash:
            if time.time() - self.hand_smash_start_time < 0.5:
                hand_smash_rect = self.hand_smash_image.get_rect(
                    center=(self.rect.width // 2, self.rect.height // 2))
                surface.blit(self.hand_smash_image, hand_smash_rect)
            else:
                self.hand_smash = False
                self.repair_items, self.target_positions = create_repair_items(
                    self.rect.width, self.rect.height, self.game_font)
                self.repaired_items = 0

        if self.error_sound:
            draw_glitch(surface, intensity=25)
            if time.time() - self.error_sound_timer > 0.1:
                self.error_sound = False
        if self.playing and not self.game_started and not self.repair_mode and not self.first_repair_complete and not self.post_repair_time:
            self.timeline_progress += 0.1/self.music_track_length / \
                60  # 120 секунд музыки, частота кадров 60
        if self.timeline_progress >= 1:
            self.timeline_progress = 0

        if self.glitch_effect:
            glitch_surface = pygame.Surface(
                (self.rect.width, self.rect.height), pygame.SRCALPHA)
            draw_glitch(glitch_surface, intensity=25)
            surface.blit(glitch_surface, (0, 0))
            if time.time() - self.glitch_start_time > 0.3:
                self.glitch_effect = False

    def handle_event(self, event, windows):

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                # Корректируем координаты
                pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)

                if not self.game_started and self.play_button_rect.collidepoint(pos) and not self.first_repair_complete:
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
                if self.show_console and not self.repair_mode and not self.first_repair_complete:
                    console_rect = pygame.Rect(self.rect.width - self.console_width, 0, self.console_width,
                                               self.rect.height)
                    if console_rect.collidepoint(pos):
                        if self.game_started:
                            for window in windows:
                                if window.minigame == self:
                                    window.is_open = False

                if self.repair_mode:
                    for i, (item, rect, type, index, is_repaired, target_x, target_y, _, _) in enumerate(self.repair_items):
                        if rect.collidepoint(pos) and not is_repaired:
                            self.dragging_item = (
                                item, rect, type, index, i, target_x, target_y)
                            self.offset_x = rect.x - pos[0]
                            self.offset_y = rect.y - pos[1]
                            break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.dragging_item:
                    item, rect, type, index, item_index, target_x, target_y = self.dragging_item
                    target_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2,
                                              item.get_width(), item.get_height())
                    if rect.colliderect(target_rect):
                        # Обновляем состояние элемента на "исправлено"
                        self.repair_items[item_index] = (
                            item, target_rect, type, index, True, target_x, target_y, 0, 0)
                        self.repaired_items += 1
                    self.dragging_item = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_item:
                item, rect, type, index, item_index, target_x, target_y = self.dragging_item
                pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                rect.x = pos[0] + self.offset_x
                rect.y = pos[1] + self.offset_y

        if self.repair_mode and self.repaired_items >= len(self.target_positions):
            if not self.first_repair_complete:
                self.vyacheslav_message = True
                self.vyacheslav_message_start_time = time.time()
                self.first_repair_complete = True
                self.repair_mode = False
                self.game_started = False
                self.show_console = False
                self.post_repair_time = time.time()
            elif not self.second_repair_complete:  # Добавляем условие для второго ремонта
                self.second_repair_complete = True
                self.repair_mode = False
                self.game_started = False
                self.show_console = False
                self.vyacheslav_message = True
                self.vyacheslav_message_start_time = time.time()

        #  Физика объектов
        if self.repair_mode and not self.hand_smash:
            for i, (item, rect, type, index, is_repaired, target_x, target_y, velocity_x, velocity_y) in enumerate(self.repair_items):
                if not is_repaired:
                    # Обновляем позицию элемента
                    rect.x += velocity_x
                    rect.y += velocity_y

                    # Отскок от стенок
                    if rect.left < 0 or rect.right > self.rect.width:
                        velocity_x *= -1
                    if rect.top < 0 or rect.bottom > self.rect.height:
                        velocity_y *= -1
                    # Сохраняем измененные значения в self.repair_items
                    self.repair_items[i] = (
                        item, rect, type, index, is_repaired, target_x, target_y, velocity_x, velocity_y)
