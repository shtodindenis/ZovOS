import pygame
import time
import sys
import random
import os
from player import Minigame  # Импортируем класс мини-игры

# Инициализация Pygame
pygame.init()

# Размеры экрана (Full HD)
screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode(
    (screen_width, screen_height), pygame.FULLSCREEN)
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

# Шрифты
try:
    font_path = "fond.otf"  # Замените на путь к вашему файлу шрифта Roboto
    font = pygame.font.Font(font_path, 200)
    file_font = pygame.font.Font(font_path, 20)
    window_font = pygame.font.Font(font_path, 30)
    game_font = pygame.font.Font(font_path, 30)
    console_font = pygame.font.Font(font_path, 24)
    context_menu_font = pygame.font.Font(font_path, 24)
except FileNotFoundError:
    font = pygame.font.SysFont(None, 200)
    file_font = pygame.font.SysFont(None, 20)
    window_font = pygame.font.SysFont(None, 30)
    game_font = pygame.font.SysFont(None, 30)
    console_font = pygame.font.SysFont(None, 24)
    context_menu_font = pygame.font.SysFont(None, 24)
    print("Using default system font.")

# Заставка
opening_frames = []
loop_frames = []
try:
    for i in range(10):
        frame = pygame.image.load(os.path.join(
            "opening", f"opening{i}.png")).convert()
        frame = pygame.transform.scale(frame, (screen_width, screen_height))
        opening_frames.append(frame)
    for i in range(10, 14):
        frame = pygame.image.load(os.path.join(
            "opening", f"opening{i}.png")).convert()
        frame = pygame.transform.scale(frame, (screen_width, screen_height))
        loop_frames.append(frame)
except FileNotFoundError:
    print("Error: opening frames not found. Please make sure the 'opening' folder and the images exist.")
    pygame.quit()
    sys.exit()

# Параметры анимации
frame_duration = 0.2  # Длительность одного кадра в секундах
startup_duration = 5  # Общая длительность заставки в секундах
current_frame = 0
current_loop_frame = 0
frame_time = 0
loop_frame_time = 0
show_startup = True
show_loop = False

# Фон
background_image = pygame.image.load("zovosbg.png").convert()
background_image = pygame.transform.scale(
    background_image, (screen_width, screen_height))

# Параметры свечения
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
        self.title_rect = self.title_surface.get_rect(
            center=self.title_bar.center)

        self.close_button_size = 20
        self.close_button_x = x + width - self.close_button_size - 10
        self.close_button_y = y + 15
        # Изменения для крестика
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
        self.minigame = None
        self.content = ""

    def draw(self, screen):
        if self.is_open:
            pygame.draw.rect(screen, white, self.title_bar)
            screen.blit(self.title_surface, self.title_rect)
            pygame.draw.rect(screen, red, self.close_button_rect)
            # Рисуем крестик поверх красного квадрата
            screen.blit(self.close_cross_surface,
                        self.close_button_rect.topleft)
            pygame.draw.rect(screen, white, self.rect)

            if self.minigame:
                self.minigame.draw(screen.subsurface(self.rect))
            elif self.title.endswith(".txt"):
                # Отрисовка текста из текстового файла
                y_offset = 10
                for line in self.content.split('\n'):
                    text_surface = file_font.render(line, True, black)
                    screen.blit(text_surface, (self.rect.x +
                                10, self.rect.y + y_offset))
                    y_offset += file_font.get_height() + 5

    def handle_event(self, event, windows):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
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
                # Ограничение перемещения окна пределами экрана
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
        if self.minigame:
            self.minigame.handle_event(event, windows)

# Класс файла рабочего стола


class DesktopFile:
    def __init__(self, name, image_path, x, y):
        self.name = name
        if image_path:
            self.image = pygame.image.load(image_path).convert_alpha()
        else:
            self.image = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.rect(self.image, white, (0, 0, 64, 64))
            pygame.draw.rect(self.image, black, (0, 0, 64, 64), 1)

            text_surface = file_font.render(".txt", True, black)
            text_rect = text_surface.get_rect(center=(32, 32))
            self.image.blit(text_surface, text_rect)

        self.rect = self.image.get_rect(topleft=(x, y))
        self.selected = False
        self.dragging = False
        self.name_surface = file_font.render(self.name, True, white)
        self.name_rect = self.name_surface.get_rect(
            center=(self.rect.centerx, self.rect.bottom + 20))

        # Рассчитываем размер рамки выделения
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

        self.content = ""

    def draw(self, screen):
        if not self.is_in_trash:
            screen.blit(self.image, self.rect)
            screen.blit(self.name_surface, self.name_rect)
            if self.selected:
                pygame.draw.rect(self.selection_surface, dark_blue,
                                 self.selection_surface.get_rect(), border_radius=5)
                pygame.draw.rect(self.selection_surface, white,
                                 self.selection_surface.get_rect(), 1, border_radius=5)
                screen.blit(self.selection_surface, self.selection_rect)

    def handle_event(self, event, files, windows):
        if not self.is_in_trash:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка мыши
                    if self.selection_rect.collidepoint(event.pos):
                        current_time = time.time()

                        if current_time - self.last_click_time < self.double_click_interval:
                            self.open_file(files, windows)
                            for file in files:  # Убираем выделение после открытия
                                file.selected = False
                        else:
                            self.selected = True
                            for file in files:
                                if file != self:
                                    file.selected = False
                            self.dragging = True

                        self.last_click_time = current_time
                    else:
                        # Сбрасываем выделение, если клик был вне файла
                        clicked_on_file = False
                        for file in files:
                            if file.selection_rect.collidepoint(event.pos):
                                clicked_on_file = True
                                break
                        if not clicked_on_file:
                            self.selected = False
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    self.rect.center = event.pos
                    self.name_rect.center = (
                        self.rect.centerx, self.rect.bottom + 20)

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
            new_window.minigame = Minigame(
                new_window.rect, game_font, console_font)
            windows.append(new_window)
        elif self.name.endswith(".txt"):
            new_window = Window(self.name, 600, 400, 200, 200)
            new_window.content = self.content
            windows.append(new_window)
# Класс корзины


class Trash:
    def __init__(self, x, y):
        self.image = pygame.image.load("musor.png").convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.selected = False
        self.dragging = False
        self.name_surface = file_font.render("Корзина", True, white)
        self.name_rect = self.name_surface.get_rect(
            center=(self.rect.centerx, self.rect.bottom + 20))

        # Рассчитываем размер рамки выделения
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
            pygame.draw.rect(self.selection_surface, dark_blue,
                             self.selection_surface.get_rect(), border_radius=5)
            pygame.draw.rect(self.selection_surface, white,
                             self.selection_surface.get_rect(), 1, border_radius=5)
            screen.blit(self.selection_surface, self.selection_rect)

    def handle_event(self, event, files):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                if self.selection_rect.collidepoint(event.pos):
                    self.selected = True
                    for file in files:
                        file.selected = False
                else:
                    self.selected = False

        elif event.type == pygame.MOUSEMOTION:
            for file in files:
                if file.dragging and file.rect.colliderect(self.rect):
                    file.is_in_trash = True
                    files.remove(file)
                    break

# Класс контекстного меню


class ContextMenu:
    def __init__(self, x, y, options):
        self.x = x
        self.y = y
        self.options = options
        self.width = 150
        self.item_height = 30
        self.height = len(options) * self.item_height
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.selected_option = -1
        self.is_open = True  # Добавляем атрибут is_open

        # Шрифты (убедитесь, что у вас правильно настроены шрифты в основной части кода)
        try:
            font_path = "fond.otf"  # Замените на путь к вашему файлу шрифта
            self.context_menu_font = pygame.font.Font(font_path, 24)
        except FileNotFoundError:
            self.context_menu_font = pygame.font.SysFont(None, 24)
            print("Using default system font for ContextMenu.")

    def draw(self, screen):
        if self.is_open:
            light_gray = (150, 150, 150)
            black = (0, 0, 0)
            white = (255, 255, 255)

            pygame.draw.rect(screen, white, self.rect)
            pygame.draw.rect(screen, black, self.rect, 1)

            for i, option in enumerate(self.options):
                text_surface = self.context_menu_font.render(
                    option, True, black)
                text_rect = text_surface.get_rect(
                    topleft=(self.x + 10, self.y + i * self.item_height + 5))

                if i == self.selected_option:
                    pygame.draw.rect(screen, light_gray, (self.x, self.y +
                                     i * self.item_height, self.width, self.item_height))

                screen.blit(text_surface, text_rect)

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
                    if self.options[self.selected_option] == "Создать .txt":
                        new_file_name = "Новый файл.txt"
                        # Проверяем, существует ли файл. Если да, добавляем число к имени
                        counter = 1
                        while os.path.exists(new_file_name):
                            new_file_name = f"Новый файл ({counter}).txt"
                            counter += 1
                        # Получаем позицию курсора мыши
                        mouse_x, mouse_y = pygame.mouse.get_pos()

                        # Создаём новый файл DesktopFile в позиции курсора
                        new_file = DesktopFile(
                            new_file_name, "txtfile.png", mouse_x, mouse_y)

                        # Создаём пустой файл в файловой системе
                        open(new_file_name, 'w').close()

                        files.append(new_file)

                    # Закрываем меню сразу после обработки нажатия
                    self.is_open = False
                    self.selected_option = -1

    def close(self):
        self.is_open = False


# Создание тестового файла
files = [DesktopFile("ВЯЧ.py", "py.png", 100, 100),
         DesktopFile("Настройки", "nastoiku.png", 1800, 200)
         ]

trash = Trash(1800, 10)

windows = []
context_menu = None
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:  # Правая кнопка мыши
                context_menu = ContextMenu(
                    event.pos[0], event.pos[1], ["Создать .txt"])
            elif event.button == 1:  # Левая кнопка мыши
                # Закрыть контекстное меню, если клик был вне его области
                if context_menu and context_menu.is_open and not context_menu.rect.collidepoint(event.pos):
                    context_menu.close()

                # Обработка событий для контекстного меню
                if context_menu and context_menu.is_open:
                    context_menu.handle_event(event, files, windows)

        # Обрабатываем события файлов только если контекстное меню не открыто
        if not (context_menu and context_menu.is_open):
            for file in files:
                file.handle_event(event, files, windows)

        for window in windows:
            window.handle_event(event, windows)
        trash.handle_event(event, files)

    if show_startup:
        current_time = time.time()
        if frame_time == 0:
            frame_time = current_time

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
    elif show_loop:
        current_time = time.time()
        if current_time - loop_frame_time >= frame_duration:
            current_loop_frame = (current_loop_frame + 1) % len(loop_frames)
            loop_frame_time = current_time

        screen.blit(loop_frames[current_loop_frame], (0, 0))

        if current_time - frame_time >= startup_duration:
            show_loop = False

    else:
        screen.blit(background_image, (0, 0))

        # Рисуем все элементы в нужном порядке
        if context_menu and context_menu.is_open:
            context_menu.draw(screen)
        for file in files:
            file.draw(screen)
        trash.draw(screen)
        for window in windows:
            window.draw(screen)

        # удаление закрытых окон
        windows = [window for window in windows if window.is_open]

    pygame.display.flip()
    clock.tick(60)  # Ограничение FPS

pygame.quit()
