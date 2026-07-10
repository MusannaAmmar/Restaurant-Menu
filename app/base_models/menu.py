from pydantic import BaseModel
from typing import List, Optional


class VariantSchema(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None


class ModifierOptionSchema(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None


class ModifierSchema(BaseModel):
    name: Optional[str] = None
    options: Optional[List[ModifierOptionSchema]] = None


class MenuItemSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    ingredients: Optional[List[str]] = None
    variants: Optional[List[VariantSchema]] = None
    modifiers: Optional[List[ModifierSchema]] = None
    images: Optional[List[str]] = None


class MenuListSchema(BaseModel):
    title: Optional[str] = None
    items: Optional[List[MenuItemSchema]] = None

class MenuSchema(BaseModel):
    title: Optional[str] = None
    currency: Optional[str] = None
    sections: Optional[List[MenuListSchema]] = None

class MenusSchema(BaseModel):
    menus: Optional[List[MenuSchema]] = None