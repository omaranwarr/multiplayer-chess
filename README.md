# 🎮 Multiplayer Chess Web Application

A full-stack real-time multiplayer chess application built with Django and React. Features instant move synchronization, WebSocket-based real-time updates, and a modern single-page application (SPA) architecture.

## ✨ Features

- **🔐 User Authentication** - Secure registration and login system
- **👥 Multiplayer Chess** - Play against other users online in real-time
- **⚡ Real-time Updates** - WebSocket connections for instant move synchronization
- **🎯 Challenge System** - Send and accept game challenges with other players
- **📊 Game History** - View all your completed and resigned games
- **🎲 Solo Play Mode** - Practice against yourself without logging in
- **🔄 Live Game State** - Automatic board updates without page refresh
- **🏁 Game Outcomes** - Track wins, losses, draws, and resignations

## 🛠️ Tech Stack

### Backend
- **Django 4.2.25** - Python web framework
- **Django REST Framework 3.14.0** - RESTful API development
- **Django Channels 4.0.0** - WebSocket support for real-time features
- **Daphne 4.1.2** - ASGI server for Django Channels
- **python-chess 1.999** - Chess game logic and validation
- **WhiteNoise 6.6.0** - Static file serving in production
- **SQLite** - Database for game state and user data

### Frontend
- **React 18.2.0** - UI library
- **React Router DOM 6.20.0** - Client-side routing
- **Vite 5.0.8** - Build tool and dev server
- **Axios 1.6.2** - HTTP client for API requests
- **WebSocket API** - Real-time bidirectional communication

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

## 🏗️ Architecture

This project uses a **Client-Side Rendered (CSR) Single-Page Application (SPA)** architecture:

- **Frontend**: React SPA with client-side routing (no page reloads)
- **Backend**: Django REST API serving JSON responses
- **Real-time**: Django Channels WebSocket connections
- **Communication**: REST API for data operations, WebSockets for live updates

### Architecture Flow

```
┌─────────────────────────────────────┐
│      React Frontend (Browser)       │
│  ┌──────────┐  ┌─────────────────┐  │
│  │Components│  │  WebSocket     │  │
│  │  State   │◄─┤  Connection    │  │
│  └────┬─────┘  └────────┬────────┘  │
└───────┼─────────────────┼───────────┘
        │                 │
        │ HTTP/JSON       │ WebSocket
        ▼                 ▼
┌─────────────────────────────────────┐
│    Django Backend (ASGI/Daphne)    │
│  ┌──────────┐  ┌─────────────────┐ │
│  │ REST API │  │  Channels       │ │
│  │ Endpoints│  │  WebSocket      │ │
│  └────┬─────┘  └────────┬────────┘ │
│       │                 │          │
│  ┌────┴─────────────────┴─────┐   │
│  │    Django Models (SQLite)  │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn
- Docker (optional, for containerized deployment)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd project4
   ```

2. **Set up the backend**
   ```bash
   cd chess-app
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser  # Optional: for admin access
   ```

3. **Set up the frontend**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Run the development servers**

   **Terminal 1 - Django backend:**
   ```bash
   cd chess-app
   python manage.py runserver
   ```
   Backend runs on `http://localhost:8000`

   **Terminal 2 - React frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend runs on `http://localhost:8080`

5. **Access the application**
   - Open `http://localhost:8080` in your browser
   - The Vite dev server proxies API requests to Django

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Or build and run manually**
   ```bash
   docker build -t chess-app .
   docker run -p 8000:8000 \
     -e SECRET_KEY=your-secret-key \
     -e DEBUG=False \
     -e ALLOWED_HOSTS=localhost,127.0.0.1 \
     chess-app
   ```

3. **Access the application**
   - Open `http://localhost:8000` in your browser

## 📖 Usage

### For Registered Users

1. **Register/Login**: Create an account or log in with existing credentials
2. **View Lobby**: See available players and pending challenges
3. **Challenge Players**: Click "Challenge" next to an available player
4. **Accept Challenges**: Accept incoming challenges from other players
5. **Play Games**: Make moves by clicking pieces and destination squares
6. **View History**: Check your game history from the lobby

### For Guests

1. **Solo Play**: Click "Solo Play" in the navigation to practice
2. **Switch Sides**: Toggle between playing as white or black
3. **Reset Game**: Start a new game anytime

## 📁 Project Structure

```
project4/
├── chess-app/                 # Django backend
│   ├── chess_game/           # Main application
│   │   ├── models.py         # Database models (Game, Challenge, Move)
│   │   ├── api_views.py      # REST API endpoints
│   │   ├── api_urls.py       # API URL routing
│   │   ├── consumers.py      # WebSocket consumers
│   │   ├── serializers.py    # DRF serializers
│   │   └── routing.py        # WebSocket routing
│   ├── chess_project/        # Django project settings
│   │   ├── settings.py       # Configuration
│   │   ├── asgi.py          # ASGI application
│   │   └── urls.py          # Main URL routing
│   ├── requirements.txt     # Python dependencies
│   └── manage.py            # Django management script
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Game.jsx    # Active game component
│   │   │   ├── Lobby.jsx   # Main lobby
│   │   │   ├── Login.jsx   # Authentication
│   │   │   └── ChessBoard.jsx # Chess board UI
│   │   ├── services/       # API and WebSocket services
│   │   │   ├── api.js      # Axios API client
│   │   │   └── websocket.js # WebSocket manager
│   │   └── App.jsx         # Main React app
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite configuration
├── Dockerfile              # Multi-stage Docker build
└── docker-compose.yml      # Docker Compose configuration
```

## 🔌 API Endpoints

### Authentication
- `POST /api/register/` - User registration
- `POST /api/login/` - User login
- `POST /api/logout/` - User logout
- `GET /api/user/` - Get current user info

### Users
- `GET /api/users/available/` - Get available players
- `GET /api/users/me/` - Get current user details

### Games
- `GET /api/games/` - List user's games
- `GET /api/games/{id}/` - Get game details
- `GET /api/games/{id}/board_state/` - Get current board state
- `POST /api/games/{id}/move/` - Make a move
- `POST /api/games/{id}/resign/` - Resign from game
- `GET /api/games/history/` - Get game history
- `GET /api/games/active/` - Get active game (if any)
- `GET /api/solo/play/` - Start solo play game

### Challenges
- `POST /api/challenges/` - Create a challenge
- `POST /api/challenges/{id}/accept/` - Accept a challenge
- `POST /api/challenges/{id}/decline/` - Decline a challenge
- `GET /api/challenges/pending/` - Get pending challenges

### WebSocket Endpoints
- `ws://host/ws/lobby/` - Lobby updates (players, challenges, history)
- `ws://host/ws/game/{game_id}/` - Game-specific updates (moves, state)

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# CORS & CSRF
CORS_ALLOWED_ORIGINS=http://localhost:8080,http://localhost:8000
CSRF_TRUSTED_ORIGINS=http://localhost:8080,http://localhost:8000

# HTTPS (for production)
USE_HTTPS=True  # Set to True in production with SSL
```

### Production Deployment

For production deployment:

1. Set `DEBUG=False`
2. Configure `ALLOWED_HOSTS` with your domain
3. Set a strong `SECRET_KEY`
4. Configure `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`
5. Set up SSL/HTTPS and enable `USE_HTTPS=True`
6. Use a production ASGI server (Daphne, Uvicorn, etc.)
7. Configure a reverse proxy (Nginx, Apache) if needed

## 🧪 Development

### Running Tests
```bash
cd chess-app
python manage.py test
```

### Creating Migrations
```bash
cd chess-app
python manage.py makemigrations
python manage.py migrate
```

### Building Frontend for Production
```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/` and are automatically copied to Django's static files during Docker build.

## 🐳 Docker Details

The Dockerfile uses a multi-stage build:

1. **Frontend Stage**: Builds React app with Vite
2. **Backend Stage**: Sets up Python environment and copies built frontend

The built React app is served as static files through Django using WhiteNoise.

## 📝 License

This project is part of a course assignment. Please refer to your course guidelines for usage and distribution.

## 🤝 Contributing

This is a course project. Contributions and improvements are welcome! Please feel free to submit issues or pull requests.

## 🙏 Acknowledgments

- [python-chess](https://github.com/niklasf/python-chess) - Chess logic library
- [Django Channels](https://channels.readthedocs.io/) - WebSocket support
- [React](https://react.dev/) - UI library
- [Vite](https://vitejs.dev/) - Build tool

---

**Built with ❤️ using Django and React**

