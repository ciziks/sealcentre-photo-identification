from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.wildbook import Wildbook
from src.database import get_db
from src import crud, schemas, constants

router = APIRouter()


# CREATE NEW SEAL
@router.post("", response_model=schemas.Seal)
def create_seal(
    seal: schemas.SealCreate,
    db: Session = Depends(get_db),
):
    db_seal = crud.get_seal(db, seal_id=seal.ID)

    if db_seal:
        raise HTTPException(
            status_code=400, detail=constants.SEAL_ALREADY_EXISTS_MESSAGE
        )

    return crud.create_seal(db=db, seal=seal)


# GET SEAL BY ID/NAME
@router.get("/{seal_id}")
def read_seal(
    seal_id: str,
    wildbook: Wildbook = Depends(Wildbook),
    db: Session = Depends(get_db),
):
    seal = crud.get_seal(db, seal_id=seal_id)

    if not seal:
        raise HTTPException(status_code=404, detail=constants.SEAL_ERROR_MESSAGE)

    seal_images = []
    for encounter in seal.encounters:
        annotation_image = wildbook.get_annotation_image(encounter.WildBookID)
        seal_images.append(annotation_image)

    return {**seal.__dict__, "images": seal_images}


# LIST SEAL WITH PAGINATION
@router.get("")
def list_seals_with_pagination(
    skip: int = 0,
    limit: int = 10,
    wildbook: Wildbook = Depends(Wildbook),
    db: Session = Depends(get_db),
):
    total_seals, seals = crud.list_seals(db, skip=skip, limit=limit)

    seals_with_encounter = {}
    for seal in seals:
        seals_with_encounter[seal.ID] = []

        if seal.encounters:
            annotation_image = wildbook.get_annotation_image(
                seal.encounters[-1].WildBookID
            )
            seals_with_encounter[seal.ID].append(annotation_image)

    return {
        "total": total_seals,
        "limit": limit,
        "skip": skip,
        "data": seals_with_encounter,
    }


# UPDATE SEAL INFORMATION
@router.put("/{seal_id}", response_model=schemas.Seal)
def update_seal(seal_id: str, seal: schemas.SealCreate, db: Session = Depends(get_db)):
    db_seal = crud.get_seal(db, seal_id=seal_id)

    if db_seal is None:
        raise HTTPException(status_code=404, detail=constants.SEAL_NOT_FOUND_MESSAGE)

    return crud.update_seal(db=db, db_seal=db_seal, seal=seal)


# DELETE SEAL REGISTER AND RELATED ENCOUNTERS
@router.delete("/{seal_id}", response_model=schemas.Seal)
def delete_seal(seal_id: str, db: Session = Depends(get_db)):
    db_seal = crud.get_seal(db, seal_id=seal_id)

    if db_seal is None:
        raise HTTPException(status_code=404, detail=constants.SEAL_NOT_FOUND_MESSAGE)

    return crud.delete_seal(db=db, db_seal=db_seal)
