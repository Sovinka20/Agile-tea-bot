Ваш файл `README.md` уже хорошо структурирован и содержит всю необходимую информацию для понимания и использования проекта. Однако я могу предложить несколько улучшений и дополнений, чтобы сделать его еще более удобным и информативным. Вот обновленная версия:

---

### Agile-tea-bot

**Description:** Telegram bot for educational purposes within the framework of the course "Practical course of an Agile leader".

### Чай-бот Agile

**Описание:** Бот телеграмма для учебных целей в рамках курса "Практический курс Agile-лидера".

---

## Table of Contents

- [Agile-tea-bot](#agile-tea-bot)

  - [Description](#description)
  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [License](#license)

- [Чай-бот Agile](#чай-бот-agile)
  - [Описание](#описание)
  - [Функционал](#функционал)
  - [Установка](#установка)
  - [Использование](#использование)
  - [Вклад](#вклад)
  - [Лицензия](#лицензия)

---

## Agile-tea-bot

### Description

This Telegram bot is designed for educational purposes within the framework of the course "Practical course of an Agile leader". It provides interactive features to help students learn and practice Agile methodologies.

### Features

- Interactive buttons for selecting different topics.
- Displaying content from a PostgreSQL database.
- Saving user data to a PostgreSQL database.
- Handling errors and reconnecting automatically.
- Customizable commands for different Agile practices.
- Support for multiple languages (if applicable).

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/agile-tea-bot.git
   cd agile-tea-bot
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables in a `.env` file:

   ```env
   DATABASE_URL=postgres://username:password@host:port/dbname
   TOKEN=YOUR_TELEGRAM_BOT_TOKEN
   ```

4. Run the database setup script:

   ```bash
   python create_tables.py
   ```

5. Start the bot:
   ```bash
   python bot.py
   ```

### Usage

1. Start a chat with your bot on Telegram.
2. Use the `/new_tea` command to interact with the bot.
3. Select a topic using the provided buttons.
4. The bot will display the content and save your interaction data to the database.

### Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) before getting started.

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Чай-бот Agile

### Описание

Этот бот телеграмма создан для учебных целей в рамках курса "Практический курс Agile-лидера". Он предоставляет интерактивные функции, которые помогают студентам изучать и практиковать Agile-методологии.

### Функционал

- Интерактивные кнопки для выбора различных тем.
- Отображение контента из базы данных PostgreSQL.
- Сохранение данных пользователей в базу данных PostgreSQL.
- Обработка ошибок и автоматическое переподключение.
- Настраиваемые команды для различных Agile-практик.
- Поддержка нескольких языков (если применимо).

### Установка

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/yourusername/agile-tea-bot.git
   cd agile-tea-bot
   ```

2. Установите необходимые зависимости:

   ```bash
   pip install -r requirements.txt
   ```

3. Настройте переменные окружения в файле `.env`:

   ```env
   DATABASE_URL=postgres://username:password@host:port/dbname
   TOKEN=YOUR_TELEGRAM_BOT_TOKEN
   ```

4. Запустите скрипт настройки базы данных:

   ```bash
   python create_tables.py
   ```

5. Запустите бота:
   ```bash
   python bot.py
   ```

### Использование

1. Начните чат с вашим ботом в Telegram.
2. Используйте команду `/new_tea` для взаимодействия с ботом.
3. Выберите тему с помощью предоставленных кнопок.
4. Бот отобразит контент и сохранит данные вашего взаимодействия в базу данных.

### Вклад

Вклад приветствуется! Пожалуйста, прочитайте [рекомендации по вкладу](CONTRIBUTING.md) перед началом работы.

### Лицензия

Этот проект лицензирован под MIT License. Подробности смотрите в файле [LICENSE](LICENSE).

---

### Дополнительные разделы (по желанию)

#### Поддержка

Если у вас возникли вопросы или проблемы, пожалуйста, создайте [issue](https://github.com/yourusername/agile-tea-bot/issues) на GitHub.

#### Благодарности

- Спасибо [название библиотеки/фреймворка] за предоставленные инструменты.
- Спасибо [имя] за вклад в проект.

#### История изменений

Смотрите [CHANGELOG.md](CHANGELOG.md) для подробной информации об изменениях в проекте.

---
