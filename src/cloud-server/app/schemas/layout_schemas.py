"""
Layout Generation Schemas for ArchBuilder.AI

Pydantic models for layout generation requests, responses, and validation.
Ensures type safety and API documentation.

Author: ArchBuilder.AI Team
Date: 2025-09-26
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict, validator


class ClimateZone(str, Enum):
    """İklim bölgeleri - Türkiye bazlı"""
    MEDITERRANEAN = "akdeniz"
    BLACK_SEA = "karadeniz"  
    AEGEAN = "ege"
    MARMARA = "marmara"
    CENTRAL_ANATOLIA = "ic_anadolu"
    EASTERN_ANATOLIA = "dogu_anadolu"
    SOUTHEASTERN_ANATOLIA = "guneydogu_anadolu"


class ArchitecturalStyle(str, Enum):
    """Mimari stil seçenekleri"""
    MODERN = "modern"
    TRADITIONAL = "geleneksel"
    CONTEMPORARY = "çağdaş"
    MINIMALIST = "minimalist"
    CLASSICAL = "klasik"
    TURKISH_TRADITIONAL = "türk_geleneksel"


class RoomType(str, Enum):
    """Oda tipleri ve fonksiyonları"""
    LIVING_ROOM = "salon"
    BEDROOM = "yatak_odasi"
    KITCHEN = "mutfak"
    BATHROOM = "banyo"
    WC = "wc"
    DINING_ROOM = "yemek_odasi"
    OFFICE = "ofis"
    BALCONY = "balkon"
    TERRACE = "teras"
    STORAGE = "depo"
    ENTRANCE = "giris"
    CORRIDOR = "koridor"
    LAUNDRY = "çamaşırhane"


class ValidationStatus(str, Enum):
    """Validation sonuç durumları"""
    VALID = "geçerli"
    REQUIRES_REVIEW = "inceleme_gerekli"
    REJECTED = "reddedildi"
    WARNING = "uyarı"


class Room(BaseModel):
    """Oda gereksinimi tanımı"""
    name: str = Field(..., description="Oda adı")
    type: RoomType = Field(..., description="Oda tipi")
    area: float = Field(..., ge=5.0, description="Oda alanı (m²), minimum 5m²")
    min_width: Optional[float] = Field(2.0, ge=1.0, description="Minimum genişlik (m)")
    min_height: Optional[float] = Field(2.4, ge=2.2, description="Minimum tavan yüksekliği (m)")
    natural_light_required: bool = Field(True, description="Doğal ışık gereksinimi")
    ventilation_required: bool = Field(True, description="Havalandırma gereksinimi")
    privacy_level: int = Field(1, ge=1, le=3, description="Mahremiyet seviyesi (1=açık, 3=özel)")
    adjacent_rooms: List[str] = Field(default_factory=list, description="Bitişik olması gereken odalar")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Ana Yatak Odası",
                "type": "yatak_odasi",
                "area": 16.0,
                "min_width": 3.0,
                "min_height": 2.7,
                "natural_light_required": True,
                "ventilation_required": True,
                "privacy_level": 3,
                "adjacent_rooms": ["banyo"]
            }
        }
    )


class RoomProgram(BaseModel):
    """Bina oda programı - tüm odalar ve gereksinimleri"""
    rooms: List[Room] = Field(..., min_length=1, description="Oda listesi")
    circulation_factor: float = Field(0.15, ge=0.1, le=0.3, description="Sirkülasyon faktörü (%)")
    
    @validator('rooms')
    def validate_room_names_unique(cls, v):
        names = [room.name for room in v]
        if len(names) != len(set(names)):
            raise ValueError("Oda isimleri tekil olmalıdır")
        return v
    
    @property 
    def total_room_area(self) -> float:
        """Toplam oda alanı (sirkülasyon hariç)"""
        return sum(room.area for room in self.rooms)
    
    @property
    def total_with_circulation(self) -> float:
        """Sirkülasyon dahil toplam alan"""
        return self.total_room_area * (1 + self.circulation_factor)


class BuildingRequirements(BaseModel):
    """Bina gereksinimleri ve kısıtlamaları"""
    total_area: float = Field(..., ge=20.0, description="Toplam bina alanı (m²)")
    floor_count: int = Field(1, ge=1, le=4, description="Kat sayısı")
    style: ArchitecturalStyle = Field(..., description="Mimari stil")
    climate_zone: ClimateZone = Field(..., description="İklim bölgesi")
    plot_width: Optional[float] = Field(None, ge=5.0, description="Parsel genişliği (m)")
    plot_depth: Optional[float] = Field(None, ge=5.0, description="Parsel derinliği (m)")
    setback_front: float = Field(5.0, ge=3.0, description="Ön bahçe mesafesi (m)")
    setback_rear: float = Field(3.0, ge=2.0, description="Arka bahçe mesafesi (m)")  
    setback_side: float = Field(3.0, ge=1.5, description="Yan bahçe mesafesi (m)")
    max_height: float = Field(9.5, ge=7.0, description="Maksimum bina yüksekliği (m)")
    constraints: List[str] = Field(default_factory=list, description="Ek tasarım kısıtlamaları")
    accessibility_required: bool = Field(True, description="Engelli erişim gereksinimi")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_area": 120.0,
                "floor_count": 2,
                "style": "modern",
                "climate_zone": "marmara",
                "plot_width": 12.0,
                "plot_depth": 15.0,
                "setback_front": 5.0,
                "setback_rear": 3.0,
                "setback_side": 3.0,
                "max_height": 9.5,
                "constraints": [
                    "Güney cephe maksimum cam yüzey",
                    "Giriş kapısı doğu cephede"
                ],
                "accessibility_required": True
            }
        }
    )


class LayoutGenerationRequest(BaseModel):
    """Layout generation talebi"""
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="Talep ID")
    room_program: RoomProgram = Field(..., description="Oda programı")
    building_requirements: BuildingRequirements = Field(..., description="Bina gereksinimleri")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="Kullanıcı tercihleri")
    reference_layouts: List[str] = Field(default_factory=list, description="Referans layout ID'leri")
    priority: int = Field(1, ge=1, le=3, description="İşlem önceliği (1=yüksek, 3=düşük)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "room_program": {
                    "rooms": [
                        {
                            "name": "Salon", 
                            "type": "salon",
                            "area": 25.0,
                            "natural_light_required": True
                        },
                        {
                            "name": "Mutfak",
                            "type": "mutfak", 
                            "area": 12.0,
                            "adjacent_rooms": ["salon"]
                        }
                    ],
                    "circulation_factor": 0.15
                },
                "building_requirements": {
                    "total_area": 85.0,
                    "floor_count": 1,
                    "style": "modern",
                    "climate_zone": "marmara"
                }
            }
        }
    )


class Point2D(BaseModel):
    """2D koordinat noktası"""
    x: float = Field(..., description="X koordinatı (mm)")
    y: float = Field(..., description="Y koordinatı (mm)")


class WallElement(BaseModel):
    """Duvar elementi tanımı"""
    start: Point2D = Field(..., description="Başlangıç noktası")
    end: Point2D = Field(..., description="Bitiş noktası") 
    type: str = Field(..., description="Duvar tipi (exterior/interior)")
    height: float = Field(2700, ge=2200, description="Duvar yüksekliği (mm)")
    thickness: float = Field(200, ge=100, description="Duvar kalınlığı (mm)")
    material: Optional[str] = Field("tuğla", description="Duvar malzemesi")


class DoorElement(BaseModel):
    """Kapı elementi tanımı"""
    wall_index: int = Field(..., ge=0, description="Duvar indeksi")
    position: float = Field(..., ge=0, description="Duvar üzerindeki pozisyon (mm)")
    width: float = Field(..., ge=700, le=1200, description="Kapı genişliği (mm)")
    height: float = Field(2000, ge=1900, description="Kapı yüksekliği (mm)")
    type: str = Field("single", description="Kapı tipi (single/double/sliding)")
    swing: str = Field("right", description="Açılım yönü (left/right/sliding)")
    threshold_height: float = Field(0, ge=0, le=20, description="Eşik yüksekliği (mm)")


class WindowElement(BaseModel):
    """Pencere elementi tanımı"""
    wall_index: int = Field(..., ge=0, description="Duvar indeksi")
    position: float = Field(..., ge=0, description="Duvar üzerindeki pozisyon (mm)")
    width: float = Field(..., ge=600, le=3000, description="Pencere genişliği (mm)")
    height: float = Field(..., ge=600, le=2000, description="Pencere yüksekliği (mm)")
    sill_height: float = Field(900, ge=300, description="Pencere eşiği yüksekliği (mm)")
    type: str = Field("casement", description="Pencere tipi")
    opening_type: str = Field("inward", description="Açılım tipi")


class RoomBoundary(BaseModel):
    """Oda sınır tanımı"""
    name: str = Field(..., description="Oda adı")
    area: float = Field(..., ge=5.0, description="Gerçekleşen alan (m²)")
    boundaries: List[int] = Field(..., description="Sınır duvar indeksleri")
    center_point: Optional[Point2D] = Field(None, description="Oda merkez noktası")


class LayoutData(BaseModel):
    """Generated layout data structure"""
    walls: List[WallElement] = Field(..., description="Duvar listesi")
    doors: List[DoorElement] = Field(..., description="Kapı listesi")
    windows: List[WindowElement] = Field(..., description="Pencere listesi")
    rooms: List[RoomBoundary] = Field(..., description="Oda sınırları")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI güven skoru")
    compliance_notes: str = Field("", description="Uyumluluk notları")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "walls": [
                    {
                        "start": {"x": 0, "y": 0},
                        "end": {"x": 5000, "y": 0},
                        "type": "exterior",
                        "height": 2700
                    }
                ],
                "doors": [
                    {
                        "wall_index": 0,
                        "position": 2500,
                        "width": 900,
                        "type": "single",
                        "swing": "right"
                    }
                ],
                "confidence": 0.92
            }
        }
    )


class ValidationError(BaseModel):
    """Validation hatası tanımı"""
    code: str = Field(..., description="Hata kodu")
    message: str = Field(..., description="Hata mesajı")
    severity: str = Field(..., description="Önem derecesi (error/warning)")
    location: Optional[str] = Field(None, description="Hata konumu")
    suggestion: Optional[str] = Field(None, description="Çözüm önerisi")


class ValidationResult(BaseModel):
    """Layout validation sonucu"""
    status: ValidationStatus = Field(..., description="Validation durumu")
    errors: List[ValidationError] = Field(default_factory=list, description="Hatalar")
    warnings: List[ValidationError] = Field(default_factory=list, description="Uyarılar")  
    confidence: float = Field(..., ge=0.0, le=1.0, description="Genel güven skoru")
    requires_human_review: bool = Field(..., description="İnsan incelemesi gerekli mi")
    compliance_score: float = Field(..., ge=0.0, le=1.0, description="Uyumluluk skoru")
    validated_at: datetime = Field(default_factory=datetime.utcnow, description="Validation zamanı")


class LayoutStatus(str, Enum):
    """Layout işlem durumları"""
    PROCESSING = "işleniyor"
    GENERATED = "oluşturuldu"
    VALIDATING = "doğrulanıyor"  
    REQUIRES_REVIEW = "inceleme_gerekli"
    APPROVED = "onaylandı"
    REJECTED = "reddedildi"
    FAILED = "başarısız"


class LayoutResult(BaseModel):
    """Layout generation sonucu"""
    layout_id: str = Field(..., description="Layout ID")
    status: LayoutStatus = Field(..., description="İşlem durumu")
    layout_data: Optional[LayoutData] = Field(None, description="Oluşturulan layout")
    validation_result: Optional[ValidationResult] = Field(None, description="Validation sonucu")
    generated_at: datetime = Field(..., description="Oluşturma zamanı")
    model_used: Dict[str, str] = Field(..., description="Kullanılan AI model")
    correlation_id: str = Field(..., description="Korelasyon ID")
    review_id: Optional[str] = Field(None, description="İnceleme ID")
    is_fallback: bool = Field(False, description="Fallback generation mi")
    processing_time_ms: Optional[int] = Field(None, description="İşlem süresi (ms)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "layout_id": "layout_123e4567-e89b-12d3-a456-426614174000",
                "status": "inceleme_gerekli",
                "generated_at": "2025-09-26T10:30:00Z",
                "model_used": {
                    "provider": "openai",
                    "model": "gpt-4.1"
                },
                "correlation_id": "req_789",
                "is_fallback": False
            }
        }
    )


class ReviewFeedback(BaseModel):
    """İnsan review feedback"""
    review_id: str = Field(..., description="Review ID")
    approved: bool = Field(..., description="Onaylandı mı")
    corrections: List[Dict[str, Any]] = Field(default_factory=list, description="Düzeltmeler")
    notes: str = Field("", description="Mimar notları")
    reviewer_id: str = Field(..., description="İnceleyen kullanıcı ID")
    reviewed_at: datetime = Field(default_factory=datetime.utcnow, description="İnceleme zamanı")


class ReviewItem(BaseModel):
    """İnceleme kuyruğu öğesi"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Review item ID")
    layout_result: LayoutResult = Field(..., description="Layout sonucu")
    validation_result: ValidationResult = Field(..., description="Validation sonucu")
    status: str = Field("pending", description="Review durumu")
    priority: int = Field(1, ge=1, le=3, description="Öncelik")
    assigned_to: Optional[str] = Field(None, description="Atanan mimar")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Oluşturma zamanı")
    completed_at: Optional[datetime] = Field(None, description="Tamamlanma zamanı")
    feedback: Optional[ReviewFeedback] = Field(None, description="Review sonucu")