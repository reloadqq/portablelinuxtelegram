# Manager tdata

Менеджер для синхронизации данных сессий Telegram из репозитория GitHub.

> Используется [AyuGram Desktop](https://github.com/AyuGram/AyuGramDesktop) (Flatpak)

## Возможности

- **Upload (ZIP)** — запаковать и загрузить папку на GitHub
- **Download (UNZIP)** — скачать и распаковать сессию из GitHub
- **Launch Session** — запустить локальную сессию
- **Web Launch** — скачать сессию с GitHub, запустить и удалить после закрытия
- **Delete** — удалить файлы из репозитория

## Установка

```bash
git clone https://github.com/reloadqq/portablelinuxtelegram.git
cd portablelinuxtelegram
pip install -r requirements.txt
```

> Используется [AyuGram](https://github.com/AyuGram/AyuGramDesktop) (Flatpak: `flatpak run com.ayugram.desktop`)

## Настройка

Создайте файл `.env`:

```env
GITHUB_TOKEN=your_github_token
REPO_OWNER=your_username
REPO_NAME=your_repo
TARGET_FOLDER=/path/to/tdata
CLIENT_LAUNCH_COMMAND=your_launch_command
TEMP_FOLDER_NAME=tdata
```

### Параметры

| Параметр | Описание | Пример |
|----------|----------|--------|
| `GITHUB_TOKEN` | Personal Access Token с доступом к репозиторию | `ghp_xxx` |
| `REPO_OWNER` | Владелец репозитория | `reloadqq` |
| `REPO_NAME` | Название репозитория | `portablelinuxtelegram` |
| `TARGET_FOLDER` | Папка с сессиями Telegram | `/home/user/.var/app/com.ayugram.desktop/data/AyuGramDesktop` |
| `CLIENT_LAUNCH_COMMAND` | Команда запуска клиента | `flatpak run com.ayugram.desktop` |
| `TEMP_FOLDER_NAME` | Временная папка для запуска | `tdata` |

## Запуск

```bash
./run.sh -env
```

Для указания другого файла конфигурации:

```bash
./run.sh -env custom.env
```

## Разработка

Этот проект был разработан с помощью [opencode](https://opencode.ai) и AI-ассистента.

### Структура

```
.
├── app.py        # Основной код
├── run.sh        # Скрипт запуска
├── .env          # Конфигурация
└── README.md     # Этот файл
```

## Лицензия хз
