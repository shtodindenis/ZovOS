# mail_app.py
import pygame


class MailApp:
    def __init__(self, window_rect, game_font, console_font):
        self.rect = window_rect
        self.font = game_font
        self.console_font = console_font
        self.is_running = True
        self.messages = ["No messages yet!"]  # Placeholder for mail messages

    def draw(self, screen):
        # White background for mail app
        pygame.draw.rect(screen, (255, 255, 255), screen.get_rect())
        title_surface = self.font.render("Mail", True, (0, 0, 0))
        title_rect = title_surface.get_rect(topleft=(10, 10))
        screen.blit(title_surface, title_rect)

        y_offset = 50
        for message in self.messages:
            message_surface = self.console_font.render(
                message, True, (0, 0, 0))
            message_rect = message_surface.get_rect(topleft=(10, y_offset))
            screen.blit(message_surface, message_rect)
            y_offset += self.console_font.get_height() + 5

    def handle_event(self, event, windows):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:  # Example action
                # Example append message
                self.messages.append("New message received!")
