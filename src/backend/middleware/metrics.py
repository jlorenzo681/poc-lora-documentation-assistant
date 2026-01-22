
import time
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Metrics definitions
REQUEST_COUNT = Counter(
    "http_requests_total", 
    "Total number of HTTP requests", 
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", 
    "HTTP request latency in seconds", 
    ["method", "endpoint"]
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Record metrics
        process_time = time.time() - start_time
        REQUEST_LATENCY.labels(
            method=request.method, 
            endpoint=request.url.path
        ).observe(process_time)
        
        REQUEST_COUNT.labels(
            method=request.method, 
            endpoint=request.url.path, 
            status_code=response.status_code
        ).inc()
        
        return response

def metrics_endpoint(request: Request):
    """Expose Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
