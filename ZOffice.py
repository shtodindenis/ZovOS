import time

import pygame

pygame.font.init()

black = (0, 0, 0)
white = (255, 255, 255)
window_color = white
text_color = black
selection_color = (200, 200, 200)
ribbon_color = (220, 220, 220)
font_path = "main_font.otf"  # Assuming this font exists, if not, use a system font
ztext_font = pygame.font.Font(font_path, 24) if font_path and pygame.font.match_font(
    font_path) else pygame.font.SysFont(None, 24)
ztable_cell_font = pygame.font.Font(font_path, 32) if font_path and pygame.font.match_font(
    font_path) else pygame.font.SysFont(None, 32)


def draw_rect(surface, color, rect, border_width=0, border_radius=0):
    pygame.draw.rect(surface, color, rect, border_width, border_radius)


def draw_text(surface, text, font, color, position, alignment='topleft'):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(**{alignment: position})
    surface.blit(text_surface, text_rect)
    return text_rect


class Cell:
    def __init__(self, rect, text=""):
        self.rect = rect
        self.text = text
        self.is_editing = False
        self.cursor_pos = 0
        self.cursor_visible = True
        self.cursor_time = time.time()
        self.font = ztable_cell_font
        self.text_color = black
        self.char_limit_per_line = 15

        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False

    def _get_char_index_from_pos(self, pos):
        lines = self.text.split('\n')
        y_offset = self.rect.y + 2
        char_count = 0
        for line_num, line in enumerate(lines):
            line_height = self.font.get_height()
            if y_offset <= pos[1] < y_offset + line_height:
                x_offset = self.rect.x + 2
                for char_index_in_line in range(len(line) + 1):
                    char_width = self.font.size(line[:char_index_in_line])[0]
                    if x_offset + char_width >= pos[0]:
                        return char_count + char_index_in_line
                    x_offset += char_width
                return char_count + len(line)
            y_offset += line_height
            char_count += len(line) + 1
        return len(self.text)

    def draw(self, surface):
        draw_rect(surface, white, self.rect)
        draw_rect(surface, black, self.rect, 1)

        lines = []
        current_line = ""
        for char in self.text:
            if char == '\n':
                lines.append(current_line)
                current_line = ""
            else:
                current_line += char
                if len(current_line) > self.char_limit_per_line:
                    lines.append(current_line)
                    current_line = ""
        lines.append(current_line)

        y_offset = self.rect.y + 2
        char_index = 0
        for line_num, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.text_color)
            text_rect = text_surface.get_rect(topleft=(self.rect.x + 2, y_offset))

            if self.selection_start is not None and self.selection_end is not None:
                selection_start = min(self.selection_start, self.selection_end)
                selection_end = max(self.selection_start, self.selection_end)

                line_start_index = char_index
                line_end_index = char_index + len(line)

                if selection_start < line_end_index and selection_end > line_start_index:
                    start_in_line = max(0, selection_start - line_start_index)
                    end_in_line = min(len(line), selection_end - line_start_index)

                    start_pos = self.rect.x + 2 + self.font.size(line[:start_in_line])[0]
                    end_pos = self.rect.x + 2 + self.font.size(line[:end_in_line])[0]
                    selection_rect = pygame.Rect(start_pos, y_offset, end_pos - start_pos, self.font.get_height())
                    draw_rect(surface, selection_color, selection_rect)

            surface.blit(text_surface, text_rect)
            y_offset += self.font.get_height()
            char_index += len(line) + 1

        if self.is_editing:
            if time.time() - self.cursor_time > 0.5:
                self.cursor_visible = not self.cursor_visible
                self.cursor_time = time.time()

            if self.cursor_visible:
                lines = self.text.split('\n')
                line_num = 0
                char_in_line = 0
                char_count = 0
                for i, line_render in enumerate(lines):
                    if char_count + len(line_render) >= self.cursor_pos:
                        line_num = i
                        char_in_line = self.cursor_pos - char_count
                        break
                    char_count += len(line_render) + 1

                cursor_x = self.rect.x + 2 + self.font.size(lines[line_num][:char_in_line])[0]
                cursor_y = self.rect.y + 2 + line_num * self.font.get_height()
                pygame.draw.line(surface, self.text_color, (cursor_x, cursor_y),
                                 (cursor_x, cursor_y + self.font.get_height()), 1)

    def handle_input(self, event):
        if not self.is_editing:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    char_index = self._get_char_index_from_pos(event.pos)
                    self.selection_start = char_index
                    self.selection_end = char_index
                    self.is_selecting = True
                    return True
            return False

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_selecting = False
                if self.selection_start == self.selection_end:
                    self.selection_start = None
                    self.selection_end = None
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.is_selecting:
                if self.rect.collidepoint(event.pos):
                    self.selection_end = self._get_char_index_from_pos(event.pos)
                else:
                    if event.pos[0] < self.rect.left:
                        self.selection_end = 0
                    elif event.pos[0] > self.rect.right:
                        self.selection_end = len(self.text)
                    elif event.pos[1] < self.rect.top:
                        self.selection_end = 0
                    elif event.pos[1] > self.rect.bottom:
                        self.selection_end = len(self.text)
                return True

        if event.type == pygame.KEYDOWN:
            if self.selection_start is not None and self.selection_end is not None:
                sel_start = min(self.selection_start, self.selection_end)
                sel_end = max(self.selection_start, self.selection_end)
                if event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
                    self.text = self.text[:sel_start] + self.text[sel_end:]
                    self.cursor_pos = sel_start
                    self.selection_start = None
                    self.selection_end = None
                elif event.unicode:
                    self.text = self.text[:sel_start] + event.unicode + self.text[sel_end:]
                    self.cursor_pos = sel_start + 1
                    self.selection_start = None
                    self.selection_end = None
                else:
                    self.selection_start = None
                    self.selection_end = None
            else:
                if event.key == pygame.K_LEFT:
                    self.cursor_pos = max(0, self.cursor_pos - 1)
                    self.selection_start = None
                    self.selection_end = None
                elif event.key == pygame.K_RIGHT:
                    self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
                    self.selection_start = None
                    self.selection_end = None
                elif event.key == pygame.K_UP:
                    lines = self.text.split('\n')
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
                    self.selection_start = None
                    self.selection_end = None

                elif event.key == pygame.K_DOWN:
                    lines = self.text.split('\n')
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
                        self.cursor_pos = len(self.text)
                    self.selection_start = None
                    self.selection_end = None
                elif event.key == pygame.K_BACKSPACE:
                    if self.cursor_pos > 0:
                        self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
                        self.cursor_pos -= 1
                    self.selection_start = None
                    self.selection_end = None
                elif event.key == pygame.K_DELETE:
                    if self.cursor_pos < len(self.text):
                        self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
                    self.selection_start = None
                    self.selection_end = None
                elif event.key == pygame.K_RETURN:
                    self.text = self.text[:self.cursor_pos] + '\n' + self.text[self.cursor_pos:]
                    self.cursor_pos += 1
                    self.selection_start = None
                    self.selection_end = None
                elif event.unicode and self.font.render(self.text[:self.cursor_pos] + event.unicode, True,
                                                        black).get_width() < self.rect.width - 4:
                    self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                    self.cursor_pos += 1
                    self.selection_start = None
                    self.selection_end = None

            self.cursor_visible = True
            self.cursor_time = time.time()
            return True

        return False


class ZTextApp:
    def __init__(self):
        self.width = 800
        self.height = 600
        # Changed to list of characters with formatting
        default_font_name = self._get_default_font_name()
        self.text_content = [{"char": "",
                              "font_name": default_font_name,
                              "font_size": 24,
                              "font_bold": False,
                              "font_italic": False,
                              "font_underline": False,
                              "font_strikethrough": False,
                              "text_color": text_color}] * 1  # Start with one empty char with default format
        self.font_name = default_font_name  # Current formatting attributes for new characters
        self.font_size = 24
        self.font_bold = False
        self.font_italic = False
        self.font_underline = False
        self.font_strikethrough = False
        self.text_color = text_color
        self.current_font = self._update_font_style()  # Current font object based on current formatting

        self.cursor_pos = 0
        self.cursor_visible = True
        self.cursor_time = time.time()
        self.char_limit_per_line = 80

        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False

        self.ribbon_height = 50
        self.ribbon_color = ribbon_color
        self.text_start_y = self.ribbon_height + 10

        # Ribbon UI elements
        self.button_width = 50
        self.button_height = 30
        self.button_spacing = 5
        self.ribbon_buttons = {}
        self.init_ribbon_buttons()

        self.color_picker_active = False
        self.color_picker_pos = (100, 100)
        self.color_picker_image = pygame.image.load("Images/color_circle.bmp") if pygame.image.get_sdl_image_version()[
                                                                                      0] >= 2 else None
        self.color_picker_rect = pygame.Rect(self.color_picker_pos,
                                             self.color_picker_image.get_size()) if self.color_picker_image else None

    def _get_default_font_name(self):
        return "main_font.otf"  # Or any default font name you prefer

    def init_ribbon_buttons(self):
        x_offset = 10
        y_offset = 10

        # Font name display
        self.ribbon_buttons['font_name_label_rect'] = pygame.Rect(x_offset, y_offset, 150, self.button_height)
        x_offset += 150 + self.button_spacing

        # Font size decrease button
        self.ribbon_buttons['font_size_down_rect'] = pygame.Rect(x_offset, y_offset, 20, self.button_height)
        x_offset += 20 + self.button_spacing

        # Font size display
        self.ribbon_buttons['font_size_label_rect'] = pygame.Rect(x_offset, y_offset, 30, self.button_height)
        x_offset += 30 + self.button_spacing

        # Font size increase button
        self.ribbon_buttons['font_size_up_rect'] = pygame.Rect(x_offset, y_offset, 20, self.button_height)
        x_offset += 20 + self.button_spacing

        # Bold button
        self.ribbon_buttons['bold_rect'] = pygame.Rect(x_offset, y_offset, self.button_width, self.button_height)
        x_offset += self.button_width + self.button_spacing

        # Italic button
        self.ribbon_buttons['italic_rect'] = pygame.Rect(x_offset, y_offset, self.button_width, self.button_height)
        x_offset += self.button_width + self.button_spacing

        # Underline button
        self.ribbon_buttons['underline_rect'] = pygame.Rect(x_offset, y_offset, self.button_width, self.button_height)
        x_offset += self.button_width + self.button_spacing

        # Strikethrough button
        self.ribbon_buttons['strikethrough_rect'] = pygame.Rect(x_offset, y_offset, self.button_width + 20,
                                                                self.button_height)
        x_offset += self.button_width + 20 + self.button_spacing

        # Color button
        self.ribbon_buttons['color_rect'] = pygame.Rect(x_offset, y_offset, self.button_width, self.button_height)
        x_offset += self.button_width + self.button_spacing

    def _update_font_style(self):
        try:
            font = pygame.font.Font(self.font_name, self.font_size) if self.font_name and pygame.font.match_font(
                self.font_name) else pygame.font.SysFont(None, self.font_size)
        except IOError:
            font = pygame.font.SysFont(None, self.font_size)
        font.set_bold(self.font_bold)
        font.set_italic(self.font_italic)
        font.set_underline(self.font_underline)
        return font

    def _get_font_for_char(self, char_data):
        try:
            font = pygame.font.Font(char_data["font_name"], char_data["font_size"]) if char_data[
                                                                                           "font_name"] and pygame.font.match_font(
                char_data["font_name"]) else pygame.font.SysFont(None, char_data["font_size"])
        except IOError:
            font = pygame.font.SysFont(None, char_data["font_size"])
        font.set_bold(char_data["font_bold"])
        font.set_italic(char_data["font_italic"])
        font.set_underline(char_data["font_underline"])
        return font

    def _get_char_index_from_pos(self, pos):
        text_area_y_offset = self.text_start_y
        lines = []
        char_indices_per_line = []  # Store start index of each line in text_content
        current_line_chars = 0

        y_offset = text_area_y_offset
        char_count_global = 0

        current_line = []
        line_start_index = 0

        for char_index, char_data in enumerate(self.text_content):
            char = char_data["char"]
            char_font = self._get_font_for_char(char_data)

            if char == '\n':
                lines.append(current_line)
                char_indices_per_line.append(line_start_index)
                current_line = []
                line_start_index = char_index + 1
            else:
                current_line.append(char_data)
                if len("".join([c_data['char'] for c_data in
                                current_line])) > self.char_limit_per_line:  # Basic word wrap - needs improvement for real word wrap
                    wrapped_line = current_line[:-1]  # Exclude last char which caused overflow
                    lines.append(wrapped_line)
                    char_indices_per_line.append(line_start_index)
                    current_line = current_line[-1:]  # Start new line with the overflowing char
                    line_start_index = char_index - len(wrapped_line)

        lines.append(current_line)  # Add the last line
        char_indices_per_line.append(line_start_index)

        line_num = 0
        for line_index in range(len(lines)):
            line = lines[line_index]
            if not line:
                line_height = self._get_font_for_char(self.text_content[
                                                          char_indices_per_line[line_index] if char_indices_per_line[
                                                                                                   line_index] < len(
                                                              self.text_content) else 0]).get_height() + 5
            else:
                line_height = self._get_font_for_char(line[0]).get_height() + 5

            if y_offset <= pos[1] < y_offset + line_height:
                x_offset = 10
                char_index_in_line_start = char_indices_per_line[line_index]
                for char_in_line_index in range(len(line) + 1):  # +1 to check after last char
                    line_text_segment = "".join([c_data['char'] for c_data in line[:char_in_line_index]])
                    char_font = self._get_font_for_char(line[char_in_line_index - 1] if char_in_line_index > 0 else (
                        self.text_content[char_indices_per_line[line_index]] if char_indices_per_line[line_index] < len(
                            self.text_content) else self.text_content[0]))

                    char_width = char_font.size(line_text_segment)[0]
                    if x_offset + char_width >= pos[0]:
                        return char_index_in_line_start + char_in_line_index
                    x_offset += char_width
                return char_index_in_line_start + len(line)
            y_offset += line_height
        return self.get_total_text_length()

    def draw_ribbon(self, surface):
        draw_rect(surface, self.ribbon_color, pygame.Rect(0, 0, self.width, self.ribbon_height))

        button_font = pygame.font.SysFont(None, 20)

        # Font Name Label
        draw_rect(surface, white, self.ribbon_buttons['font_name_label_rect'], 1)
        draw_text(surface, self.font_name, button_font, black, self.ribbon_buttons['font_name_label_rect'].topleft,
                  'topleft')

        # Font Size Down Button
        draw_rect(surface, white, self.ribbon_buttons['font_size_down_rect'], 1)
        draw_text(surface, "-", button_font, black, self.ribbon_buttons['font_size_down_rect'].center, 'center')

        # Font Size Label
        draw_rect(surface, white, self.ribbon_buttons['font_size_label_rect'], 1)
        draw_text(surface, str(self.font_size), button_font, black, self.ribbon_buttons['font_size_label_rect'].center,
                  'center')

        # Font Size Up Button
        draw_rect(surface, white, self.ribbon_buttons['font_size_up_rect'], 1)
        draw_text(surface, "+", button_font, black, self.ribbon_buttons['font_size_up_rect'].center, 'center')

        # Bold Button
        bold_button_color = selection_color if self.font_bold else white
        draw_rect(surface, bold_button_color, self.ribbon_buttons['bold_rect'], 1)
        draw_text(surface, "Bold", button_font, black, self.ribbon_buttons['bold_rect'].center, 'center')

        # Italic Button
        italic_button_color = selection_color if self.font_italic else white
        draw_rect(surface, italic_button_color, self.ribbon_buttons['italic_rect'], 1)
        draw_text(surface, "Italic", button_font, black, self.ribbon_buttons['italic_rect'].center, 'center')

        # Underline Button
        underline_button_color = selection_color if self.font_underline else white
        draw_rect(surface, underline_button_color, self.ribbon_buttons['underline_rect'], 1)
        draw_text(surface, "Underline", button_font, black, self.ribbon_buttons['underline_rect'].center, 'center')

        # Strikethrough Button
        strikethrough_button_color = selection_color if self.font_strikethrough else white
        draw_rect(surface, strikethrough_button_color, self.ribbon_buttons['strikethrough_rect'], 1)
        draw_text(surface, "Strike", button_font, black, self.ribbon_buttons['strikethrough_rect'].center, 'center')

        # Color Button
        draw_rect(surface, white, self.ribbon_buttons['color_rect'], 1)
        draw_text(surface, "Color", button_font, black, self.ribbon_buttons['color_rect'].center, 'center')

        if self.color_picker_active and self.color_picker_image:
            surface.blit(self.color_picker_image, self.color_picker_pos)
        elif self.color_picker_active and not self.color_picker_image:
            draw_text(surface, "Color Picker Image Not Loaded (Pygame < 2)", button_font, black,
                      (self.ribbon_buttons['color_rect'].right + 10, 10), 'topleft')

    def draw(self, screen_surface):
        draw_rect(screen_surface, window_color, screen_surface.get_rect())
        self.draw_ribbon(screen_surface)

        line_y_offset = self.text_start_y

        lines = []
        char_indices_per_line = []  # Store start index of each line in text_content
        current_line_chars = 0

        y_offset = self.text_start_y
        char_count_global = 0

        current_line = []
        line_start_index = 0

        for char_index, char_data in enumerate(self.text_content):
            char = char_data["char"]
            char_font = self._get_font_for_char(char_data)

            if char == '\n':
                lines.append(current_line)
                char_indices_per_line.append(line_start_index)
                current_line = []
                line_start_index = char_index + 1
            else:
                current_line.append(char_data)
                if len("".join([c_data['char'] for c_data in
                                current_line])) > self.char_limit_per_line:  # Basic word wrap - needs improvement for real word wrap
                    wrapped_line = current_line[:-1]  # Exclude last char which caused overflow
                    lines.append(wrapped_line)
                    char_indices_per_line.append(line_start_index)
                    current_line = current_line[-1:]  # Start new line with the overflowing char
                    line_start_index = char_index - len(wrapped_line)

        lines.append(current_line)  # Add the last line
        char_indices_per_line.append(line_start_index)

        line_y_offset = self.text_start_y
        char_index_global = 0
        lines_data_for_cursor = []  # Store line info for cursor positioning

        for line_index in range(len(lines)):
            line = lines[line_index]
            line_start_global_index = char_indices_per_line[line_index]

            if not line:
                line_height = self._get_font_for_char(
                    self.text_content[line_start_global_index] if line_start_global_index < len(self.text_content) else
                    self.text_content[0]).get_height() + 5
                line_y_offset += line_height
                continue  # Skip drawing empty lines

            line_x_offset = 10
            first_char_font = self._get_font_for_char(line[0])
            line_height = first_char_font.get_height() + 5
            lines_data_for_cursor.append({'line_start_index': line_start_global_index, 'y_offset': line_y_offset,
                                          'font': first_char_font})  # Use first char's font as representative

            for char_data in line:
                char_font = self._get_font_for_char(char_data)
                char_surface = char_font.render(char_data["char"], True, char_data["text_color"])
                if char_data["font_strikethrough"]:
                    strike_pos = char_surface.get_height() // 2
                    pygame.draw.line(char_surface, char_data["text_color"], (0, strike_pos),
                                     (char_surface.get_width(), strike_pos), 2)
                text_rect = char_surface.get_rect(topleft=(line_x_offset, line_y_offset))

                # Selection drawing - needs adjustment for char-level
                if self.selection_start is not None and self.selection_end is not None:
                    selection_start = min(self.selection_start, self.selection_end)
                    selection_end = max(self.selection_start, self.selection_end)

                    char_global_index = line_start_global_index + line.index(char_data)

                    if selection_start <= char_global_index < selection_end:
                        selection_rect = pygame.Rect(line_x_offset, line_y_offset, char_surface.get_width(),
                                                     char_surface.get_height())
                        draw_rect(screen_surface, selection_color, selection_rect)

                screen_surface.blit(char_surface, text_rect)
                if char_data["font_underline"]:
                    underline_y_pos = line_y_offset + char_surface.get_height()
                    pygame.draw.line(screen_surface, char_data["text_color"], (text_rect.left, underline_y_pos),
                                     (text_rect.right, underline_y_pos), 2)
                line_x_offset += char_surface.get_width()
                char_index_global += 1  # Global char index incremented per char drawn

            line_y_offset += line_height

        if time.time() - self.cursor_time > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_time = time.time()

        if self.cursor_visible and self.selection_start is None:
            line_num = 0
            char_in_line_in_total_text = 0
            char_count_total = 0

            lines_total_text = []
            for line_data in lines_data_for_cursor:
                line_start_index = line_data['line_start_index']
                line_end_index = line_start_index
                current_line_chars = []
                while line_end_index < len(self.text_content) and self.text_content[line_end_index]['char'] != '\n':
                    current_line_chars.append(self.text_content[line_end_index]['char'])
                    line_end_index += 1
                lines_total_text.append("".join(current_line_chars))

            for i, line_render in enumerate(lines_total_text):
                if char_count_total + len(line_render) >= self.cursor_pos:
                    line_num = i
                    char_in_line_in_total_text = self.cursor_pos - char_count_total
                    break
                char_count_total += len(line_render) + 1  # +1 for newline

            if lines_data_for_cursor and line_num < len(lines_data_for_cursor):  # Check if line_num is valid
                cursor_line_data = lines_data_for_cursor[line_num]
                cursor_font = cursor_line_data['font']
                cursor_y = cursor_line_data['y_offset']

                line_start_index_global = cursor_line_data['line_start_index']
                cursor_x = 10
                char_index_in_line = 0

                current_char_index_global = line_start_index_global
                while current_char_index_global < len(self.text_content) and \
                        self.text_content[current_char_index_global]['char'] != '\n':
                    if char_index_in_line == char_in_line_in_total_text:
                        break
                    char_font = self._get_font_for_char(self.text_content[current_char_index_global])
                    cursor_x += char_font.size(self.text_content[current_char_index_global]['char'])[0]
                    char_index_in_line += 1
                    current_char_index_global += 1

                pygame.draw.line(screen_surface, self.text_color, (cursor_x, cursor_y),
                                 (cursor_x, cursor_y + cursor_font.get_height()), 2)

    def handle_ribbon_click(self, mouse_pos_relative):
        if self.ribbon_buttons['bold_rect'].collidepoint(mouse_pos_relative):
            self.font_bold = not self.font_bold
            self.current_font = self._update_font_style()
        elif self.ribbon_buttons['italic_rect'].collidepoint(mouse_pos_relative):
            self.font_italic = not self.font_italic
            self.current_font = self._update_font_style()
        elif self.ribbon_buttons['underline_rect'].collidepoint(mouse_pos_relative):
            self.font_underline = not self.font_underline
            self.current_font = self._update_font_style()
        elif self.ribbon_buttons['strikethrough_rect'].collidepoint(mouse_pos_relative):
            self.font_strikethrough = not self.font_strikethrough
            self.current_font = self._update_font_style()
        elif self.ribbon_buttons['font_size_up_rect'].collidepoint(mouse_pos_relative):
            self.font_size = min(72, self.font_size + 2)
            self.current_font = self._update_font_style()
        elif self.ribbon_buttons['font_size_down_rect'].collidepoint(mouse_pos_relative):
            self.font_size = max(8, self.font_size - 2)
            self.current_font = self._update_font_style()
        elif self.ribbon_buttons['color_rect'].collidepoint(mouse_pos_relative):
            self.color_picker_active = not self.color_picker_active
        elif self.color_picker_active and self.color_picker_image and self.color_picker_rect.collidepoint(
                mouse_pos_relative):
            picker_rect = self.color_picker_rect
            local_x = mouse_pos_relative[0] - picker_rect.x
            local_y = mouse_pos_relative[1] - picker_rect.y
            try:
                pixel_array = pygame.PixelArray(self.color_picker_image)
                clicked_color = self.color_picker_image.unmap_rgb(pixel_array[local_x, local_y])
                self.text_color = clicked_color
                pixel_array.close()
            except IndexError:
                pass
            self.color_picker_active = False

    def get_total_text_length(self):
        return len(self.text_content)

    def handle_event(self, event, window_rect):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos_relative = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                if mouse_pos_relative[1] < self.ribbon_height:
                    if self.color_picker_active and self.color_picker_image and self.color_picker_rect.collidepoint(
                            mouse_pos_relative):
                        self.handle_ribbon_click(mouse_pos_relative)
                    elif not self.color_picker_active:
                        self.handle_ribbon_click(mouse_pos_relative)
                    self.selection_start = None
                    self.selection_end = None
                    return
                elif self.color_picker_active and self.color_picker_rect and self.color_picker_rect.collidepoint(
                        mouse_pos_relative):
                    self.handle_ribbon_click(mouse_pos_relative)
                    return
                elif self.color_picker_active:
                    self.color_picker_active = False
                    return
                else:
                    char_index = self._get_char_index_from_pos(mouse_pos_relative)
                    self.selection_start = char_index
                    self.selection_end = char_index
                    self.is_selecting = True


        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_selecting = False
                if self.selection_start == self.selection_end:
                    self.selection_start = None
                    self.selection_end = None

        elif event.type == pygame.MOUSEMOTION:
            if self.is_selecting:
                mouse_pos_relative = (event.pos[0] - window_rect.x, event.pos[1] - window_rect.y)
                if mouse_pos_relative[1] < self.ribbon_height:
                    self.selection_end = self.selection_start
                else:
                    self.selection_end = self._get_char_index_from_pos(mouse_pos_relative)

        if event.type == pygame.KEYDOWN:
            if self.selection_start is not None and self.selection_end is not None:
                sel_start = min(self.selection_start, self.selection_end)
                sel_end = max(self.selection_start, self.selection_end)

                if event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
                    if sel_start < sel_end:
                        del self.text_content[sel_start:sel_end]
                        self.cursor_pos = sel_start
                    elif sel_start == sel_end and sel_start < len(self.text_content):
                        del self.text_content[sel_start]  # delete single char at cursor if selection empty
                        self.cursor_pos = sel_start
                    else:
                        self.cursor_pos = max(0, sel_start - 1)

                    self.selection_start = None
                    self.selection_end = None


                elif event.unicode:
                    new_char_data = {
                        "char": event.unicode,
                        "font_name": self.font_name,
                        "font_size": self.font_size,
                        "font_bold": self.font_bold,
                        "font_italic": self.font_italic,
                        "font_underline": self.font_underline,
                        "font_strikethrough": self.font_strikethrough,
                        "text_color": self.text_color
                    }
                    if self.selection_start != self.selection_end and self.selection_start is not None:  # Replace selection
                        sel_start = min(self.selection_start, self.selection_end)
                        sel_end = max(self.selection_start, self.selection_end)
                        del self.text_content[sel_start:sel_end]
                        self.text_content.insert(sel_start, new_char_data)
                        self.cursor_pos = sel_start + 1
                        self.selection_start = None
                        self.selection_end = None
                    else:  # Insert at cursor
                        self.text_content.insert(self.cursor_pos, new_char_data)
                        self.cursor_pos += 1
                        self.selection_start = None
                        self.selection_end = None


                else:
                    self.selection_start = None
                    self.selection_end = None


            else:
                if event.key == pygame.K_LEFT:
                    self.cursor_pos = max(0, self.cursor_pos - 1)
                    self.selection_start = None
                    self.selection_end = None
                elif event.key == pygame.K_RIGHT:
                    self.cursor_pos = min(self.get_total_text_length(), self.cursor_pos + 1)
                    self.selection_start = None
                    self.selection_end = None
                elif event.key == pygame.K_UP:
                    lines = ["".join([c['char'] for c in line_chars]) for line_chars in self._get_lines_for_display()]
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
                    self.selection_start = None
                    self.selection_end = None

                elif event.key == pygame.K_DOWN:
                    lines = ["".join([c['char'] for c in line_chars]) for line_chars in self._get_lines_for_display()]
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
                        self.cursor_pos = self.get_total_text_length()
                    self.selection_start = None
                    self.selection_end = None

                elif event.key == pygame.K_BACKSPACE:
                    if self.cursor_pos > 0:
                        del self.text_content[self.cursor_pos - 1]
                        self.cursor_pos -= 1
                    self.selection_start = None
                    self.selection_end = None


                elif event.key == pygame.K_DELETE:
                    if self.cursor_pos < self.get_total_text_length():
                        del self.text_content[self.cursor_pos]
                    self.selection_start = None
                    self.selection_end = None

                elif event.key == pygame.K_RETURN:
                    new_char_data = {
                        "char": '\n',
                        "font_name": self.font_name,
                        "font_size": self.font_size,
                        "font_bold": self.font_bold,
                        "font_italic": self.font_italic,
                        "font_underline": self.font_underline,
                        "font_strikethrough": self.font_strikethrough,
                        "text_color": self.text_color
                    }
                    self.text_content.insert(self.cursor_pos, new_char_data)
                    self.cursor_pos += 1
                    self.selection_start = None
                    self.selection_end = None


                elif event.unicode and self.current_font.render("W", True,
                                                                black).get_width() > 0 and self.current_font.render("W",
                                                                                                                    True,
                                                                                                                    black).get_width() < window_rect.width - 20:  # Fix to check with 'W' and ensure font is loaded

                    new_char_data = {
                        "char": event.unicode,
                        "font_name": self.font_name,
                        "font_size": self.font_size,
                        "font_bold": self.font_bold,
                        "font_italic": self.font_italic,
                        "font_underline": self.font_underline,
                        "font_strikethrough": self.font_strikethrough,
                        "text_color": self.text_color
                    }
                    self.text_content.insert(self.cursor_pos, new_char_data)
                    self.cursor_pos += 1
                    self.selection_start = None
                    self.selection_end = None

            self.cursor_visible = True
            self.cursor_time = time.time()

    def _get_segment_and_char_index(self, global_char_index):  # Not needed anymore, kept for potential future use
        """
        Returns the segment index and character index within that segment for a given global character index.
        """
        char_count = 0
        for seg_index, segment in enumerate(self.text_content):
            segment_length = len(segment["char"])
            if char_count + segment_length > global_char_index:
                return seg_index, global_char_index - char_count
            char_count += segment_length
        return len(self.text_content) - 1, len(
            self.text_content[-1]["char"]) if self.text_content else 0  # Default to last segment, end of text

    def update_theme(self):
        self.text_color = text_color

    def _get_lines_for_display(self):
        lines = []
        current_line = []

        for char_data in self.text_content:
            char = char_data["char"]
            if char == '\n':
                lines.append(current_line)
                current_line = []
            else:
                current_line.append(char_data)
                if len("".join(
                        [c_data['char'] for c_data in current_line])) > self.char_limit_per_line:  # Basic word wrap
                    wrapped_line = current_line[:-1]
                    lines.append(wrapped_line)
                    current_line = current_line[-1:]
        lines.append(current_line)
        return lines


class ZTableApp:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.rows = 20
        self.cols = 10
        self.cells = []
        self.cell_width = self.width // self.cols
        self.cell_height = self.height // self.rows
        self.active_cell = None
        self._create_cells()

    def _create_cells(self):
        self.cells = []
        for row in range(self.rows):
            for col in range(self.cols):
                rect = pygame.Rect(col * self.cell_width, row * self.cell_height, self.cell_width, self.cell_height)
                self.cells.append(Cell(rect))

    def draw(self, screen_surface):
        draw_rect(screen_surface, window_color, screen_surface.get_rect())
        for cell in self.cells:
            cell.draw(screen_surface)

    def handle_event(self, event, window_rect):
        if self.active_cell and self.active_cell.is_editing:
            if self.active_cell.handle_input(event):
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos_global = event.pos
            mouse_pos_relative = (mouse_pos_global[0] - window_rect.x, mouse_pos_global[1] - window_rect.y)
            clicked_cell = None
            for cell in self.cells:
                if cell.rect.collidepoint(mouse_pos_relative):
                    clicked_cell = cell
                    break

            if clicked_cell:
                if self.active_cell and self.active_cell != clicked_cell:
                    self.active_cell.is_editing = False
                    self.active_cell.selection_start = None
                    self.active_cell.selection_end = None
                self.active_cell = clicked_cell
                self.active_cell.is_editing = True
                return self.active_cell.handle_input(event)
            else:
                if self.active_cell:
                    self.active_cell.is_editing = False
                    self.active_cell.selection_start = None
                    self.active_cell.selection_end = None
        return False


class ZDBApp(ZTableApp):
    def __init__(self):
        super().__init__()
        self.width = 800
        self.height = 600

    def draw(self, screen_surface):
        draw_rect(screen_surface, window_color, screen_surface.get_rect())
        for cell in self.cells:
            cell.draw(screen_surface)

    def handle_event(self, event, window_rect):
        return super().handle_event(event, window_rect)
