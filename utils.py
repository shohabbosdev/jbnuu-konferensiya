from io import BytesIO
from PIL import Image, ImageFont, ImageDraw

path = r'src/Times New Roman Bold.ttf'
# Global Variables
FONT_FILE_1 = ImageFont.truetype(path, 30)
FONT_FILE_2 = ImageFont.truetype(path, 14)
FONT_COLOR_1 = "#5E17EB"
FONT_COLOR_2 = "#0E477D"
TEMPLATE_IMAGE = Image.open(r'src/Sertifikat.png')
WIDTH, HEIGHT = TEMPLATE_IMAGE.size
MAX_WIDTH = WIDTH - 80  # Ikkinchi matn uchun maksimal eni
MAX_WORDS_PER_LINE = 8  # Har bir qatorda maksimal so'z soni
OUTPUT_DIR = "out"

# Sertifikat yasash qismi
def make_certificates(name, second_text):
    template = TEMPLATE_IMAGE.copy()
    draw = ImageDraw.Draw(template)

    # Birinchi matnning eni va balandligini topish
    bbox_1 = FONT_FILE_1.getbbox(name)
    text_width_1 = bbox_1[2] - bbox_1[0]
    text_height_1 = bbox_1[3] - bbox_1[1]

    # Birinchi matnni markazga joylashtirish
    draw.text(((WIDTH - text_width_1) / 2 - 40, (HEIGHT - text_height_1) / 2 + 40), name, fill=FONT_COLOR_1, font=FONT_FILE_1)

    # Ikkinchi matnni bir necha qatorga bo'lish
    words = second_text.split()
    lines = []
    line = []
    for word in words:
        if len(line) < MAX_WORDS_PER_LINE:
            line.append(word)
        else:
            lines.append(' '.join(line))
            line = [word]
        # Har bir qatordan keyin matnning o'lchamini tekshiramiz
        bbox_2 = FONT_FILE_2.getbbox(' '.join(line))
        text_width_2 = bbox_2[2] - bbox_2[0]
        if text_width_2 > MAX_WIDTH:
            line.pop()  # Ohirgi so'zni olib tashlash
            lines.append(' '.join(line))
            line = [word]

    if line:
        lines.append(' '.join(line))

    y = (HEIGHT - text_height_1) / 2 + 55 + text_height_1 + 10
    for line in lines:
        bbox_2 = FONT_FILE_2.getbbox(line)
        text_width_2 = bbox_2[2] - bbox_2[0]
        text_height_2 = bbox_2[3] - bbox_2[1]
        draw.text(((WIDTH - text_width_2) / 2 - 40, y), line, fill=FONT_COLOR_2, font=FONT_FILE_2)
        y += text_height_2 + 5  # Qatorlar orasidagi masofani oshirish

    # Sertifikatni BytesIO obyektiga saqlash
    image_bytes = BytesIO()
    template.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    
    return image_bytes