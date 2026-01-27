from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

app = FastAPI(title="Device Registration API")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/devicedb"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DeviceRegistration(Base):
    __tablename__ = "device_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_key = Column(String, index=True)
    device_type = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class RegisterRequest(BaseModel):
    userKey: str
    deviceType: str

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "DeviceRegistrationAPI"}

@app.post("/Device/register")
def register_device(request: RegisterRequest):
    try:
        valid_types = ["iOS", "Android", "Watch", "TV"]
        if request.deviceType not in valid_types:
            return {"statusCode": 400}
        
        if not request.userKey or request.userKey.strip() == "":
            return {"statusCode": 400}
        
        db = SessionLocal()
        try:
            registration = DeviceRegistration(
                user_key=request.userKey,
                device_type=request.deviceType
            )
            db.add(registration)
            db.commit()
            db.refresh(registration)
            return {"statusCode": 200}
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 400}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
