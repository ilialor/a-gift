import logging
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter(prefix="/twa", tags=["twa"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def index(request: Request):
    """Main TWA page"""
    return templates.TemplateResponse("pages/index.html", {"request": request})

@router.get("/wishlist")
async def wishlist(request: Request):
    """User's wishlist page"""
    return templates.TemplateResponse("pages/wishlist.html", {
        "request": request,
        "page_title": "My Wishlist"
    })

@router.get("/gifts")
async def gifts(request: Request):
    """Gift ideas page"""
    return templates.TemplateResponse("pages/gifts.html", {
        "request": request,
        "page_title": "Gift Ideas"
    })

@router.get("/groups")
async def groups(request: Request):
    """User's groups page"""
    return templates.TemplateResponse("pages/groups.html", {
        "request": request,
        "page_title": "Groups"
    })

@router.get("/contacts")
async def contacts(request: Request):
    """User's contacts page"""
    return templates.TemplateResponse("pages/contacts.html", {
        "request": request,
        "page_title": "My Contacts"
    })

@router.get("/publish")
async def publish(request: Request):
    """Publishing page"""
    return templates.TemplateResponse("pages/publish.html", {
        "request": request,
        "page_title": "To Publish"
    })
