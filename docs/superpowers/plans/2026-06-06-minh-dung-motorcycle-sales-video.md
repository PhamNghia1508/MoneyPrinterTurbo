# Minh Dung Motorcycle Sales Video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Minh Dung sales preset that turns verified used-motorcycle details and ordered local media into editable 35-45 second Vietnamese sales videos plus TikTok and Facebook Reels captions.

**Architecture:** Add a focused motorcycle-sales domain model and pure prompt/audit helpers, then expose a small LLM wrapper and integrate the preset into the existing Streamlit page. Reuse the current TTS, subtitle, local-material, rendering, and social-metadata pipelines; do not replace the generic MoneyPrinterTurbo workflow.

**Tech Stack:** Python 3.11, Pydantic, Streamlit, unittest, existing OpenAI-compatible LLM service, MoviePy/FFmpeg pipeline.

---

## File Structure

- Create `app/models/motorcycle.py`: validated motorcycle-sale input and price/ODO disclosure enums.
- Create `app/services/motorcycle_sales.py`: brand constants, prompt construction, script audit, subject/context builders, and preset defaults.
- Create `test/services/test_motorcycle_sales.py`: domain, prompt, audit, metadata-context, and defaults tests.
- Modify `app/services/llm.py`: add a retrying motorcycle-script generation wrapper while restoring the generic default prompt.
- Modify `test/services/test_llm.py`: cover the new wrapper and preserve generic prompt behavior.
- Modify `webui/Main.py`: add the sales-mode form, editable script flow, ordered local media defaults, and editable social metadata.
- Modify `webui/i18n/vi.json`: add Vietnamese labels and messages for the sales preset.
- Modify `webui/i18n/en.json`: add English fallbacks for the same UI keys.
- Modify `config.example.toml`: document optional Minh Dung brand defaults without storing secrets.

### Task 1: Add the validated motorcycle-sale domain model

**Files:**
- Create: `app/models/motorcycle.py`
- Create: `test/services/test_motorcycle_sales.py`

- [ ] **Step 1: Write failing model-validation tests**

```python
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
                model_year="",
                condition="",
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

    def test_public_price_requires_price(self):
        with self.assertRaises(ValidationError):
            UsedMotorcycleListing(
                name="Vision",
                model_year="2020",
                condition="Vận hành ổn định",
                highlights=["Tiết kiệm xăng"],
                price_disclosure=PriceDisclosure.public,
            )
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `uv run python -m unittest test.services.test_motorcycle_sales.TestUsedMotorcycleListing -v`

Expected: FAIL because `app.models.motorcycle` does not exist.

- [ ] **Step 3: Implement the model and disclosure rules**

```python
from enum import Enum
from typing import List, Optional

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
    odometer_km: Optional[int] = Field(default=None, ge=0, le=2_000_000)
    odometer_disclosure: OdometerDisclosure = OdometerDisclosure.not_verified
    license_plate: str = Field(default="", max_length=30)
    mask_license_plate: bool = True
    price: Optional[int] = Field(default=None, ge=0)
    price_disclosure: PriceDisclosure = PriceDisclosure.contact
    condition: str = Field(min_length=1, max_length=1000)
    highlights: List[str] = Field(min_length=1, max_length=10)
    legal_documents: str = "Hồ sơ pháp lý đầy đủ, hỗ trợ sang tên"
    notes: str = Field(default="", max_length=1000)
    store_name: str = "Minh Dũng"
    phone: str = "0902 143 241"
    address: str = "08 Quang Trung, TP. Quảng Ngãi"

    @model_validator(mode="after")
    def validate_disclosures(self):
        self.name = self.name.strip()
        self.model_year = self.model_year.strip()
        self.condition = self.condition.strip()
        self.highlights = [item.strip() for item in self.highlights if item.strip()]
        if not self.highlights:
            raise ValueError("at least one highlight is required")
        if self.price_disclosure == PriceDisclosure.public and self.price is None:
            raise ValueError("price is required when price disclosure is public")
        if (
            self.odometer_disclosure == OdometerDisclosure.verified
            and self.odometer_km is None
        ):
            raise ValueError("odometer is required when marked verified")
        return self
```

- [ ] **Step 4: Run the focused tests**

Run: `uv run python -m unittest test.services.test_motorcycle_sales.TestUsedMotorcycleListing -v`

Expected: PASS.

- [ ] **Step 5: Commit the domain model**

```powershell
git add app/models/motorcycle.py test/services/test_motorcycle_sales.py
git commit -m "feat: add motorcycle sales listing model"
```

### Task 2: Build truthful sales prompts and audit generated scripts

**Files:**
- Create: `app/services/motorcycle_sales.py`
- Modify: `test/services/test_motorcycle_sales.py`

- [ ] **Step 1: Write failing prompt and audit tests**

```python
from app.services import motorcycle_sales


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

    def test_prompt_contains_hook_duration_brand_and_verified_facts(self):
        prompt = motorcycle_sales.build_sales_script_prompt(self.listing)

        self.assertIn("1-3 giây", prompt)
        self.assertIn("35-45 giây", prompt)
        self.assertIn("90-120 từ", prompt)
        self.assertIn("SH 150i nhập Ý", prompt)
        self.assertIn("68.000.000 đồng", prompt)
        self.assertIn("0902 143 241", prompt)
        self.assertIn("08 Quang Trung, TP. Quảng Ngãi", prompt)

    def test_unverified_odometer_is_not_rendered_as_a_number(self):
        prompt = motorcycle_sales.build_sales_script_prompt(self.listing)

        self.assertIn("ODO: chưa xác minh, không được khẳng định", prompt)
        self.assertNotIn("ODO chuẩn", prompt)

    def test_contact_price_asks_viewer_to_contact_store(self):
        listing = self.listing.model_copy(
            update={"price": None, "price_disclosure": PriceDisclosure.contact}
        )

        prompt = motorcycle_sales.build_sales_script_prompt(listing)

        self.assertIn("không đọc một con số giá", prompt)
        self.assertIn("liên hệ để nhận giá", prompt)

    def test_script_audit_flags_unsupported_claims_and_missing_cta(self):
        issues = motorcycle_sales.audit_sales_script(
            "Xe zin đét, ODO chuẩn, nhanh tay thì còn!",
            self.listing,
        )

        self.assertIn("unsupported_claim:zin đét", issues)
        self.assertIn("unsupported_claim:ODO chuẩn", issues)
        self.assertIn("missing_phone", issues)
        self.assertIn("missing_address", issues)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run python -m unittest test.services.test_motorcycle_sales.TestMotorcycleSalesPrompt -v`

Expected: FAIL because `app.services.motorcycle_sales` does not exist.

- [ ] **Step 3: Implement pure prompt, context, audit, and defaults helpers**

The module must define:

```python
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


def format_vnd(value: int) -> str:
    return f"{value:,}".replace(",", ".") + " đồng"


def build_sales_script_prompt(listing: UsedMotorcycleListing) -> str:
    facts = [
        f"Tên xe: {listing.name}",
        f"Đời xe: {listing.model_year}",
        f"Tình trạng được người bán cung cấp: {listing.condition}",
        "Ưu điểm: " + "; ".join(listing.highlights),
        f"Pháp lý: {listing.legal_documents}",
    ]
    if listing.odometer_disclosure == OdometerDisclosure.verified:
        facts.append(f"ODO đã xác nhận: {listing.odometer_km:,} km")
    elif listing.odometer_disclosure == OdometerDisclosure.not_verified:
        facts.append("ODO: chưa xác minh, không được khẳng định")
    else:
        facts.append("ODO: không công bố, không nhắc trong kịch bản")

    if listing.price_disclosure == PriceDisclosure.public:
        facts.append(f"Giá bán công khai: {format_vnd(listing.price)}")
    else:
        facts.append(
            "Giá: không đọc một con số giá; mời khách liên hệ để nhận giá"
        )

    return MOTORCYCLE_SALES_SYSTEM_PROMPT + "\n\n# Dữ liệu đã xác nhận\n" + "\n".join(
        f"- {fact}" for fact in facts
    )


def audit_sales_script(script: str, listing: UsedMotorcycleListing) -> list[str]:
    normalized = script.casefold()
    issues = []
    for claim in UNSUPPORTED_CLAIMS:
        if claim.casefold() in normalized and claim.casefold() not in listing.notes.casefold():
            issues.append(f"unsupported_claim:{claim}")
    if listing.phone.replace(" ", "") not in script.replace(" ", ""):
        issues.append("missing_phone")
    if "08 Quang Trung" not in script:
        issues.append("missing_address")
    word_count = len(script.split())
    if word_count < TARGET_MIN_WORDS or word_count > TARGET_MAX_WORDS:
        issues.append(f"word_count:{word_count}")
    return issues
```

`MOTORCYCLE_SALES_SYSTEM_PROMPT` must explicitly require:

- Vietnamese raw text only.
- A one-sentence hook that can be spoken in 1-3 seconds.
- 90-120 words and approximately 35-45 seconds.
- Moderate humor without shouting throughout.
- Facts only from the supplied listing.
- No fake scarcity.
- Legal-document trust point.
- Public-price/contact-price behavior.
- A closing CTA containing store name, phone, and address.

Also add:

```python
def build_video_subject(listing: UsedMotorcycleListing) -> str:
    return f"Bán {listing.name} đời {listing.model_year} tại Minh Dũng Quảng Ngãi"


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
```

- [ ] **Step 4: Run the focused service tests**

Run: `uv run python -m unittest test.services.test_motorcycle_sales -v`

Expected: PASS.

- [ ] **Step 5: Commit prompt and audit helpers**

```powershell
git add app/services/motorcycle_sales.py test/services/test_motorcycle_sales.py
git commit -m "feat: add truthful motorcycle sales prompts"
```

### Task 3: Add the LLM generation wrapper and restore generic behavior

**Files:**
- Modify: `app/services/llm.py`
- Modify: `test/services/test_llm.py`

- [ ] **Step 1: Write failing wrapper tests**

Add imports for `UsedMotorcycleListing`, disclosure enums, and `motorcycle_sales`, then add:

```python
class TestMotorcycleSalesScriptGeneration(unittest.TestCase):
    def setUp(self):
        self.listing = UsedMotorcycleListing(
            name="Vision",
            model_year="2020",
            condition="Vận hành ổn định",
            highlights=["Hồ sơ đầy đủ"],
            price_disclosure=PriceDisclosure.contact,
            odometer_disclosure=OdometerDisclosure.hidden,
        )

    def test_generate_sales_script_uses_specialized_prompt(self):
        response = (
            "Giá này mà gặp Vision đời 2020 giấy tờ đủ thì đáng xem nha! "
            "Chiếc xe vận hành ổn định, phù hợp đi làm và đi phố mỗi ngày. "
            "Hồ sơ pháp lý đầy đủ, cửa hàng hỗ trợ sang tên rõ ràng. "
            "Giá cụ thể anh chị liên hệ để nhận mức tốt nhất. "
            "Gọi Minh Dũng số 0902 143 241 hoặc ghé 08 Quang Trung, "
            "TP. Quảng Ngãi để xem xe."
        )
        with patch.object(llm, "_generate_response", return_value=response) as generate:
            result = llm.generate_motorcycle_sales_script(self.listing)

        self.assertEqual(result["script"], response)
        self.assertIn("Vision", generate.call_args.args[0])
        self.assertIn("35-45 giây", generate.call_args.args[0])
        self.assertIsInstance(result["warnings"], list)

    def test_generic_default_prompt_remains_generic(self):
        self.assertIn("# Role: Video Script Generator", llm.DEFAULT_SCRIPT_SYSTEM_PROMPT)
        self.assertNotIn("Alo ngay em Nghĩa", llm.DEFAULT_SCRIPT_SYSTEM_PROMPT)
```

- [ ] **Step 2: Run tests to verify the wrapper is missing**

Run: `uv run python -m unittest test.services.test_llm.TestMotorcycleSalesScriptGeneration -v`

Expected: FAIL because `generate_motorcycle_sales_script` does not exist and the generic prompt is still shop-specific.

- [ ] **Step 3: Restore the generic default prompt and implement the wrapper**

In `app/services/llm.py`:

```python
from app.models.motorcycle import UsedMotorcycleListing
from app.services import motorcycle_sales


DEFAULT_SCRIPT_SYSTEM_PROMPT = """
# Role: Video Script Generator

## Goals:
Generate a script for a video, depending on the subject of the video.

## Constraints:
1. Return raw narration text with the requested number of paragraphs.
2. Get straight to the point without greetings or titles.
3. Do not include markdown, narrator labels, or prompt commentary.
4. Respond in the requested language or the subject language.
""".strip()


def generate_motorcycle_sales_script(
    listing: UsedMotorcycleListing,
) -> dict:
    prompt = motorcycle_sales.build_sales_script_prompt(listing)
    last_error = ""
    for attempt in range(_max_retries):
        try:
            script = _generate_response(prompt)
            if script and "Error: " not in script:
                cleaned = script.replace("*", "").replace("#", "").strip()
                return {
                    "script": cleaned,
                    "warnings": motorcycle_sales.audit_sales_script(
                        cleaned, listing
                    ),
                }
            last_error = script or "empty response"
        except Exception as exc:
            last_error = str(exc)
        if attempt < _max_retries - 1:
            logger.warning(
                "failed to generate motorcycle sales script, "
                f"trying again... {attempt + 1}"
            )
    return {"script": f"Error: {last_error}", "warnings": ["generation_failed"]}
```

Do not route the generic `/scripts` endpoint through this wrapper. The sales preset calls it explicitly.

- [ ] **Step 4: Run focused and existing LLM tests**

Run: `uv run python -m unittest test.services.test_llm.TestMotorcycleSalesScriptGeneration test.services.test_llm.TestScriptPromptOptions test.services.test_llm.TestSocialMetadata -v`

Expected: PASS. Update only stale assertions that expected the shop-specific prompt to be the global default.

- [ ] **Step 5: Commit the LLM integration**

```powershell
git add app/services/llm.py test/services/test_llm.py
git commit -m "feat: generate motorcycle sales scripts"
```

### Task 4: Add the Minh Dung preset to Streamlit

**Files:**
- Modify: `webui/Main.py`
- Modify: `webui/i18n/vi.json`
- Modify: `webui/i18n/en.json`
- Modify: `config.example.toml`
- Modify: `test/services/test_motorcycle_sales.py`

- [ ] **Step 1: Add failing tests for preset defaults and social context**

```python
class TestMotorcycleSalesPreset(unittest.TestCase):
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

    def test_social_context_contains_store_contact_and_legal_documents(self):
        listing = UsedMotorcycleListing(
            name="Air Blade",
            model_year="2021",
            condition="Máy êm",
            highlights=["Ngoại hình gọn"],
        )

        context = motorcycle_sales.build_social_context(listing)

        self.assertIn("Minh Dũng", context)
        self.assertIn("0902 143 241", context)
        self.assertIn("08 Quang Trung", context)
        self.assertIn("Hồ sơ pháp lý đầy đủ", context)
```

- [ ] **Step 2: Run the preset tests**

Run: `uv run python -m unittest test.services.test_motorcycle_sales.TestMotorcycleSalesPreset -v`

Expected: PASS only after Task 2 helpers are complete; this is the regression gate before UI wiring.

- [ ] **Step 3: Add sales-mode session state and form controls**

At the top of `webui/Main.py`, import:

```python
from app.models.motorcycle import (
    OdometerDisclosure,
    PriceDisclosure,
    UsedMotorcycleListing,
)
from app.services import motorcycle_sales
```

Add session keys for:

```python
"content_mode" = "motorcycle_sales"
"sales_script_warnings" = []
"tiktok_metadata" = {"title": "", "caption": "", "hashtags": []}
"facebook_metadata" = {"title": "", "caption": "", "hashtags": []}
```

Add a mode selector above the three main panels:

```python
content_mode = st.selectbox(
    tr("Content Mode"),
    options=["motorcycle_sales", "generic"],
    format_func=lambda value: tr(
        "Minh Dung Motorcycle Sales"
        if value == "motorcycle_sales"
        else "Generic Video"
    ),
    key="content_mode",
)
```

When `content_mode == "motorcycle_sales"`, render fields for:

- Vehicle name.
- Model year.
- ODO value and disclosure.
- License plate and mask toggle.
- Price and public/contact disclosure.
- Actual condition.
- Highlights as one item per line.
- Legal documents.
- Additional verified notes.

Construct `UsedMotorcycleListing` only when the user requests script generation. Catch `pydantic.ValidationError` and show translated field errors without clearing form state.

- [ ] **Step 4: Wire script generation, warnings, and editable output**

Replace the sales-mode generation branch with:

```python
listing = UsedMotorcycleListing(...)
result = llm.generate_motorcycle_sales_script(listing)
if result["script"].startswith("Error: "):
    st.error(result["script"])
else:
    st.session_state["video_subject"] = motorcycle_sales.build_video_subject(listing)
    st.session_state["video_script"] = result["script"]
    st.session_state["sales_script_warnings"] = result["warnings"]
```

Display each warning before the editable script box:

- `unsupported_claim:*`: error.
- `missing_phone`, `missing_address`: error.
- `word_count:*`: warning.

Re-run `audit_sales_script` on the edited script when the user presses Generate Video. Block unsupported claims and missing CTA; allow word-count warnings after explicit display.

- [ ] **Step 5: Apply video defaults and require ordered local media**

In sales mode, force or preselect:

```python
params.video_aspect = VideoAspect.portrait
params.video_source = "local"
params.video_concat_mode = VideoConcatMode.sequential
params.video_clip_duration = 3
params.voice_rate = 1.1
```

Keep upload order when building `params.video_materials`. Before starting a sales video:

```python
if not params.video_materials:
    st.error(tr("Please upload at least one motorcycle photo or video"))
    st.stop()
```

Explain beside the uploader that the first file is the 1-3 second hook shot. Do not add automatic image ranking.

- [ ] **Step 6: Add editable TikTok and Facebook metadata**

After a successful sales script generation, call:

```python
social_subject = motorcycle_sales.build_social_context(listing)
for platform, state_key in (
    ("tiktok", "tiktok_metadata"),
    ("facebook_reels", "facebook_metadata"),
):
    st.session_state[state_key] = llm.generate_social_metadata(
        video_subject=social_subject,
        video_script=st.session_state["video_script"],
        language="vi-VN",
        platform=platform,
    )
```

Render editable title, caption, and hashtag text areas for both platforms. This is draft-only; do not call `upload_post` or any external publishing API.

- [ ] **Step 7: Add translations and documented brand defaults**

Add matching keys to `webui/i18n/vi.json` and `webui/i18n/en.json`, including:

```json
{
  "Content Mode": "Chế độ nội dung",
  "Minh Dung Motorcycle Sales": "Bán xe Minh Dũng",
  "Generic Video": "Video thông thường",
  "Vehicle Name": "Tên xe",
  "Model Year": "Đời xe",
  "Actual Condition": "Tình trạng thực tế",
  "Vehicle Highlights": "Ưu điểm nổi bật",
  "Public Price": "Đọc giá trong video",
  "Contact For Price": "Liên hệ để nhận giá",
  "Legal Documents": "Hồ sơ pháp lý",
  "First Upload Hook Help": "Tệp đầu tiên sẽ được dùng làm cảnh hook 1-3 giây.",
  "Please upload at least one motorcycle photo or video": "Vui lòng tải lên ít nhất một ảnh hoặc video của xe."
}
```

In `config.example.toml`, add non-secret defaults:

```toml
# Optional motorcycle-sales brand defaults used by the Streamlit preset.
motorcycle_store_name = "Minh Dũng"
motorcycle_store_phone = "0902 143 241"
motorcycle_store_address = "08 Quang Trung, TP. Quảng Ngãi"
```

Use these config values as model defaults when present, with the constants as fallback.

- [ ] **Step 8: Run service tests and compile the Streamlit page**

Run:

```powershell
uv run python -m unittest test.services.test_motorcycle_sales test.services.test_llm.TestMotorcycleSalesScriptGeneration -v
uv run python -m py_compile webui/Main.py
```

Expected: all tests PASS and compilation exits 0.

- [ ] **Step 9: Commit the WebUI preset**

```powershell
git add webui/Main.py webui/i18n/vi.json webui/i18n/en.json config.example.toml test/services/test_motorcycle_sales.py
git commit -m "feat: add Minh Dung motorcycle sales preset"
```

### Task 5: Remove the current WebUI crash and audit text encoding

**Files:**
- Modify: `webui/Main.py`
- Modify: `app/services/llm.py`
- Modify: `webui/i18n/vi.json`
- Modify: `test/services/test_motorcycle_sales.py`

- [ ] **Step 1: Add a source-regression test for the page footer**

```python
from pathlib import Path


class TestWebUISourceRegression(unittest.TestCase):
    def test_main_page_has_one_final_config_save_and_no_undefined_bottom_call(self):
        source = Path("webui/Main.py").read_text(encoding="utf-8")
        footer = source[source.rfind("config.save_config()") - 100 :]

        self.assertNotIn("_bottom()", source)
        self.assertEqual(footer.count("config.save_config()"), 1)

    def test_vietnamese_brand_text_decodes_cleanly(self):
        source = Path("app/services/motorcycle_sales.py").read_text(encoding="utf-8")

        self.assertIn("Minh Dũng", source)
        self.assertIn("Quảng Ngãi", source)
        self.assertNotIn("Minh DÆ", source)
```

- [ ] **Step 2: Run the regression test to verify the footer failure**

Run: `uv run python -m unittest test.services.test_motorcycle_sales.TestWebUISourceRegression -v`

Expected: FAIL because `webui/Main.py` contains `_bottom()` and duplicate final saves.

- [ ] **Step 3: Fix the footer and malformed literals only**

Replace:

```python
config.save_config()
_bottom()

config.save_config()
```

with:

```python
config.save_config()
```

Read edited Python and JSON files explicitly as UTF-8. Correct only literals that contain actual mojibake in the file; do not mechanically rewrite unrelated Chinese comments or the entire repository.

- [ ] **Step 4: Validate Python and JSON syntax**

Run:

```powershell
uv run python -m py_compile app/models/motorcycle.py app/services/motorcycle_sales.py app/services/llm.py webui/Main.py
uv run python -c "import json, pathlib; [json.loads(pathlib.Path(p).read_text(encoding='utf-8')) for p in ('webui/i18n/vi.json','webui/i18n/en.json')]"
uv run python -m unittest test.services.test_motorcycle_sales.TestWebUISourceRegression -v
```

Expected: all commands exit 0.

- [ ] **Step 5: Commit the cleanup**

```powershell
git add webui/Main.py app/services/llm.py webui/i18n/vi.json test/services/test_motorcycle_sales.py
git commit -m "fix: stabilize motorcycle sales webui"
```

### Task 6: Run the full verification loop and manually inspect the workflow

**Files:**
- Modify only files needed for defects found during verification.

- [ ] **Step 1: Run the complete automated suite**

Run:

```powershell
uv run python -m unittest discover -s test -p "test_*.py" -v
```

Expected: PASS, with live-provider tests skipped when credentials are absent.

- [ ] **Step 2: Run syntax and diff checks**

Run:

```powershell
uv run python -m compileall -q app webui
git diff --check
git status --short
```

Expected: compile and diff checks exit 0; status contains only intentional changes.

- [ ] **Step 3: Start the Streamlit app**

Run: `uv run streamlit run ./webui/Main.py --server.headless true --server.port 8501 --browser.gatherUsageStats false`

Expected: Streamlit reports `http://localhost:8501` and no `NameError: _bottom`.

- [ ] **Step 4: Verify the local UI in the in-app browser**

Open `http://localhost:8501` and confirm:

- "Bán xe Minh Dũng" is the default mode.
- Vietnamese text displays with correct accents.
- Required vehicle fields are visible.
- Public-price and contact-price choices behave differently.
- Local media is selected, portrait 9:16 is selected, and sequential mode is selected.
- The uploader explains that the first file is the hook shot.
- Generated script remains editable.
- Script warnings are visible and actionable.
- TikTok and Facebook Reels metadata are separately editable.

- [ ] **Step 5: Exercise one sample listing without external publishing**

Use:

```text
Tên xe: SH 150i nhập Ý
Đời xe: 2012
ODO: chưa xác minh
Giá: liên hệ
Tình trạng: Máy vận hành êm, dàn áo còn đẹp theo hiện trạng
Ưu điểm: Hồ sơ pháp lý đầy đủ; hỗ trợ sang tên
```

Upload the existing local SH images from `assets/`, place the strongest front-angle image first, and confirm the app accepts the ordered files. If no LLM API key is configured, verify validation and UI behavior up to the generation boundary and report that live script/video generation was not exercised.

- [ ] **Step 6: Review the final diff**

Run:

```powershell
git diff --stat
git diff -- app/models/motorcycle.py app/services/motorcycle_sales.py app/services/llm.py webui/Main.py webui/i18n/vi.json webui/i18n/en.json config.example.toml test/services/test_motorcycle_sales.py test/services/test_llm.py
```

Expected: changes stay within the approved sales preset, its tests, translations, defaults, and the related WebUI bug fix.

- [ ] **Step 7: Commit verification fixes if any**

```powershell
git add app webui test config.example.toml
git commit -m "test: verify motorcycle sales workflow"
```

Skip this commit when verification required no code changes.
