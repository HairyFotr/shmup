import random
import sys
from dataclasses import dataclass, field
from datetime import datetime
from math import sqrt

import pygame as pg
from dateutil.relativedelta import relativedelta
from pygame import Rect, Surface

# Initialize Pygame
pg.init()

# Constants for screen size
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
# FIXME: most code isn't resolution independent, and while other resolutions works, it changes gameplay

# Set up the display
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pg.display.set_caption("Shmup Game")

# Controls
CONTROLS = {
    "left": {
        "keyboard": [pg.K_LEFT, pg.K_a],
        "joystick_axis": (0, -1),
        "joystick_hat": (0, -1),
    },
    "right": {
        "keyboard": [pg.K_RIGHT, pg.K_d],
        "joystick_axis": (0, 1),
        "joystick_hat": (0, 1),
    },
    "up": {
        "keyboard": [pg.K_UP, pg.K_w],
        "joystick_axis": (1, -1),
        "joystick_hat": (1, 1),
    },
    "down": {
        "keyboard": [pg.K_DOWN, pg.K_s],
        "joystick_axis": (1, 1),
        "joystick_hat": (1, -1),
    },
    "shoot": {
        "keyboard": [pg.K_SPACE, pg.K_RETURN],
        "joystick_button": 0,
        "mouse_button": 0,
    },
    "dash": {
        "keyboard": [pg.K_z, pg.K_x, pg.K_c, pg.K_v, pg.K_b, pg.K_n, pg.K_m],  # Bottom row
        "joystick_button": 1,
        "mouse_button": 2,
    },
    "quit": {
        "keyboard": [pg.K_ESCAPE],
    },
}

joysticks = [pg.joystick.Joystick(joystick_id) for joystick_id in range(pg.joystick.get_count())]


def get_controls() -> dict[str, bool]:
    """Check input devices state and return control actions."""
    controls = {}
    pressed_keys = pg.key.get_pressed()
    pressed_buttons = pg.mouse.get_pressed()

    for event in pg.event.get():
        if event.type == pg.QUIT:
            controls["quit"] = True

    for action, control in CONTROLS.items():
        # Check keyboard
        for key in control["keyboard"]:
            if pressed_keys[key]:
                controls[action] = True

        # Check joystick
        for joystick in joysticks:
            # Joystick buttons
            if "joystick_button" in control and joystick.get_button(control["joystick_button"]):
                controls[action] = True

            # Joystick axes
            if "joystick_axis" in control:
                axis, direction = control["joystick_axis"]
                if joystick.get_axis(axis) * direction > 0.6:
                    controls[action] = True

            # Joystick hat (D-pad)
            if "joystick_hat" in control:
                axis, direction = control["joystick_hat"]
                if joystick.get_numhats() > 0:
                    hat_state = joystick.get_hat(0)
                    if hat_state[axis] == direction:
                        controls[action] = True

        # Check mouse
        if "mouse_button" in control:
            if pressed_buttons[control["mouse_button"]]:
                controls[action] = True
    return controls


def load_image(name: str, size: int | None = None, rect_center: tuple[float, float] | None = None, size_by: str = "width"):
    image = pg.image.load(f"data/{name}.png").convert_alpha()

    if size is not None:
        if size_by == "width":
            image = pg.transform.scale(image, (size, int(size * image.get_height() / image.get_width())))
        elif size_by == "height":
            image = pg.transform.scale(image, (int(size * image.get_width() / image.get_height()), size))
        else:
            raise ValueError(f"Invalid size_by option: {size_by}")

    if rect_center is not None:
        rect = image.get_rect(center=rect_center)
        return image, rect

    return image


def rotate_image(image, rect, angle):
    rotated_image = pg.transform.rotate(image, angle)
    rotated_rect = rotated_image.get_rect(center=rect.center)
    return rotated_image, rotated_rect


# Player, Alien, and bullet logic
bullets = []
player_bullet_image = load_image("blue_bullet", 17)
alien_bullet_image = load_image("green_bullet", 20)
explosion_image = load_image("explosion")


@dataclass
class Bullet:
    image: Surface
    rect: Rect
    speed: int
    direction: tuple[float, float]
    target_type: str
    active: bool = True

    def update(self, shift_x, shift_y):
        if bullet.active:
            bullet.rect.move_ip(
                bullet.speed * bullet.direction[0] - shift_x,
                bullet.speed * bullet.direction[1] + shift_y,
            )

            match bullet.target_type:
                case "Alien":
                    for alien in aliens:
                        if alien.health > 0 and bullet.rect.colliderect(alien.rect):
                            bullet.active = False
                            alien.health -= 1
                            if alien.health <= 0:
                                alien.die()
                case "Player":
                    if not player.dashing and bullet.rect.colliderect(player.rect.scale_by(0.5, 0.5)):
                        bullet.active = False
                        player.health -= 1
                        if player.health <= 0:
                            player.die()


@dataclass
class BaseBeing:
    """Base class for player and alien."""

    image: Surface
    rect: Rect
    health: int = 5
    bullet_image: Surface = player_bullet_image
    shot_freq: relativedelta = relativedelta(microseconds=300000)
    last_shot: datetime = datetime.now()
    target_type: str = "Alien"
    targeting_style: str = "random"
    opacity: int = 200

    def __post_init__(self):
        self.original_image = self.image.copy()
        self.original_health = self.health
        self.original_opacity = self.opacity

    def reset(self):
        self.image = self.original_image.copy()
        self.health = self.original_health
        self.opacity = self.original_opacity

    def can_shoot(self):
        return self.health > 0

    def shoot(self):
        if datetime.now() > self.last_shot + self.shot_freq:
            global bullets
            if isinstance(self, Alien):
                bullets.append(
                    Bullet(
                        alien_bullet_image,
                        pg.Rect(0, 0, 10, 10).move(self.rect.centerx - 5, self.rect.centery - 5),
                        speed=int(16 + (random.random() - random.random()) * 2),
                        direction=(-1, 0.6 * ((random.random() + random.random() + random.random()) / 3 - 0.5)),
                        target_type="Player",
                    ),
                )
            else:
                bullets.extend(
                    [
                        Bullet(
                            player_bullet_image,
                            pg.Rect(0, 0, 10, 10).move(self.rect.centerx - 15, self.rect.centery - 5 + 35),
                            speed=25,
                            direction=(1, -shift_y * 0.1),
                            target_type="Alien",
                        ),
                        Bullet(
                            player_bullet_image,
                            pg.Rect(0, 0, 10, 10).move(self.rect.centerx - 15, self.rect.centery - 5 - 35),
                            speed=25,
                            direction=(1, -shift_y * 0.1),
                            target_type="Alien",
                        ),
                    ]
                )
            self.last_shot = datetime.now()

    def die(self):
        self.image = explosion_image.copy()
        self.image = pg.transform.scale(self.image, self.rect.size)


@dataclass
class Player(BaseBeing):
    dash_fuel: float = 10
    dash_fuel_capacity: float = 30
    dashing: bool = False

    def update(self):
        if self.health <= 0:
            self.opacity -= 15
        else:
            if self.dashing:
                self.dash_fuel -= 0.5
                if self.dash_fuel <= 0:
                    self.dashing = False
                blinking_part = self.original_opacity / 2 if frame % 6 >= 3 else self.original_opacity / 3
                fuel_depletion_part = self.original_opacity / 2 * (player.dash_fuel_capacity - player.dash_fuel) / player.dash_fuel_capacity
                self.opacity = int(blinking_part + fuel_depletion_part)
            elif self.dash_fuel < self.dash_fuel_capacity:
                self.dash_fuel += 0.075
                self.opacity = self.original_opacity

        if self.opacity < -1500:  # FIXME: should be time based, or on button
            self.rect.x = SCREEN_WIDTH / 4
            self.rect.y = SCREEN_HEIGHT / 2
            self.reset()

        self.image.set_alpha(self.opacity)


player = Player(*load_image("ship", 100, (SCREEN_WIDTH / 4, SCREEN_HEIGHT / 2)))


# Alien
@dataclass
class Alien(BaseBeing):
    def can_shoot(self):
        return super().can_shoot() and self.rect.x > player.rect.x and player.health > 0

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
            self.reset()

        self.image.set_alpha(self.opacity)


aliens = (
    [
        Alien(
            *load_image(
                "alien1",
                int(90 + 25 * random.random()),
                (SCREEN_WIDTH * 3 / 4 + random.randint(0, 1500), random.randint(100, SCREEN_HEIGHT - 100)),
            ),
            health=2,
        )
        for _ in range(8)
    ]
    + [
        Alien(
            *load_image(
                "alien2",
                int(130 + 30 * random.random()),
                (SCREEN_WIDTH * 3 / 4 + random.randint(0, 1500), random.randint(100, SCREEN_HEIGHT - 100)),
            ),
            targeting_style="random_hit",
            health=8,
        )
        for _ in range(5)
    ]
    + [
        Alien(
            *load_image(
                "alien3",
                int(90 + 30 * random.random()),
                (SCREEN_WIDTH * 3 / 4 + random.randint(0, 1500), random.randint(100, SCREEN_HEIGHT - 100)),
            ),
            targeting_style="mirror",
            health=5,
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
            pg.draw.circle(screen, self.color, star, self.radius)

    def update(self, shift_x, shift_y):
        for star in self.stars:
            star[0] -= self.speed + shift_x * self.speed / 2
            star[1] += shift_y
            if star[0] < 0:
                star[0] = SCREEN_WIDTH
                star[1] = random.randint(-SCREEN_HEIGHT, SCREEN_HEIGHT * 2)


star_layers = [
    StarLayer(speed=3.1, count=200, color=(240, 240, 240), radius=1.9),
    StarLayer(speed=2.4, count=200, color=(220, 220, 220), radius=1.7),
    StarLayer(speed=1.5, count=100, color=(150, 150, 150), radius=1.4),
    StarLayer(speed=1.1, count=50, color=(75, 75, 75), radius=1.2),
]

# Background
bg_image = load_image("background", SCREEN_HEIGHT, size_by="height")
bg_x1 = 0
bg_x2 = bg_image.get_width()


def update_background():
    global bg_x1, bg_x2

    # Move backgrounds
    bg_x1 -= 1  # Adjust speed as needed
    bg_x2 -= 1

    # Reset backgrounds when they go off screen
    if bg_x1 < -bg_image.get_width():
        bg_x1 += bg_image.get_width() * 2
    if bg_x2 < -bg_image.get_width():
        bg_x2 += bg_image.get_width() * 2


# Game loop
frame = 0
last_controls = {}
while True:
    frame += 1

    difficulty = 0.0015 + frame * 0.0000001
    if frame % 1000 == 0:
        print(difficulty)

    shift_x = 0
    shift_y = 0

    # Process controls
    controls = get_controls()

    if "quit" in controls:
        pg.quit()
        sys.exit()

    if player.health > 0:
        move_by = 6
        if player.dashing:
            # Make controls faster and sticky
            controls |= {key: value for key, value in last_controls.items() if key == "left" and "right" not in controls or key == "right" and "left" not in controls or key == "up" and "down" not in controls or key == "down" and "up" not in controls}
            move_by = 6.5 + 4 * player.dash_fuel / player.dash_fuel_capacity

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
            shift_y += 1.0 * move_by / 2

        if "down" in controls:
            player.rect.y += move_by
            shift_y -= 1.0 * move_by / 2

        if player.dashing:
            shift_y *= 2

        if "dash" in controls and player.dash_fuel > 10:
            player.dashing = True
        if "dash" not in controls:
            player.dashing = False
            if "shoot" in controls:
                player.shoot()
    last_controls = controls.copy()

    # Clear screen
    screen.fill((0, 0, 0))

    # Background
    update_background()
    screen.blit(bg_image, (bg_x1, 0))
    screen.blit(bg_image, (bg_x2, 0))

    # Stars
    for star_layer in star_layers:
        star_layer.update(shift_x, shift_y)
        star_layer.draw()

    # Aliens
    for alien in aliens:
        alien.update(shift_x, shift_y)
        if alien.can_shoot():
            if alien.targeting_style == "random" and random.random() * random.random() < difficulty:
                alien.shoot()
            if alien.targeting_style == "random_hit" and random.random() * random.random() < difficulty * (alien.original_health - alien.health + 1):
                alien.shoot()
            if alien.targeting_style == "mirror" and random.random() * random.random() < difficulty * 6 and datetime.now() - player.shot_freq * 3 < player.last_shot and alien.rect.x < SCREEN_WIDTH:
                alien.shoot()
        screen.blit(alien.image, alien.rect)

    # Bullets
    for bullet in bullets:
        bullet.update(shift_x, shift_y)

        if bullet.active:
            if bullet.target_type == "Player":
                img, _ = rotate_image(bullet.image, bullet.rect, 360 * random.random())
            else:
                img = bullet.image
            screen.blit(img, bullet.rect)
        else:
            img = bullet.image.copy()
            img.set_alpha(127)
            screen.blit(img, bullet.rect)

    bullets = [b for b in bullets if b.active]

    # Player
    player.update()
    screen.blit(*rotate_image(player.image, player.rect, shift_y * 1.5))

    pg.display.flip()
    pg.time.Clock().tick(60)
