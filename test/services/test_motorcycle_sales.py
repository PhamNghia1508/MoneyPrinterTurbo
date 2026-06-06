import unittest

from pydantic import ValidationError

from app.models.motorcycle import (
    OdometerDisclosure,
    PriceDisclosure,
    UsedMotorcycleListing,
)
from app.services import motorcycle_sales


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

    def test_public_price_accepts_valid_price(self):
        listing = UsedMotorcycleListing(
            name="Vision",
            model_year="2020",
            condition="Vận hành ổn định",
            highlights=["Tiết kiệm xăng"],
            price=35_000_000,
            price_disclosure=PriceDisclosure.public,
        )

        self.assertEqual(listing.price, 35_000_000)

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

    def test_verified_odometer_accepts_valid_value(self):
        listing = UsedMotorcycleListing(
            name="Vision",
            model_year="2020",
            condition="Vận hành ổn định",
            highlights=["Tiết kiệm xăng"],
            odometer_km=25_000,
            odometer_disclosure=OdometerDisclosure.verified,
        )

        self.assertEqual(listing.odometer_km, 25_000)

    def test_trims_contact_details_and_legal_documents(self):
        listing = UsedMotorcycleListing(
            name="Vision",
            model_year="2020",
            condition="Vận hành ổn định",
            highlights=["Tiết kiệm xăng"],
            legal_documents="  Hồ sơ đầy đủ  ",
            store_name="  Minh Dũng  ",
            phone="  0902 143 241  ",
            address="  08 Quang Trung  ",
        )

        self.assertEqual(listing.legal_documents, "Hồ sơ đầy đủ")
        self.assertEqual(listing.store_name, "Minh Dũng")
        self.assertEqual(listing.phone, "0902 143 241")
        self.assertEqual(listing.address, "08 Quang Trung")

    def test_rejects_blank_contact_details_and_legal_documents(self):
        for field_name in ("legal_documents", "store_name", "phone", "address"):
            with self.subTest(field_name=field_name):
                with self.assertRaises(ValidationError):
                    UsedMotorcycleListing(
                        name="Vision",
                        model_year="2020",
                        condition="Vận hành ổn định",
                        highlights=["Tiết kiệm xăng"],
                        **{field_name: "   "},
                    )


class TestMotorcycleSalesPrompt(unittest.TestCase):
    def setUp(self):
        self.listing = UsedMotorcycleListing(
            name="SH 150i nhập Ý",
            model_year="2012",
            odometer_disclosure=OdometerDisclosure.not_verified,
            license_plate="76-B1 123.45",
            price=68_000_000,
            price_disclosure=PriceDisclosure.public,
            condition="Máy vận hành êm, dàn áo còn đẹp theo hiện trạng",
            highlights=["Hồ sơ pháp lý đầy đủ", "Hỗ trợ sang tên"],
        )

    def test_constants_and_vnd_format_match_sales_requirements(self):
        self.assertEqual(motorcycle_sales.STORE_NAME, "Minh Dũng")
        self.assertEqual(motorcycle_sales.STORE_PHONE, "0902 143 241")
        self.assertEqual(
            motorcycle_sales.STORE_ADDRESS,
            "08 Quang Trung, TP. Quảng Ngãi",
        )
        self.assertEqual(motorcycle_sales.TARGET_MIN_WORDS, 90)
        self.assertEqual(motorcycle_sales.TARGET_MAX_WORDS, 120)
        self.assertEqual(motorcycle_sales.format_vnd(68_000_000), "68.000.000 đồng")

    def test_system_prompt_sets_truthful_vietnamese_script_contract(self):
        prompt = motorcycle_sales.MOTORCYCLE_SALES_SYSTEM_PROMPT

        for requirement in (
            "chỉ văn bản thô tiếng Việt",
            "một câu",
            "1-3 giây",
            "90-120 từ",
            "35-45 giây",
            "hài hước vừa phải",
            "không la hét liên tục",
            "chỉ dùng sự thật",
            "không tạo khan hiếm giả",
            "pháp lý",
            "giá công khai",
            "giá liên hệ",
            "tên cửa hàng",
            "số điện thoại",
            "địa chỉ",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, prompt)

    def test_prompt_contains_listing_facts_public_price_and_contact(self):
        prompt = motorcycle_sales.build_sales_script_prompt(self.listing)

        for value in (
            "SH 150i nhập Ý",
            "2012",
            "Máy vận hành êm, dàn áo còn đẹp theo hiện trạng",
            "Hồ sơ pháp lý đầy đủ",
            "Hỗ trợ sang tên",
            "68.000.000 đồng",
            "Minh Dũng",
            "0902 143 241",
            "08 Quang Trung, TP. Quảng Ngãi",
        ):
            with self.subTest(value=value):
                self.assertIn(value, prompt)

    def test_unverified_odometer_uses_exact_caution(self):
        prompt = motorcycle_sales.build_sales_script_prompt(self.listing)

        self.assertIn("ODO: chưa xác minh, không được khẳng định", prompt)
        self.assertNotIn("ODO chuẩn", prompt)

    def test_verified_odometer_renders_number(self):
        listing = self.listing.model_copy(
            update={
                "odometer_km": 25_000,
                "odometer_disclosure": OdometerDisclosure.verified,
            }
        )

        prompt = motorcycle_sales.build_sales_script_prompt(listing)

        self.assertIn("ODO đã xác nhận: 25.000 km", prompt)

    def test_hidden_odometer_instructs_script_not_to_mention_it(self):
        listing = self.listing.model_copy(
            update={"odometer_disclosure": OdometerDisclosure.hidden}
        )

        prompt = motorcycle_sales.build_sales_script_prompt(listing)

        self.assertIn("ODO: không công bố, không nhắc trong kịch bản", prompt)

    def test_contact_price_uses_exact_non_numeric_instruction(self):
        listing = self.listing.model_copy(
            update={"price": None, "price_disclosure": PriceDisclosure.contact}
        )

        prompt = motorcycle_sales.build_sales_script_prompt(listing)

        self.assertIn("không đọc một con số giá", prompt)
        self.assertIn("liên hệ để nhận giá", prompt)
        self.assertNotIn("68.000.000 đồng", prompt)

    def test_license_plate_is_masked_when_requested(self):
        prompt = motorcycle_sales.build_sales_script_prompt(self.listing)

        self.assertIn("Biển số: 76-B1 ***.**", prompt)
        self.assertNotIn("76-B1 123.45", prompt)

    def test_license_plate_is_omitted_when_blank(self):
        listing = self.listing.model_copy(update={"license_plate": " "})

        prompt = motorcycle_sales.build_sales_script_prompt(listing)

        self.assertNotIn("Biển số:", prompt)

    def test_license_plate_is_shown_when_masking_is_disabled(self):
        listing = self.listing.model_copy(update={"mask_license_plate": False})

        prompt = motorcycle_sales.build_sales_script_prompt(listing)

        self.assertIn("Biển số: 76-B1 123.45", prompt)

    def test_notes_are_labeled_as_confirmed_supplemental_information(self):
        listing = self.listing.model_copy(
            update={"notes": "Đã thay lốp trước tháng 5/2026"}
        )

        prompt = motorcycle_sales.build_sales_script_prompt(listing)

        self.assertIn(
            "Thông tin bổ sung đã xác nhận: Đã thay lốp trước tháng 5/2026",
            prompt,
        )

    def test_audit_flags_unsupported_claims_and_missing_cta(self):
        issues = motorcycle_sales.audit_sales_script(
            "Xe ZIN ĐÉT, ODO chuẩn, nhanh tay thì còn!",
            self.listing,
        )

        self.assertIn("unsupported_claim:zin đét", issues)
        self.assertIn("unsupported_claim:odo chuẩn", issues)
        self.assertIn("missing_phone", issues)
        self.assertIn("missing_address", issues)
        self.assertIn("missing_store_name", issues)
        self.assertIn("missing_legal_documents", issues)

    def test_audit_allows_claim_explicitly_confirmed_in_notes(self):
        listing = self.listing.model_copy(update={"notes": "Xe zin đét đã xác nhận"})
        script = self._valid_script(
            listing,
            extra="Xe zin đét theo thông tin bổ sung đã xác nhận.",
        )

        issues = motorcycle_sales.audit_sales_script(script, listing)

        self.assertNotIn("unsupported_claim:zin đét", issues)

    def test_audit_accepts_practical_valid_cta_and_legal_trust_point(self):
        script = self._valid_script(self.listing)

        self.assertEqual(
            motorcycle_sales.audit_sales_script(script, self.listing),
            [],
        )

    def test_audit_public_price_accepts_common_separator_formats(self):
        for rendered_price in ("68.000.000 đồng", "68,000,000đ", "68000000 VND"):
            with self.subTest(rendered_price=rendered_price):
                script = self._valid_script(
                    self.listing,
                    price_text=rendered_price,
                )

                issues = motorcycle_sales.audit_sales_script(script, self.listing)

                self.assertNotIn("missing_public_price", issues)

    def test_audit_public_price_accepts_exact_million_shorthand(self):
        script = self._valid_script(self.listing, price_text="Giá bán 68 triệu")

        issues = motorcycle_sales.audit_sales_script(script, self.listing)

        self.assertNotIn("missing_public_price", issues)

    def test_audit_public_price_flags_missing_configured_price(self):
        script = self._valid_script(self.listing, price_text="Giá bán công khai")

        issues = motorcycle_sales.audit_sales_script(script, self.listing)

        self.assertIn("missing_public_price", issues)

    def test_audit_public_price_is_not_satisfied_by_matching_model_year(self):
        listing = self.listing.model_copy(
            update={"price": 2012, "price_disclosure": PriceDisclosure.public}
        )
        script = self._valid_script(
            listing,
            extra="Xe đời 2012.",
            price_text="",
        )

        issues = motorcycle_sales.audit_sales_script(script, listing)

        self.assertIn("missing_public_price", issues)

    def test_audit_contact_price_flags_contextual_sale_price_disclosure(self):
        listing = self.listing.model_copy(
            update={"price": None, "price_disclosure": PriceDisclosure.contact}
        )

        for disclosed_price in (
            "Giá bán 68 triệu",
            "Chốt xe 68.000.000 đồng",
            "Xe đang để mức 68000k",
            "Giá chỉ 68tr",
        ):
            with self.subTest(disclosed_price=disclosed_price):
                script = self._valid_script(
                    listing,
                    extra=disclosed_price,
                    price_text="",
                )

                issues = motorcycle_sales.audit_sales_script(script, listing)

                self.assertIn("unexpected_price_disclosure", issues)

    def test_audit_contact_price_ignores_unrelated_numbers(self):
        listing = self.listing.model_copy(
            update={
                "price": None,
                "price_disclosure": PriceDisclosure.contact,
                "odometer_km": 25_000,
                "odometer_disclosure": OdometerDisclosure.verified,
            }
        )
        script = self._valid_script(
            listing,
            extra=(
                "Xe đời 2012, ODO 25.000 km. "
                "Liên hệ 0902 143 241 tại 08 Quang Trung."
            ),
            price_text="",
        )

        issues = motorcycle_sales.audit_sales_script(script, listing)

        self.assertNotIn("unexpected_price_disclosure", issues)

    def test_audit_restricted_odometer_flags_contextual_mileage_claims(self):
        for disclosure in (
            OdometerDisclosure.hidden,
            OdometerDisclosure.not_verified,
        ):
            listing = self.listing.model_copy(
                update={"odometer_disclosure": disclosure}
            )
            for mileage_claim in (
                "ODO hiện 25.000",
                "Xe mới đi 25 nghìn km",
                "Đã đi 25.000 cây",
            ):
                with self.subTest(
                    disclosure=disclosure,
                    mileage_claim=mileage_claim,
                ):
                    script = self._valid_script(
                        listing,
                        extra=mileage_claim,
                    )

                    issues = motorcycle_sales.audit_sales_script(script, listing)

                    self.assertIn("unexpected_odometer_claim", issues)

    def test_audit_restricted_odometer_ignores_phone_year_and_address(self):
        listing = self.listing.model_copy(
            update={"odometer_disclosure": OdometerDisclosure.not_verified}
        )
        script = self._valid_script(
            listing,
            extra=(
                "Xe đời 2012. Liên hệ 0902 143 241 "
                "tại 08 Quang Trung để xem xe."
            ),
        )

        issues = motorcycle_sales.audit_sales_script(script, listing)

        self.assertNotIn("unexpected_odometer_claim", issues)

    def test_audit_verified_odometer_accepts_configured_mileage(self):
        listing = self.listing.model_copy(
            update={
                "odometer_km": 25_000,
                "odometer_disclosure": OdometerDisclosure.verified,
            }
        )

        for mileage in ("ODO 25.000 km", "Xe đã đi 25,000 cây", "ODO 25000"):
            with self.subTest(mileage=mileage):
                script = self._valid_script(listing, extra=mileage)

                issues = motorcycle_sales.audit_sales_script(script, listing)

                self.assertNotIn("missing_verified_odometer", issues)

    def test_audit_verified_odometer_flags_missing_or_wrong_mileage(self):
        listing = self.listing.model_copy(
            update={
                "odometer_km": 25_000,
                "odometer_disclosure": OdometerDisclosure.verified,
            }
        )

        for mileage_text in ("Không nhắc số km.", "ODO 32.000 km"):
            with self.subTest(mileage_text=mileage_text):
                script = self._valid_script(listing, extra=mileage_text)

                issues = motorcycle_sales.audit_sales_script(script, listing)

                self.assertIn("missing_verified_odometer", issues)

    def test_audit_verified_odometer_is_not_satisfied_by_matching_model_year(self):
        listing = self.listing.model_copy(
            update={
                "odometer_km": 2012,
                "odometer_disclosure": OdometerDisclosure.verified,
            }
        )
        script = self._valid_script(listing, extra="Xe đời 2012.")

        issues = motorcycle_sales.audit_sales_script(script, listing)

        self.assertIn("missing_verified_odometer", issues)

    def test_audit_uses_whitespace_insensitive_phone_and_key_address(self):
        script = self._valid_script(self.listing).replace(
            "0902 143 241",
            "0902143241",
        ).replace(
            "08 Quang Trung, TP. Quảng Ngãi",
            "08 Quang Trung",
        )

        issues = motorcycle_sales.audit_sales_script(script, self.listing)

        self.assertNotIn("missing_phone", issues)
        self.assertNotIn("missing_address", issues)

    def test_audit_reports_word_count_outside_target_range(self):
        issues = motorcycle_sales.audit_sales_script(
            "Minh Dũng hồ sơ 08 Quang Trung 0902143241",
            self.listing,
        )

        self.assertIn("word_count:8", issues)

    def _valid_script(
        self,
        listing: UsedMotorcycleListing,
        extra: str = "",
        price_text: str | None = None,
    ) -> str:
        if price_text is None:
            price_text = (
                motorcycle_sales.format_vnd(listing.price)
                if listing.price_disclosure == PriceDisclosure.public
                else ""
            )
        required = (
            f"{listing.store_name} giới thiệu xe với {listing.legal_documents}. "
            f"{price_text} Liên hệ {listing.phone} tại {listing.address}. {extra}"
        )
        filler_count = motorcycle_sales.TARGET_MIN_WORDS - len(required.split())
        return required + " " + " ".join(["xe"] * filler_count)


class TestMotorcycleSalesPreset(unittest.TestCase):
    def test_video_subject_uses_listing_store(self):
        listing = UsedMotorcycleListing(
            name="Air Blade",
            model_year="2021",
            condition="Máy êm",
            highlights=["Ngoại hình gọn"],
            store_name="Minh Dũng",
        )

        self.assertEqual(
            motorcycle_sales.build_video_subject(listing),
            "Bán Air Blade đời 2021 tại Minh Dũng Quảng Ngãi",
        )

    def test_video_subject_derives_locality_from_listing_address(self):
        listing = UsedMotorcycleListing(
            name="Air Blade",
            model_year="2021",
            condition="Máy êm",
            highlights=["Ngoại hình gọn"],
            address="12 Lê Lợi, TP. Đà Nẵng",
        )

        self.assertEqual(
            motorcycle_sales.build_video_subject(listing),
            "Bán Air Blade đời 2021 tại Minh Dũng Đà Nẵng",
        )

    def test_video_subject_falls_back_to_full_address_without_commas(self):
        listing = UsedMotorcycleListing(
            name="Vision",
            model_year="2020",
            condition="Máy êm",
            highlights=["Gọn nhẹ"],
            address="Quảng Nam",
        )

        self.assertEqual(
            motorcycle_sales.build_video_subject(listing),
            "Bán Vision đời 2020 tại Minh Dũng Quảng Nam",
        )

    def test_sales_defaults_match_vertical_ordered_local_video(self):
        self.assertEqual(
            motorcycle_sales.sales_video_defaults(),
            {
                "video_aspect": "9:16",
                "video_source": "local",
                "video_concat_mode": "sequential",
                "video_clip_duration": 3,
                "voice_rate": 1.1,
            },
        )

    def test_social_context_contains_subject_store_contact_and_legal_documents(self):
        listing = UsedMotorcycleListing(
            name="Air Blade",
            model_year="2021",
            condition="Máy êm",
            highlights=["Ngoại hình gọn"],
        )

        context = motorcycle_sales.build_social_context(listing)

        self.assertIn("Bán Air Blade đời 2021 tại Minh Dũng Quảng Ngãi", context)
        self.assertIn(listing.legal_documents, context)
        self.assertIn(listing.store_name, context)
        self.assertIn(listing.phone, context)
        self.assertIn(listing.address, context)


if __name__ == "__main__":
    unittest.main()
