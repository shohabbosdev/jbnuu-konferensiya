from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import base64
import os

# Global o'zgaruvchilarni yangilash
def load_template(template_name="template_1.png"):
    """Sertifikat shablonini yuklash"""
    path = r'src/Times New Roman Bold.ttf'
    template_path = os.path.join('src', 'templates', template_name)
    
    # Shriftlarni yuklash
    FONT_FILE_1 = ImageFont.truetype(path, 30)
    FONT_FILE_2 = ImageFont.truetype(path, 14)
    
    # Sertifikat shablonini yuklash
    if os.path.exists(template_path):
        TEMPLATE_IMAGE = Image.open(template_path)
    else:
        # Agar sertifikat shabloni mavjud bo'lmasa, oq fonli rasm yaratamiz
        TEMPLATE_IMAGE = Image.new('RGB', (800, 600), color='white')
    
    return FONT_FILE_1, FONT_FILE_2, TEMPLATE_IMAGE

# Sertifikat yasash qismi
def make_certificates(name, second_text, template_name="template_1.png"):
    # Sertifikat shablonini har safar yangilab olish
    FONT_FILE_1, FONT_FILE_2, TEMPLATE_IMAGE = load_template(template_name)
    FONT_COLOR_1 = "#5E17EB"
    FONT_COLOR_2 = "#0E477D"
    WIDTH, HEIGHT = TEMPLATE_IMAGE.size
    MAX_WIDTH = WIDTH - 80  # Ikkinchi matn uchun maksimal eni
    MAX_WORDS_PER_LINE = 8  # Har bir qatorda maksimal so'z soni
    OUTPUT_DIR = "out"
    
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

# PDF yaratish funksiyasi
def create_pdf_certificate(name, second_text, template_name="template_1.png"):
    # Avval rasmni yaratamiz
    image_bytes = make_certificates(name, second_text, template_name)
    
    # PDF yaratish
    template_path = os.path.join('src', 'templates', template_name)
    WIDTH, HEIGHT = Image.open(template_path).size if os.path.exists(template_path) else (800, 600)
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(WIDTH, HEIGHT))
    
    # Rasmni PDF ga qo'shish
    image_bytes.seek(0)
    img_data = base64.b64encode(image_bytes.getvalue()).decode()
    c.drawImage(f"data:image/png;base64,{img_data}", 0, 0, width=WIDTH, height=HEIGHT)
    
    c.save()
    pdf_buffer.seek(0)
    
    return pdf_buffer

# Mavjud shablonlarni olish
def get_available_templates():
    """Mavjud sertifikat shablonlarini ro'yxat qilish"""
    templates_dir = os.path.join('src', 'templates')
    if not os.path.exists(templates_dir):
        return []
    
    templates = []
    for file in os.listdir(templates_dir):
        if file.endswith('.png'):
            templates.append(file)
    return templates

# Shablonni o'chirish
def delete_template(template_name):
    """Sertifikat shablonini o'chirish"""
    template_path = os.path.join('src', 'templates', template_name)
    if os.path.exists(template_path):
        os.remove(template_path)
        return True
    return False