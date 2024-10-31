from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import PositiveInt, NonNegativeFloat, NonNegativeInt
from typing import Iterable, Annotated, List
from lecture_2.hw.shop_api.models import Item, ItemInCart, Cart

app = FastAPI(title="Shop API")


def cart_id_generator() -> Iterable[int]:
    i = 0
    while True:
        yield i
        i += 1


def item_id_generator() -> Iterable[int]:
    i = 0
    while True:
        yield i
        i += 1


_cart_id_generator = cart_id_generator()
_item_id_generator = item_id_generator()

carts: List[Cart] = []
items: List[Item] = []


def find_cart(cart_id: int) -> Cart:
    # При нескольких потоках не будет нормально работать
    # if len(carts) <= cart_id:
    #     raise HTTPException(status_code=404, detail="Cart not found")
    # else:
    #     return carts[cart_id]
    cart = next((cart for cart in carts if cart.id == cart_id), None)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart


def find_item(item_id: int) -> Item:
    # При нескольких потоках не будет нормально работать
    # if len(items) <= item_id:
    #     raise HTTPException(status_code=404, detail="Item not found")
    # else:
    #     return items[item_id]
    item = next((item for item in items if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.post('/cart', status_code=status.HTTP_201_CREATED)
def create_cart(response: Response):
    cart_id = next(_cart_id_generator)
    new_cart = Cart(id=cart_id, items=[], price=0.0)
    carts.append(new_cart)
    response.headers["Location"] = f'/cart/{cart_id}'
    return {"id": cart_id}

@app.get('/cart/{id}')
def get_cart(id: int):
    return find_cart(id)


@app.get('/cart')
async def list_carts(offset: Annotated[NonNegativeInt, Query()] = 0,
                     limit: Annotated[PositiveInt, Query()] = 10,
                     min_price: Annotated[NonNegativeFloat, Query()] = None,
                     max_price: Annotated[NonNegativeFloat, Query()] = None,
                     min_quantity: Annotated[NonNegativeInt, Query()] = None,
                     max_quantity: Annotated[NonNegativeInt, Query()] = None):
    filtered_carts = carts[offset:offset + limit]

    if min_price is not None:
        filtered_carts = [cart for cart in filtered_carts if cart.price >= min_price]

    if max_price is not None:
        filtered_carts = [cart for cart in filtered_carts if cart.price <= max_price]

    if min_quantity is not None:
        filtered_carts = [cart for cart in filtered_carts if sum(item.quantity for item in cart.items) >= min_quantity]

    if max_quantity is not None:
        filtered_carts = [cart for cart in filtered_carts if sum(item.quantity for item in cart.items) <= max_quantity]

    return filtered_carts


@app.post('/cart/{cart_id}/add/{item_id}')
def add_item_to_cart(cart_id: int, item_id: int):
    cart = find_cart(cart_id)
    item = find_item(item_id)

    for cart_item in cart.items:
        if cart_item.id == item_id:
            cart_item.quantity += 1
            break
    else:
        cart.items.append(ItemInCart(id=item.id, quantity=1))

    cart.price += item.price
    return {"status": "Item added"}


@app.post('/item', status_code=201)
def create_item(response: Response, item: Item):
    item.id = next(_item_id_generator)
    items.append(item)
    response.headers["Location"] = f'/item/{item.id}'
    return item


@app.get('/item/{id}')
async def get_item(id: int):
    item = find_item(id)
    if item.deleted:
        raise HTTPException(status_code=404, detail="Item deleted")
    return item


@app.get('/item')
def list_items(offset: Annotated[NonNegativeInt, Query()] = 0,
               limit: Annotated[PositiveInt, Query()] = 10,
               min_price: Annotated[NonNegativeFloat, Query()] = None,
               max_price: Annotated[NonNegativeFloat, Query()] = None,
               show_deleted: Annotated[bool, Query()] = False):
    filtered_items = items[offset:offset + limit]

    if min_price is not None:
        filtered_items = [item for item in filtered_items if item.price >= min_price]

    if max_price is not None:
        filtered_items = [item for item in filtered_items if item.price <= max_price]

    if not show_deleted:
        filtered_items = [item for item in filtered_items if not item.deleted]

    return filtered_items


@app.put('/item/{id}')
def update_item(id: int, updated_item: Item):
    existing_item = find_item(id)
    updated_item.id = id
    items[existing_item.id] = updated_item
    return updated_item


@app.patch('/item/{id}')
def patch_item(id: int, updates: dict):
    existing_item = find_item(id)

    if existing_item.deleted:
        raise HTTPException(status_code=304, detail="Item not found")

    for key, value in updates.items():
        if key == "deleted" and value:
            raise HTTPException(status_code=422, detail="Cannot modify attribute 'deleted'")

        if key not in existing_item.__dict__:
            raise HTTPException(status_code=422, detail=f"Attribute '{key}' is not found")

        setattr(existing_item, key, value)

    return existing_item


@app.delete('/item/{id}')
def delete_item(id: int):
    existing_item = find_item(id)
    existing_item.deleted = True
    return existing_item
