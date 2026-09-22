import logging
from typing import Optional
import redis
from app.config import settings

logger = logging.getLogger("app.services.redis_queue")

class RedisQueueService:
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None

    @property
    def client(self) -> Optional[redis.Redis]:
        if self._redis_client is None:
            try:
                url = settings.REDIS_URL or "redis://localhost:6379/0"
                kwargs = {
                    "decode_responses": True,
                    "socket_connect_timeout": 5,
                    "socket_timeout": 5,
                    "retry_on_timeout": True
                }
                if url.startswith("rediss://"):
                    kwargs["ssl_cert_reqs"] = None

                self._redis_client = redis.Redis.from_url(url, **kwargs)
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client: {str(e)}")
                self._redis_client = None
        return self._redis_client

    def is_healthy(self) -> bool:
        """Check if Redis connection is active."""
        try:
            c = self.client
            if c and c.ping():
                return True
        except Exception as e:
            logger.debug(f"Redis ping failed: {str(e)}")
            self._redis_client = None
        return False

    def enqueue_document_processing(self, document_id: str) -> bool:
        """Push document_id to Redis job queue list."""
        try:
            c = self.client
            if c:
                c.rpush("docu_intel:jobs", document_id)
                logger.info(f"Enqueued document {document_id} to Redis queue 'docu_intel:jobs'.")
                return True
        except Exception as e:
            logger.warning(f"Could not enqueue job to Redis ({str(e)}). Resetting client connection.")
            self._redis_client = None
        return False

    def dequeue_document_processing(self, timeout: int = 2) -> Optional[str]:
        """Pop next document_id from Redis job queue using BLPOP."""
        try:
            c = self.client
            if c:
                res = c.blpop("docu_intel:jobs", timeout=timeout)
                if res:
                    # res is a tuple: (queue_name, value)
                    return res[1]
        except Exception as e:
            logger.warning(f"Redis dequeue error ({str(e)}). Resetting client connection.")
            self._redis_client = None
        return None

redis_queue_service = RedisQueueService()

