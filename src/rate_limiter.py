"""
Rate Limiter - 20 msg/min por usuario, 5s cooldown por comando
"""
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self):
        self.users = defaultdict(lambda: {"count": 0, "reset": time.time() + 60})
        self.max_per_minute = 20
        self.command_cooldown = {}

    def is_allowed(self, user_id, command=None):
        now = time.time()
        uid = str(user_id)

        if now > self.users[uid]["reset"]:
            self.users[uid] = {"count": 0, "reset": now + 60}

        self.users[uid]["count"] += 1
        if self.users[uid]["count"] > self.max_per_minute:
            return False

        if command:
            key = f"{uid}:{command}"
            if key in self.command_cooldown and now < self.command_cooldown[key]:
                return False
            self.command_cooldown[key] = now + 5

        return True

    def get_remaining(self, user_id):
        uid = str(user_id)
        return max(0, self.max_per_minute - self.users[uid]["count"])

rate_limiter = RateLimiter()