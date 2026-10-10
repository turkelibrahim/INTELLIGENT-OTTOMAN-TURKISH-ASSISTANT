import time
import asyncio
from enum import Enum
from app.core.config import settings

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class ResilientClient:
    def __init__(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.max_failures = settings.NVIDIA_MAX_RETRIES + 1
        self.reset_timeout = 30  # seconds
        self.last_failure_time = 0
        
        # Rate Limiting
        self.max_concurrent = settings.NVIDIA_MAX_CONCURRENT
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.requests_last_minute = 0
        self.last_minute_timestamp = time.time()
        self.rpm_limit = settings.NVIDIA_REQUESTS_PER_MINUTE

    async def _check_rate_limit(self):
        now = time.time()
        if now - self.last_minute_timestamp >= 60:
            self.requests_last_minute = 0
            self.last_minute_timestamp = now
        
        if self.requests_last_minute >= self.rpm_limit:
            wait_time = 60 - (now - self.last_minute_timestamp)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.requests_last_minute = 0
            self.last_minute_timestamp = time.time()
            
        self.requests_last_minute += 1

    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
        self.failure_count = 0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.max_failures:
            self.state = CircuitState.OPEN

    async def execute(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.reset_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit Breaker OPEN - Cloud temporally paused")

        await self._check_rate_limit()

        async with self.semaphore:
            retry_count = 0
            while retry_count <= settings.NVIDIA_MAX_RETRIES:
                try:
                    result = await func(*args, **kwargs)
                    self.record_success()
                    return result
                except Exception as e:
                    err_str = str(e).lower()
                    if "429" in err_str or "timeout" in err_str or "50" in err_str:
                        retry_count += 1
                        if retry_count > settings.NVIDIA_MAX_RETRIES:
                            self.record_failure()
                            raise e
                        # Exponential backoff
                        await asyncio.sleep(2 ** retry_count)
                    else:
                        self.record_failure()
                        raise e

resilience_manager = ResilientClient()
