# 📚 AI Homework Reviewer

An AI-powered homework reviewing system built with FastAPI, LangChain, and LangGraph. This project automates the process of checking students' homework submissions, evaluates them based on technical requirements, code style, and other quality metrics, and stores the results in Excel files mapped to each student.

## 🚀 Features

### Homework Repository Integration
- **Structured repository of submissions:**
  ```
  homework/
  ├── lecture1_task_1/
  │   ├── Ivanov/
  │   ├── Petrov/
  │   └── Sidorov/
  ├── lecture1_task_2/
  │   ├── Ivanov/
  │   ├── Petrov/
  │   └── Sidorov/
  └── ...
  ```

### Automated Review with AI Agent
- Uses LangChain + LangGraph to orchestrate evaluation of each task
- Checks functionality, technical requirements, coding style, documentation, and more
- Percentage scoring & detailed comments for each student

### Excel Report Export
- Looks up the student by surname in the Excel file
- Stores percentage & feedback under the correct row
- Supports both Excel (.xlsx) and CSV export formats

### FastAPI API Layer
- RESTful endpoints to trigger reviews per lecture
- Individual student review capabilities
- Repository validation and management
- Health checks and monitoring

## 🏗️ Project Architecture

```
fastapi-app/
├── app/
│   ├── api/              # FastAPI endpoints
│   ├── agents/           # LangGraph agents & workflow definitions
│   ├── chains/           # LangChain chains (prompt templates, tools)
│   ├── core/             # Config, logging, settings
│   ├── services/         # File I/O, Excel handling, repo management
│   ├── models/           # Pydantic schemas for API requests/responses
│   └── main.py           # FastAPI entrypoint
├── homework/             # Homework submissions repository
├── results/              # Output Excel files with reviews
├── requirements.txt
└── README.md
```

## ⚙️ Tech Stack

- **FastAPI** → REST API layer
- **LangChain** → LLM orchestration, prompt management
- **LangGraph** → Agent workflows (review process per task)
- **Pandas / openpyxl** → Excel export
- **Pydantic** → Data validation
- **OpenAI** → AI-powered code review

## 🔄 Workflow

1. **Upload or sync homework repository** with student submissions
2. **Trigger review** for a specific lecture via API
3. **AI agent** iterates over all tasks in the lecture and analyzes code with multiple criteria:
   - ✅ Technical correctness
   - 📏 Code style & readability
   - 📚 Documentation & comments
   - ⚡ Performance (basic checks)
4. **Assigns a percentage** & generates detailed feedback
5. **Results stored in Excel** with student lookup by surname

## 📌 API Usage Examples

### Trigger Student Review
```bash
POST /api/v1/review/student
Content-Type: application/json

{
  "surname": "Ivanov",
  "lecture_number": 1
}
```

**Example Response:**
```json
{
  "surname": "Ivanov",
  "lecture_number": 1,
  "average_score": 87,
  "total_tasks": 2,
  "details": [
    {
      "task": "lecture1_task_1",
      "score": 90,
      "comments": "Good solution, variable names could be clearer.",
      "technical_correctness": 95,
      "code_style": 85,
      "documentation": 90,
      "performance": 85
    },
    {
      "task": "lecture1_task_2",
      "score": 84,
      "comments": "Meets requirements but missing edge case handling.",
      "technical_correctness": 80,
      "code_style": 85,
      "documentation": 75,
      "performance": 90
    }
  ],
  "processing_time": 15.2
}
```

### Trigger Lecture Review
```bash
POST /api/v1/review/lecture
Content-Type: application/json

{
  "lecture_number": 1
}
```

### Get Review Results
```bash
GET /api/v1/results/1
```

### Export Results
```bash
GET /api/v1/export/1?format=excel
GET /api/v1/export/1?format=csv
```

## 📊 Output Excel Format

| Surname | Lecture | Task | Score (%) | Comments | Technical Correctness | Code Style | Documentation | Performance | Review Date |
|---------|---------|------|-----------|----------|---------------------|------------|---------------|-------------|------------|
| Ivanov | 1 | lecture1_task_1 | 90 | Good solution, minor naming issue | 95 | 85 | 90 | 85 | 2024-01-15 10:30:00 |
| Ivanov | 1 | lecture1_task_2 | 84 | Missing edge case handling | 80 | 85 | 75 | 90 | 2024-01-15 10:32:00 |
| Petrov | 1 | lecture1_task_1 | 78 | Works but inefficient | 75 | 80 | 70 | 85 | 2024-01-15 10:35:00 |

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- OpenAI API key

### 1. Clone Repository
```bash
git clone <repository-url>
cd ai-homework-reviewer
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Application Settings
DEBUG=false
HOST=0.0.0.0
PORT=8000

# File Paths
HOMEWORK_DIR=homework
RESULTS_DIR=results

# Review Settings
MAX_CONCURRENT_REVIEWS=5
REVIEW_TIMEOUT=300
```

### 5. Set Up Homework Repository
Organize your homework submissions in the following structure:
```
homework/
├── lecture1_task_1/
│   ├── Student1/
│   │   ├── main.py
│   │   └── utils.py
│   ├── Student2/
│   │   └── solution.py
│   └── ...
├── lecture1_task_2/
│   └── ...
└── ...
```

### 6. Run the Application
```bash
# Development mode
uvicorn fastapi-app.app.main:app --reload

# Production mode
uvicorn fastapi-app.app.main:app --host 0.0.0.0 --port 8000
```

### 7. Access the Application
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Configuration Options

### Review Criteria Weights
You can customize the scoring weights in the review criteria:

```python
# Default weights
technical_correctness_weight = 0.4  # 40%
code_style_weight = 0.3            # 30%
documentation_weight = 0.2        # 20%
performance_weight = 0.1          # 10%
```

### Supported Programming Languages
The system supports analysis for:
- Python (.py)
- JavaScript (.js)
- Java (.java)
- C++ (.cpp)
- C (.c)
- And generic analysis for other languages

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API information |
| GET | `/health` | Health check |
| POST | `/api/v1/review/student` | Review individual student |
| POST | `/api/v1/review/lecture` | Review entire lecture |
| GET | `/api/v1/students/{lecture_number}` | Get students in lecture |
| GET | `/api/v1/tasks/{lecture_number}` | Get tasks in lecture |
| GET | `/api/v1/results/{lecture_number}` | Get review results |
| GET | `/api/v1/summary/{lecture_number}` | Get lecture summary |
| GET | `/api/v1/export/{lecture_number}` | Export results |
| POST | `/api/v1/validate` | Validate repository structure |
| POST | `/api/v1/setup/sample/{lecture_number}` | Create sample structure |

## 🧪 Testing the System

### 1. Validate Repository Structure
```bash
curl -X POST http://localhost:8000/api/v1/validate
```

### 2. Create Sample Data (for testing)
```bash
curl -X POST http://localhost:8000/api/v1/setup/sample/1
```

### 3. Review a Student
```bash
curl -X POST http://localhost:8000/api/v1/review/student \
  -H "Content-Type: application/json" \
  -d '{"surname": "Ivanov", "lecture_number": 1}'
```

### 4. Review Entire Lecture
```bash
curl -X POST http://localhost:8000/api/v1/review/lecture \
  -H "Content-Type: application/json" \
  -d '{"lecture_number": 1}'
```

## 🐳 Docker Deployment (Optional)

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "fastapi-app.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t ai-homework-reviewer .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key ai-homework-reviewer
```

## 🔍 Troubleshooting

### Common Issues

1. **OpenAI API Key Not Set**
   - Ensure `OPENAI_API_KEY` is set in your environment or `.env` file
   - Check the API key is valid and has sufficient credits

2. **Repository Structure Issues**
   - Use the `/api/v1/validate` endpoint to check repository structure
   - Ensure homework directories follow the naming convention: `lecture{N}_task_{N}`

3. **Import Errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.8+)

4. **File Permission Issues**
   - Ensure the application has read/write permissions to `homework/` and `results/` directories

### Logging
The application logs important events. Check the console output or log files for detailed error information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Commit your changes: `git commit -m "Add feature"`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT models
- LangChain team for the excellent LLM orchestration framework
- LangGraph team for the workflow management capabilities
- FastAPI team for the modern Python web framework

## 📞 Support

For questions, issues, or contributions, please:
- Open an issue on GitHub
- Check the documentation at `/docs` endpoint
- Review the API examples in this README

---

**Happy Coding! 🎓✨**
