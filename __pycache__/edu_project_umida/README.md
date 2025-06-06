# edu_project_umida

## Overview
This project is a Telegram bot designed for educational purposes. It allows administrators and owners to manage courses, lessons, and user roles within a structured environment.

## Project Structure
```
edu_project_umida
├── src
│   ├── main.py          # Main entry point for the Telegram bot
│   ├── owner_menu.py    # Contains the implementation of the owner command menu
│   └── __init__.py      # Marks the directory as a Python package
├── config.py            # Configuration settings for the bot
├── db.py                # Database interaction functions
├── requirements.txt      # List of dependencies
└── README.md            # Documentation for the project
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd edu_project_umida
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration
Before running the bot, you need to set up the configuration file (`config.py`) with your bot token, owner ID, and admin IDs. 

Example configuration:
```python
BOT_TOKEN = 'your_bot_token_here'
OWNER_ID = your_owner_id_here
ADMIN_IDS = [list_of_admin_ids]
```

## Usage
To start the bot, run the following command:
```
python src/main.py
```

## Features
- Owner command menu for managing users and courses.
- Admin functionalities for course and lesson management.
- User role management to control access and permissions.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.