# pong_app.py
import pygame
import random

# --- Constants ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
PADDLE_WIDTH = 15  # Slightly wider paddles
PADDLE_HEIGHT = 120  # Slightly taller paddles
BALL_RADIUS = 12  # Slightly larger ball
PADDLE_SPEED = 12  # Increased paddle speed
BALL_SPEED_INITIAL = 8
BALL_SPEED_INCREMENT = 0.5
AI_SPEED_FACTOR = 0.9  # AI speed multiplier (slightly slower than player)

# --- Classes ---


class Paddle(pygame.sprite.Sprite):
    """
    Paddle class with enhanced movement and appearance.
    """

    def __init__(self, color, width, height, initial_x):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = initial_x  # Set initial x position
        self.width = width
        self.height = height
        self.speed = PADDLE_SPEED

    def move_up(self, pixels):
        self.rect.y -= pixels
        if self.rect.top < 0:  # Use top for boundary check
            self.rect.top = 0

    def move_down(self, pixels, screen_height):
        self.rect.y += pixels
        if self.rect.bottom > screen_height:  # Use bottom for boundary check
            self.rect.bottom = screen_height


class Ball(pygame.sprite.Sprite):
    """
    Ball class with enhanced appearance, variable speed and spin on paddle hit.
    """

    def __init__(self, color, radius):
        super().__init__()
        self.radius = radius
        self.image = pygame.Surface(
            [radius * 2, radius * 2], pygame.SRCALPHA, 32)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.image = self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.speed_x = BALL_SPEED_INITIAL
        self.speed_y = BALL_SPEED_INITIAL
        self.last_paddle_hit = None  # To control spin/angle on consecutive paddle hits

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

    def bounce_y(self):
        self.speed_y *= -1
        # Add slight random variation to y direction for more dynamic bounces
        self.speed_y += random.uniform(-0.5, 0.5)
        if abs(self.speed_y) > BALL_SPEED_INITIAL * 1.5:  # Limit speed to avoid crazy values
            self.speed_y = BALL_SPEED_INITIAL * \
                1.5 * (1 if self.speed_y > 0 else -1)

    def bounce_x(self, paddle_y_center):
        self.speed_x *= -1
        self.speed_x += BALL_SPEED_INCREMENT * \
            (1 if self.speed_x > 0 else -1)  # Increase speed on hit
        if abs(self.speed_x) > BALL_SPEED_INITIAL * 2.5:  # Limit max ball speed
            self.speed_x = BALL_SPEED_INITIAL * \
                2.5 * (1 if self.speed_x > 0 else -1)

        # Introduce spin based on where the ball hits the paddle relative to paddle center
        relative_intersect_y = (
            paddle_y_center - self.rect.centery) / (PADDLE_HEIGHT / 2)
        self.speed_y += relative_intersect_y * 2  # Adjust spin factor as needed
        if abs(self.speed_y) > BALL_SPEED_INITIAL * 1.5:  # Limit spin effect
            self.speed_y = BALL_SPEED_INITIAL * \
                1.5 * (1 if self.speed_y > 0 else -1)

    def reset_position(self, screen_width, screen_height):
        self.rect.center = (screen_width // 2, screen_height // 2)
        self.speed_x = BALL_SPEED_INITIAL * \
            random.choice([-1, 1])  # Random initial direction
        self.speed_y = BALL_SPEED_INITIAL * random.choice([-1, 1])
        self.last_paddle_hit = None  # Reset last hit


class MyGameApp:
    """
    Main Pong game application class, refactored and improved.
    """

    def __init__(self):
        self.width = 800
        self.height = 600
        self.player_paddle = Paddle(
            WHITE, PADDLE_WIDTH, PADDLE_HEIGHT, 20)  # Initial x position set
        self.opponent_paddle = Paddle(
            # Initial x position set
            WHITE, PADDLE_WIDTH, PADDLE_HEIGHT, self.width - 20 - PADDLE_WIDTH)
        self.ball = Ball(WHITE, BALL_RADIUS)
        self.all_sprites_list = pygame.sprite.Group()
        self.all_sprites_list.add(self.player_paddle)
        self.all_sprites_list.add(self.opponent_paddle)
        self.all_sprites_list.add(self.ball)
        self.player_score = 0
        self.opponent_score = 0
        self.game_font = pygame.font.Font(None, 74)  # Default font
        self.running = True
        self.game_over = False  # Game over state
        self.winner_text = ""

        # Sound effects (optional, you'd need to provide sound files or remove)
        pygame.mixer.init()
        try:
            self.paddle_sound = pygame.mixer.Sound(
                "Sounds/paddle_hit.wav")  # Replace with your sound file
            self.score_sound = pygame.mixer.Sound(
                "Sounds/score.wav")       # Replace with your sound file
            self.wall_sound = pygame.mixer.Sound(
                "Sounds/wall_hit.wav")        # Replace with your sound file
        except pygame.error as e:
            print(f"Warning: Could not load sound files: {e}")
            self.paddle_sound = None
            self.score_sound = None
            self.wall_sound = None

    def stop_running(self):
        self.running = False

    def run_app(self, subsurface_rect):
        screen_width = subsurface_rect.width
        screen_height = subsurface_rect.height

        # Center paddles vertically on game start
        self.player_paddle.rect.centery = screen_height // 2
        self.opponent_paddle.rect.centery = screen_height // 2
        self.ball.reset_position(screen_width, screen_height)
        self.game_over = False  # Reset game over state
        self.player_score = 0  # Reset scores
        self.opponent_score = 0
        self.ball.speed_x = BALL_SPEED_INITIAL * \
            random.choice([-1, 1])  # Ensure initial ball direction
        self.ball.speed_y = BALL_SPEED_INITIAL * random.choice([-1, 1])

        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if not self.game_over:  # Only handle game input if game is not over
                        self.handle_event(event)
                    else:  # Handle input when game is over (e.g., restart)
                        if event.key == pygame.K_SPACE:  # Example restart on Space
                            # Reset and restart
                            self.reset_game(subsurface_rect)
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False

            if not self.game_over:  # Only update game elements if game is not over
                keys = pygame.key.get_pressed()
                if keys[pygame.K_w]:
                    self.player_paddle.move_up(PADDLE_SPEED)
                if keys[pygame.K_s]:
                    self.player_paddle.move_down(PADDLE_SPEED, screen_height)

                self.ball.update()

                # Ball collision with walls (top/bottom)
                if self.ball.rect.top < 0 or self.ball.rect.bottom > screen_height:
                    self.ball.bounce_y()
                    if self.wall_sound:
                        self.wall_sound.play()

                # Ball collision with paddles
                if pygame.sprite.collide_rect(self.ball, self.player_paddle):
                    self.ball.bounce_x(self.player_paddle.rect.centery)
                    self.ball.last_paddle_hit = self.player_paddle  # Track last hit paddle
                    if self.paddle_sound:
                        self.paddle_sound.play()
                elif pygame.sprite.collide_rect(self.ball, self.opponent_paddle):
                    self.ball.bounce_x(self.opponent_paddle.rect.centery)
                    self.ball.last_paddle_hit = self.opponent_paddle  # Track last hit paddle
                    if self.paddle_sound:
                        self.paddle_sound.play()

                # Ball passes paddles - scoring
                if self.ball.rect.right > screen_width:
                    self.player_score += 1
                    self.ball.reset_position(screen_width, screen_height)
                    if self.score_sound:
                        self.score_sound.play()
                elif self.ball.rect.left < 0:
                    self.opponent_score += 1
                    self.ball.reset_position(screen_width, screen_height)
                    if self.score_sound:
                        self.score_sound.play()

                # Improved Opponent AI (predictive and slightly slower)
                # Only move AI when ball is moving towards it and past halfway
                if self.ball.speed_x > 0 and self.ball.rect.x > screen_width // 2:
                    if self.opponent_paddle.rect.centery < self.ball.rect.centery:
                        self.opponent_paddle.move_down(
                            PADDLE_SPEED * AI_SPEED_FACTOR, screen_height)
                    elif self.opponent_paddle.rect.centery > self.ball.rect.centery:
                        self.opponent_paddle.move_up(
                            PADDLE_SPEED * AI_SPEED_FACTOR)

                # Check for game over condition (e.g., score limit)
                if self.player_score >= 10:  # Example score limit
                    self.game_over = True
                    self.winner_text = "Player Wins!"
                elif self.opponent_score >= 10:
                    self.game_over = True
                    self.winner_text = "Opponent Wins!"

            # --- Drawing ---
            surface = pygame.Surface(subsurface_rect.size).convert()
            surface.fill(BLACK)

            self.draw(surface)  # Draw game elements

            screen = pygame.display.get_surface()
            screen.blit(surface, subsurface_rect)
            pygame.display.flip()
            clock.tick(60)

    def reset_game(self, subsurface_rect):
        """Resets the game to start a new match."""
        screen_width = subsurface_rect.width
        screen_height = subsurface_rect.height
        self.game_over = False
        self.player_score = 0
        self.opponent_score = 0
        self.ball.reset_position(screen_width, screen_height)
        self.ball.speed_x = BALL_SPEED_INITIAL * random.choice([-1, 1])
        self.ball.speed_y = BALL_SPEED_INITIAL * random.choice([-1, 1])

    def draw(self, subsurface):
        """Draws all game elements on the provided surface."""
        subsurface.fill(BLACK)

        # Draw dashed center line
        self.draw_dashed_line(subsurface, WHITE, [subsurface.get_width(
        )//2, 0], [subsurface.get_width()//2, subsurface.get_height()], dash_length=10)

        self.all_sprites_list.draw(subsurface)  # Draw paddles and ball

        # Display scores (slightly improved positioning)
        player_score_surface = self.game_font.render(
            str(self.player_score), True, WHITE)
        opponent_score_surface = self.game_font.render(
            str(self.opponent_score), True, WHITE)

        score_y_pos = 10  # Common vertical position for scores
        subsurface.blit(player_score_surface, (subsurface.get_width(
            # Centered above line
        ) // 4 - player_score_surface.get_width() // 2, score_y_pos))
        subsurface.blit(opponent_score_surface, (subsurface.get_width(
            # Centered above line
        ) * 3 // 4 - opponent_score_surface.get_width() // 2, score_y_pos))

        if self.game_over:
            game_over_font = pygame.font.Font(None, 84)
            game_over_text_surface = game_over_font.render(
                self.winner_text, True, RED)
            text_rect = game_over_text_surface.get_rect(
                center=(subsurface.get_width() // 2, subsurface.get_height() // 2))
            subsurface.blit(game_over_text_surface, text_rect)

    def draw_dashed_line(self, surface, color, start_pos, end_pos, dash_length=10):
        """ Draws a dashed line between start_pos and end_pos."""
        x1, y1 = start_pos
        x2, y2 = end_pos
        dl = dash_length

        if x1 == x2:  # Vertical line
            y_range = range(int(min(y1, y2)), int(max(y1, y2)), dl)
            for y in y_range:
                start = (x1, y)
                end = (x1, y + dl)
                pygame.draw.line(surface, color, start, end)
        elif y1 == y2:  # Horizontal line
            x_range = range(int(min(x1, x2)), int(max(x1, x2)), dl)
            for x in x_range:
                start = (x, y1)
                end = (x + dl, y1)
                pygame.draw.line(surface, color, start, end)

    def handle_event(self, event):
        """Handles keyboard events for player control."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                # Make single key press more responsive
                self.player_paddle.move_up(PADDLE_SPEED * 2)
            elif event.key == pygame.K_s:
                # Use self.height from init
                self.player_paddle.move_down(PADDLE_SPEED * 2, self.height)
