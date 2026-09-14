import os
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- РЕГИСТРАЦИЯ ТТF ШРИФТОВ INTER ---
FONTS_DIR = "./fonts"

INTER_FONTS = {
    "Inter": "Inter_18pt-Regular.ttf",
    "Inter-Bold": "Inter_18pt-Bold.ttf",
    "Inter-Medium": "Inter_18pt-Medium.ttf",
    "Inter-Italic": "Inter_18pt-Italic.ttf"
}

for font_name, font_file in INTER_FONTS.items():
    full_path = os.path.join(FONTS_DIR, font_file)
    if os.path.exists(full_path):
        pdfmetrics.registerFont(TTFont(font_name, full_path))
    else:
        print(f"Предупреждение: файл {font_file} не найден в {FONTS_DIR}")
# -------------------------------------------

def modify_pdf(input_path, output_path):
    temp_page_path = "temp_generated_page.pdf"
    
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        if len(reader.pages) == 0:
            print("Файл пуст.")
            return

        # Удаляем первую страницу (копируем со 2-й и далее)
        for page_num in range(1, len(reader.pages)):
            writer.add_page(reader.pages[page_num])
            
        # Генерация новой страницы
        c = canvas.Canvas(temp_page_path, pagesize=letter)
        width, height = letter
        
        c.setFillColor(colors.HexColor("#1A365D"))
        c.rect(0, height - 140, width, 140, fill=True, stroke=False)
        
        c.setFillColor(colors.white)
        c.setFont("Inter-Bold", 26) 
        c.drawString(50, height - 65, "Новый Титульный Лист")
        
        c.setFont("Inter-Medium", 14)
        c.drawString(50, height - 100, "Сгенерировано с использованием TTF")
        
        c.setFillColor(colors.HexColor("#2D3748"))
        c.setFont("Inter", 12)
        c.drawString(50, height - 200, "Теперь кириллица в шрифте Inter отображается корректно!")
        
        c.save()
        
        # Сшиваем файлы: Читаем временный PDF
        new_page_reader = PdfReader(temp_page_path)
        
        # ИСПРАВЛЕНИЕ: Берем строго первую страницу через [0]
        new_page_object = new_page_reader.pages[0] 
        writer.insert_page(new_page_object, index=0)
        
        # Сохраняем финальный результат
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
            
        print(f"Успех! Файл сохранен: {output_path}")

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if os.path.exists(temp_page_path):
            os.remove(temp_page_path)

modify_pdf("source.pdf", "ready_document.pdf")
