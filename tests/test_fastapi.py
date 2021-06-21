from typing import Optional

from fastapi import Body, FastAPI
from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse

app = FastAPI()


class Item(BaseModel):
    name: str
    description: Optional[str] = Field(
        None, title="The description of the item", max_length=300
    )
    price: float = Field(..., gt=0, description="The price must be greater than zero")
    tax: Optional[float] = None


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item = Body(..., embed=True)):
    results = {"item_id": item_id, "item": item}
    return results


@app.get("/items/", response_class=HTMLResponse)
async def render_html():
    return """
    <html>
        <head>
        </head>
        <body>
            <h1>Hello World</h1>
        </body>
    </html>
    """


@app.get("/")
async def root():
    return {"message": "Hello World"}
