import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.controllers.menu import router as menu_router


app = FastAPI()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Serve uploaded images publicly
os.makedirs("uploads/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="uploads/images"), name="images")

@app.get("/")
def read_root():
    return {"message": "Welcome to your FastAPI app!"}

app.include_router(menu_router, prefix="/api")
