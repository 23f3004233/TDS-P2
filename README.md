# LLM Analysis Quiz Solver

An automated quiz-solving system that uses multiple AI agents to solve data analysis challenges involving various file types, web scraping, data processing, and visualization.

## Features

- **Multi-Agent Architecture**: Coordinated system with Fetcher, Analyzer, Verifier, and Executor agents
- **JavaScript Rendering**: Uses Playwright for dynamic page rendering
- **Multi-Modal Support**: Handles PDF, images, audio, video, CSV, Excel, and more
- **AI-Powered Analysis**: Uses GPT-4o, Claude Sonnet 4, and Gemini models via AIPipe
- **Verification Loop**: Self-correcting system with verification and refinement
- **Robust Error Handling**: Fallback models and retry logic
- **Time Management**: 3-minute deadline tracking with buffer for submission

## Architecture

```
┌─────────────────┐
│  FastAPI Server │
└────────┬────────┘
         │
    ┌────▼─────────┐
    │ Orchestrator │  (Coordinates workflow)
    └──┬─────┬─────┘
       │     │
   ┌───▼──┐ │  ┌────────┐
   │Fetch │ └──►Analyzer │ (Primary Solver)
   └──────┘    └───┬────┘
                   │
             ┌─────▼────┐
             │ Verifier │ (Quality Check)
             └──────────┘
```

## Setup

### Prerequisites

- Python 3.11+
- AIPipe Token
- Git

### Environment Variables

Create a `.env` file:

```bash
AIPIPE_TOKEN=your_token_here
EMAIL=your_email@example.com
QUIZ_SECRET=your_secret_string
GITHUB_REPO=https://github.com/yourusername/repo

PRIMARY_MODEL=openai/gpt-4o
VERIFIER_MODEL=anthropic/claude-sonnet-4
ENABLE_VERIFICATION=true
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run server
python -m uvicorn app.main:app --reload
```

### Docker Build

```bash
# Build image
docker build -t quiz-solver .

# Run container
docker run -p 8000:8000 --env-file .env quiz-solver
```

### Railway Deployment

1. Connect GitHub repository to Railway
2. Add environment variables in Railway dashboard
3. Deploy automatically from main branch

## API Endpoints

### POST /quiz

Accept quiz requests:

```json
{
  "email": "student@example.com",
  "secret": "your_secret",
  "url": "https://example.com/quiz-834"
}
```

Response:

```json
{
  "status": "processing",
  "message": "Quiz processing started successfully"
}
```

### GET /

Service information

### GET /health

Health check endpoint

## How It Works

1. **Receive Request**: FastAPI receives POST with quiz URL
2. **Fetch Content**: Playwright renders JavaScript page and downloads files
3. **Process Files**: Specialized processors handle PDF, images, data, audio, video
4. **Analyze**: AI model analyzes question and generates solution
5. **Verify** (optional): Second AI reviews solution and provides feedback
6. **Refine**: If feedback received, analyzer refines solution
7. **Execute**: Python code executed if generated
8. **Submit**: Answer submitted to quiz system
9. **Chain**: If next URL received, repeat process

## Supported File Types

- **Documents**: PDF, TXT, JSON
- **Data**: CSV, Excel (XLSX, XLS)
- **Images**: JPG, PNG, GIF, BMP, WebP
- **Audio**: MP3, WAV, OGG, M4A
- **Video**: MP4, AVI, MOV, MKV
- **Code**: Python scripts

## AI Models Used

### Primary (Analyzer)
- OpenAI GPT-4o (multimodal)
- Google Gemini 2.0 Flash
- Claude Sonnet 4

### Verifier
- Claude Sonnet 4 (reasoning)
- GPT-4o (cross-validation)

## Testing

```bash
# Run tests
python -m pytest tests/

# Test specific module
python -m pytest tests/test_fetcher.py -v
```

### Test with Demo Endpoint

```bash
curl -X POST http://localhost:8000/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "secret": "your_secret",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
```

## Project Structure

```
project/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── models.py            # Pydantic models
│   └── utils/               # Authentication, logging, timer
├── agents/
│   ├── orchestrator.py      # Main coordinator
│   ├── fetcher.py           # Content fetcher
│   ├── analyzer.py          # AI solver
│   ├── verifier.py          # Solution verifier
│   └── executor.py          # Code executor
├── processors/
│   ├── pdf_processor.py     # PDF handling
│   ├── image_processor.py   # Image/OCR
│   ├── audio_processor.py   # Audio transcription
│   ├── video_processor.py   # Video processing
│   ├── data_processor.py    # CSV/Excel analysis
│   └── viz_processor.py     # Visualizations
├── llm/
│   ├── aipipe_client.py     # AIPipe API client
│   ├── prompt_templates.py  # AI prompts
│   └── model_manager.py     # Model selection
├── tests/                   # Test suite
├── Dockerfile               # Container definition
└── requirements.txt         # Dependencies
```

## Performance Considerations

- **Timing**: System tracks 3-minute deadline, reserves 30s for submission
- **Model Selection**: Task-specific model routing for optimal results
- **Verification**: Optional verification can be disabled to save time
- **Retries**: Configurable retry logic for failed submissions
- **Caching**: File processors cache results where applicable

## Troubleshooting

### Common Issues

1. **Playwright Timeout**: Increase `BROWSER_TIMEOUT` in config
2. **Model Errors**: Check AIPipe token and quota
3. **File Processing**: Ensure all system dependencies installed
4. **Code Execution**: Check file permissions in /tmp

### Logs

All operations are logged with timestamps. Check logs for:
- Quiz processing flow
- Model selections and responses
- File processing details
- Answer submissions
- Verification feedback

## License

MIT License - See LICENSE file

## Authors

Student Project for IIT Madras Data Science Program

## Acknowledgments

- AIPipe for LLM API access
- OpenAI, Anthropic, Google for AI models
- Playwright for browser automation