import re

from app.models.motorcycle import (
    OdometerDisclosure,
    PriceDisclosure,
    UsedMotorcycleListing,
)


STORE_NAME = "Minh Dũng"
STORE_PHONE = "0902 143 241"
STORE_ADDRESS = "08 Quang Trung, TP. Quảng Ngãi"
TARGET_MIN_WORDS = 90
TARGET_MAX_WORDS = 120

UNSUPPORTED_CLAIMS = (
    "zin đét",
    "odo chuẩn",
    "chưa đâm đụng",
    "máy nguyên bản",
    "bao không lỗi",
)

MOTORCYCLE_SALES_SYSTEM_PROMPT = """
Viết kịch bản bán xe bằng chỉ văn bản thô tiếng Việt, không Markdown và không
chú thích sản xuất. Mở đầu bằng một câu hook duy nhất, nói được trong 1-3 giây.
Toàn bộ kịch bản dài 90-120 từ, tương đương khoảng 35-45 giây.
Dùng hài hước vừa phải, tự nhiên, không la hét liên tục.
Kịch bản chỉ dùng sự thật có trong dữ liệu xe được cung cấp; không suy diễn tình
trạng, ODO, lịch sử xe hoặc chất lượng; không tạo khan hiếm giả hay thúc ép giả tạo.
Nêu pháp lý như một điểm tạo niềm tin đúng với dữ liệu đã xác nhận.
Nếu là giá công khai thì đọc đúng giá; nếu là giá liên hệ thì không đọc một con
số giá và mời khách liên hệ để nhận giá.
Kết thúc bằng CTA có tên cửa hàng, số điện thoại và địa chỉ đúng như dữ liệu.
""".strip()


def format_vnd(value: int) -> str:
    return f"{value:,}".replace(",", ".") + " đồng"


def _format_number(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _mask_license_plate(license_plate: str) -> str:
    prefix, separator, private_part = license_plate.partition(" ")
    if separator:
        masked = "".join(
            "*" if character.isalnum() else character
            for character in private_part
        )
        return f"{prefix}{separator}{masked}"

    visible_length = min(4, len(license_plate))
    return license_plate[:visible_length] + "".join(
        "*" if character.isalnum() else character
        for character in license_plate[visible_length:]
    )


def build_sales_script_prompt(listing: UsedMotorcycleListing) -> str:
    facts = [
        f"Tên xe: {listing.name}",
        f"Đời xe: {listing.model_year}",
        f"Tình trạng được người bán cung cấp: {listing.condition}",
        "Ưu điểm: " + "; ".join(listing.highlights),
        f"Pháp lý: {listing.legal_documents}",
    ]

    if listing.odometer_disclosure == OdometerDisclosure.verified:
        facts.append(f"ODO đã xác nhận: {_format_number(listing.odometer_km)} km")
    elif listing.odometer_disclosure == OdometerDisclosure.not_verified:
        facts.append("ODO: chưa xác minh, không được khẳng định")
    else:
        facts.append("ODO: không công bố, không nhắc trong kịch bản")

    license_plate = listing.license_plate.strip()
    if license_plate:
        rendered_plate = (
            _mask_license_plate(license_plate)
            if listing.mask_license_plate
            else license_plate
        )
        facts.append(f"Biển số: {rendered_plate}")

    if listing.price_disclosure == PriceDisclosure.public:
        facts.append(f"Giá bán công khai: {format_vnd(listing.price)}")
    else:
        facts.append(
            "Giá: không đọc một con số giá; mời khách liên hệ để nhận giá"
        )

    notes = listing.notes.strip()
    if notes:
        facts.append(f"Thông tin bổ sung đã xác nhận: {notes}")

    facts.extend(
        (
            f"Tên cửa hàng trong CTA: {listing.store_name}",
            f"Số điện thoại trong CTA: {listing.phone}",
            f"Địa chỉ trong CTA: {listing.address}",
        )
    )

    rendered_facts = "\n".join(f"- {fact}" for fact in facts)
    return (
        f"{MOTORCYCLE_SALES_SYSTEM_PROMPT}\n\n"
        f"# Dữ liệu đã xác nhận\n{rendered_facts}"
    )


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _without_whitespace(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def _normalized_amount(value: str, multiplier: int = 1) -> str:
    return str(int(re.sub(r"\D", "", value)) * multiplier)


def _sale_price_amounts(script: str) -> set[str]:
    normalized = script.casefold()
    amount = r"\d+(?:[., ]\d+)*"
    amounts = set()
    currency_pattern = re.compile(
        rf"(?P<amount>{amount})\s*(?P<marker>đồng|triệu|tr|vnd|k|đ)\b",
        flags=re.IGNORECASE,
    )
    for match in currency_pattern.finditer(normalized):
        marker = match.group("marker")
        if marker == "k":
            following = normalized[match.end() : match.end() + 8]
            if re.match(r"\s*(?:km|cây)\b", following):
                continue
        multiplier = 1_000_000 if marker in {"triệu", "tr"} else 1
        if marker == "k":
            multiplier = 1_000
        amounts.add(_normalized_amount(match.group("amount"), multiplier))

    price_phrase_pattern = re.compile(
        rf"\bgiá\b[^\d\r\n]{{0,24}}(?P<amount>{amount})",
        flags=re.IGNORECASE,
    )
    for match in price_phrase_pattern.finditer(normalized):
        amounts.add(_normalized_amount(match.group("amount")))
    return amounts


def _contains_public_price(script: str, price: int) -> bool:
    return str(price) in _sale_price_amounts(script)


def _contains_sale_price_disclosure(script: str) -> bool:
    return bool(_sale_price_amounts(script))


def _odometer_amounts(script: str) -> set[str]:
    normalized = script.casefold()
    amount = r"\d+(?:[., ]\d+)*"
    patterns = (
        rf"\bodo\b[^\d\r\n]{{0,24}}(?P<amount>{amount})",
        rf"(?<!\d)(?P<amount>{amount})"
        rf"\s*(?P<scale>nghìn|ngàn|k)?\s*(?:km|cây)\b",
        rf"\bđi\b[^\d\r\n]{{0,20}}(?P<amount>{amount})"
        rf"\s*(?P<scale>nghìn|ngàn|k)?\s*(?:km|cây)\b",
    )
    amounts = set()
    for pattern in patterns:
        for match in re.finditer(pattern, normalized):
            scale = match.groupdict().get("scale")
            multiplier = 1_000 if scale else 1
            amounts.add(_normalized_amount(match.group("amount"), multiplier))
    return amounts


def _contains_odometer_claim(script: str) -> bool:
    return bool(_odometer_amounts(script))


def audit_sales_script(
    script: str,
    listing: UsedMotorcycleListing,
) -> list[str]:
    normalized_script = _normalize_text(script)
    normalized_notes = _normalize_text(listing.notes)
    issues = []

    for claim in UNSUPPORTED_CLAIMS:
        normalized_claim = claim.casefold()
        if (
            normalized_claim in normalized_script
            and normalized_claim not in normalized_notes
        ):
            issues.append(f"unsupported_claim:{claim}")

    if listing.price_disclosure == PriceDisclosure.public:
        if not _contains_public_price(script, listing.price):
            issues.append("missing_public_price")
    elif _contains_sale_price_disclosure(script):
        issues.append("unexpected_price_disclosure")

    if listing.odometer_disclosure == OdometerDisclosure.verified:
        if str(listing.odometer_km) not in _odometer_amounts(script):
            issues.append("missing_verified_odometer")
    elif _contains_odometer_claim(script):
        issues.append("unexpected_odometer_claim")

    if _without_whitespace(listing.phone) not in _without_whitespace(script):
        issues.append("missing_phone")

    normalized_address = _normalize_text(listing.address)
    key_address = _normalize_text(listing.address.split(",", maxsplit=1)[0])
    if (
        normalized_address not in normalized_script
        and key_address not in normalized_script
    ):
        issues.append("missing_address")

    if _normalize_text(listing.store_name) not in normalized_script:
        issues.append("missing_store_name")

    legal_trust_markers = (
        _normalize_text(listing.legal_documents),
        "hồ sơ",
        "pháp lý",
        "sang tên",
    )
    if not any(marker in normalized_script for marker in legal_trust_markers):
        issues.append("missing_legal_documents")

    word_count = len(script.split())
    if word_count < TARGET_MIN_WORDS or word_count > TARGET_MAX_WORDS:
        issues.append(f"word_count:{word_count}")

    return issues


def ensure_required_sales_facts(
    script: str,
    listing: UsedMotorcycleListing,
) -> str:
    issues = audit_sales_script(script, listing)
    required_additions = []

    if "missing_public_price" in issues:
        required_additions.append(f"Giá bán công khai {format_vnd(listing.price)}.")

    if "missing_verified_odometer" in issues:
        required_additions.append(
            f"ODO {_format_number(listing.odometer_km)} km đã xác minh."
        )

    if "missing_legal_documents" in issues:
        required_additions.append(f"Hồ sơ pháp lý: {listing.legal_documents}.")

    if any(
        issue in issues
        for issue in ("missing_store_name", "missing_phone", "missing_address")
    ):
        required_additions.append(
            f"Liên hệ {listing.store_name} qua số {listing.phone}, "
            f"địa chỉ {listing.address} để xem xe và chạy thử."
        )

    if not required_additions:
        return script.strip()

    return f"{script.strip()}\n\n{' '.join(required_additions)}".strip()


def _address_locality(address: str) -> str:
    locality = address.rsplit(",", maxsplit=1)[-1].strip() or address.strip()
    cleaned = re.sub(
        r"^(?:tp\.?|thành phố)\s*",
        "",
        locality,
        flags=re.IGNORECASE,
    )
    return cleaned or address.strip()


def build_video_subject(listing: UsedMotorcycleListing) -> str:
    return (
        f"Bán {listing.name} đời {listing.model_year} "
        f"tại {listing.store_name} {_address_locality(listing.address)}"
    )


def sales_video_defaults() -> dict:
    return {
        "video_aspect": "9:16",
        "video_source": "local",
        "video_concat_mode": "sequential",
        "video_clip_duration": 3,
        "voice_rate": 1.1,
    }


def build_social_context(listing: UsedMotorcycleListing) -> str:
    return (
        f"{build_video_subject(listing)}. "
        f"Hồ sơ: {listing.legal_documents}. "
        f"Liên hệ {listing.store_name}, {listing.phone}, {listing.address}."
    )
