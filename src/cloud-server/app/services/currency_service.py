from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import json

logger = logging.getLogger(__name__)


class CurrencyCode(Enum):
    """TR: Desteklenen para birimleri"""

    TRY = "TRY"  # Turkish Lira
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    CAD = "CAD"  # Canadian Dollar
    AUD = "AUD"  # Australian Dollar
    JPY = "JPY"  # Japanese Yen
    CHF = "CHF"  # Swiss Franc
    SEK = "SEK"  # Swedish Krona
    NOK = "NOK"  # Norwegian Krone
    DKK = "DKK"  # Danish Krone
    BRL = "BRL"  # Brazilian Real
    MXN = "MXN"  # Mexican Peso
    CNY = "CNY"  # Chinese Yuan
    INR = "INR"  # Indian Rupee
    KRW = "KRW"  # South Korean Won
    SGD = "SGD"  # Singapore Dollar
    THB = "THB"  # Thai Baht


class CurrencyService:
    """TR: Para birimi desteği ve currency conversion servisi"""

    def __init__(self):
        self._currency_configs = {}
        self._exchange_rates = {}
        self._last_rate_update = None
        self._load_currency_configurations()
        self._load_default_exchange_rates()

    def _load_currency_configurations(self) -> None:
        """TR: Para birimi yapılandırmalarını yükle"""
        try:
            self._currency_configs = {
                CurrencyCode.TRY.value: {
                    "name": "Turkish Lira",
                    "symbol": "₺",
                    "symbol_position": "suffix",  # prefix veya suffix
                    "decimal_places": 2,
                    "decimal_separator": ",",
                    "thousands_separator": ".",
                    "regions": ["TR"],
                    "format_template": "{amount}{symbol}",
                },
                CurrencyCode.USD.value: {
                    "name": "US Dollar",
                    "symbol": "$",
                    "symbol_position": "prefix",
                    "decimal_places": 2,
                    "decimal_separator": ".",
                    "thousands_separator": ",",
                    "regions": ["US", "CA"],
                    "format_template": "{symbol}{amount}",
                },
                CurrencyCode.EUR.value: {
                    "name": "Euro",
                    "symbol": "€",
                    "symbol_position": "suffix",
                    "decimal_places": 2,
                    "decimal_separator": ",",
                    "thousands_separator": ".",
                    "regions": ["EU", "DE", "FR", "IT", "ES", "NL", "AT", "BE"],
                    "format_template": "{amount} {symbol}",
                },
                CurrencyCode.GBP.value: {
                    "name": "British Pound",
                    "symbol": "£",
                    "symbol_position": "prefix",
                    "decimal_places": 2,
                    "decimal_separator": ".",
                    "thousands_separator": ",",
                    "regions": ["GB", "UK"],
                    "format_template": "{symbol}{amount}",
                },
                CurrencyCode.CAD.value: {
                    "name": "Canadian Dollar",
                    "symbol": "C$",
                    "symbol_position": "prefix",
                    "decimal_places": 2,
                    "decimal_separator": ".",
                    "thousands_separator": ",",
                    "regions": ["CA"],
                    "format_template": "{symbol}{amount}",
                },
                CurrencyCode.JPY.value: {
                    "name": "Japanese Yen",
                    "symbol": "¥",
                    "symbol_position": "prefix",
                    "decimal_places": 0,  # TR: Yen ondalık kullanmaz
                    "decimal_separator": "",
                    "thousands_separator": ",",
                    "regions": ["JP"],
                    "format_template": "{symbol}{amount}",
                },
                CurrencyCode.BRL.value: {
                    "name": "Brazilian Real",
                    "symbol": "R$",
                    "symbol_position": "prefix",
                    "decimal_places": 2,
                    "decimal_separator": ",",
                    "thousands_separator": ".",
                    "regions": ["BR"],
                    "format_template": "{symbol} {amount}",
                },
                CurrencyCode.CNY.value: {
                    "name": "Chinese Yuan",
                    "symbol": "¥",
                    "symbol_position": "prefix",
                    "decimal_places": 2,
                    "decimal_separator": ".",
                    "thousands_separator": ",",
                    "regions": ["CN"],
                    "format_template": "{symbol}{amount}",
                },
                CurrencyCode.SGD.value: {
                    "name": "Singapore Dollar",
                    "symbol": "S$",
                    "symbol_position": "prefix",
                    "decimal_places": 2,
                    "decimal_separator": ".",
                    "thousands_separator": ",",
                    "regions": ["SG"],
                    "format_template": "{symbol}{amount}",
                },
            }

            logger.info(
                f"TR: {len(self._currency_configs)} para birimi yapılandırması yüklendi"
            )

        except Exception as e:
            logger.error(f"TR: Currency configuration yükleme hatası: {e}")
            self._currency_configs = {}

    def _load_default_exchange_rates(self) -> None:
        """TR: Varsayılan döviz kurlarını yükle (gerçek implementasyon external API kullanmalı)"""
        try:
            # TR: Varsayılan kurlar - Production'da external API'den alınmalı
            self._exchange_rates = {
                CurrencyCode.USD.value: {
                    CurrencyCode.TRY.value: 34.25,
                    CurrencyCode.EUR.value: 0.85,
                    CurrencyCode.GBP.value: 0.73,
                    CurrencyCode.CAD.value: 1.25,
                    CurrencyCode.JPY.value: 110.0,
                    CurrencyCode.BRL.value: 5.20,
                    CurrencyCode.CNY.value: 6.45,
                    CurrencyCode.SGD.value: 1.35,
                },
                CurrencyCode.EUR.value: {
                    CurrencyCode.USD.value: 1.18,
                    CurrencyCode.TRY.value: 40.30,
                    CurrencyCode.GBP.value: 0.86,
                    CurrencyCode.JPY.value: 130.0,
                },
                CurrencyCode.TRY.value: {
                    CurrencyCode.USD.value: 0.029,
                    CurrencyCode.EUR.value: 0.025,
                    CurrencyCode.GBP.value: 0.021,
                },
            }

            self._last_rate_update = datetime.utcnow()
            logger.info("TR: Varsayılan döviz kurları yüklendi")

        except Exception as e:
            logger.error(f"TR: Exchange rate yükleme hatası: {e}")
            self._exchange_rates = {}

    def format_currency(
        self,
        amount: Union[float, Decimal],
        currency_code: str,
        region: Optional[str] = None,
    ) -> str:
        """TR: Para birimini bölgesel formata göre formatla"""
        try:
            config = self._currency_configs.get(currency_code.upper())
            if not config:
                logger.warning(f"TR: Bilinmeyen para birimi: {currency_code}")
                return f"{amount} {currency_code}"

            # TR: Decimal precision
            decimal_places = config.get("decimal_places", 2)
            if decimal_places > 0:
                amount_decimal = Decimal(str(amount)).quantize(
                    Decimal('0.' + '0' * decimal_places), rounding=ROUND_HALF_UP
                )
            else:
                amount_decimal = Decimal(str(amount)).quantize(
                    Decimal('1'), rounding=ROUND_HALF_UP
                )

            # TR: Thousands separator ve decimal separator
            decimal_separator = config.get("decimal_separator", ".")
            thousands_separator = config.get("thousands_separator", ",")

            # TR: Format amount
            if decimal_places > 0:
                amount_str = f"{amount_decimal:,.{decimal_places}f}"
                # TR: Separatorları değiştir
                amount_str = amount_str.replace(",", "TEMP_THOUSANDS")
                amount_str = amount_str.replace(".", decimal_separator)
                amount_str = amount_str.replace("TEMP_THOUSANDS", thousands_separator)
            else:
                amount_str = f"{int(amount_decimal):,}".replace(
                    ",", thousands_separator
                )

            # TR: Symbol pozisyonu
            symbol = config.get("symbol", currency_code)
            format_template = config.get("format_template", "{symbol}{amount}")

            return format_template.format(amount=amount_str, symbol=symbol)

        except Exception as e:
            logger.error(f"TR: Currency formatting hatası: {e}")
            return f"{amount} {currency_code}"

    def convert_currency(
        self, amount: Union[float, Decimal], from_currency: str, to_currency: str
    ) -> Optional[Decimal]:
        """TR: Para birimi çevirisi yap"""
        try:
            from_currency = from_currency.upper()
            to_currency = to_currency.upper()

            if from_currency == to_currency:
                return Decimal(str(amount))

            # TR: Direct conversion rate
            if from_currency in self._exchange_rates:
                if to_currency in self._exchange_rates[from_currency]:
                    rate = self._exchange_rates[from_currency][to_currency]
                    return Decimal(str(amount)) * Decimal(str(rate))

            # TR: USD üzerinden çeviri (triangular conversion)
            if from_currency != "USD" and to_currency != "USD":
                # TR: from_currency -> USD -> to_currency
                usd_amount = self.convert_currency(amount, from_currency, "USD")
                if usd_amount is not None:
                    return self.convert_currency(usd_amount, "USD", to_currency)

            logger.warning(
                f"TR: {from_currency} -> {to_currency} dönüşümü için kur bulunamadı"
            )
            return None

        except Exception as e:
            logger.error(f"TR: Currency conversion hatası: {e}")
            return None

    def get_supported_currencies(
        self, region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """TR: Desteklenen para birimlerini listele"""
        currencies = []

        for currency_code, config in self._currency_configs.items():
            if region is None or region.upper() in config.get("regions", []):
                currencies.append(
                    {
                        "code": currency_code,
                        "name": config.get("name"),
                        "symbol": config.get("symbol"),
                        "regions": config.get("regions", []),
                    }
                )

        return currencies

    def get_currency_info(self, currency_code: str) -> Dict[str, Any]:
        """TR: Para birimi detaylarını getir"""
        config = self._currency_configs.get(currency_code.upper(), {})
        if not config:
            return {"error": f"Unsupported currency: {currency_code}"}

        return {
            "code": currency_code.upper(),
            "name": config.get("name"),
            "symbol": config.get("symbol"),
            "decimal_places": config.get("decimal_places"),
            "regions": config.get("regions", []),
            "format_example": self.format_currency(1234.56, currency_code),
        }

    def calculate_subscription_price(
        self,
        base_usd_price: Union[float, Decimal],
        target_currency: str,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """TR: Subscription fiyatını hedef para birimine çevir"""
        try:
            converted_amount = self.convert_currency(
                base_usd_price, "USD", target_currency
            )
            if converted_amount is None:
                return {
                    "error": f"Conversion not available for {target_currency}",
                    "base_usd_price": float(base_usd_price),
                }

            formatted_price = self.format_currency(
                converted_amount, target_currency, region
            )

            return {
                "base_usd_price": float(base_usd_price),
                "converted_amount": float(converted_amount),
                "currency": target_currency.upper(),
                "formatted_price": formatted_price,
                "exchange_rate": float(converted_amount) / float(base_usd_price),
                "last_updated": (
                    self._last_rate_update.isoformat()
                    if self._last_rate_update
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"TR: Subscription price calculation hatası: {e}")
            return {"error": str(e), "base_usd_price": float(base_usd_price)}

    async def update_exchange_rates(
        self, external_api_data: Optional[Dict[str, Dict[str, float]]] = None
    ) -> bool:
        """TR: Döviz kurlarını güncelle (external API integration)"""
        try:
            if external_api_data:
                # TR: External API'den gelen kurları güncelle
                for base_currency, rates in external_api_data.items():
                    if base_currency not in self._exchange_rates:
                        self._exchange_rates[base_currency] = {}

                    for target_currency, rate in rates.items():
                        self._exchange_rates[base_currency][target_currency] = rate

                self._last_rate_update = datetime.utcnow()
                logger.info("TR: Exchange rates external API'den güncellendi")
                return True
            else:
                # TR: Varsayılan kurları yeniden yükle
                self._load_default_exchange_rates()
                logger.info("TR: Exchange rates varsayılan değerlerle güncellendi")
                return True

        except Exception as e:
            logger.error(f"TR: Exchange rate güncelleme hatası: {e}")
            return False

    def get_exchange_rate_info(self) -> Dict[str, Any]:
        """TR: Döviz kuru bilgilerini getir"""
        return {
            "last_updated": (
                self._last_rate_update.isoformat() if self._last_rate_update else None
            ),
            "available_conversions": list(self._exchange_rates.keys()),
            "total_rates": sum(len(rates) for rates in self._exchange_rates.values()),
        }

    def validate_currency_for_region(
        self, currency_code: str, region: str
    ) -> Dict[str, Any]:
        """TR: Para biriminin bölge için uygunluğunu kontrol et"""
        config = self._currency_configs.get(currency_code.upper())
        if not config:
            return {
                "valid": False,
                "reason": "Unsupported currency",
                "supported_currencies": self.get_supported_currencies(region),
            }

        supported_regions = config.get("regions", [])
        is_valid = region.upper() in supported_regions

        return {
            "valid": is_valid,
            "currency": currency_code.upper(),
            "region": region.upper(),
            "supported_regions": supported_regions,
            "recommendations": (
                self.get_supported_currencies(region) if not is_valid else []
            ),
        }


# TR: Global instance
currency_service = CurrencyService()
