from __future__ import annotations

from typing import TypeVar, Generic, List, Optional, Dict, Any
from dataclasses import dataclass
import math

try:
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql import Select
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

T = TypeVar('T')

@dataclass
class PaginatedResult(Generic[T]):
    """TR: Sayfalanmış sorgu sonucu"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

class PaginationHelper:
    """TR: Database pagination helper - N+1 query problemini önler"""
    
    @staticmethod
    async def paginate(
        session: AsyncSession,
        query: Select,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ) -> PaginatedResult:
        """TR: Efficient pagination implementation"""
        
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("SQLAlchemy is not available")
        
        # TR: Page size limiti
        page_size = min(page_size, max_page_size)
        page = max(1, page)  # TR: Minimum 1. sayfa
        
        # TR: Total count query (without LIMIT/OFFSET)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0
        
        # TR: Calculate pagination info
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        
        # TR: Items query with LIMIT/OFFSET
        items_query = query.offset(offset).limit(page_size)
        items_result = await session.execute(items_query)
        items = items_result.all()
        
        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
    
    @staticmethod
    def get_pagination_info(page: int, page_size: int, total: int) -> Dict[str, Any]:
        """TR: Pagination metadata"""
        page = max(1, page)
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
            "offset": (page - 1) * page_size
        }