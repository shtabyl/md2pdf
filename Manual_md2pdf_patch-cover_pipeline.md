# Документация по развертыванию пайплайна md2pdf c кастомными обложками patch-cover

Данный репозиторий содержит инструменты для автоматической конвертации документации из Markdown в PDF с динамической генерацией и заменой титульной страницы на кастомный векторный дизайн (шрифты Inter, векторные логотипы, сплошная заливка фона).

Ниже описана последовательность шагов для воссоздания рабочего окружения на новом компьютере с ОС Linux / WSL.

## Требования к системе

* **ОС:** Linux (Ubuntu/Debian) или WSL (Windows Subsystem for Linux)
* **Инструменты:** Python 3.10+, Pandoc, утилиты `wget`, `unzip`

---

## Пошаговое руководство по развертыванию

### Шаг 1. Клонирование репозитория и структура папок

Склонируйте ваш репозиторий в рабочую директорию. Убедитесь, что структура проекта выглядит следующим образом:

```text
/home/user/projects/md2pdf/
├── replace_pdf_title_page.py               # Основной Python-скрипт модификации PDF
├── patch-cover                             # Bash-скрипт обертки
├── static/
|    ├── logo_vector_full.pdf                     # Векторный логотип для верхней части (из Figma, PDF 1x)
|    └── watermark_vector.pdf                # Векторный водяной знак для правого нижнего угла (из Figma, PDF 1x)
└── fonts/                                   # Папка со шрифтами Inter (TTF)
    ├── Inter_18pt-Regular.ttf
    └── Inter_18pt-SemiBold.ttf
```

*Примечание: Если имя пользователя или путь отличаются от `/home/user/projects/md2pdf/`, скорректируйте их на шагах 4 и 5.*

### Шаг 2. Развертывание виртуального окружения (venv)

Для изоляции зависимостей Python необходимо создать виртуальное окружение строго в папке проекта под именем `md2pdf_venv`:

1. Перейдите в папку проекта:

   ```bash
   cd /home/user/projects/md2pdf/
   ```

2. Создайте виртуальное окружение:

   ```bash
   python3 -m venv md2pdf_venv
   ```

3. Установите необходимые библиотеки напрямую в созданное окружение (активация через `source` не требуется):

   ```bash
   ./md2pdf_venv/bin/pip install --upgrade pip
   ./md2pdf_venv/bin/pip install pypdf reportlab
   ```

### Шаг 3. Подготовка шрифтов

Если в склонированном репозитории отсутствуют TrueType версии шрифтов Inter, скачайте их официальный релиз:

```bash
mkdir -p fonts
wget https://github.com
unzip -j Inter-4.1.zip "extras/ttf/*" -d fonts/
rm Inter-4.1.zip
```

*Убедитесь, что файлы внутри папки `fonts/` называются именно так, как прописано в конфигурации `replace_pdf_title_page.py`.*

### Шаг 4. Настройка глобального скрипта-обертки `patch-cover`

Скрипт `patch-cover` отвечает за вызов Python из изолированного venv, передачу аргументов путей и безопасную перезапись исходного PDF-файла «на месте».

1. Убедитесь, что файл `patch-cover` имеет права на исполнение:

   ```bash
   chmod +x /home/user/projects/md2pdf/patch-cover
   ```

2. Создайте alias в `~/.bashrc` для быстрого вызова скрипта:

    ```bash
    nano ~/.bashrc
    alias patch-cover='/home/user/projects/md2pdf/patch-cover'
    ```

3. Альтернатива алиасу: сделайте команду доступной глобально во всей системе WSL, скопировав ее в локальный бинарный каталог:

   ```bash
   sudo cp /home/user/projects/md2pdf/patch-cover /usr/local/bin/patch-cover
   ```

### Шаг 5. Интеграция пайплайна в профиль Bash

Чтобы объединить генерацию через Pandoc и автоматическую модификацию обложки в единую команду, необходимо обновить переменные окружения пользователя.

1. Откройте конфигурационный файл вашего терминала:

   ```bash
   nano ~/.bashrc
   ```

2. Добавьте в самый конец файла alias для обложки и новую функцию `md2pdf-pc()`:

   ```bash
   # Псевдоним для ручного вызова патча обложки
   alias patch-cover="/home/user/projects/md2pdf/patch-cover"

   # Единый пайплайн: Компиляция Pandoc -> Автоматический патч титульной страницы
   md2pdf-pc() {
       # \$1 - имя файла конфигурации TOC в папке manual-tocs
       # \$2 - имя выходного .pdf файла
       local t_dir="/home/user/docs/docs-config/pandoc-templates"

       echo "[1/2] Запуск компиляции Pandoc..."
       pandoc -o "\$2" \
       -d "\${t_dir}/config.yaml" \
       -d "\${t_dir}/manual-tocs/\$1" \
       --resource-path=.:/home/user/docs/docs-man/manual \
       --pdf-engine-opt=--shell-escape \
       --standalone \
       --file-scope
       
       local pandoc_status=\$?

       if [ \$pandoc_status -eq 0 ]; then
           echo "[2/2] Pandoc успешно завершил работу. Запуск патча обложки..."
           patch-cover "\$2"
       else
           echo "[Ошибка] Сборка Pandoc завершилась с ошибкой. Накатка обложки отменена."
           return \$pandoc_status
       fi

       shift 2
       "\$@"
   }
   ```

3. Сохраните изменения (`Ctrl+O`, `Enter`, `Ctrl+X`) и примените их к текущей сессии терминала:

   ```bash
   source ~/.bashrc
   ```

---

## Проверка работы

Перейдите в любую рабочую директорию и запустите компиляцию:

```bash
md2pdf-pc pad-admin.yaml document.pdf
```

**Ожидаемый результат:**

1. Pandoc соберет базовый документ `document.pdf`.
2. Автоматически включится скрипт `patch-cover`.
3. Из `document.pdf` извлечется текст первой страницы (разделится по предпоследнему переносу на Title и Subtitle).
4. Первая страница удалится, сгенерируется новая фирменная фиолетовая обложка, на которую сверху наложатся векторный логотип `logo_vector_full.pdf` и водяной знак `watermark_vector.pdf`.
5. Файл `document.pdf` обновится «на месте» без создания дубликатов.
