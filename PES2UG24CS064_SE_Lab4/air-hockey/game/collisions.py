"""
collisions: puck-vs-paddle collision handling.
"""

import math


def _segment_circle_hit(x1, y1, x2, y2, cx, cy, radius):
    """
    Find the first point where the puck's movement segment enters the
    paddle's collision circle.

    Returns the collision point and the fraction of the frame at which the
    collision happened, or (None, None) when the segment misses the circle.
    """
    dx = x2 - x1
    dy = y2 - y1
    fx = x1 - cx
    fy = y1 - cy

    a = dx * dx + dy * dy
    if a == 0:
        return None, None

    b = 2 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - radius * radius
    discriminant = b * b - 4 * a * c

    if discriminant < 0:
        return None, None

    sqrt_discriminant = math.sqrt(discriminant)
    t1 = (-b - sqrt_discriminant) / (2 * a)
    t2 = (-b + sqrt_discriminant) / (2 * a)

    # The smaller valid root is the first point at which the puck reaches
    # the paddle's expanded collision area.
    valid_t = [t for t in (t1, t2) if 0.0 <= t <= 1.0]

    if not valid_t:
        return None, None

    t = min(valid_t)

    return (
        (x1 + t * dx, y1 + t * dy),
        t,
    )


def _resolve_collision(puck, paddle, normal_x, normal_y, separation_distance):
    """Reflect the puck and place it outside the paddle."""

    # Calculate the component of the puck's velocity moving towards
    # the paddle.
    velocity_into_paddle = puck.vx * normal_x + puck.vy * normal_y

    # Only reflect the puck if it is actually moving towards the paddle.
    # This prevents repeated bouncing when the puck is already moving away.
    if velocity_into_paddle < 0:

        # Reflection formula:
        #
        # v' = v - 2(v . n)n
        #
        # where n is the collision normal.
        puck.vx -= 2 * velocity_into_paddle * normal_x
        puck.vy -= 2 * velocity_into_paddle * normal_y

    # Move the puck outside the paddle so that it cannot remain
    # embedded inside it and vibrate between frames.
    puck.x = paddle.x + normal_x * separation_distance
    puck.y = paddle.y + normal_y * separation_distance


def handle_paddle_collision(puck, paddle):
    """
    Detect and resolve a puck-paddle collision.

    The paddle and puck are treated as circles. The collision normal is used
    to reflect the puck, which makes angled impacts change both vx and vy
    instead of always reversing only vx.

    The puck's previous position is also checked, so a fast puck cannot simply
    move from one side of a paddle to the other between two frames.

    Returns True if a collision was handled this frame.
    """

    # The distance at which the puck and paddle begin to overlap.
    # Since both are circles, this is simply the sum of their radii.
    collision_radius = puck.radius + paddle.radius
    collision_radius_squared = collision_radius * collision_radius

    # The puck needs to know where it was before the current frame.
    # This allows us to detect cases where it travelled through the
    # paddle between two frames at high speed.
    previous_x = getattr(puck, "previous_x", puck.x)
    previous_y = getattr(puck, "previous_y", puck.y)

    previous_dx = previous_x - paddle.x
    previous_dy = previous_y - paddle.y

    previous_distance_squared = (
        previous_dx * previous_dx
        + previous_dy * previous_dy
    )

    # If the puck started outside the paddle, check the complete path
    # travelled during this frame.
    #
    # This prevents "tunnelling", where a fast-moving puck can move
    # completely through a paddle without its final position overlapping it.
    if previous_distance_squared > collision_radius_squared:

        collision_point, _ = _segment_circle_hit(
            previous_x,
            previous_y,
            puck.x,
            puck.y,
            paddle.x,
            paddle.y,
            collision_radius,
        )

        if collision_point is not None:

            collision_x, collision_y = collision_point

            # The collision normal points from the paddle centre towards
            # the point where the puck collided.
            normal_dx = collision_x - paddle.x
            normal_dy = collision_y - paddle.y
            normal_length = math.hypot(normal_dx, normal_dy)

            if normal_length > 1e-9:

                normal_x = normal_dx / normal_length
                normal_y = normal_dy / normal_length

            else:
                # A direct centre hit has no position-based normal.
                # In that rare case, use the direction opposite to the
                # incoming puck velocity.
                speed = math.hypot(puck.vx, puck.vy)

                if speed > 1e-9:
                    normal_x = -puck.vx / speed
                    normal_y = -puck.vy / speed
                else:
                    normal_x = 1.0
                    normal_y = 0.0

            # A very small separation prevents floating-point rounding
            # from immediately detecting the same collision again.
            _resolve_collision(
                puck,
                paddle,
                normal_x,
                normal_y,
                collision_radius + 1e-6,
            )

            return True

    # If the puck was already overlapping the paddle at the beginning
    # of the frame, repair the current overlap directly.
    dx = puck.x - paddle.x
    dy = puck.y - paddle.y

    distance_squared = dx * dx + dy * dy

    if distance_squared <= collision_radius_squared:

        distance = math.sqrt(distance_squared)

        if distance > 1e-9:

            # Normal points from the paddle towards the puck.
            normal_x = dx / distance
            normal_y = dy / distance

        else:
            # If the puck is exactly at the paddle centre, use its
            # incoming direction to construct a collision normal.
            speed = math.hypot(puck.vx, puck.vy)

            if speed > 1e-9:
                normal_x = -puck.vx / speed
                normal_y = -puck.vy / speed
            else:
                normal_x = 1.0
                normal_y = 0.0

        _resolve_collision(
            puck,
            paddle,
            normal_x,
            normal_y,
            collision_radius,
        )

        return True

    return False