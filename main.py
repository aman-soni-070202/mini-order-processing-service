from fastapi import FastAPI
from src.db.models import model
from src.db.database import engine
from src import router

model.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mini Order Processing Service")

app.include_router(router=router)

@app.get("/")
async def read_root():
    return {"message": "Mini Order Processing Service"}
