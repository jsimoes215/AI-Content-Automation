# AI Content Automation - Web Interface

A comprehensive web interface for the AI Content Automation system featuring project management, real-time progress tracking, content library, and analytics.

## Features

- **Project Management**: Create, edit, and manage video content projects
- **Real-time Progress Tracking**: WebSocket-based live updates during content generation
- **Content Library**: Search, filter, and organize reusable scenes with meta-tagging
- **Scene Management**: Browse and reuse saved scenes with performance metrics
- **Analytics Dashboard**: Track content performance across platforms
- **Dark/Light Theme**: Toggle between themes for comfortable viewing
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Recharts** for data visualization
- **Lucide React** for icons

### Backend
- **FastAPI** for REST API
- **SQLite** for local database
- **WebSocket** for real-time updates
- **Python 3.10+**

## Quick Start

### Prerequisites
- Node.js 18+ and pnpm
- Python 3.10+
- pip

### Installation

1. **Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Install Frontend Dependencies**
```bash
cd web-interface
pnpm install
```

### Running the System

**Option 1: Use the startup script (recommended)**
```bash
./start.sh
```

**Option 2: Manual start**

Terminal 1 - Backend:
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - Frontend:
```bash
cd web-interface
pnpm run dev
```

### Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

## Project Structure

```
content-creator/
├── api/                      # Existing AI content generation pipeline
│   ├── scripts/              # Script generation
│   ├── video-generation/     # Video creation
│   ├── audio-processing/     # Audio & TTS
│   ├── content-library/      # Scene storage
│   └── platform-adapters/    # Platform adaptation
├── backend/                  # FastAPI backend
│   ├── database/             # SQLite database
│   │   ├── schema.sql        # Database schema
│   │   └── db.py             # Database operations
│   ├── main.py               # FastAPI application
│   └── requirements.txt      # Python dependencies
├── web-interface/            # React frontend
│   ├── src/
│   │   ├── pages/            # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Projects.tsx
│   │   │   ├── ProjectDetail.tsx
│   │   │   ├── ContentLibrary.tsx
│   │   │   └── Analytics.tsx
│   │   ├── lib/
│   │   │   └── api.ts        # API client
│   │   └── App.tsx           # Main app
│   └── package.json
├── data/                     # Local data storage
│   ├── content_creator.db    # SQLite database
│   └── generated-content/    # Generated media files
└── start.sh                  # Startup script
```

## Database Schema

The SQLite database includes these main tables:

- **projects** - User content creation projects
- **scripts** - Generated scripts with scenes
- **scenes** - Individual video scenes
- **generated_content** - Generated media files
- **content_library** - Reusable scenes with tags
- **generation_jobs** - Background job tracking
- **performance_metrics** - Content analytics
- **analytics** - Aggregated performance data

## API Endpoints

### Projects
- `POST /api/projects` - Create new project
- `GET /api/projects` - List all projects
- `GET /api/projects/{id}` - Get project details
- `DELETE /api/projects/{id}` - Delete project

### Scripts
- `POST /api/scripts/generate` - Generate script from idea
- `GET /api/scripts/{id}` - Get script details

### Content Library
- `POST /api/library/search` - Search library scenes
- `POST /api/library/add` - Add scene to library

### Analytics
- `GET /api/analytics/overview` - Get dashboard analytics
- `GET /api/analytics/projects/{id}` - Get project analytics

### WebSocket
- `WS /ws` - Real-time progress updates

## Development

### Frontend Development
```bash
cd web-interface
pnpm run dev      # Start development server
pnpm run build    # Build for production
pnpm run preview  # Preview production build
```

### Backend Development
```bash
cd backend
python -m uvicorn main:app --reload  # Auto-reload on changes
```

### Database Management
```bash
cd backend
python -c "from database.db import init_database; init_database()"
```

## Features in Detail

### 1. Dashboard
- Overview statistics
- Recent projects
- Quick access to key features
- Real-time updates

### 2. Projects
- Create new projects with video ideas
- Search and filter projects
- Project status tracking
- Delete projects

### 3. Project Detail
- View project information
- Generate scripts
- Monitor generation progress
- View analytics
- Real-time WebSocket updates

### 4. Content Library
- Browse reusable scenes
- Search by tags
- Filter by category
- View performance metrics
- Reuse scenes in projects

### 5. Analytics
- Performance charts
- Platform comparisons
- Engagement metrics
- Project status breakdown

## Deployment

### Production Build

1. **Build Frontend**
```bash
cd web-interface
pnpm run build
```

2. **Run Backend in Production**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

3. **Serve Frontend**
Use a web server like nginx to serve the `web-interface/dist` directory.

### Environment Variables

Create `.env` file in `web-interface/`:
```
VITE_API_URL=http://your-backend-url
VITE_WS_URL=ws://your-backend-url/ws
```

## Troubleshooting

### Backend won't start
- Ensure Python 3.10+ is installed
- Install dependencies: `pip install -r backend/requirements.txt`
- Check port 8000 is available

### Frontend won't start
- Ensure Node.js 18+ and pnpm are installed
- Install dependencies: `cd web-interface && pnpm install`
- Check port 5173 is available

### WebSocket connection fails
- Ensure backend is running
- Check WebSocket URL in `.env`
- Verify firewall settings

### Database errors
- Delete `data/content_creator.db` and restart to recreate
- Check file permissions

## License

MIT

## Support

For issues and questions, please check the documentation or create an issue in the repository.
