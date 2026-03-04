from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from database import get_db

app = FastAPI(title="4viso Backend")

@app.get("/")
async def root():
    return {"message": "Backend is running! Go to /spy-data to check PostgreSQL"}

@app.get("/spy-data")
async def check_db(db = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT version();"))
        version = result.scalar()
        return {
            "status": "PostgreSQL is connected!",
            "version": version
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")