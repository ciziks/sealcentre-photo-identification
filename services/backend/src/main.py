from typing import Union
from antidote import world, inject
from fastapi import FastAPI

from .wrappers.Wildbook import Wildbook

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
