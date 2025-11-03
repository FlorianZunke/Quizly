# 🎯 Quizly

Quizly is a Django + Django REST Framework project that generates multiple-choice quizzes from a video URL. It downloads the video's audio, transcribes it locally using Whisper, sends the transcript to an LLM (Gemini or other configured model) to produce structured quiz data, and stores the quiz and questions in a database.

This README explains how to set up the project, run it on Windows and macOS, and covers important runtime requirements (ffmpeg, Whisper models, API keys, JWT usage, and background-processing considerations).

---

## ✨ Features

- Create a quiz by POSTing a video URL. The backend downloads audio, transcribes it and generates multiple-choice questions.
- JWT authentication (Simple JWT) for protected endpoints.
- List quizzes of the authenticated user.
- CRUD on quizzes with owner-based permissions.
- Questions are stored as nested objects and returned in API responses.

---

## 📁 Repository Layout

- `manage.py` — Django CLI entrypoint  
- `core/` — Django project and settings  
- `quiz_app/` — main app containing models, API and generation utils  
  - `quiz_app/api/serializers.py` — API serializers  
  - `quiz_app/api/views.py` — API views  
  - `quiz_app/api/utils.py` — audio download, transcription and LLM integration  
  - `quiz_app/api/authentication.py` — handle JWTCOOKIES
  - `quiz_app/models.py` — `Quiz` and `Question` models  
- `auth_app/` — authentication / registration API and serializers  
- `requirements.txt` — Python dependencies

---

## 🔧 Requirements

- Python 3.10+  
- pip  
- ffmpeg (required by yt-dlp / Whisper)  
- Internet access for downloading video/audio and calling the LLM API  
- An API key for the Gemini (or other LLM) client used in `quiz_app/api/utils.py`

Notes on external tools:

- `yt-dlp`: used to download the audio track from video URLs.  
- `whisper`: local transcription (the code calls `whisper.load_model("small")` by default).

On Windows, download ffmpeg and add `ffmpeg.exe` to your PATH. On macOS, install ffmpeg with Homebrew: `brew install ffmpeg`.

---

## 🔐 Environment Variables

Create a `.env` file in the project root or set environment variables in your system. Important variables used by the project:

- `API_KEY` — API key for the Gemini (or equivalent) client used in `quiz_app/api/utils.py`.
- `SECRET_KEY` — Django SECRET_KEY (for local development you may set a simple value).

There is a `.env.template` file in the project root that lists all required environment variables with example values. Copy and edit that template to create your actual `.env` file:

- Unix / macOS / WSL:
  ```bash
  cp .env.template .env
  ```
- Windows PowerShell:
  ```powershell
  Copy-Item .env.template .env
  ```

After copying, open `.env` and fill in your API keys and any other values.

Example `.env`:

The project loads `.env` in `quiz_app/api/utils.py` using `python-dotenv`.

---

## 💻 Installation

### Windows

1. Clone the repo and open PowerShell in the project root.  
2. Create and activate a virtual environment:


```powershell
python -m venv env
.\env\Scripts\Activate
```

3. Install dependencies:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Setup database and create admin user:
```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

5. Run the development server:
```powershell
python manage.py runserver
```


### macOS

1. Clone the repo and open Terminal in the project root.
2. Create and activate a virtual environment:
```bash
python3 -m venv env
source env/bin/activate
```

3. Install dependencies:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Install ffmpeg:
```bash
brew install ffmpeg
```

5. Setup database and create admin user:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```


## 🚀 Using the API

### Authentication
The project uses Simple JWT for authentication. Token endpoints are available in `auth_app` (see `auth_app/api/urls.py`). The default `REST_FRAMEWORK` configuration uses JWT authentication.

<!-- Added: CORS / Request headers guidance -->
#### CORS / Required Request Headers
- Server (Django + django-cors-headers) typical settings:
  - CORS_ALLOWED_ORIGINS: ["http://127.0.0.1:5500", "http://localhost:5500"]
  - CORS_ALLOW_CREDENTIALS: True
  - CORS_ALLOW_HEADERS should include: "authorization", "content-type", "x-csrftoken", "x-requested-with"
  - Optional: CSRF_TRUSTED_ORIGINS for cookie-based auth

- Browser client: always send the Authorization header and, when using cookie-based auth, include credentials.
  Example (fetch):
  ```javascript
  fetch('http://127.0.0.1:8000/api/quizzes/', {
    method: 'GET',
    headers: {
      'Authorization': 'Bearer ' + ACCESS_TOKEN, // genau: "Bearer <token>"
      'Content-Type': 'application/json'
    },
    credentials: 'include' // nur nötig, wenn Cookies verwendet werden
  });
  ```

- Important: For "non-simple" requests, browsers send an OPTIONS (preflight) request. The server must respond correctly to OPTIONS requests (returning proper CORS headers), otherwise the client will encounter CORS/401/403 errors.

### Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/api/quizzes/` | Create a new quiz | Required |
| GET | `/api/quizzes/` | List user's quizzes | Required |
| GET | `/api/quizzes/<pk>/` | Get quiz details | Required (owner only) |

### Example Requests

#### Create a Quiz
```bash
curl -X POST http://127.0.0.1:8000/api/quizzes/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=..."}'
```

### Response Format

#### Success (HTTP 201)
```json
{
    "id": 1,
    "video_url": "https://...",
    "title": "Quiz Title",
    "description": "Quiz Description",
    "timestamps": [...],
    "questions": [
        {
            "text": "Question text",
            "options": [...],
            "correct_answer": "..."
        }
    ]
}
```

#### Error (HTTP 400)
```json
{
    "error": "Error message",
    "detail": "Detailed error description"
}
```

### Important Notes
- The `url` field is write-only when creating a quiz
- The response includes `video_url` (read-only), `title`, `description`, `timestamps` and nested `questions`
- All endpoints require a valid JWT token in the `Authorization: Bearer <token>` header

## 📝 Implementation Notes and Caveats

### Generation Pipeline
- Currently runs synchronously (download → transcribe → LLM)
- Can block HTTP requests for extended periods
- Recommended: Move to background worker (Celery + Redis) for production
- Should return HTTP 202 Accepted immediately in production

### Resource Management
- Temporary audio files are automatically deleted after transcription
- Whisper transcription is compute-intensive
- LLM API calls require adequate quotas and network connectivity
- Monitor system resources during operation

### Data Integrity
- Uses `generate_quiz_data_from_video` helper for validation
- Quiz creation wrapped in `transaction.atomic()` block
- Prevents partial/incomplete quiz insertions
- Validates LLM output before saving


## ❗ Troubleshooting

### Common Issues and Solutions

#### Authentication Problems (HTTP 401)
- **Problem**: Unauthorized access errors
- **Solution**: 
  - Verify JWT token is included in header: `Authorization: Bearer <ACCESS_TOKEN>`
  - Check token expiration
  - Consider configuring cookie-based JWT auth if needed
  - CORS-specific checks:
    - Ensure the browser request sends the Authorization header (inspect Network tab → Request Headers).
    - Verify server returns Access-Control-Allow-Origin (must match origin) and Access-Control-Allow-Credentials if credentials are used.
    - Ensure OPTIONS preflight returns HTTP 200 with proper CORS headers (Access-Control-Allow-Methods, Access-Control-Allow-Headers).
    - If using cookies, confirm CSRF token handling and add your frontend origin to CSRF_TRUSTED_ORIGINS.

#### Quiz Creation Errors (HTTP 400)
- **Problem**: Bad Request during quiz creation
- **Solution**: Check server logs for specific errors:
  - Video download failures
  - Empty transcriptions
  - Invalid LLM responses
  - Malformed video URLs

#### FFmpeg Issues
- **Problem**: FFmpeg-related errors
- **Solution**:
  - Verify ffmpeg is installed
  - Ensure ffmpeg is in system PATH
  - Windows: Check `ffmpeg.exe` location
  - macOS: Verify Homebrew installation

## 🔜 Next Steps / Improvements

### Performance Optimization
- [ ] Implement background processing with Celery + Redis
- [ ] Add job status monitoring endpoint
- [ ] Implement rate limiting system
- [ ] Add per-user generation quotas

### Monitoring & Reliability
- [ ] Enhanced error logging system
- [ ] Pipeline monitoring dashboard
- [ ] Automated health checks
- [ ] System resource monitoring

### Testing & Documentation
- [ ] Add unit tests for quiz generation
- [ ] Integration tests for API endpoints
- [ ] Pipeline component tests
- [ ] Create README-dev.md with:
  - Local Whisper setup guide
  - LLM integration testing
  - Sample transcripts
  - Debugging procedures

#### How to run tests

Run the Django test suite from the project root.

PowerShell (Windows):
```powershell
# from project root
python manage.py test
```

macOS / Linux (bash):
```bash
python manage.py test
```

Run a single app's tests:
```bash
python manage.py test quiz_app
python manage.py test auth_app
```

Add `-v 2` for more verbose output, or use `--failfast` to stop on first failure.