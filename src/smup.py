import random
import sys
from dataclasses import dataclass, field
from datetime import datetime
from math import sqrt

import pygame
from dateutil.relativedelta import relativedelta
from pygame import Rect, Surface

# Initialize Pygame
pygame.init()

# Constants for screen size
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shmup Game")

# Controls
joystick = None
if pygame.joystick.get_count() > 0:
    for joystick_id in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(joystick_id)
        if joystick.get_name() == "Controller":
            break
        joystick = None

CONTROLS = {
    "left": {
        "keyboard": pygame.K_LEFT,
        "joystick_axis": (0, -1),
        "joystick_hat": (0, -1),
    },
    "right": {
        "keyboard": pygame.K_RIGHT,
        "joystick_axis": (0, 1),
        "joystick_hat": (0, 1),
    },
    "up": {
        "keyboard": pygame.K_UP,
        "joystick_axis": (1, -1),
        "joystick_hat": (1, 1),
    },
    "down": {
        "keyboard": pygame.K_DOWN,
        "joystick_axis": (1, 1),
        "joystick_hat": (1, -1),
    },
    "shoot": {
        "keyboard": pygame.K_SPACE,
        "joystick_button": 0,
    },
    "quit": {
        "keyboard": pygame.K_ESCAPE,
    },
}


# Function to check input state and return actions
def get_controls():
    controls = {}
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            controls["quit"] = True

        """
        # Joystick button press
        if event.type == pygame.JOYBUTTONDOWN:
            print(f"Joystick Button Pressed: {event.button}")

        # Joystick button release
        if event.type == pygame.JOYBUTTONUP:
            print(f"Joystick Button Released: {event.button}")

        # Joystick axis movement
        if event.type == pygame.JOYAXISMOTION:
            print(f"Joystick Axis Moved: {event.axis} -> Value: {event.value}")

        # Joystick hat (D-pad) movement
        if event.type == pygame.JOYHATMOTION:
            print(f"Joystick Hat Moved: {event.hat} -> Value: {event.value}")
        """

    for action, control in CONTROLS.items():
        # Check keyboard
        if keys[control["keyboard"]]:
            controls[action] = True
            continue

        # Check joystick
        if "joystick" in globals():
            # Joystick buttons
            if "joystick_button" in control and joystick.get_button(control["joystick_button"]):
                controls[action] = True

            # Joystick axes
            if "joystick_axis" in control:
                axis, direction = control["joystick_axis"]
                if joystick.get_axis(axis) * direction > 0.1:
                    controls[action] = True

            # Joystick hat
            # Joystick hat (D-pad)
            if "joystick_hat" in control:
                axis, direction = control["joystick_hat"]
                hat_state = joystick.get_hat(0)
                if hat_state[axis] == direction:
                    controls[action] = True

    # if controls:
    #    print(controls)
    return controls


def load_image(name: str, size: int | None = None, center: tuple[float, float] | None = None, size_by: str = "width"):
    image = pygame.image.load(f"data/{name}.png").convert_alpha()
    if size is not None:
        if size_by == "width":
            image = pygame.transform.scale(image, (size, int(size * image.get_height() / image.get_width())))
        else:
            image = pygame.transform.scale(image, (int(size * image.get_width() / image.get_height()), size))
    if center is not None:
        rect = image.get_rect(center=center)
        return image, rect
    return image


# Player
bullets = []


@dataclass
class Bullet:
    image: Surface
    rect: Rect
    speed: int
    direction: tuple[float, float]
    target_type: str
    active: bool = False

    def update(self, shift_x, shift_y):
        if bullet.active:
            bullet.rect.move_ip(
                bullet.speed * bullet.direction[0] - shift_x,
                bullet.speed * bullet.direction[1] + shift_y,
            )

            # Check collision based on target type
            if bullet.target_type == "Alien":
                for alien in aliens:
                    if alien.health > 0:
                        if bullet.rect.colliderect(alien.rect):
                            bullet.active = False
                            alien.health -= 1
                            if alien.health <= 0:
                                alien.die()

            elif bullet.target_type == "Player":
                if bullet.rect.colliderect(player.rect.scale_by(0.5, 0.5)):
                    bullet.active = False
                    player.health -= 1
                    if player.health <= 0:
                        player.die()


player_bullet_image = load_image("blue_bullet", 17)
alien_bullet_image = load_image("green_bullet", 20)
explosion_image = load_image("explosion")


@dataclass
class Shooter:
    image: Surface
    rect: Rect
    health: int = 5
    bullet_image: Surface = player_bullet_image
    last_shot: datetime = datetime.now()
    shot_freq: relativedelta = relativedelta(microseconds=300000)
    shoot_pos: tuple[float, float] = (70, 50)
    target_type: str = "Alien"
    opacity: int = 200

    def __post_init__(self):
        self.original_image = self.image.copy()
        self.original_health = self.health
        self.original_opacity = self.opacity

    def shoot(self):
        if datetime.now() > self.last_shot + self.shot_freq:
            global bullets
            if isinstance(self, Alien):
                bullets.append(
                    Bullet(
                        alien_bullet_image,
                        pygame.Rect(0, 0, 10, 10).move(self.rect.centerx - 5, self.rect.centery - 5),
                        int(-16 + (random.random() - random.random()) * 2),
                        (1, 0.25 * (random.random() - random.random())),
                        "Player",
                        True,
                    ),
                )
            else:
                bullets.extend(
                    [
                        Bullet(
                            player_bullet_image,
                            pygame.Rect(0, 0, 10, 10).move(self.rect.centerx - 15, self.rect.centery - 5 + 35),
                            25,
                            (1, -shift_y * 0.075),
                            "Alien",
                            True,
                        ),
                        Bullet(
                            player_bullet_image,
                            pygame.Rect(0, 0, 10, 10).move(self.rect.centerx - 15, self.rect.centery - 5 - 35),
                            25,
                            (1, -shift_y * 0.075),
                            "Alien",
                            True,
                        ),
                    ]
                )
            self.last_shot = datetime.now()

    def die(self):
        self.image = explosion_image.copy()
        self.image = pygame.transform.scale(self.image, self.rect.size)


@dataclass
class Player(Shooter):
    def update(self):
        if self.health <= 0:
            self.opacity -= 15

        if self.opacity < -1000:
            self.rect.x = 100
            self.rect.y = SCREEN_HEIGHT / 2
            self.health = self.original_health
            self.image = self.original_image.copy()
            self.opacity = self.original_opacity

        self.image.set_alpha(self.opacity)


player = Player(*load_image("ship", 100, (SCREEN_WIDTH / 4, SCREEN_HEIGHT / 2)))


# Alien
@dataclass
class Alien(Shooter):
    def update(self, shift_x, shift_y):
        movement = 4  # Remaining movement

        total_x = 0
        total_y = 0

        # Alien avoidance logic
        for other in random.sample(aliens, len(aliens)):
            if other != self and self.rect.colliderect(other.rect.inflate(10 + random.random() * 5, 10 + random.random() * 5)):
                if self.rect.x < other.rect.x:
                    total_x -= random.random()
                else:
                    total_x += random.random() * 0.5

                if self.rect.y < other.rect.y:
                    total_y -= random.random() * 2
                else:
                    total_y += random.random() * 2

        # Movement towards player
        ratio_y = 0.75 if player.rect.x < self.rect.x else 0.15

        if player.rect.y > self.rect.y:
            total_y += random.random() * ratio_y
        else:
            total_y -= random.random() * ratio_y

        # General movement
        total_x -= 1 + random.random()

        # Normalize the movement
        movement_distance = sqrt(total_x**2 + total_y**2)
        if movement_distance > 0:
            normalized_x = total_x / movement_distance * movement
            normalized_y = total_y / movement_distance * movement

            self.rect.x += normalized_x - shift_x
            self.rect.y += normalized_y + shift_y

        if self.health <= 0:
            self.opacity -= 15

        if self.rect.x < -100:
            self.rect.x = SCREEN_WIDTH + 100
            self.rect.y = random.randint(-100, SCREEN_HEIGHT + 100)
            self.health = self.original_health
            self.image = self.original_image.copy()
            self.opacity = self.original_opacity

        self.image.set_alpha(self.opacity)


aliens = (
    [
        Alien(
            *load_image(
                "alien1",
                int(100 + 15 * random.random()),
                (SCREEN_WIDTH * 3 / 4 + random.randint(0, 1500), random.randint(100, SCREEN_HEIGHT - 100)),
            )
        )
        for _ in range(8)
    ]
    + [
        Alien(
            *load_image(
                "alien2",
                int(130 + 20 * random.random()),
                (SCREEN_WIDTH * 3 / 4 + random.randint(0, 1500), random.randint(100, SCREEN_HEIGHT - 100)),
            )
        )
        for _ in range(5)
    ]
    + [
        Alien(
            *load_image(
                "alien3",
                int(90 + 20 * random.random()),
                (SCREEN_WIDTH * 3 / 4 + random.randint(0, 1500), random.randint(100, SCREEN_HEIGHT - 100)),
            )
        )
        for _ in range(3)
    ]
)


# Stars
@dataclass
class StarLayer:
    speed: float
    count: int
    color: tuple[int, int, int]
    radius: float
    stars: list[list[float]] = field(default_factory=list)

    def __post_init__(self):
        self.stars = [[random.randint(0, SCREEN_WIDTH), random.randint(-SCREEN_HEIGHT, SCREEN_HEIGHT * 2)] for _ in range(self.count)]

    def draw(self):
        for star in self.stars:
            pygame.draw.circle(screen, self.color, star, self.radius)

    def update(self, shift_x, shift_y):
        for star in self.stars:
            star[0] -= self.speed + shift_x * self.speed / 2
            star[1] += shift_y
            if star[0] < 0:
                star[0] = SCREEN_WIDTH
                star[1] = random.randint(-SCREEN_HEIGHT, SCREEN_HEIGHT * 2)


star_layers = [
    StarLayer(
        speed=3.1,
        count=200,
        color=(240, 240, 240),
        radius=1.9,
    ),
    StarLayer(
        speed=2.4,
        count=200,
        color=(220, 220, 220),
        radius=1.7,
    ),
    StarLayer(
        speed=1.5,
        count=100,
        color=(150, 150, 150),
        radius=1.4,
    ),
    StarLayer(
        speed=1.1,
        count=50,
        color=(75, 75, 75),
        radius=1.2,
    ),
]

# Background
bg_image = load_image("background", SCREEN_HEIGHT, size_by="height")
bg_x1 = 0
bg_x2 = bg_image.get_width()


def update_background():
    global bg_x1, bg_x2

    # Move backgrounds
    bg_x1 -= 2  # Adjust speed as needed
    bg_x2 -= 2

    # Reset backgrounds when they go off screen
    if bg_x1 < -bg_image.get_width():
        bg_x1 += bg_image.get_width() * 2
    if bg_x2 < -bg_image.get_width():
        bg_x2 += bg_image.get_width() * 2


# Game loop
while True:
    shift_x = 0
    shift_y = 0

    controls = get_controls()

    if "quit" in controls:
        pygame.quit()
        sys.exit()

    if player.opacity > 0:
        move_by = 6
        if ("left" in controls or "right" in controls) and ("up" in controls or "down" in controls):
            move_by /= sqrt(2)

        if "left" in controls:
            player.rect.x -= move_by
            shift_x -= 0.1 * move_by / 2

        if "right" in controls:
            player.rect.x += move_by
            shift_x += 0.5 * move_by / 2

        if "up" in controls:
            player.rect.y -= move_by
            shift_y += 1 * move_by / 2

        if "down" in controls:
            player.rect.y += move_by
            shift_y -= 1 * move_by / 2

        if "shoot" in controls:
            player.shoot()

    screen.fill((0, 0, 0))
    update_background()
    screen.blit(bg_image, (bg_x1, 0))
    screen.blit(bg_image, (bg_x2, 0))

    for star_layer in star_layers:
        star_layer.update(shift_x, shift_y)
        star_layer.draw()

    for alien in aliens:
        alien.update(shift_x, shift_y)
        if random.random() * random.random() < 0.002 and alien.health > 0:
            alien.shoot()
        screen.blit(alien.image, alien.rect)

    for bullet in bullets:
        bullet.update(shift_x, shift_y)
        if bullet.active:
            screen.blit(bullet.image, bullet.rect)
        else:
            img = bullet.image.copy()
            img.set_alpha(127)
            screen.blit(img, bullet.rect)
    bullets = [b for b in bullets if b.active]

    def rotate_image(angle):
        rotated_image = pygame.transform.rotate(player.image, angle)
        rotated_rect = rotated_image.get_rect(center=player.rect.center)
        return rotated_image, rotated_rect

    player.update()
    screen.blit(*rotate_image(shift_y * 1.5))

    pygame.display.flip()
    pygame.time.Clock().tick(60)
