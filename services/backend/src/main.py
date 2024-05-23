from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .wrappers.Wildbook import Wildbook
import os
from sqlalchemy.orm import Session, joinedload
from .database import SessionLocal, engine, Base
from .models import Seal, Sighting, Encounter
from .schemas import (
    SealCreate,
    Seal as SealSchema,
    SightingCreate,
    Sighting as SightingSchema,
    EncounterCreate,
    Encounter as EncounterSchema,
)

Base.metadata.create_all(bind=engine)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Function to connect a session to the database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root(wildbook: Wildbook = Depends(Wildbook), db: Session = Depends(get_db)):
    wildbook_running = wildbook.is_running()

    # Query to get the first seal entry
    seal = db.query(Seal).first()

    return {
        "text": "Hello World",
        "wildbook": wildbook_running,
        "db": seal if seal else "No data found",
    }


# Create Seal
@app.post("/seal", response_model=SealSchema)
async def new_seal(
    seal: SealCreate,
    db: Session = Depends(get_db),
):
    db_seal = db.query(Seal).filter(Seal.ID == seal.ID).first()
    if db_seal:
        raise HTTPException(status_code=400, detail="Seal already registered")

    new_seal = Seal(**seal.model_dump())
    db.add(new_seal)
    db.commit()
    db.refresh(new_seal)
    return new_seal


# Read Individual Seal
@app.get("/seals/{seal_id}", response_model=SealSchema)
def read_seal(
    seal_id: str, wildbook: Wildbook = Depends(Wildbook), db: Session = Depends(get_db)
):
    seal = (
        db.query(Seal)
        .filter(Seal.ID == seal_id)
        .options(joinedload(Seal.encounters))
        .first()
    )

    if not seal:
        raise HTTPException(status_code=404, detail="Seal not found")

    seal_images = []

    for encounter in seal.encounters:
        annotation_image = wildbook.get_annotation_image(encounter.WildBookID)
        seal_images.append(annotation_image)

    return {**seal.__dict__, "images": seal_images}


# List Seals with their images with pagination
@app.get("/seals")
def list_seals(
    wildbook: Wildbook = Depends(Wildbook),
    db: Session = Depends(get_db),
    limit: int = Query(10, description="# of maximum results", gt=0),
    offset: int = Query(0, description="# of results to skip", ge=0),
):
    seals_query = db.query(Seal).options(joinedload(Seal.encounters))
    total_seals = seals_query.count()
    seals = seals_query.offset(offset).limit(limit).all()
    seals_with_encounters = {}

    for seal in seals:
        seals_with_encounters[seal.ID] = []

        for encounter in seal.encounters:
            annotation_image = wildbook.get_annotation_image(encounter.WildBookID)
            seals_with_encounters[seal.ID].append(annotation_image)

    return {
        "total": total_seals,
        "limit": limit,
        "offset": offset,
        "data": seals_with_encounters,
    }


# Update Seals
@app.put("/seals/{seal_id}", response_model=SealSchema)
def update_seal(seal_id: str, seal: SealCreate, db: Session = Depends(get_db)):
    db_seal = db.query(Seal).filter(Seal.ID == seal_id).first()
    if not db_seal:
        raise HTTPException(status_code=404, detail="Seal not found")

    seal_data = seal.model_dump()
    for key, value in seal_data.items():
        setattr(db_seal, key, value)

    db.commit()
    db.refresh(db_seal)
    return db_seal


# Delete Seal
@app.delete("/seals/{seal_id}", response_model=SealSchema)
def delete_seal(seal_id: str, db: Session = Depends(get_db)):
    db_seal = db.query(Seal).filter(Seal.ID == seal_id).first()
    if not db_seal:
        raise HTTPException(status_code=404, detail="Seal not found")

    db.delete(db_seal)
    db.commit()
    return db_seal


# Create Sighting
@app.post("/sightings", response_model=SightingSchema)
def add_sighting(
    sighting: SightingCreate,
    db: Session = Depends(get_db),
):
    # Check if the sighting already exists
    existing_sighting = (
        db.query(Sighting)
        .filter(Sighting.Date == sighting.Date, Sighting.Location == sighting.Location)
        .first()
    )

    if existing_sighting:
        new_sighting = existing_sighting
    else:
        # Create the Sighting Register
        sighting_data = sighting.model_dump()
        new_sighting = Sighting(**sighting_data)

        db.add(new_sighting)
        db.commit()
        db.refresh(new_sighting)

    return new_sighting


# Read Sighting
@app.get("/sightings/{sighting_id}", response_model=SightingSchema)
def read_sighting(
    sighting_id: int,
    db: Session = Depends(get_db),
    wildbook: Wildbook = Depends(Wildbook),
):
    sighting = (
        db.query(Sighting)
        .filter(Sighting.SightingID == sighting_id)
        .options(joinedload(Seal.encounters))
        .first()
    )

    if not sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")

    sighting_images = []

    for encounter in sighting.encounters:
        annotation_image = wildbook.get_annotation_image(encounter.WildBookID)
        sighting_images.append(annotation_image)

    return {**sighting, "images": sighting_images}


# List Sightings
@app.get("/sightings", response_model=list[SightingSchema])
def list_sightings(
    wildbook: Wildbook = Depends(Wildbook), db: Session = Depends(get_db)
):
    sightings = db.query(Sighting).options(joinedload(Sighting.encounters)).all()

    sightings_with_encounters = {}

    for sighting in sightings:
        sightings_with_encounters[sighting.ID] = []

        for encounter in sighting.encounters:
            annotation_image = wildbook.get_annotation_image(encounter.WildBookID)
            sightings_with_encounters[sighting.ID].append(annotation_image)

    return sightings_with_encounters


# Update Sightings
@app.put("/sightings/{sighting_id}", response_model=SightingSchema)
def update_sighting(
    sighting_id: int, sighting: SightingCreate, db: Session = Depends(get_db)
):
    db_sighting = db.query(Sighting).filter(Sighting.SightingID == sighting_id).first()
    if not db_sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")
    sighting_data = sighting.model_dump()
    for key, value in sighting_data.items():
        setattr(db_sighting, key, value)
    db.commit()
    db.refresh(db_sighting)
    return db_sighting


# Remove Sightings
@app.delete("/sightings/{sighting_id}", response_model=SightingSchema)
def delete_sighting(sighting_id: int, db: Session = Depends(get_db)):
    db_sighting = db.query(Sighting).filter(Sighting.SightingID == sighting_id).first()
    if not db_sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")
    db.delete(db_sighting)
    db.commit()
    return db_sighting


@app.post("/detect")
async def detect_seal(
    image: UploadFile = File(...),
    wildbook: Wildbook = Depends(Wildbook),
):
    if not image:  # Check for image
        raise HTTPException(status_code=400, detail="No image uploaded")

    # Save the image temporarily
    temp_image_path = "temp_image_storage.png"
    with open(temp_image_path, "wb") as f:
        f.write(await image.read())

    try:
        # Upload image
        image_id = wildbook.upload_image(temp_image_path)

        # Get Image Size
        image_size = [0, 0] + list(wildbook.get_images_size([image_id])[0])

        # Create Annotation in WildBook
        aid_list = wildbook.create_annotations(
            [image_id],
            [image_size],
        )
        print(aid_list)
        # Match seal with seals in DB
        scores = wildbook.seal_matching(aid_list[0])

    finally:
        # Clean up after upload
        os.remove(temp_image_path)

    return {"wildbook_id": aid_list[0], **scores}


@app.post("/encounters", response_model=EncounterSchema)
def create_encounter(encounter: EncounterCreate, db: Session = Depends(get_db)):
    # Check if the specified sighting exists
    existing_sighting = (
        db.query(Sighting).filter(Sighting.SightingID == encounter.SightingID).first()
    )
    if not existing_sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")

    # Check if the specified seal exists
    existing_seal = db.query(Seal).filter(Seal.ID == encounter.SealID).first()
    if not existing_seal:
        raise HTTPException(status_code=404, detail="Seal not found")

    # Create the Encounter
    new_encounter = Encounter(
        SightingID=encounter.SightingID,
        SealID=encounter.SealID,
        WildBookID=encounter.WildBookID,
    )

    db.add(new_encounter)
    db.commit()
    db.refresh(new_encounter)

    return new_encounter
