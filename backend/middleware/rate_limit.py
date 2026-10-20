"""
Middleware - Rate Limiting
Simple in-memory rate limiting to prevent abuse.
"""
from fastapi import Request, HTTPException, status
from typing import Dict, Tuple
import time
from config import settings

# Store mapping: IP -> (request_count, window_start_time)
_rate_limits: Dict[str, Tuple[int, float]] = {}

def rate_limit(request: Request):
    """
    Simple in-memory rate limiter based on client IP.
    Allows MAX_REQUESTS_PER_MINUTE per minute.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # 60 second window
    window_duration = 60
    max_requests = getattr(settings, 'MAX_REQUESTS_PER_MINUTE', 60)
    
    count, window_start = _rate_limits.get(client_ip, (0, now))
    
    if now - window_start > window_duration:
        # Reset window
        _rate_limits[client_ip] = (1, now)
    else:
        if count >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later."
            )
        _rate_limits[client_ip] = (count + 1, window_start)
