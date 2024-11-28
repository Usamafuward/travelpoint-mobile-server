from fastapi import FastAPI
from app.routers import auth, posts, profile, guides, equipments, authorities, vehicles, home, follow
from starlette.middleware.sessions import SessionMiddleware
from app.database import conn, cur

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="YOUR_SECRET_KEY")

@app.get("/")
async def root():
    return {"message": "Welcome to TravelPoint!"}   

# Include Routers
app.include_router(auth.router)
app.include_router(home.router)
app.include_router(posts.router)
app.include_router(profile.router)
app.include_router(guides.router)
app.include_router(equipments.router)
app.include_router(authorities.router)
app.include_router(vehicles.router)
app.include_router(follow.router)



