from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class PriceDisclosure(str, Enum):
    public = "public"
    contact = "contact"


class OdometerDisclosure(str, Enum):
    verified = "verified"
    not_verified = "not_verified"
    hidden = "hidden"


class UsedMotorcycleListing(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    model_year: str = Field(min_length=1, max_length=40)
    odometer_km: int | None = Field(default=None, ge=0, le=2_000_000)
    odometer_disclosure: OdometerDisclosure = OdometerDisclosure.not_verified
    license_plate: str = Field(default="", max_length=30)
    mask_license_plate: bool = True
    price: int | None = Field(default=None, ge=0)
    price_disclosure: PriceDisclosure = PriceDisclosure.contact
    condition: str = Field(min_length=1, max_length=1000)
    highlights: list[str] = Field(min_length=1, max_length=10)
    legal_documents: str = Field(
        default="Hồ sơ pháp lý đầy đủ, hỗ trợ sang tên",
        min_length=1,
        max_length=500,
    )
    notes: str = Field(default="", max_length=1000)
    store_name: str = Field(default="Minh Dũng", min_length=1, max_length=120)
    phone: str = Field(default="0902 143 241", min_length=1, max_length=40)
    address: str = Field(
        default="08 Quang Trung, TP. Quảng Ngãi",
        min_length=1,
        max_length=300,
    )

    @model_validator(mode="before")
    @classmethod
    def trim_sales_facts(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        cleaned = data.copy()
        for field_name in (
            "name",
            "model_year",
            "condition",
            "legal_documents",
            "store_name",
            "phone",
            "address",
        ):
            value = cleaned.get(field_name)
            if isinstance(value, str):
                cleaned[field_name] = value.strip()

        highlights = cleaned.get("highlights")
        if isinstance(highlights, list):
            cleaned["highlights"] = [
                item.strip() if isinstance(item, str) else item
                for item in highlights
                if not isinstance(item, str) or item.strip()
            ]
        return cleaned

    @model_validator(mode="after")
    def validate_disclosures(self) -> "UsedMotorcycleListing":
        if self.price_disclosure == PriceDisclosure.public and self.price is None:
            raise ValueError("price is required when price disclosure is public")
        if (
            self.odometer_disclosure == OdometerDisclosure.verified
            and self.odometer_km is None
        ):
            raise ValueError("odometer is required when marked verified")
        return self
