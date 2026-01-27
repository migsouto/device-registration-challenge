from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import httpx
import os

app = FastAPI(title="Statistics API")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/devicedb"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

DEVICE_API_URL = os.getenv(
    "DEVICE_API_URL",
    "http://localhost:8001"
)

class DeviceRegistration(Base):
    __tablename__ = "device_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_key = Column(String, index=True)
    device_type = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuthLogRequest(BaseModel):
    userKey: str
    deviceType: str

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "StatisticsAPI"}

@app.post("/Log/auth")
async def log_auth(request: AuthLogRequest):
    try:
        valid_types = ["iOS", "Android", "Watch", "TV"]
        if request.deviceType not in valid_types:
            return {"statusCode": 400, "message": "bad_request"}
        
        if not request.userKey or request.userKey.strip() == "":
            return {"statusCode": 400, "message": "bad_request"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DEVICE_API_URL}/Device/register",
                json={
                    "userKey": request.userKey,
                    "deviceType": request.deviceType
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("statusCode") == 200:
                    return {"statusCode": 200, "message": "success"}
            
            return {"statusCode": 400, "message": "bad_request"}
            
    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 400, "message": "bad_request"}

@app.get("/Log/auth/statistics")
def get_statistics(deviceType: str):
    try:
        valid_types = ["iOS", "Android", "Watch", "TV"]
        if deviceType not in valid_types:
            return {"deviceType": deviceType, "count": -1}
        
        db = SessionLocal()
        try:
            count = db.query(DeviceRegistration).filter(
                DeviceRegistration.device_type == deviceType
            ).count()
            
            return {"deviceType": deviceType, "count": count}
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error: {e}")
        return {"deviceType": deviceType, "count": -1}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
