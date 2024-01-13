from typing import Any, Optional
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import orjson
from pydantic import BaseModel, conint
from fastapi import HTTPException, status


class CustomORJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        assert orjson is not None, "orjson must be installed"
        return orjson.dumps(content, option=orjson.OPT_INDENT_2)


server = FastAPI(default_response_class=CustomORJSONResponse)

# Define the list of origins that should be allowed
origins = [
    "http://localhost:8000",
    "http://localhost:5500",
    "http://localhost:80",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:80",
    "http://127.0.0.1:8080",
]

# Add CORS middleware to allow the specified origins
server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# fakedb
listitems = []

# pydantic model for list item


class ListItem(BaseModel):
    content: str = "Insert item content here."
    index: conint(ge=0)
    marked: bool = False

# helper functions for list items


def item_index_exists(item_index: int) -> bool:
    '''checks if a list item index exists'''
    return any(item for item in listitems if item.index == item_index)


def sort_item_list(listitems: list[ListItem]):
    '''sort the listitems by index'''
    listitems.sort(key=lambda item: item.index)


def seed_listitems(n: int):
    global listitems
    listitems = [
        ListItem(content=f"Item {i}", index=i, marked=(i % 2 == 0))
        for i in range(n)
    ]


# CRUD

@server.get("/")
async def read_root():
    return {"message": "Hello World"}

# add a set of items to itemlist, or a single one


@server.post("/list/items")
def add_list_item(new_items: list[ListItem]):
    '''adds a list of one or more listitems to memory'''
    global listitems
    # for each new item, check if they are a duplicate index
    for item in new_items:
        # if a duplicate ID exists
        if item_index_exists(item.index):
            # raise an error
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Item index collision. Ensure all items have a unique index.")
    # the items are not duplicates, add them to the list
    for item in new_items:
        listitems.append(item)
    # sort the list
    sort_item_list(listitems)
    # return success
    return {"data": "success"}
# read list items


@server.get("/list/items")
async def get_items(start_index: Optional[int] = None,
                    end_index: Optional[int] = None,
                    specific_index: Optional[int] = None) -> list[ListItem]:
    '''get items by a start/end index or a specific index'''
    global listitems
    if specific_index is not None:
        # Return items with specific index
        return [item for item in listitems if item.index == specific_index]
    elif start_index is not None and end_index is not None:
        # Return items within the range of indices
        return [item for item in listitems if start_index <= item.index <= end_index]
    else:
        # Return all items if no parameters are provided
        return listitems


# delete list items


@server.delete("/list/items")
async def delete_items(start_index: Optional[int] = None,
                       end_index: Optional[int] = None,
                       specific_index: Optional[int] = None,
                       content: Optional[str] = None):
    '''delete list items by a start/end index or a specific index or by contente'''
    global listitems

    if specific_index is not None:
        # Delete item by specific index
        listitems = [
            item for item in listitems if item.index != specific_index]
    elif start_index is not None and end_index is not None:
        # Delete items by range of indices
        listitems = [item for item in listitems if not (
            start_index <= item.index <= end_index)]
    elif content is not None:
        # Delete items by content
        listitems = [item for item in listitems if item.content != content]
    else:
        raise HTTPException(status_code=400, detail="Invalid parameters")

    # sort the item list
    sort_item_list(listitems)
    return {"data": "success"}
# update a list item


@server.put("/list/items")
async def update_items(updated_items: list[ListItem]):
    global listitems

    for updated_item in updated_items:
        if item_index_exists(updated_item.index):
            # Update the item
            for i, item in enumerate(listitems):
                if item.index == updated_item.index:
                    listitems[i] = updated_item
                    break
        else:
            # Item not found, raise an error
            raise HTTPException(
                status_code=404, detail=f"Item with index {updated_item.index} not found")

    sort_item_list(listitems)
    return {"data": "success"}


@server.get("/api/dump")
async def api_dump():
    global listitems
    return {
        "listitems": listitems
    }


@server.get("/api/clear")
async def api_clear():
    global listitems
    listitems = []
    return {
        "debug": "all list items cleared!"
    }


@server.get("/api/seed")
async def api_seed(n: int = 8):
    listitems = []
    seed_listitems(n)
    return {
        "debug": f"{n} list items seeded"
    }
