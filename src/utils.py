from pygame import Rect


class FloatRect:
    def __init__(self, x, y, width, height):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def topleft(self):
        return (self.left, self.top)

    @property
    def bottomright(self):
        return (self.right, self.bottom)

    @property
    def size(self):
        return (self.width, self.height)

    @property
    def center(self):
        return (self.x + self.width / 2, self.y + self.height / 2)

    @property
    def centerx(self):
        return self.x + self.width / 2

    @property
    def centery(self):
        return self.y + self.height / 2

    def inflate(self, x, y):
        return FloatRect(self.x - x / 2, self.y - y / 2, self.width + x, self.height + y)

    def scale_by(self, factorx, factory):
        return FloatRect(self.x, self.y, self.width * factorx, self.height * factory)

    def move(self, x, y):
        return FloatRect(self.x + x, self.y + y, self.width, self.height)

    def clamp(self, other):
        # This method would be used to keep the rect within another
        new_rect = self.copy()
        if self.left < other.left:
            new_rect.left = other.left
        if self.right > other.right:
            new_rect.right = other.right
        if self.top < other.top:
            new_rect.top = other.top
        if self.bottom > other.bottom:
            new_rect.bottom = other.bottom
        return new_rect

    def colliderect(self, other):
        # Check for collision with another rect
        return not (self.right <= other.left or self.left >= other.right or self.bottom <= other.top or self.top >= other.bottom)

    def copy(self):
        return FloatRect(self.x, self.y, self.width, self.height)

    def __repr__(self):
        return f"FloatRect({self.x}, {self.y}, {self.width}, {self.height})"

    @classmethod
    def from_rect(cls, rect: Rect):
        return FloatRect(rect.x, rect.y, rect.width, rect.height)

    def to_rect(self):
        return Rect(round(self.left), round(self.top), round(self.width), round(self.height))
