# 🚀 Gemini Clone Backend

A comprehensive FastAPI backend for the Gemini Clone application with authentication, chat functionality, and admin dashboard.

## 📁 Project Structure

```
Gemini-backend/
├── 📄 main.py              # FastAPI application entry point
├── 📄 start.py             # Startup script with database initialization
├── 📄 config.py            # Configuration settings and environment variables
├── 📄 database.py          # Database connection and session management
├── 📄 models.py            # SQLAlchemy database models
├── 📄 schemas.py           # Pydantic request/response schemas
├── 📄 auth.py              # Authentication utilities and JWT handling
├── 📄 gemini_service.py    # Google Gemini AI integration service
├── 📄 init_db.py           # Database initialization script
├── 📄 requirements.txt     # Python dependencies
├── 📄 test_login.py        # Login functionality test script
├── 📄 test_chat.py         # Chat API test script
├── 📄 gemini_clone.db      # SQLite database file
├── 📁 uploads/             # File upload storage directory
├── 📁 __pycache__/         # Python bytecode cache
├── 📄 .gitignore           # Git ignore rules
└── 📄 LICENSE              # Project license
```

## ✨ Features

### 🔐 Authentication System
- **JWT-based authentication** with secure token management
- **User registration and login** with email validation
- **Role-based access control** (Admin/User roles)
- **Password hashing** using bcrypt
- **Session management** with token expiration

### 💬 Chat Functionality
- **Google Gemini AI integration** for text and image analysis
- **Real-time chat responses** with conversation context
- **Image upload and analysis** with base64 encoding
- **Chat history storage** in database
- **Message persistence** across sessions

### 👨‍💼 Admin Dashboard
- **User management** with CRUD operations
- **System statistics** and analytics
- **Activity monitoring** and user tracking
- **Role management** and permissions
- **Pagination and search** functionality

### 🗄️ Database Management
- **SQLite/PostgreSQL support** with automatic switching
- **Automatic database creation** and table initialization
- **Migration support** with SQLAlchemy
- **Data validation** and integrity constraints

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager
- (Optional) PostgreSQL for production

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start the server:**
```bash
python start.py
```

The server will automatically:
- Create the database and tables
- Set up the admin user
- Start the FastAPI server on http://localhost:8000

### Default Admin Credentials
- **Email:** admin@geminiclone.com
- **Password:** admin123

## 📚 API Documentation

Once the server is running, visit:
- **Interactive API Docs:** http://localhost:8000/docs
- **ReDoc Documentation:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## 🔧 Configuration

### Environment Variables
Create a `.env` file to customize settings:

```env
# Database Configuration
USE_SQLITE=true
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=gemini_clone_db

# Admin Configuration
ADMIN_EMAIL=your-admin@example.com
ADMIN_PASSWORD=your-secure-password

# Google Gemini API
GOOGLE_API_KEY=your-gemini-api-key

# JWT Configuration
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=720
```

### Database Options

**SQLite (Default - Easier Setup):**
- Automatically creates `gemini_clone.db` file
- No additional setup required
- Perfect for development and testing

**PostgreSQL (Production):**
- Set `USE_SQLITE=false` in config.py
- Ensure PostgreSQL is running
- Update connection credentials

## 🧪 Testing

### Test Scripts

**Test Login Functionality:**
```bash
python test_login.py
```

**Test Chat API:**
```bash
python test_chat.py
```

### Manual Testing
1. Start the backend: `python start.py`
2. Visit http://localhost:8000/docs
3. Use the interactive API documentation
4. Test with the frontend application

## 📊 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info
- `PUT /auth/me` - Update user profile

### Chat
- `POST /chat` - Send message to AI
- `GET /chats` - Get user's chat history
- `POST /chats` - Create new chat
- `GET /chats/{id}` - Get specific chat with messages

### Admin
- `GET /admin/stats` - System statistics
- `GET /admin/users` - List all users (paginated)
- `PUT /admin/users/{id}` - Update user
- `DELETE /admin/users/{id}` - Delete user

### File Upload
- `POST /upload` - Upload files (images)

## 🔒 Security Features

- **JWT token authentication** with expiration
- **Password hashing** with bcrypt
- **Input validation** with Pydantic
- **SQL injection prevention** with SQLAlchemy ORM
- **CORS protection** with configurable origins
- **File upload validation** with size and type limits

## 🚀 Deployment

### Development
```bash
python start.py
```

### Production
```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000

# Using gunicorn (recommended)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Run the test scripts to verify functionality
3. Check the logs for error messages
4. Ensure all dependencies are installed correctly

---

**Happy Coding! 🎉**