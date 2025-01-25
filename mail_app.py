# mail_app.py
import pygame


class MailApp:
    def __init__(self, window_rect, game_font, console_font):
        self.rect = window_rect
        self.font = game_font
        self.console_font = console_font
        self.is_running = True
        self.messages = []
        self.pending_messages = []  # To hold messages received before app is opened
        self.pending_vyach_message = None
        self.check_pending_messages()
        self.check_inbox()  # Initial check for messages

    def check_pending_messages(self):
        if self.pending_vyach_message is None:  # Only check file if no pending message in memory
            self.pending_vyach_message = load_pending_message_from_file()  # Load from file
        if self.pending_vyach_message:
            print(self.pending_vyach_message)
            vah = self.pending_vyach_message.split('Zv')
            self.receive_message(vah[0])
            self.receive_message(vah[1])
            pending_vyach_message = None

    def check_inbox(self):
        if not self.messages:
            self.messages = ["No messages yet!"]

    def draw(self, screen):
        # White background for mail app
        pygame.draw.rect(screen, (255, 255, 255), screen.get_rect())
        title_surface = self.font.render("Mail", True, (0, 0, 0))
        title_rect = title_surface.get_rect(topleft=(10, 10))
        screen.blit(title_surface, title_rect)

        y_offset = 60
        for message in self.messages:
            message_surface = self.console_font.render(
                message, True, (0, 0, 0))
            message_rect = message_surface.get_rect(topleft=(10, y_offset))
            screen.blit(message_surface, message_rect)
            y_offset += self.console_font.get_height() + 5

    def handle_event(self, event, windows):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:  # Example action
                pass

    def receive_message(self, message_content):
        if "No messages yet!" in self.messages:
            self.messages = [message_content]
        elif not self.messages:
            self.messages = [message_content]
        else:
            self.messages.append(message_content)


def load_pending_message_from_file():
    try:
        with open("messages.txt", "r") as f:
            message = f.readline().strip()
            if message:
                print(message)
                return message
    except FileNotFoundError:
        pass  # It's okay if the file doesn't exist yet
    return None