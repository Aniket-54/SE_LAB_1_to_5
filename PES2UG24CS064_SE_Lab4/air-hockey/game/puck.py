"""
Puck: the disc players are trying to hit into the opponent's goal.
"""


class Puck:
    def __init__(self, x, y, radius=12):
        self.x = x
        self.y = y
        self.radius = radius
        self.vx = 0.0
        self.vy = 0.0

        # Store the previous position of the puck.
        #
        # Task 1 uses this value to examine the puck's complete
        # movement path during one frame. Without it, a fast puck
        # could move from one side of a paddle to the other without
        # ever being detected as overlapping the paddle.
        self.previous_x = x
        self.previous_y = y

    def move(self):
        # Save the current position before moving.
        #
        # Collision detection will compare this previous position
        # with the new position to detect high-speed collisions.
        self.previous_x = self.x
        self.previous_y = self.y

        self.x += self.vx
        self.y += self.vy

    def bounce_off_walls(self, height, margin):
        """Bounce off the top and bottom walls only - left/right are handled
        separately by the game engine, since they contain the goals."""
        if self.y - self.radius < margin:
            self.y = margin + self.radius
            self.vy = -self.vy

        elif self.y + self.radius > height - margin:
            self.y = height - margin - self.radius
            self.vy = -self.vy