"""
GameEngine: owns the puck, both paddles, and the computer AI, and runs
one frame's worth of game logic.

Implemented tasks:
- Task 1: puck-paddle collision physics
- Task 2: match scoring
- Task 3: 30-second match timer
- Task 4: post-goal puck reset and relaunch
"""

import math
import random

import pygame

from game.puck import Puck
from game.paddle import Paddle
from game.ai import ComputerAI
from game.collisions import handle_paddle_collision
from game.renderer import (
    WIDTH,
    HEIGHT,
    MARGIN,
    GOAL_TOP,
    GOAL_BOTTOM,
)

PLAYER_SPEED = 6
PUCK_RADIUS = 12
PADDLE_RADIUS = 28
INITIAL_PUCK_SPEED = 4.5

# Task 3:
# The match lasts exactly 30 seconds.
MATCH_DURATION = 30


class GameEngine:
    def __init__(self):
        # Create the puck at the centre of the table.
        self.puck = Puck(
            WIDTH / 2,
            HEIGHT / 2,
            PUCK_RADIUS
        )

        # Give the puck an initial velocity.
        self._launch_puck()

        self.player = Paddle(
            x=WIDTH * 0.15,
            y=HEIGHT / 2,
            radius=PADDLE_RADIUS,
            min_x=MARGIN + PADDLE_RADIUS,
            max_x=WIDTH / 2 - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS,
            max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )

        self.computer = Paddle(
            x=WIDTH * 0.85,
            y=HEIGHT / 2,
            radius=PADDLE_RADIUS,
            min_x=WIDTH / 2 + PADDLE_RADIUS,
            max_x=WIDTH - MARGIN - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS,
            max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )

        self.ai = ComputerAI()

        # Task 2:
        # Maintain separate scores for the player and computer.
        self.player_score = 0
        self.computer_score = 0

        # Task 3:
        # Store the exact time at which the match begins.
        pygame_start_time = pygame.time.get_ticks()
        self.match_start_time = pygame_start_time

        # Task 3:
        # This becomes True once the 30-second match has ended.
        self.match_over = False

    def _launch_puck(self):
        """
        Give the puck a fresh velocity for the beginning of a point.

        A random horizontal direction and vertical angle prevent every
        point from starting with exactly the same trajectory.
        """

        angle_choices = [0.3, 0.6, -0.3, -0.6]

        direction = random.choice([-1, 1])
        vy_factor = random.choice(angle_choices)

        self.puck.vx = INITIAL_PUCK_SPEED * direction
        self.puck.vy = INITIAL_PUCK_SPEED * vy_factor

    def _get_elapsed_time(self):
        """
        Return the number of seconds that have elapsed since the
        match started.
        """

        return (
            pygame.time.get_ticks() - self.match_start_time
        ) / 1000.0

    def _get_remaining_time(self):
        """
        Return the number of whole seconds remaining in the match.

        ceil() keeps the display at 30 at the start of the match and
        decreases it once each whole second has elapsed.
        """

        elapsed_seconds = self._get_elapsed_time()

        return max(
            0,
            math.ceil(MATCH_DURATION - elapsed_seconds)
        )

    def handle_input(self, keys_pressed):
        """
        Handle keyboard input for the player paddle.

        Input is ignored once the match has ended.
        """

        # Task 3:
        # Do not allow the player to move after time expires.
        if self.match_over:
            return

        # Check the timer here as well as in update().
        # This prevents the player from moving during the frame in
        # which the timer first reaches zero.
        if self._get_elapsed_time() >= MATCH_DURATION:
            self.match_over = True
            return

        dx = 0
        dy = 0

        if keys_pressed[pygame.K_UP]:
            dy -= PLAYER_SPEED

        if keys_pressed[pygame.K_DOWN]:
            dy += PLAYER_SPEED

        if keys_pressed[pygame.K_LEFT]:
            dx -= PLAYER_SPEED

        if keys_pressed[pygame.K_RIGHT]:
            dx += PLAYER_SPEED

        self.player.move_by(dx, dy)

    def update(self):
        """
        Update one frame of the game.

        Timer expiration is checked before any gameplay logic so that
        the match stops when the 30-second limit is reached.
        """

        # Task 3:
        # End the match once 30 seconds have elapsed.
        if self._get_elapsed_time() >= MATCH_DURATION:
            self.match_over = True
            return

        # Safety check in case update() is called after the match ends.
        if self.match_over:
            return

        # Update computer AI.
        self.ai.update(self.computer, self.puck)

        # Move the puck.
        self.puck.move()

        # Handle top and bottom wall collisions.
        self.puck.bounce_off_walls(HEIGHT, MARGIN)

        # Task 1:
        # Use the collision system to handle paddle impacts.
        handle_paddle_collision(
            self.puck,
            self.player
        )

        handle_paddle_collision(
            self.puck,
            self.computer
        )

        # Task 2:
        # Check for goals and side-wall collisions.
        self._handle_goals()

    def _handle_goals(self):
        """
        Handle goals and collisions with the left/right end walls.

        A point is scored only when the entire puck fits through the
        goal opening and completely crosses the end of the table.

        If the puck reaches a wall outside the goal opening, it
        bounces normally instead.
        """

        # The complete puck must fit vertically inside the goal gap.
        #
        # Simply checking the puck's centre is not enough. This prevents
        # the puck from being counted as a goal while still touching
        # the goalpost.
        puck_fits_in_goal = (
            GOAL_TOP + self.puck.radius
            <= self.puck.y
            <= GOAL_BOTTOM - self.puck.radius
        )

        # ---------------------------------------------------------
        # LEFT SIDE
        # ---------------------------------------------------------
        if self.puck.vx < 0:

            if puck_fits_in_goal:
                # The puck is inside the goal opening.
                #
                # Do NOT bounce it at MARGIN. The goal is an opening
                # in the end wall, so the puck is allowed to travel
                # through it.
                #
                # Register the goal only after the entire puck has
                # crossed the left edge of the screen.
                if self.puck.x + self.puck.radius <= 0:

                    # The puck entered the player's goal,
                    # therefore the computer receives the point.
                    self.computer_score += 1

                    # Reset the puck for the next point.
                    self._reset_puck()
                    return

            else:
                # Outside the goal opening, the left end wall behaves
                # like a normal wall.
                if self.puck.x - self.puck.radius < MARGIN:

                    self.puck.x = MARGIN + self.puck.radius
                    self.puck.vx = -self.puck.vx
                    return

        # ---------------------------------------------------------
        # RIGHT SIDE
        # ---------------------------------------------------------
        elif self.puck.vx > 0:

            if puck_fits_in_goal:
                # The puck is inside the goal opening, so allow it
                # to travel through the opening.
                #
                # Register the goal only after the entire puck has
                # crossed the right edge of the screen.
                if self.puck.x - self.puck.radius >= WIDTH:

                    # The puck entered the computer's goal,
                    # therefore the player receives the point.
                    self.player_score += 1

                    # Reset the puck for the next point.
                    self._reset_puck()
                    return

            else:
                # Outside the goal opening, the right end wall
                # behaves like a normal wall.
                if self.puck.x + self.puck.radius > WIDTH - MARGIN:

                    self.puck.x = (
                        WIDTH - MARGIN - self.puck.radius
                    )
                    self.puck.vx = -self.puck.vx
                    return

    def _get_match_result(self):
        """
        Determine the final match result from the current scores.
        """

        if self.player_score > self.computer_score:
            return "Player wins!"

        if self.computer_score > self.player_score:
            return "Computer wins!"

        return "Draw!"
    def _reset_puck(self):
        """
        Reset the puck to the centre of the table and immediately launch it
        for the next point.

        Any previous-position state used by the collision system is also
        reset so the new point starts cleanly.
        """

        # Place the puck exactly at the centre of the table.
        self.puck.x = WIDTH / 2
        self.puck.y = HEIGHT / 2

        # Task 1 compatibility:
        # Reset the previous position as well, if it exists.
        # Otherwise the collision system could interpret the new point
        # as the puck travelling directly from the goal to the centre.
        if hasattr(self.puck, "previous_x"):
            self.puck.previous_x = self.puck.x

        if hasattr(self.puck, "previous_y"):
            self.puck.previous_y = self.puck.y

        # Task 4:
        # Immediately give the puck a fresh velocity and direction.
        self._launch_puck()

    def draw(self, surface, font):
        """
        Draw the complete game state.
        """

        from game import renderer

        renderer.draw_table(surface)

        renderer.draw_paddle(
            surface,
            self.player,
            renderer.COLOR_PLAYER
        )

        renderer.draw_paddle(
            surface,
            self.computer,
            renderer.COLOR_COMPUTER
        )

        renderer.draw_puck(
            surface,
            self.puck
        )

        # ---------------------------------------------------------
        # Task 2: SCORE DISPLAY
        # ---------------------------------------------------------

        player_text = f"Player: {self.player_score}"
        computer_text = f"Computer: {self.computer_score}"

        renderer.draw_text(
            surface,
            font,
            player_text,
            (MARGIN + 10, MARGIN + 8)
        )

        computer_width = font.size(computer_text)[0]

        renderer.draw_text(
            surface,
            font,
            computer_text,
            (
                WIDTH - MARGIN - computer_width - 10,
                MARGIN + 8
            )
        )

        # ---------------------------------------------------------
        # Task 3: TIMER DISPLAY
        # ---------------------------------------------------------

        time_text = f"Time: {self._get_remaining_time()}"
        time_width = font.size(time_text)[0]

        renderer.draw_text(
            surface,
            font,
            time_text,
            (
                (WIDTH - time_width) // 2,
                MARGIN + 8
            )
        )

        # ---------------------------------------------------------
        # Task 3: FINAL RESULT
        # ---------------------------------------------------------

        if self.match_over:
            renderer.draw_banner(
                surface,
                font,
                self._get_match_result()
            )