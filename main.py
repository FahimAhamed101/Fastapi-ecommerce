from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from db import init_db
from routes import app_router
from fastapi.staticfiles import StaticFiles

init_db()

app = FastAPI(title='Welcome to Ecommerce App', description='create product, place order', summary='Developed by @iamanx17')

@app.get("/")
async def welcome() -> dict:
    return {"message": "Welcome to FastAPI Ecommerce App!"}

app.mount("/static", StaticFiles(directory="uploads"), name="static")
app.include_router(app_router)

print('server started successfully')