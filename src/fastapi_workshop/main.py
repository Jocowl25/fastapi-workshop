import hashlib
import os
from math import sqrt
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel
from starlette.responses import FileResponse

from fastapi_workshop.card_data_helper import Card, cards, cards_dict

import random

description = """
This is the list of functions that we will be showing off.
It uses markdown to render the text so anything you can do in markdown you can do here.

## Treasure
* **Lay Treasure** - (_not implemented_)
* **search for treasure** - gives how far away from treasure

## Cards
* **all cards** - gets all the cards.
* **cards**  - gets a specified card
* **random card** - (_not implemented_)

## File
* **upload file**  - Lets you upload a file
* **download file** - Lets you download a file
* **delete file** - Lets you delete a file


"""
tags_metadata = [
    {
        "name": "Treasure",
        "description": "Operations to deal with the treasure hunt",
    },
    {
        "name": "Cards",
        "description": "Interacts with cards to do a variety of things with",
    },
    {
        "name": "File",
        "description": "Lets you upload, download, and delete files",
    },
]

app = FastAPI(
    title="FastAPI Workshop",
    description=description,
    summary="The fuctions that are being implemented or are already implemented",
    version="0.0.1",
    openapi_tags=tags_metadata,
    terms_of_service="http://example.com/terms/",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/license/mit",
    },
)


@app.get("/")
def hello_world() -> str:
    """A hello world function, shows basic syntax for FastAPI"""
    return "Hello World! This is the root of the app, served through the hello_world() function."


def distance(loc_1: tuple[int, int], loc_2: tuple[int, int]) -> float:
    return sqrt((loc_1[0] - loc_2[0]) ** 2 + (loc_1[1] - loc_2[1]) ** 2)

SECRET_LOCATION = (1, 5)


class TreasureResult(BaseModel):
    """The response from a search for treasure. Tells you how far away you were."""

    found: bool | None = None
    distance_away: float | None = None


times_found: int = 0

@app.post("/lay_treasure", response_model_exclude_none=True, tags=["Treasure"])
def lay_treasure(x: int, y: int):
    global SECRET_LOCATION
    SECRET_LOCATION=(x,y)

@app.post("/search-for-treasure", response_model_exclude_none=True, tags=["Treasure"])
def search_for_treasure(x: int, y: int) -> TreasureResult:
    """
    Do a search for treasure. A more complicated code, using python logic.
    Takes in two parameters, x & y, and tells you how far away you were.
    """
    given_location = (x, y)
    if (x, y) == SECRET_LOCATION:
        global times_found
        times_found += 1
        return TreasureResult(found=True)
    else:
        return TreasureResult(distance_away=distance(given_location, SECRET_LOCATION))


@app.get("/random-deck", tags=["Cards"])
def get_random_deck() -> list[str]:
    """
    Gets card names.
    """
    cardSubset=random.sample(cards,k=60)
    cardNames=[]
    for card in cardSubset:
        cardNames.append(card.name)
    return cardNames

@app.get("/all-cards", tags=["Cards"])
def get_all_cards() -> list[Card]:
    """
    Gets all the cards from the database.

    Very slow and laggy because there is ~3mb of card data.
    """
    return cards


@app.get("/card", tags=["Cards"])
def get_card(card_name: str) -> Card:
    """Gets a single card from the card dictionary. Fast."""
    return cards_dict[card_name]


class UploadFileResponse(BaseModel):
    type: str | None
    filename: str


@app.put("/file", tags=["File"])
def upload_file(file: UploadFile, name: str | None = None) -> UploadFileResponse:
    """Uploads a file. If its a png, saves it to the local database."""

    assert file.size is not None

    if name is None:
        assert file.filename is not None
        name = file.filename

    # Checks the file size to see if it is larger than 0. The file must be named.
    if file.size > 0:
        # Make sure that the database folders are available
        os.makedirs("db/files", exist_ok=True)

        # Hash the filename. This prevents attacks such as specifying the filename ../../main.py
        hash = hashlib.sha256(
            name.encode(errors="ignore"), usedforsecurity=False
        ).hexdigest()

        # Writes the file to the database
        with open(f"db/files/{hash}", "wb") as f:
            f.write(file.file.read())

    # Either way, we should return a response with the file's
    # content type and the files name for debugging purposes.
    return UploadFileResponse(type=file.content_type, filename=name)


@app.get("/file", tags=["File"])
def download_file(filename: str) -> FileResponse:
    """Downloads a file. Requires a filename that has been uploaded previously."""

    # Hash the filename to retrieve the correct path
    hash = hashlib.sha256(
        filename.encode(errors="ignore"), usedforsecurity=False
    ).hexdigest()
    # Construct the path
    path = Path(f"db/files/{hash}")
    # If the file doesn't exist, return an error
    if not path.exists():
        raise HTTPException(404, detail="That file does not exist.")
    # Otherwise, return the file asyncronously
    return FileResponse(path, filename=filename, content_disposition_type="inline")


@app.delete("/file", tags=["File"])
def delete_file(filename: str) -> bool:
    """Deletes a file that was previously updated."""

    # Hash the filename to retrieve the correct path
    hash = hashlib.sha256(
        filename.encode(errors="ignore"), usedforsecurity=False
    ).hexdigest()
    # Construct the path
    path = Path(f"db/files/{hash}")
    # If the file doesn't exist, return an error
    if not path.exists():
        raise HTTPException(404, detail="That file does not exist.")

    os.remove(path)
    return True
