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


# --- 2. ФУНКЦИЯ ДЛЯ ОТРИСОВКИ ФОНА СТРАНИЦЫ ---
def draw_background(canvas, doc):
    """Окрашивает всю страницу в фирменный сиреневый цвет."""
    canvas.saveState()
    # Цвет фона с картинки (приглушенный сиреневый / лавандовый)
    canvas.setFillColor(colors.HexColor("#8A6F93"))
    # Закрашиваем весь лист (размеры берутся из объекта doc)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)
    canvas.restoreState()


# --- 3. ГЕНЕРАЦИЯ ДИЗАЙНА ТИТУЛЬНОЙ СТРАНИЦЫ ---
def generate_cover_page(output_temp_path):
    """Создает временный PDF-файл, повторяющий дизайн с картинки."""
    # Задаем размеры и убираем поля, так как фон должен быть во весь экран
    # Но для текста внутри сделаем отступы по 40 пунктов
    doc = SimpleDocTemplate(
        output_temp_path,
        pagesize=letter,
        leftMargin=40, rightMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Стиль для верхнего мелкого текста
    top_text_style = ParagraphStyle(
        'TopText',
        parent=styles['Normal'],
        fontName='Inter',
        fontSize=14,
        leading=16,
        textColor=colors.white,
        alignment=1 # По центру
    )
    
    # Стиль для главного большого заголовка
    main_title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Normal'],
        fontName='Inter-SemiBold',
        fontSize=18,
        leading=24,
        textColor=colors.white,
        alignment=1 # По центру
    )
    
    story = []
    
    # Сдвигаем текст примерно к центру страницы по вертикали
    story.append(Spacer(1, 180))
    
    # Маленький надзаголовок
    story.append(Paragraph("Инструкция для пользователей", top_text_style))
    
    # Небольшой отступ между строками текста
    story.append(Spacer(1, 25))
    
    # Главный заголовок (капсом, как на фото)
    title_text = "ПОДКЛЮЧЕНИЕ БЕСПРОВОДНОЙ<br/>ТЕРМОГОЛОВКИ РАДИАТОРА ОТОПЛЕНИЯ<br/>CLEVERHOME ZIGBEE"
    story.append(Paragraph(title_text, main_title_style))
    
    # Отступ вниз до логотипа (подбирается экспериментально под высоту страницы)
    story.append(Spacer(1, 340))
    
    # Добавление логотипа в самый низ
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        # Подберите ширину и высоту вашего логотипа в пунктах
        logo_img = Image(logo_path, width=90, height=35)
        logo_img.hAlign = 'CENTER'
        story.append(logo_img)
    else:
        print(f"Предупреждение: Файл логотипа '{logo_path}' не найден. Страница будет сгенерирована без него.")

    # Собираем документ, применяя функцию draw_background для покраски фона
    doc.build(story, onFirstPage=draw_background)


# --- 4. ОСНОВНАЯ ФУНКЦИЯ ДЛЯ ЗАМЕНЫ СТРАНИЦЫ ---
def replace_pdf_first_page(source_pdf_path, final_pdf_path):
    """Считывает исходный файл, удаляет 1-ю страницу и вшивает новую с заданным дизайном."""
    temp_cover_path = "temp_cover.pdf"
    
    try:
        # Проверяем и читаем исходный файл
        reader = PdfReader(source_pdf_path)
        writer = PdfWriter()
        
        if len(reader.pages) == 0:
            print("Ошибка: Исходный файл пуст.")
            return
            
        # Удаляем первую страницу: копируем в новый файл страницы со 2-й (индекс 1) до конца
        for page_num in range(1, len(reader.pages)):
            writer.add_page(reader.pages[page_num])
            
        # Запускаем генерацию нашей красивой страницы во временный файл
        generate_cover_page(temp_cover_path)
        
        # Открываем созданную обложку через pypdf и забираем ее единственный лист
        cover_reader = PdfReader(temp_cover_path)
        new_cover_page = cover_reader.pages[0]
        
        # Вшиваем новую страницу в самое начало (индекс 0)
        writer.insert_page(new_cover_page, index=0)
        
        # Сохраняем и закрываем итоговый файл
        with open(final_pdf_path, "wb") as f_out:
            writer.write(f_out)
            
        print(f"Успешно! Документ с новым дизайном сохранен: {final_pdf_path}")
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        
    finally:
        # Чистим за собой временную обложку
        if os.path.exists(temp_cover_path):
            os.remove(temp_cover_path)

# --- ЗАПУСК ---
replace_pdf_first_page("source.pdf", "final_manual.pdf")
