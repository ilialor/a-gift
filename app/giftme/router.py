from fastapi import APIRouter, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.dao import UserDAO, GiftDAO, GiftListDAO, UserListDAO
from app.dao.session_maker import async_session_maker
from app.giftme.models import Gift, User, GiftList, UserList
from app.giftme.schemas import GiftResponse, GiftUpdate
import logging

from app.giftme.schemas import (
    GiftCreate,
    GiftUpdate,
    GiftResponse,
    GiftListCreate,
    GiftListUpdate,
    GiftListResponse,
    UserListCreate,
    UserListUpdate,
    UserListResponse,
    DeleteResponse
)

router = APIRouter(prefix='', tags=['GIFTME'])
templates = Jinja2Templates(directory='app/templates')


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("pages/index.html", {"request": request})


# @router.get("/records", response_class=HTMLResponse)
# async def read_records(request: Request, session: AsyncSession = Depends(async_session_maker)):
#     # Получаем топовые рекорды с их позициями
#     user_dao = UserDAO(session)
#     records = await user_dao.get_top_scores()
#     # Передаем актуальный список рекордов в шаблон
#     return templates.TemplateResponse("pages/records.html", {"request": request, "records": records})


# @router.put("/api/bestScore/{user_id}", response_model=SetBestScoreResponse, summary="Set Best Score")
# async def set_best_score(
#         user_id: int,
#         request: SetBestScoreRequest,
#         session: AsyncSession = Depends(async_session_maker)
# ):
#     """
#     Установить лучший счет пользователя.
#     Обновляет значение `best_score` в базе данных для текущего `user_id`.
#     """
#     user_dao = UserDAO(session)
#     user = await user_dao.get_user_by_id(user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     user.best_score = request.score
#     await session.commit()
#     return SetBestScoreResponse(status="success", best_score=request.score)


# Gifts Endpoints

@router.post("/gifts", response_model=GiftResponse, summary="Create a new gift")
async def create_gift(
    gift: GiftCreate, 
    request: Request, 
    session: AsyncSession = Depends(async_session_maker)
):
    # Log the request body
    logging.info(f"Request body for /gifts: {gift.model_dump()}")
    
    current_user_id = await get_current_user(request)  # Retrieve the authenticated user's ID
    if gift.owner_id != current_user_id:
        logging.warning(f"User ID {current_user_id} attempted to create gift for User ID {gift.owner_id}")
        raise HTTPException(status_code=403, detail="Forbidden: Cannot create gift for another user.")
    
    gift_dao = GiftDAO(session)
    new_gift = await gift_dao.create_gift(gift.model_dump())
    logging.info(f"Gift created with ID: {new_gift.id} for User ID: {current_user_id}")
    return new_gift

async def get_current_user(request: Request):
    # Implement your user retrieval logic here
    # For example, you can get the user from a session or a token
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user

@router.get("/gifts/{gift_id}", response_model=GiftResponse, summary="Retrieve a gift by ID")
async def get_gift(gift_id: int, session: AsyncSession = Depends(async_session_maker)):
    gift_dao = GiftDAO(session)
    gift = await gift_dao.get_gift_by_id(gift_id)
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    return gift

@router.put("/gifts/{gift_id}", response_model=GiftResponse, summary="Update a gift by ID")
async def update_gift(gift_id: int, gift: GiftUpdate, session: AsyncSession = Depends(async_session_maker)):
    gift_dao = GiftDAO(session)
    updated_gift = await gift_dao.update_gift(gift_id, gift.dict())
    if not updated_gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    return updated_gift

@router.delete("/gifts/{gift_id}", response_model=DeleteResponse, summary="Delete a gift by ID")
async def delete_gift(gift_id: int, session: AsyncSession = Depends(async_session_maker)):
    gift_dao = GiftDAO(session)
    success = await gift_dao.delete_gift(gift_id)
    if not success:
        raise HTTPException(status_code=404, detail="Gift not found")
    return DeleteResponse(status="success")


# Gift Lists Endpoints

@router.post("/giftlists", response_model=GiftListResponse, summary="Create a new gift list")
async def create_gift_list(gift_list: GiftListCreate, session: AsyncSession = Depends(async_session_maker)):
    gift_list_dao = GiftListDAO(session)
    new_gift_list = await gift_list_dao.create_gift_list(gift_list.dict())
    return new_gift_list

@router.get("/giftlists/{gift_list_id}", response_model=GiftListResponse, summary="Retrieve a gift list by ID")
async def get_gift_list(gift_list_id: int, session: AsyncSession = Depends(async_session_maker)):
    gift_list_dao = GiftListDAO(session)
    gift_list = await gift_list_dao.get_gift_list_by_id(gift_list_id)
    if not gift_list:
        raise HTTPException(status_code=404, detail="Gift list not found")
    return gift_list

@router.put("/giftlists/{gift_list_id}", response_model=GiftListResponse, summary="Update a gift list by ID")
async def update_gift_list(gift_list_id: int, gift_list: GiftListUpdate, session: AsyncSession = Depends(async_session_maker)):
    gift_list_dao = GiftListDAO(session)
    updated_gift_list = await gift_list_dao.update_gift_list(gift_list_id, gift_list.dict())
    if not updated_gift_list:
        raise HTTPException(status_code=404, detail="Gift list not found")
    return updated_gift_list

@router.delete("/giftlists/{gift_list_id}", response_model=DeleteResponse, summary="Delete a gift list by ID")
async def delete_gift_list(gift_list_id: int, session: AsyncSession = Depends(async_session_maker)):
    gift_list_dao = GiftListDAO(session)
    success = await gift_list_dao.delete_gift_list(gift_list_id)
    if not success:
        raise HTTPException(status_code=404, detail="Gift list not found")
    return DeleteResponse(status="success")


# User Lists Endpoints

@router.post("/userlists", response_model=UserListResponse, summary="Add a user to a user list")
async def add_user_to_list(user_list: UserListCreate, session: AsyncSession = Depends(async_session_maker)):
    user_list_dao = UserListDAO(session)
    new_user_list = await user_list_dao.add_user_to_list(user_list.dict())
    if not new_user_list:
        raise HTTPException(status_code=400, detail="Failed to add user to list")
    return new_user_list

@router.get("/userlists/{user_list_id}", response_model=UserListResponse, summary="Retrieve a user list by ID")
async def get_user_list(user_list_id: int, session: AsyncSession = Depends(async_session_maker)):
    user_list_dao = UserListDAO(session)
    user_list = await user_list_dao.get_user_list_by_id(user_list_id)
    if not user_list:
        raise HTTPException(status_code=404, detail="User list not found")
    return user_list

@router.put("/userlists/{user_list_id}", response_model=UserListResponse, summary="Update a user list by ID")
async def update_user_list(user_list_id: int, user_list: UserListUpdate, session: AsyncSession = Depends(async_session_maker)):
    user_list_dao = UserListDAO(session)
    updated_user_list = await user_list_dao.update_user_list(user_list_id, user_list.dict())
    if not updated_user_list:
        raise HTTPException(status_code=404, detail="User list not found")
    return updated_user_list

@router.delete("/userlists/{user_list_id}", response_model=DeleteResponse, summary="Remove a user from a user list")
async def remove_user_from_list(user_list_id: int, session: AsyncSession = Depends(async_session_maker)):
    user_list_dao = UserListDAO(session)
    success = await user_list_dao.remove_user_from_list(user_list_id)
    if not success:
        raise HTTPException(status_code=404, detail="User list not found")
    return DeleteResponse(status="success")
