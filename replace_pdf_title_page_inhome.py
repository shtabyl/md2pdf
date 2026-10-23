import os
import sys
from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 1. РЕГИСТРАЦИЯ ШРИФТОВ ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

vector_logo_path = os.path.join(SCRIPT_DIR, "static/logo_vector_full_inhome.pdf")

# Привязываем папку шрифтов к абсолютной директории скрипта
FONTS_DIR = os.path.join(SCRIPT_DIR, "fonts")
pdfmetrics.registerFont(TTFont("Inter", os.path.join(FONTS_DIR, "Inter_18pt-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Inter-SemiBold", os.path.join(FONTS_DIR, "Inter_18pt-SemiBold.ttf")))

def parse_text(text: str) -> tuple[str, str]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return "", ""
    if len(lines) == 1:
        return "", lines[0]
    title = " ".join(lines[:-2])
    subtitle = lines[-2]
    return title, subtitle

# --- 2. ФУНКЦИЯ ДЛЯ ОТРИСОВКИ ТОЛЬКО ЦВЕТА ФОНА ---
def draw_background(canvas, doc):
    """Просто закрашивает фоновый лист в фирменный цвет."""
    canvas.saveState()
    width, height = doc.pagesize
    canvas.setFillColor(colors.HexColor("#78BE20"))
    canvas.rect(0, 0, width, height, fill=True, stroke=False)
    canvas.restoreState()


# --- 3. ГЕНЕРАЦИЯ ДИЗАЙНА ТИТУЛЬНОЙ СТРАНИЦЫ ---
def generate_cover_page(output_temp_path, title_text, subtitle_text):
    """Создает временный PDF-файл с текстом, смещенным ближе к центру."""
    doc = SimpleDocTemplate(
        output_temp_path,
        pagesize=letter,
        leftMargin=50, rightMargin=50,
        topMargin=20, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    top_text_style = ParagraphStyle(
        'TopText',
        parent=styles['Normal'],
        fontName='Inter',
        fontSize=14,
        leading=16,
        textColor=colors.white,
        alignment=1
    )
    
    main_title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Normal'],
        fontName='Inter-SemiBold',
        fontSize=18,
        leading=26,
        textColor=colors.white,
        alignment=1
    )
    
    story = []
    
    # Опускаем блок текста вниз, чтобы начать его примерно с верхней трети страницы
    story.append(Spacer(1, 240))
    
    formatted_subtitle = subtitle_text.capitalize()
    story.append(Paragraph(formatted_subtitle, top_text_style))
    story.append(Spacer(1, 30))
    
    formatted_title = title_text.upper().replace('\n', '<br/>')
    story.append(Paragraph(formatted_title, main_title_style))
    
    doc.build(story, onFirstPage=draw_background)


# --- 4. ОСНОВНАЯ ФУНКЦИЯ ДЛЯ ЗАМЕНЫ СТРАНИЦЫ И СШИВАНИЯ ---
def replace_pdf_first_page(source_pdf_path, final_pdf_path):
    temp_cover_path = "temp_cover.pdf"
    
    try:
        reader = PdfReader(source_pdf_path)
        writer = PdfWriter()
        
        if len(reader.pages) == 0:
            print("Ошибка: Исходный файл пуст.")
            return
            
        # Извлечение и парсинг текста с первой страницы
        first_page = reader.pages[0]
        extracted_text = first_page.extract_text()
        extracted_text = extracted_text.strip() if extracted_text else ""
        
        if not extracted_text:
            title_text, subtitle_text = "Без названия", ""
        else:
            title_text, subtitle_text = parse_text(extracted_text)
        
        # Копируем в новый файл страницы со 2-й до конца
        for page_num in range(1, len(reader.pages)):
            writer.add_page(reader.pages[page_num])
            
        # Генерируем текстовую обложку
        generate_cover_page(temp_cover_path, title_text, subtitle_text)
        
        # Читаем созданную текстовую обложку
        cover_reader = PdfReader(temp_cover_path)
        new_cover_page = cover_reader.pages[0]
        
        # Размеры страницы letter: ширина 612, высота 792 пунктов
        PAGE_W, PAGE_H = 612, 792
        
        # --- 4А. СЛИЯНИЕ С ВЕКТОРНЫМ ЛОГОТИПОМ ПО ЦЕНТРУ ОСТАВШЕГОСЯ МЕСТА ---
        if os.path.exists(vector_logo_path):
            logo_reader = PdfReader(vector_logo_path)
            logo_page = logo_reader.pages[0]
            
            orig_logo_w = float(logo_page.mediabox.width)
            orig_logo_h = float(logo_page.mediabox.height)
            
            # Размеры логотипа по вашему запросу
            target_logo_w, target_logo_h = 60, 77
            
            # Находим Y-координату нижней строчки текста
            text_bottom_y = PAGE_H
            
            def visitor_body(text, cm, tm, font_dict, font_size):
                nonlocal text_bottom_y
                if text.strip():
                    # tm[5] — это реальная координата Y текущей базовой линии текста
                    if tm[5] < text_bottom_y:
                        text_bottom_y = tm[5]
            
            new_cover_page.extract_text(visitor_text=visitor_body)
            
            if text_bottom_y == PAGE_H:
                text_bottom_y = PAGE_H / 2
            
            # Вычисляем координату Y для логотипа:
            # Расстояние от text_bottom_y до низа логотипа должно делить этот остаток
            # так, чтобы верхний отступ (до текста) и нижний отступ (до края листа) были равны.
            shift_logo_y = (text_bottom_y - target_logo_h) / 2
            
            # Защитный отступ на случай, если заголовок слишком длинный
            if shift_logo_y < 30:
                shift_logo_y = 50
            
            scale_logo_x = target_logo_w / orig_logo_w
            scale_logo_y = target_logo_h / orig_logo_h
            
            # Центрирование логотипа по горизонтали
            shift_logo_x = (PAGE_W - target_logo_w) / 2
            
            tf_logo = Transformation().scale(sx=scale_logo_x, sy=scale_logo_y).translate(tx=shift_logo_x, ty=shift_logo_y)
            new_cover_page.merge_transformed_page(logo_page, tf_logo, over=True)
        else:
            print(f"Предупреждение: Векторный файл логотипа '{vector_logo_path}' не найден.")
        
        # Вшиваем готовую обложку в начало документа
        writer.insert_page(new_cover_page, index=0)
        
        with open(final_pdf_path, "wb") as f_out:
            writer.write(f_out)
            
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        
    finally:
        if os.path.exists(temp_cover_path):
            os.remove(temp_cover_path)

# --- ЗАПУСК ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python3 replace_pdf_title_page_inhome.py <путь_к_исходному_pdf> <выходной_pdf>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    replace_pdf_first_page(input_file, output_file)
