# CuraSetu - AI Healthcare Chatbot

A Django-based AI healthcare chatbot that provides information on minor diseases, their generic cures, and traditional Indian (desi) remedies.

## Features

- **User Authentication**: Secure registration and login with password visibility toggle
- **User Profile Management**: Edit profile information and upload profile pictures
- **AI Chatbot**: Powered by Google Gemini API for health advice
- **Chat History**: Persistent chat threads with message history
- **Dark Theme**: Modern UI with frosted glass effects
- **Responsive Design**: Works on desktop and mobile devices

## Technologies Used

- **Backend**: Django 4.2.7
- **Database**: MySQL
- **AI Model**: Google Gemini API
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Authentication**: Django's built-in authentication system

## Setup Instructions

### Prerequisites

1. Python 3.8 or higher
2. MySQL Server
3. MySQL Workbench (optional, for database management)
4. Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   cd ai_healthcare_chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Fill in your database credentials and Gemini API key:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DB_NAME=curasetu_db
   DB_USER=root
   DB_PASSWORD=your-mysql-password
   DB_HOST=localhost
   DB_PORT=3306
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

4. **Set up MySQL database**
   - Create a new database named `curasetu_db` in MySQL
   - Update the database credentials in `.env`

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open your browser and go to `http://127.0.0.1:8000`
   - Register a new account or login with existing credentials

## Usage

1. **Registration**: Create a new account with username, email, and password
2. **Login**: Sign in to access your personal chat interface
3. **Chat**: Describe your symptoms to get AI-powered health advice
4. **Profile**: Update your profile information and upload a profile picture
5. **Chat History**: View and resume previous conversations

## API Integration

The application uses Google Gemini API to provide health advice. The AI is prompted to:
- Identify potential minor illnesses based on symptoms
- Provide generic medical remedies
- Suggest traditional Indian (desi) home remedies
- Format responses in an easy-to-read table format

## Project Structure

```
ai_healthcare_chatbot/
├── accounts/              # User authentication and profile management
├── chatbot/              # AI chatbot functionality
├── curasetu/             # Main Django project settings
├── templates/            # HTML templates
├── static/               # CSS, JavaScript, and images
├── media/                # User uploaded files
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This application is for educational purposes only. The health advice provided should not replace professional medical consultation. Always consult with a qualified healthcare provider for serious health concerns.