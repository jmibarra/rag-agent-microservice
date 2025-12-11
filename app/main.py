from fastapi import FastAPI, Depends
from app.core.config import settings
from app.core.security import get_api_key

app = FastAPI(title=settings.APP_NAME)

@app.get("/health")
def health_check():
    return {"status": "ok"}

from app.api import routes
app.include_router(routes.router, prefix=settings.API_V1_STR) # dependencies=[Depends(get_api_key)] is already on the router, but adding here is fine too or duplicate. 
# Routes invoke get_api_key in their own dependencies, so we can clean this up.
# Let's just import and include.


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
