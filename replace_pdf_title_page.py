import os
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader


# --- 1. РЕГИСТРАЦИЯ ШРИФТОВ ---
FONTS_DIR = "./fonts"
pdfmetrics.registerFont(TTFont("Inter", os.path.join(FONTS_DIR, "Inter_18pt-Medium.ttf")))
pdfmetrics.registerFont(TTFont("Inter-SemiBold", os.path.join(FONTS_DIR, "Inter_28pt-SemiBold.ttf")))

def parse_text(text: str) -> tuple[str, str]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return "", ""
    if len(lines) == 1:
        return "", lines[0]
    title = " ".join(lines[:-2])
    subtitle = lines[-2]
    return title, subtitle

# --- 2. ФУНКЦИЯ ДЛЯ ОТРИСОВКИ ФОНА СТРАНИЦЫ И ВОДЯНОГО ЗНАКА ---
def draw_background(canvas, doc):
    """Окрашивает страницу в фирменный цвет и рисует фоновый водяной знак."""
    canvas.saveState()
    width, height = doc.pagesize
    
    # Сплошной фиолетовый фон
    canvas.setFillColor(colors.HexColor("#906996"))
    canvas.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Отрисовка фонового водяного знака в правом нижнем углу
    watermark_path = "watermark4.png"
    if os.path.exists(watermark_path):
        wm_w, wm_h = 224, 340
        
        # Вычисляем позицию X для прижатия к правому краю
        x_pos = width - wm_w
        y_pos = 0
        
        # Полностью отключаем цвет обводки для canvas перед рисованием картинки
        canvas.setStrokeColor(colors.transparent)
        
        # 2. Используем drawImage с флагом сохранения пропорций и точной маской
        canvas.drawImage(
            watermark_path, 
            x_pos, 
            y_pos, 
            width=wm_w, 
            height=wm_h, 
            mask='auto',
            preserveAspectRatio=True,
            anchor='se'
        )
        
    canvas.restoreState()


# --- 3. ГЕНЕРАЦИЯ ДИЗАЙНА ТИТУЛЬНОЙ СТРАНИЦЫ С ДИНАМИЧЕСКИМ ТЕКСТОМ ---
def generate_cover_page(output_temp_path, title_text, subtitle_text):
    """Создает временный PDF-файл в соответствии с новым макетом."""
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
    
    # 1. Добавление логотипа НАВЕРХ страницы
    story.append(Spacer(1, 40)) 
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=90, height=35)
        logo_img.hAlign = 'CENTER'
        story.append(logo_img)
    else:
        print(f"Предупреждение: Файл логотипа '{logo_path}' не найден.")
        story.append(Spacer(1, 35))
        
    # 2. Расстояние между верхним лого и подзаголовком
    story.append(Spacer(1, 160))
    
    # Подставляем subtitle_text
    story.append(Paragraph(subtitle_text, top_text_style))
    
    # Отступ между подзаголовком и главным заголовком
    story.append(Spacer(1, 30))
    
    # Подставляем title_text
    formatted_title = title_text.upper().replace('\n', '<br/>')
    story.append(Paragraph(formatted_title, main_title_style))
    
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
            
        # Извлечение и парсинг текста с первой страницы
        first_page = reader.pages[0]
        extracted_text = first_page.extract_text()
        extracted_text = extracted_text.strip() if extracted_text else ""
        
        if not extracted_text:
            print("Предупреждение: Не удалось извлечь текст. Используются дефолтные строки.")
            title_text, subtitle_text = "Без названия", ""
        else:
            title_text, subtitle_text = parse_text(extracted_text)
        
        # print(f"--- Извлеченный текст ---")
        # print(f"До последнего переноса (title_text):\n{title_text}")
        # print(f"После последнего переноса (subtitle_text): {subtitle_text}")
        # print(f"-------------------------")

        # Перенос страниц со 2-й до конца во writer
        for page_num in range(1, len(reader.pages)):
            writer.add_page(reader.pages[page_num])
            
        # Генерация новой обложки
        generate_cover_page(temp_cover_path, title_text, subtitle_text.capitalize())
        
        # Сшивание
        cover_reader = PdfReader(temp_cover_path)
        new_cover_page = cover_reader.pages[0]
        writer.insert_page(new_cover_page, index=0)
        
        with open(final_pdf_path, "wb") as f_out:
            writer.write(f_out)
            
        print(f"Успешно! Документ с новым дизайном сохранен: {final_pdf_path}")
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        
    finally:
        if os.path.exists(temp_cover_path):
            os.remove(temp_cover_path)

# --- ЗАПУСК ---
replace_pdf_first_page("source.pdf", "final_manual.pdf")
