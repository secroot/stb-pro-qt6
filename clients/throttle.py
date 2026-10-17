"""
Thread-sicherer Rate-Limit & Backoff-Controller für den Multi-MAC-Scanner.
Verhindert Paketfluten bei HTTP 429 / Cloudflare / WAF-Sperren durch automatische
Cooldown-Phasen, Worker-Pausierung und adaptives Pacing.
"""
import time
import threading
from typing import Optional, Callable


class ScanThrottleController:
    def __init__(
        self,
        base_delay: float = 0.05,
        on_throttle_notify: Optional[Callable[[str], None]] = None,
    ):
        self.lock = threading.Lock()
        self.base_delay = max(0.0, float(base_delay))
        self.current_delay = self.base_delay
        self.cooldown_until = 0.0
        self.consecutive_429 = 0
        self.on_throttle_notify = on_throttle_notify

    def wait_turn(self, stop_check: Optional[Callable[[], bool]] = None):
        """Wird vor jedem HTTP-Request aufgerufen und pausiert bei Cooldown/Pacing."""
        while True:
            if stop_check and not stop_check():
                return
            now = time.time()
            with self.lock:
                rem_pause = self.cooldown_until - now
                delay = self.current_delay

            if rem_pause > 0:
                time.sleep(min(rem_pause, 0.25))
            else:
                break

        if delay > 0:
            time.sleep(delay)

    def handle_rate_limit(self, retry_after: Optional[int] = None):
        """Wird bei HTTP 429 oder Cloudflare/WAF-Blocks aufgerufen und bremst alle Threads."""
        with self.lock:
            self.consecutive_429 += 1
            now = time.time()
            if retry_after and retry_after > 0:
                pause_s = min(float(retry_after), 60.0)
            else:
                pause_s = min(4.0 * (2 ** min(self.consecutive_429 - 1, 3)), 30.0)

            new_cooldown = now + pause_s
            if new_cooldown > self.cooldown_until:
                self.cooldown_until = new_cooldown

            self.current_delay = min(max(self.current_delay + 0.15, 0.2), 2.5)

        if self.on_throttle_notify:
            self.on_throttle_notify(
                f"[⚠️ RATE LIMIT] Server meldet HTTP 429/WAF! Scanner pausiert für {pause_s:.0f}s. "
                f"Pacing erhöht auf {self.current_delay:.2f}s."
            )

    def handle_success(self):
        with self.lock:
            if self.consecutive_429 > 0:
                self.consecutive_429 = max(0, self.consecutive_429 - 1)
            if self.current_delay > self.base_delay:
                self.current_delay = max(self.base_delay, self.current_delay - 0.01)
