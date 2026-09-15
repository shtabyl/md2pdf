import os
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 1. РЕГИСТРАЦИЯ ШРИФТОВ ---
FONTS_DIR = "./fonts"
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

# --- 2. ФУНКЦИЯ ДЛЯ ОТРИСОВКИ ФОНА СТРАНИЦЫ ---
def draw_background(canvas, doc):
    """Окрашивает всю страницу в фирменный сиреневый цвет."""
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#906996"))
    width, height = doc.pagesize
    canvas.rect(0, 0, width, height, fill=True, stroke=False)
    canvas.restoreState()


# --- 3. ГЕНЕРАЦИЯ ДИЗАЙНА ТИТУЛЬНОЙ СТРАНИЦЫ С ДИНАМИЧЕСКИМ ТЕКСТОМ ---
def generate_cover_page(output_temp_path, title_text, subtitle_text):
    """Создает временный PDF-файл, используя текст со старой страницы."""
    doc = SimpleDocTemplate(
        output_temp_path,
        pagesize=letter,
        leftMargin=40, rightMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Стиль для subtitle_text (бывшая "Инструкция для пользователей")
    top_text_style = ParagraphStyle(
        'TopText',
        parent=styles['Normal'],
        fontName='Inter',
        fontSize=14,
        leading=16,
        textColor=colors.white,
        alignment=1
    )
    
    # Стиль для главного большого заголовка title_text
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
    
    # Отрегулированная высота, чтобы заголовок был выше
    story.append(Spacer(1, 180))
    
    # Подставляем subtitle_text (текст ПОСЛЕ последнего переноса строки)
    story.append(Paragraph(subtitle_text, top_text_style))
    
    story.append(Spacer(1, 25))
    
    # Подставляем title_text (текст ДО последнего переноса строки)
    # Заменяем обычные переносы строк \n на HTML-теги <br/>, чтобы ReportLab их понял
    formatted_title = title_text.upper().replace('\n', '<br/>')
    story.append(Paragraph(formatted_title, main_title_style))
    
    story.append(Spacer(1, 340))
    
    # Добавление логотипа
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=90, height=35)
        logo_img.hAlign = 'CENTER'
        story.append(logo_img)
    else:
        print(f"Предупреждение: Файл логотипа '{logo_path}' не найден.")

    doc.build(story, onFirstPage=draw_background)


# --- 4. ОСНОВНАЯ ФУНКЦИЯ ДЛЯ ЗАМЕНЫ СТРАНИЦЫ ---
def replace_pdf_first_page(source_pdf_path, final_pdf_path):
    temp_cover_path = "temp_cover.pdf"
    
    try:
        reader = PdfReader(source_pdf_path)
        writer = PdfWriter()
        
        if len(reader.pages) == 0:
            print("Ошибка: Исходный файл пуст.")
            return
            
        # --- ИЗВЛЕЧЕНИЕ И ПАРСИНГ ТЕКСТА С ПЕРВОЙ СТРАНИЦЫ ---
        first_page = reader.pages[0]
        extracted_text = first_page.extract_text()
        
        # Очищаем текст от лишних пробелов по краям
        extracted_text = extracted_text.strip() if extracted_text else ""
        
        if not extracted_text:
            print("Предупреждение: Не удалось извлечь текст с первой страницы. Будут использованы пустые строки.")
            title_text, subtitle_text = "Без названия", ""
        else:
            title_text, subtitle_text = parse_text(extracted_text)
        
        # Печатаем в консоль для проверки, что получилось достать
        print(f"--- Извлеченный текст ---")
        print(f"До последнего переноса (title_text):\n{title_text}")
        print(f"После последнего переноса (subtitle_text): {subtitle_text}")
        print(f"-------------------------")
        # -----------------------------------------------------

        # Удаляем первую страницу: копируем в новый файл страницы со 2-й (индекс 1) до конца
        for page_num in range(1, len(reader.pages)):
            writer.add_page(reader.pages[page_num])
            
        # Запускаем генерацию обложки, передавая туда динамический текст
        generate_cover_page(temp_cover_path, title_text, subtitle_text.capitalize())
        
        # Открываем созданную обложку и забираем её лист
        cover_reader = PdfReader(temp_cover_path)
        new_cover_page = cover_reader.pages[0]
        
        # Вшиваем новую страницу в самое начало
        writer.insert_page(new_cover_page, index=0)
        
        with open(final_pdf_path, "wb") as f_out:
            writer.write(f_out)
            
        print(f"Успешно! Документ с динамическим текстом сохранен: {final_pdf_path}")
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        
    finally:
        if os.path.exists(temp_cover_path):
            os.remove(temp_cover_path)

# --- ЗАПУСК ---
replace_pdf_first_page("source.pdf", "final_manual.pdf")
