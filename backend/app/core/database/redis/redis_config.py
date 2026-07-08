from core.logger.logging_tool import get_logger
from config import Configs
config = Configs()

logger = get_logger(name="Redis Connection Logs",feature="database/redis/redis_config.py")

def get_redis_url():
    redis_url = f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}"
    logger.debug(f"Using Redis URL: {redis_url}")
    return redis_url

# Test Redis connection during startup
if __name__ == "__main__":
    import redis
    try:
        r = redis.Redis(host=config.REDIS_HOST, port=int(config.REDIS_PORT), db=int(config.REDIS_DB))
        if r.ping():
            logger.info("Successfully connected to Redis!")
        else:
            logger.error("Redis connection failed.")
    except Exception as e:
        logger.error(f"Redis connection error: {e}")