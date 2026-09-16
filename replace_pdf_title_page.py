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

vector_wm_path = os.path.join(SCRIPT_DIR, "watermark_vector.pdf")
vector_logo_path = os.path.join(SCRIPT_DIR, "logo_vector_full.pdf")

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
    canvas.setFillColor(colors.HexColor("#906996"))
    canvas.rect(0, 0, width, height, fill=True, stroke=False)
    canvas.restoreState()


# --- 3. ГЕНЕРАЦИЯ ДИЗАЙНА ТИТУЛЬНОЙ СТРАНИЦЫ (ТОЛЬКО ТЕКСТ И ОТСТУПЫ) ---
def generate_cover_page(output_temp_path, title_text, subtitle_text):
    """Создает временный PDF-файл с текстом и правильными отступами под векторы."""
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
    
    # Резервируем место под верхний логотип с помощью отступов
    story.append(Spacer(1, 40))   # Отступ от верхнего края до логотипа
    story.append(Spacer(1, 35))   # Высота самого логотипа (чтобы текст не наехал)
    story.append(Spacer(1, 140))  # Отступ от логотипа до начала текста
    
    # Подставляем текст
    story.append(Paragraph(subtitle_text, top_text_style))
    story.append(Spacer(1, 30))
    
    formatted_title = title_text.upper().replace('\n', '<br/>')
    story.append(Paragraph(formatted_title, main_title_style))
    
    doc.build(story, onFirstPage=draw_background)


# --- 4. ОСНОВНАЯ ФУНКЦИЯ ДЛЯ ЗАМЕНЫ СТРАНИЦЫ И СШИВАНИЯ С ДВУМЯ ВЕКТОРАМИ ---
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
        
        # Удаляем первую страницу: копируем в новый файл страницы со 2-й до конца
        for page_num in range(1, len(reader.pages)):
            writer.add_page(reader.pages[page_num])
            
        # Генерируем текстовую обложку на фиолетовом фоне
        generate_cover_page(temp_cover_path, title_text, subtitle_text.capitalize())
        
        # Читаем созданную текстовую обложку
        cover_reader = PdfReader(temp_cover_path)
        new_cover_page = cover_reader.pages[0]
        
        # Размеры страницы letter: ширина 612, высота 792 пунктов
        PAGE_W, PAGE_H = 612, 792
        
        # --- 4А. СЛИЯНИЕ С ВЕКТОРНЫМ ВОДЯНЫМ ЗНАКОМ (ПРАВЫЙ НИЖНИЙ УГОЛ) ---
        if os.path.exists(vector_wm_path):
            wm_reader = PdfReader(vector_wm_path)
            wm_page = wm_reader.pages[0]
            
            orig_wm_w = float(wm_page.mediabox.width)
            orig_wm_h = float(wm_page.mediabox.height)
            
            target_wm_w, target_wm_h = 224, 340
            
            scale_wm_x = target_wm_w / orig_wm_w
            scale_wm_y = target_wm_h / orig_wm_h
            
            shift_wm_x = PAGE_W - target_wm_w
            shift_wm_y = 0
            
            tf_wm = Transformation().scale(sx=scale_wm_x, sy=scale_wm_y).translate(tx=shift_wm_x, ty=shift_wm_y)
            new_cover_page.merge_transformed_page(wm_page, tf_wm, over=True)
            print("Векторный водяной знак успешно наложен.")
            
        # --- 4Б. СЛИЯНИЕ С ВЕКТОРНЫМ ЛОГОТИПОМ (СВЕРХУ ПО ЦЕНТРУ) ---
        if os.path.exists(vector_logo_path):
            logo_reader = PdfReader(vector_logo_path)
            logo_page = logo_reader.pages[0]
            
            orig_logo_w = float(logo_page.mediabox.width)
            orig_logo_h = float(logo_page.mediabox.height)
            
            # Желаемые размеры логотипа на листе
            target_logo_w, target_logo_h = 90, 35
            
            scale_logo_x = target_logo_w / orig_logo_w
            scale_logo_y = target_logo_h / orig_logo_h
            
            # Считаем координаты центра: (ШиринаЛиста - ШиринаЛого) / 2
            shift_logo_x = (PAGE_W - target_logo_w) / 2
            # Считаем координату Y сверху: ВысотаЛиста - ВерхнийОтступ(40) - ВысотаЛого(35)
            shift_logo_y = PAGE_H - 40 - target_logo_h
            
            tf_logo = Transformation().scale(sx=scale_logo_x, sy=scale_logo_y).translate(tx=shift_logo_x, ty=shift_logo_y)
            new_cover_page.merge_transformed_page(logo_page, tf_logo, over=True)
        else:
            print(f"Предупреждение: Векторный файл логотипа '{vector_logo_path}' не найден.")
        
        # Вшиваем готовую обложку в начало документа
        writer.insert_page(new_cover_page, index=0)
        
        with open(final_pdf_path, "wb") as f_out:
            writer.write(f_out)
            
        print(f"Успешно! Итоговый документ сохранен: {final_pdf_path}")
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        
    finally:
        if os.path.exists(temp_cover_path):
            os.remove(temp_cover_path)

# --- ЗАПУСК ---
if __name__ == "__main__":
    # Проверяем, передал ли пользователь файлы при запуске
    if len(sys.argv) < 3:
        print("Использование: python3 replace_pdf_title_page.py <путь_к_исходному_pdf> <путь_к_выходному_pdf>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    replace_pdf_first_page(input_file, output_file)
