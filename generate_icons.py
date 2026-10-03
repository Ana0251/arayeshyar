"""
تولید آیکون‌های PWA از یه تصویر مادر.

─── استفاده: ───
    python generate_icons.py
"""

from pathlib import Path

from PIL import Image

# ═══════════════════════════════════════════════════════════════
#  مسیرها
# ═══════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent
SOURCE = BASE_DIR / "logo.png"
OUTPUT_DIR = BASE_DIR / "static" / "icons"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
#  سایزها
# ═══════════════════════════════════════════════════════════════

SIZES = [72, 96, 128, 144, 152, 192, 256, 384, 512]

# ═══════════════════════════════════════════════════════════════
#  چک فایل مادر
# ═══════════════════════════════════════════════════════════════

if not SOURCE.exists():
    print(f"❌ فایل {SOURCE} پیدا نشد.")
    print("لطفاً یه تصویر با اسم logo.png توی ریشه‌ی پروژه بذار.")
    exit(1)

img = Image.open(SOURCE).convert("RGBA")
print(f"📷 فایل مادر: {SOURCE.name} ({img.size[0]}x{img.size[1]})")
print("")

# ═══════════════════════════════════════════════════════════════
#  Resize + Save
# ═══════════════════════════════════════════════════════════════

for size in SIZES:
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    output = OUTPUT_DIR / f"icon-{size}.png"
    resized.save(output, "PNG", optimize=True)
    print(f"✅ {output.name}")

# ═══════════════════════════════════════════════════════════════
#  Apple Touch Icon
# ═══════════════════════════════════════════════════════════════

apple = img.resize((180, 180), Image.Resampling.LANCZOS)
apple.save(OUTPUT_DIR / "apple-touch-icon.png", "PNG", optimize=True)
print("✅ apple-touch-icon.png")

# ═══════════════════════════════════════════════════════════════
#  Favicon (ICO)
# ═══════════════════════════════════════════════════════════════

favicon = img.resize((32, 32), Image.Resampling.LANCZOS)
favicon.save(OUTPUT_DIR / "favicon.ico", "ICO")
print("✅ favicon.ico")

print("")
print("🎉 همه‌ی آیکون‌ها ساخته شدن!")
print(f"📁 پوشه: {OUTPUT_DIR}")