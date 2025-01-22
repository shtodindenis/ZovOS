import pygame
import sys
import random
import time
import math

# Инициализация Pygame
pygame.init()

# Параметры окна
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Хоррор Аудиоплеер")

# Цвета
black = (0, 0, 0)
dark_gray = (30, 30, 30)
light_gray = (150, 150, 150)
red = (180, 0, 0)
bright_red = (255, 0, 0)
green = (0, 200, 0)
white = (255, 255, 255)
orange = (255, 165, 0)
transparent_white = (255, 255, 255, 100)

# Шрифты
try:
    font_path = "font.otf"
    font_size = 30
    font = pygame.font.Font(font_path, font_size)
    console_font = pygame.font.Font(font_path, 24)
except:
    print("ERROR: Roboto font not found.")
    font = pygame.font.SysFont(None, 30)
    console_font = pygame.font.SysFont(None, 24)
    print("Using default system font.")

# Иконки (заглушки)
play_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.polygon(play_icon, light_gray, [(5, 5), (25, 15), (5, 25)])
pause_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.rect(pause_icon, light_gray, (5, 5, 8, 20))
pygame.draw.rect(pause_icon, light_gray, (17, 5, 8, 20))
stop_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.rect(stop_icon, light_gray, (5, 5, 20, 20))

# Элементы управления
controls_y = height - 80
controls_height = 60
play_button_rect = pygame.Rect(width // 2 - 15, controls_y + 15, 30, 30)
stop_button_rect = pygame.Rect(width // 2 - 65, controls_y + 15, 30, 30)
rewind_button_rect = pygame.Rect(width // 2 - 115, controls_y + 15, 30, 30)
forward_button_rect = pygame.Rect(width // 2 + 35, controls_y + 15, 30, 30)
volume_rect = pygame.Rect(width - 150, controls_y + 15, 100, 30)
timeline_rect = pygame.Rect(50, controls_y - 15, width - 100, 10)
timeline_progress = 0
progress_bar_width = timeline_rect.width * timeline_progress

# Состояния
playing = False
show_console = False
console_width = 350
console_messages = []
last_error_time = 0
glitch_effect = False
glitch_start_time = 0
ending_text_index = 0
ending_text_timer = 0
error_sound = False
error_sound_timer = 0
game_started = False
repair_mode = False
repair_items = []
repaired_items = 0
target_positions = {}
dragging_item = None
offset_x = 0
offset_y = 0
repair_complete = False

# Текст для "концовки"
ending_text = [
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

# Функция для отрисовки текста на экране
def draw_text(text, color, rect, surface, aa=True, bkg=None, text_font=font):
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

# Функция генерации ошибок
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

# Функция для создания эффекта глитча
def draw_glitch(surface, intensity=5):
    for _ in range(intensity):
        x = random.randint(0, width)
        y = random.randint(0, height)
        w = random.randint(10, 100)
        h = random.randint(5, 20)
        color = random.choice([red, bright_red, black])
        pygame.draw.rect(surface, color, (x, y, w, h))

# Функция для создания звукового глитч-эффекта
def play_error_sound():
    global error_sound, error_sound_timer
    error_sound = True
    error_sound_timer = time.time()

def create_repair_items():
    global repair_items, target_positions

    # Надпись "ВЯЧПЛЕЕР"
    text = "ВЯЧПЛЕЕР"
    text_surface = font.render(text, True, white)
    text_rect = text_surface.get_rect(topleft=(10,10))
    for i, char in enumerate(text):
        char_surface = font.render(char, True, white)
        char_rect = char_surface.get_rect(topleft=(random.randint(50, width - 50), random.randint(50, height - 100)))
        repair_items.append((char_surface, char_rect, "char", i, False))  # type, index, is_repaired
        target_positions[(char_surface, "char", i)] = text_rect.topleft[0] + text_surface.get_rect(x=0, y=0, width=0, height=0).width/len(text) * i, 10

    # Иконки плеера
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

# Игровой цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not game_started and play_button_rect.collidepoint(event.pos):
                playing = not playing
                if playing:
                    pass
                else:
                    play_error_sound()
                    show_console = True
                    play_button_rect.x -= console_width // 2
                    stop_button_rect.x -= console_width // 2
                    rewind_button_rect.x -= console_width // 2
                    forward_button_rect.x -= console_width // 2
                    volume_rect.x -= console_width // 2
                    timeline_rect.x -= console_width // 2

            if show_console and not repair_mode:
                console_rect = pygame.Rect(width - console_width, 0, console_width, height)
                if console_rect.collidepoint(event.pos):
                    if game_started:
                        if ending_text_index < len(ending_text):
                            ending_text_index += 1
                            glitch_effect = True
                            glitch_start_time = time.time()
                            play_error_sound()
                        else:
                            running = False
            if repair_mode:
                for i, (item, rect, type, index, is_repaired) in enumerate(repair_items):
                    if rect.collidepoint(event.pos) and not is_repaired:
                        dragging_item = (item, rect, type, index, i)
                        offset_x = rect.x - event.pos[0]
                        offset_y = rect.y - event.pos[1]
                        break

        if event.type == pygame.MOUSEBUTTONUP:
             if dragging_item:
                item, rect, type, index, item_index = dragging_item
                target_x, target_y = target_positions[(item, type, index)]
                target_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2, item.get_width(), item.get_height())
                if rect.colliderect(target_rect):
                    repair_items[item_index] = (item, target_rect, type, index, True)
                    repaired_items += 1
                dragging_item = None
        if event.type == pygame.MOUSEMOTION:
            if dragging_item:
                item, rect, type, index, item_index = dragging_item
                rect.x = event.pos[0] + offset_x
                rect.y = event.pos[1] + offset_y


    # Обновление экрана
    screen.fill(dark_gray)

    # Надпись в левом верхнем углу
    if not repair_mode:
        draw_text("ВЯЧПЛЕЕР", white, pygame.Rect(10, 10, 200, 50), screen)

    # Отрисовка элементов управления
    if not repair_mode:
        pygame.draw.rect(screen, black, (0, controls_y, width, controls_height))

        # Отрисовка полосы прогресса
        progress_bar_width = timeline_rect.width * timeline_progress

        pygame.draw.rect(screen, light_gray, timeline_rect)
        progress_bar_rect = pygame.Rect(timeline_rect.x, timeline_rect.y, int(progress_bar_width), timeline_rect.height)
        pygame.draw.rect(screen, green, progress_bar_rect)

        screen.blit(play_icon if not playing else pause_icon, play_button_rect)
        screen.blit(stop_icon, stop_button_rect)
        pygame.draw.polygon(screen, light_gray, [(rewind_button_rect.centerx - 10, rewind_button_rect.centery - 8),
                                                (rewind_button_rect.centerx - 10, rewind_button_rect.centery + 8),
                                                (rewind_button_rect.centerx - 18, rewind_button_rect.centery)])
        pygame.draw.polygon(screen, light_gray, [(rewind_button_rect.centerx - 1, rewind_button_rect.centery - 8),
                                                (rewind_button_rect.centerx - 1, rewind_button_rect.centery + 8),
                                                (rewind_button_rect.centerx - 9, rewind_button_rect.centery)])
        pygame.draw.polygon(screen, light_gray, [(forward_button_rect.centerx + 10, forward_button_rect.centery - 8),
                                                (forward_button_rect.centerx + 10, forward_button_rect.centery + 8),
                                                (forward_button_rect.centerx + 18, forward_button_rect.centery)])
        pygame.draw.polygon(screen, light_gray, [(forward_button_rect.centerx + 1, forward_button_rect.centery - 8),
                                                (forward_button_rect.centerx + 1, forward_button_rect.centery + 8),
                                                (forward_button_rect.centerx + 9, forward_button_rect.centery)])
        pygame.draw.rect(screen, light_gray, volume_rect)
        draw_text("VOL", light_gray, pygame.Rect(volume_rect.x - 45, volume_rect.y, 45, 30), screen)

    # Отрисовка консоли
    if show_console:
        console_rect = pygame.Rect(width - console_width, 0, console_width, height)
        if not repair_mode:  # Условие, чтобы консоль не рисовалась во время ремонта
            pygame.draw.rect(screen, (20, 20, 20), console_rect)

        if not game_started:
            current_time = time.time()
            if current_time - last_error_time > random.uniform(1, 2):
                console_messages.append(generate_error())
                last_error_time = current_time

            if len(console_messages) > 15:
                game_started = True
                repair_mode = True
                create_repair_items()
                console_messages = ["SYSTEM: Repair mode activated.",
                                    "SYSTEM: Fix the audio player to proceed."
                                    ]
            text_rect = pygame.Rect(console_rect.x + 10, console_rect.y + 10, console_width - 20, height - 20)
            # Calculate the available height for text in the console
            available_height = text_rect.height
            line_height = console_font.get_linesize()
            max_lines_in_console = available_height // line_height

            # Get only the last messages to fit in the console area
            lines_to_draw = console_messages[-max_lines_in_console:]

            # Draw the text
            text_y = text_rect.y
            for line in lines_to_draw:
                draw_text(line, red, pygame.Rect(text_rect.x, text_y, text_rect.width, line_height), screen,
                          text_font=console_font)
                text_y += line_height

        elif game_started and not repair_mode: # Вывод "концовки"
            if ending_text_index > 0:
                ending_text_timer += 1
                text_y = console_rect.y + 20
                for i in range(ending_text_index):
                    if i < len(ending_text) - 1:
                        color = red
                    else:
                        color = bright_red
                    draw_text(ending_text[i], color, pygame.Rect(console_rect.x + 10, text_y, console_width - 20, height),
                             screen, text_font=console_font)
                    text_y += console_font.get_height() + 5

            else:
                console_messages = ["SYSTEM: Repair complete.",
                                    "SYSTEM: Audio player is stable.",
                                    "...",
                                    "SYSTEM: The void is gone for now."]
                text_rect = pygame.Rect(console_rect.x + 10, console_rect.y + 10, console_width - 20, height - 20)

                # Calculate the available height for text in the console
                available_height = text_rect.height
                line_height = console_font.get_linesize()
                max_lines_in_console = available_height // line_height

                # Get only the last messages to fit in the console area
                lines_to_draw = console_messages[-max_lines_in_console:]

                # Draw the text
                text_y = text_rect.y
                for line in lines_to_draw:
                    draw_text(line, green, pygame.Rect(text_rect.x, text_y, text_rect.width, line_height), screen,
                              text_font=console_font)
                    text_y += line_height

        if glitch_effect:
            draw_glitch(screen, intensity=25)
            if time.time() - glitch_start_time > 0.3:
                glitch_effect = False

    #Отрисовка элементов ремонта
    if repair_mode:
        for item, rect, type, index, is_repaired in repair_items:
            screen.blit(item, rect)
            if dragging_item and dragging_item == (item, rect, type, index, repair_items.index((item, rect, type, index, is_repaired))):
                target_x, target_y = target_positions[(item, type, index)]

                # Создаем rect для целевого положения
                target_item_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2, item.get_width(), item.get_height())

                draw_target_indicator(screen, target_item_rect.center, (item.get_width()+10,item.get_height()+10))
            if is_repaired:
                target_x, target_y = target_positions[(item, type, index)]
                target_rect = pygame.Rect(target_x - item.get_width() // 2, target_y - item.get_height() // 2, item.get_width(), item.get_height())
                screen.blit(item,target_rect)


    if error_sound:
        draw_glitch(screen, intensity=25)
        if time.time() - error_sound_timer > 0.1:
            error_sound = False


    if playing and not game_started and not repair_mode:
        timeline_progress += 0.0001
    if timeline_progress >= 1:
        timeline_progress = 0

    if repair_mode and repaired_items >= len(target_positions):
        repair_mode = False
        game_started = False
        show_console = True
        repaired_items = 0
        ending_text_index = 0
        play_button_rect.x += console_width // 2
        stop_button_rect.x += console_width // 2
        rewind_button_rect.x += console_width // 2
        forward_button_rect.x += console_width // 2
        volume_rect.x += console_width // 2
        timeline_rect.x += console_width // 2


    pygame.display.flip()

pygame.quit()
sys.exit()