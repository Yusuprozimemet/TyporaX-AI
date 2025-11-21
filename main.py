"""
Main FastAPI application entry point
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import API routers
from src.api.chat_router import router as chat_router
from src.api.assessment_router import router as assessment_router
from src.api.main_router import router as main_router
from src.api.scenario_router import router as scenario_router

# Initialize FastAPI
app = FastAPI(
    title="TyporaX-AI - AI Language Coach",
    description="AI-powered language learning with personality-based personalization",
    version="8.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")


# Development helper: force browsers to re-fetch static assets
# (prevents 304 caching during active development)
@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    response = await call_next(request)
    try:
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
    except Exception:
        # Be tolerant to any unexpected request/response types
        pass
    return response

# Include routers
app.include_router(main_router, tags=["main"])
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(assessment_router, prefix="/api", tags=["assessment"])
app.include_router(scenario_router, prefix="/api/scenario", tags=["scenario"])

if __name__ == "__main__":
    import uvicorn
    # Debug: Print all routes
    print("[*] Registered routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {route.methods} {route.path}")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
