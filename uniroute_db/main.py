from contextlib import asynccontextmanager
from typing import Optional
import json

from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

import models
import security
import database
from security import verify_token
from trie import Trie

campus_trie = Trie()


# =======================
# PYDANTIC ŞEMALARI
# =======================
class RoomCreate(BaseModel):
    room_number: str
    floor: int
    description: Optional[str] = None

class RoomUpdate(BaseModel):
    room_number: str
    floor: int
    description: Optional[str] = None

class RoomResponse(BaseModel):
    id: int
    room_number: str
    floor: int
    description: Optional[str] = None

    class Config:
        from_attributes = True


# =======================
# TRİE YÜKLEME
# =======================
def load_rooms_into_trie(db: Session):
    """Tüm odaları veritabanından Trie'ye yükler."""
    global campus_trie
    campus_trie = Trie()

    rooms = db.query(models.Room).all()
    for room in rooms:
        campus_trie.insert(room.room_number, {
            "id": room.id,
            "floor": room.floor,
            "description": room.description
        })


# =======================
# UYGULAMA BAŞLATMA
# =======================
@asynccontextmanager
async def lifespan(app: FastAPI):
    db_gen = database.get_db()
    db = next(db_gen)
    try:
        load_rooms_into_trie(db)
        print("Trie başarıyla yüklendi.")
    except Exception as e:
        print(f"Başlatma hatası: {e}")
    finally:
        db.close()
    yield


app = FastAPI(title="UniRoute API", version="3.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =======================
# GENEL ENDPOINT'LER
# =======================
@app.get("/")
async def root():
    return {"message": "UniRoute sistemi aktif!"}


@app.get("/search")
async def search_room(q: str = Query(..., min_length=1)):
    """Oda adına göre fuzzy arama yapar."""
    results = campus_trie.fuzzy_search(q)
    return {"data": results}


# =======================
# PUBLIC ROOM ENDPOINT'LERİ (token gerekmez)
# =======================
@app.get("/rooms", response_model=list[RoomResponse])
def get_all_rooms(db: Session = Depends(database.get_db)):
    """Tüm odaları listeler. Frontend oda seçimi için kullanır."""
    return db.query(models.Room).all()


@app.get("/rooms/{room_id}", response_model=RoomResponse)
def get_room_by_id(room_id: int, db: Session = Depends(database.get_db)):
    """Tek bir odanın detayını döndürür."""
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")
    return room


@app.get("/floors")
def get_floors(db: Session = Depends(database.get_db)):
    """Mevcut kat numaralarını listeler. Frontend kat seçimi için kullanır."""
    floors = db.query(models.Room.floor).distinct().order_by(models.Room.floor).all()
    return {"floors": [f[0] for f in floors]}


# =======================
# HARİTA ENDPOINT'İ (GeoJSON — token gerekmez)
# =======================
@app.get("/map/rooms")
async def get_all_rooms_for_map(db: Session = Depends(database.get_db)):
    """Tüm odaları GeoJSON formatında döndürür. Frontend harita için kullanır."""
    try:
        query = text("""
            SELECT
                id,
                room_number,
                floor,
                description,
                ST_AsGeoJSON(geom) AS geometry
            FROM rooms
            WHERE geom IS NOT NULL
        """)

        result = db.execute(query).fetchall()

        features = []
        for row in result:
            geometry = row.geometry
            if isinstance(geometry, str):
                geometry = json.loads(geometry)

            features.append({
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "id": row.id,
                    "room_number": row.room_number,
                    "floor": row.floor,
                    "description": row.description
                }
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =======================
# NAVIGASYON
# =======================
@app.get("/navigation/route")
async def get_route(
    start: str,
    end: str,
    disabled: bool = False,
    db: Session = Depends(database.get_db)
):
    """İki oda arasındaki rotayı GeoJSON olarak döndürür. disabled=true ise merdivenlerden kaçınır."""
    try:
        query = text("""
            SELECT ST_AsGeoJSON(geom) AS geometry
            FROM get_route_by_rooms(:start, :end, :disabled)
        """)

        result = db.execute(query, {
            "start": start,
            "end": end,
            "disabled": disabled
        }).fetchall()

        features = []
        for row in result:
            geometry = row.geometry
            if isinstance(geometry, str):
                geometry = json.loads(geometry)

            features.append({
                "type": "Feature",
                "geometry": geometry,
                "properties": {}
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =======================
# AUTH
# =======================
@app.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(
        models.User.username == form_data.username
    ).first()

    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")

    token = security.create_access_token({
        "sub": user.username,
        "role": user.role
    })

    return {"access_token": token, "token_type": "bearer"}


# =======================
# ADMIN KONTROLÜ
# =======================
def admin_required(user=Depends(verify_token)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem sadece admin kullanıcılara açıktır")
    return user


# =======================
# ADMIN ENDPOINT'LERİ
# =======================
@app.post("/admin/rooms", response_model=RoomResponse)
def create_room(
    room_data: RoomCreate,
    db: Session = Depends(database.get_db),
    user=Depends(admin_required)
):
    existing = db.query(models.Room).filter(
        models.Room.room_number == room_data.room_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu oda numarası zaten mevcut")

    room = models.Room(
        room_number=room_data.room_number,
        floor=room_data.floor,
        description=room_data.description
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    load_rooms_into_trie(db)
    return room


@app.get("/admin/rooms", response_model=list[RoomResponse])
def get_rooms(
    db: Session = Depends(database.get_db),
    user=Depends(admin_required)
):
    return db.query(models.Room).all()


@app.put("/admin/rooms/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_data: RoomUpdate,
    db: Session = Depends(database.get_db),
    user=Depends(admin_required)
):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()

    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")

    room.room_number = room_data.room_number
    room.floor = room_data.floor
    room.description = room_data.description
    db.commit()
    db.refresh(room)

    load_rooms_into_trie(db)
    return room


@app.delete("/admin/rooms/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(database.get_db),
    user=Depends(admin_required)
):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()

    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")

    db.delete(room)
    db.commit()

    load_rooms_into_trie(db)
    return {"message": "Oda silindi"}
