"""
Database Schemas for Mobile Legend Account Store

Each Pydantic model maps to a MongoDB collection (lowercased class name).
- Account -> "account"
- Order -> "order"
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class Account(BaseModel):
    """
    Mobile Legend accounts being sold
    Collection: account
    """
    title: str = Field(..., description="Nama/judul akun")
    description: Optional[str] = Field(None, description="Deskripsi singkat")
    rank: str = Field(..., description="Rank saat ini, contoh: Epic, Legend, Mythic")
    price: float = Field(..., ge=0, description="Harga dalam IDR")
    hero_count: Optional[int] = Field(None, ge=0, description="Jumlah hero")
    skin_count: Optional[int] = Field(None, ge=0, description="Jumlah skin")
    login_method: Optional[str] = Field(None, description="Metode login: Moonton, VK, Google, Facebook")
    email_access: Optional[bool] = Field(False, description="Include akses email?")
    images: Optional[List[str]] = Field(default_factory=list, description="URL gambar akun")
    is_available: bool = Field(True, description="Apakah masih tersedia")

class Order(BaseModel):
    """
    Customer orders to purchase accounts
    Collection: order
    """
    account_id: str = Field(..., description="ID akun yang dibeli")
    buyer_name: str = Field(..., description="Nama pembeli")
    whatsapp: str = Field(..., description="Nomor WhatsApp untuk dihubungi")
    note: Optional[str] = Field(None, description="Catatan tambahan")
    status: str = Field("pending", description="Status order: pending, processed, completed, cancelled")
