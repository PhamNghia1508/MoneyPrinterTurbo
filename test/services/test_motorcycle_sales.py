import unittest

from pydantic import ValidationError

from app.models.motorcycle import (
    OdometerDisclosure,
    PriceDisclosure,
    UsedMotorcycleListing,
)


class TestUsedMotorcycleListing(unittest.TestCase):
    def test_requires_sales_facts(self):
        with self.assertRaises(ValidationError):
            UsedMotorcycleListing(
                name="SH 150i",
                model_year=" ",
                condition=" ",
                highlights=[],
            )

    def test_contact_price_does_not_require_numeric_price(self):
        listing = UsedMotorcycleListing(
            name="SH 150i",
            model_year="2012",
            condition="Máy êm, dàn áo còn đẹp",
            highlights=["Hồ sơ pháp lý đầy đủ"],
            price_disclosure=PriceDisclosure.contact,
            odometer_disclosure=OdometerDisclosure.not_verified,
        )

        self.assertIsNone(listing.price)
        self.assertEqual(listing.store_name, "Minh Dũng")
        self.assertEqual(listing.phone, "0902 143 241")
        self.assertEqual(listing.address, "08 Quang Trung, TP. Quảng Ngãi")
        self.assertEqual(
            listing.legal_documents,
            "Hồ sơ pháp lý đầy đủ, hỗ trợ sang tên",
        )

    def test_public_price_requires_price(self):
        with self.assertRaises(ValidationError):
            UsedMotorcycleListing(
                name="Vision",
                model_year="2020",
                condition="Vận hành ổn định",
                highlights=["Tiết kiệm xăng"],
                price_disclosure=PriceDisclosure.public,
            )

    def test_trims_core_strings_and_highlights(self):
        listing = UsedMotorcycleListing(
            name="  Air Blade  ",
            model_year="  2021  ",
            condition="  Máy êm  ",
            highlights=["  Ngoại hình gọn  ", "  Hồ sơ đầy đủ  "],
        )

        self.assertEqual(listing.name, "Air Blade")
        self.assertEqual(listing.model_year, "2021")
        self.assertEqual(listing.condition, "Máy êm")
        self.assertEqual(
            listing.highlights,
            ["Ngoại hình gọn", "Hồ sơ đầy đủ"],
        )

    def test_rejects_blank_only_highlights(self):
        with self.assertRaises(ValidationError):
            UsedMotorcycleListing(
                name="Vision",
                model_year="2020",
                condition="Vận hành ổn định",
                highlights=[" ", "\t"],
            )

    def test_verified_odometer_requires_value(self):
        with self.assertRaises(ValidationError):
            UsedMotorcycleListing(
                name="Vision",
                model_year="2020",
                condition="Vận hành ổn định",
                highlights=["Tiết kiệm xăng"],
                odometer_disclosure=OdometerDisclosure.verified,
            )


if __name__ == "__main__":
    unittest.main()
