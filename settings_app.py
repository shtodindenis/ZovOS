# settings_app.py
import pygame
import os
import sqlite3  # Import sqlite3 for settings persistence

pygame.font.init()

light_blue_grey = (220, 230, 240)
black = (0, 0, 0)
white = (255, 255, 255)
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
settings_font = get_font(font_path, 20)  # Font for settings text


# Database functions (duplicate from main.py for simplicity)
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


class SettingsApp:
    def __init__(self):
        self.settings_options_rects = {}
        self.settings_options = ["Background 1", "Background 2",
                                 "Background 3", "Color"]  # "Color" option is kept but not functional in this version
        self.settings_option_positions = {}
        self.background_previews = {}
        self.load_background_previews()
        self.settings_section_title_font = get_font(
            font_path, 24)  # Initialize font here
        self.width = 600  # Define width for SettingsApp window
        self.height = 600  # Define height for SettingsApp window

        self.layout_options_rects = {}  # For layout options buttons
        self.current_layout = get_setting(
            'icon_layout', 'grid')  # Load current layout from DB, default to 'grid'

        self.layout_grid_rect = None
        self.layout_free_rect = None

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
        # "color" option preview - using a placeholder, not functional in image change
        self.background_previews["color"] = pygame.Surface(preview_size)
        self.background_previews["color"].fill(
            light_blue_grey)  # Placeholder color

    def draw(self, screen_surface):
        screen_rect = screen_surface.get_rect()
        section_title_y_offset = 20
        start_x = screen_rect.x + 20
        current_y = screen_rect.y + section_title_y_offset

        # Background Section
        section_title_surface = self.settings_section_title_font.render(
            "Фон", True, black)
        section_title_rect = section_title_surface.get_rect(
            topleft=(start_x, current_y))
        screen_surface.blit(section_title_surface, section_title_rect)

        current_y += section_title_rect.height + 10
        x_offset_start = start_x
        option_margin_x = 20
        option_margin_y = 30

        background_options = ["zovosbg.png",
                              # "color" option is kept but not functional
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

        # Icon Layout Section
        current_y += preview_rect.height + option_margin_y
        layout_title_surface = self.settings_section_title_font.render(
            "Размещение значков", True, black)
        layout_title_rect = layout_title_surface.get_rect(
            topleft=(start_x, current_y))
        screen_surface.blit(layout_title_surface, layout_title_rect)

        current_y += layout_title_rect.height + 10

        layout_option_width = 130  # Increased button width to fit text
        layout_option_height = 30
        layout_margin_x = 10

        # "По сетке" button
        grid_layout_rect = pygame.Rect(
            start_x, current_y, layout_option_width, layout_option_height)
        pygame.draw.rect(screen_surface, white, grid_layout_rect)
        pygame.draw.rect(screen_surface, black, grid_layout_rect, 1)
        grid_text_surface = settings_font.render("По сетке", True, black)
        grid_text_rect = grid_text_surface.get_rect(
            center=grid_layout_rect.center)
        screen_surface.blit(grid_text_surface, grid_text_rect)
        self.layout_grid_rect = grid_layout_rect  # Store for event handling

        # "Произвольно" button
        free_layout_rect = pygame.Rect(
            start_x + layout_option_width + layout_margin_x, current_y, layout_option_width, layout_option_height)
        pygame.draw.rect(screen_surface, white, free_layout_rect)
        pygame.draw.rect(screen_surface, black, free_layout_rect, 1)
        free_text_surface = settings_font.render("Произвольно", True, black)
        free_text_rect = free_text_surface.get_rect(
            center=free_layout_rect.center)
        screen_surface.blit(free_text_surface, free_text_rect)
        self.layout_free_rect = free_layout_rect  # Store for event handling

        # Indicate selected layout
        if self.current_layout == 'grid':
            # Highlight grid layout
            pygame.draw.rect(screen_surface, black, grid_layout_rect, 3)
        elif self.current_layout == 'free':
            # Highlight free layout
            pygame.draw.rect(screen_surface, black, free_layout_rect, 3)

        # Restart OS message
        restart_message_surface = settings_font.render(
            "Чтобы изменения вступили в силу, перезапустите ОС", True, black)
        restart_message_rect = restart_message_surface.get_rect(
            # Position at the bottom, centered
            centerx=screen_rect.centerx, bottom=screen_rect.bottom - 20)
        screen_surface.blit(restart_message_surface, restart_message_rect)

    def handle_event(self, mouse_pos, window_rect):
        """Handles mouse events within the settings window.

        Args:
            mouse_pos: The mouse position as a tuple (x, y).
            window_rect: The pygame.Rect of the settings window.

        Returns:
            str or None: The new background setting filename if a background option was clicked, or 'layout_change' if layout changed, otherwise None.
        """
        relative_mouse_pos = (mouse_pos[0] - window_rect.x,
                              # Mouse position relative to the window
                              mouse_pos[1] - window_rect.y)
        for option_key, option_rect in self.settings_options_rects.items():
            if option_rect.collidepoint(relative_mouse_pos):
                if option_key == "zovosbg.png":
                    return "zovosbg.png"
                elif option_key == "zovosbg2.png":
                    return "zovosbg2.png"
                elif option_key == "zovosbg3.png":
                    return "zovosbg3.png"
                # "color" option is kept but not functional for image change
                elif option_key == "color":
                    print(
                        "Color background option selected (not functional for image change in this version)")
                    return "color"  # Still return "color" so main.py can handle it if needed for future color background implementation

        if self.layout_grid_rect and self.layout_grid_rect.collidepoint(relative_mouse_pos):
            if self.current_layout != 'grid':
                self.current_layout = 'grid'
                update_setting('icon_layout', 'grid')
                return 'layout_change'  # Indicate layout change
        elif self.layout_free_rect and self.layout_free_rect.collidepoint(relative_mouse_pos):
            if self.current_layout != 'free':
                self.current_layout = 'free'
                update_setting('icon_layout', 'free')
                return 'layout_change'  # Indicate layout change

        return None  # No background or layout option clicked
