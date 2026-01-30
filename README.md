# Stateful AI Agents — Memory, Context & Personalization at Scale

## 📋 Overview
This project showcases an advanced conversational agent built with Chainlit and LlamaIndex, featuring sophisticated memory management capabilities. The system leverages multiple memory strategies (Semantic, Summary, and User Preference) to maintain context-aware conversations and provide personalized interactions. It uses PostgreSQL with pgVector for efficient vector storage and retrieval, supporting both OpenAI and Anthropic models.

## 🌟 Key Features
- 🧠 **Multi-Strategy Memory System**: Semantic search, conversation summarization, and user preference tracking
- 💬 **Advanced Conversational AI**: Powered by OpenAI GPT-4/4.1 and Anthropic Claude models
- 📊 **PostgreSQL + pgVector**: Efficient vector storage and similarity search
- 🎨 **Interactive UI**: Built with Chainlit for seamless user experience
- 🔧 **Configurable Settings**: Dynamic model selection and memory strategy configuration
- 🐳 **Docker-Ready**: Complete containerized setup with Docker Compose
- 📈 **pgAdmin Integration**: Database management and monitoring interface

## 📁 Project Structure
```
├── .dockerignore
├── .gitignore
├── app.py                           # Main Chainlit application
├── chainlit.md                      # Welcome page content
├── docker-compose.yml               # Docker orchestration
├── Dockerfile                       # Application container
├── pgVector.Dockerfile              # PostgreSQL with pgVector extension
├── init.sql                         # Database initialization script
├── requirements.txt                 # Python dependencies
├── README.md
├── examples/
│   ├── fiteness_health_tracking.md  # Fitness health tracking use case
│   ├── tech_career_growth.md        # Tech career growth use case
│   └── travel_booking_automation.md # Travel booking automation use case
├── public/
│   ├── custom.css                   # Custom styling
│   └── theme.json                   # UI theme configuration
└── src/
    ├── config/
    │   ├── settings.py              # Application configuration
    ├── core/
    │   ├── agent.py                 # Main agent implementation
    │   ├── memory_config.py         # Memory configuration
    │   └── session_manager.py       # Session management
    ├── prompts/
    │   ├── agent.py                 # Agent system prompts
    │   ├── memory_retrieval.py      # Memory retrieval prompts
    │   ├── semantic.py              # Semantic search prompts
    │   ├── summary.py               # Summarization prompts
    │   └── user_preference.py       # User preference prompts
    ├── storage/
    │   ├── enums.py                 # Memory strategy enums
    │   ├── models.py                # Database models
    │   └── repository.py            # Data access layer
    ├── strategies/
    │   ├── base.py                  # Base memory strategy
    │   ├── semantic.py              # Semantic memory strategy
    │   ├── summary.py               # Summary memory strategy
    │   └── user_preference.py       # User preference strategy
    └── tools/
        ├── __init__.py
        └── memory_tools.py          # Memory management tools
```

## 🐳 Docker Setup

### ✅ Clone the repository
```bash
git clone https://github.com/taiconnect/taiconnect-3-workshop
cd taiconnect-3-workshop
```

## ⚙️ Prerequisites

### 1. API Keys Required
- **OpenAI API Key**: Get it from [OpenAI Platform](https://platform.openai.com/api-keys)
  - Supports: GPT-4.1, GPT-4.1-mini, GPT-4o, GPT-4o-mini
- **Anthropic API Key**: Get it from [Anthropic Console](https://console.anthropic.com/)
  - Supports: Claude Sonnet 4.5, Claude Haiku 4.5, Claude 4 Sonnet

### 2. System Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- Minimum 4GB RAM
- 10GB available disk space

### ✅ Build and Run the Containers

For **Windows**, **Mac**, and **Linux**, run:
```bash
docker compose up --build
```

Or to run in detached mode:
```bash
docker compose up -d --build
```

This command:
- Builds the Docker images for the application and PostgreSQL
- Initializes the database with pgVector extension
- Creates necessary tables and indexes
- Starts the Chainlit application
- Launches pgAdmin for database management

## 🌐 Accessing the Application

### Main Services
- **Chainlit Application**: [http://localhost:8000](http://localhost:8000)
  - Interactive AI chat interface
  - Memory strategy configuration
  - Model selection and settings

- **pgAdmin (Database Management)**: [http://localhost:5051](http://localhost:5051)
  - Login with credentials from `.env` file
  - View and manage database tables
  - Monitor vector embeddings and memory storage

### Default Ports
- Application: `8000`
- PostgreSQL: `5532` (mapped from container's 5432)
- pgAdmin: `5051`

Got it 👍 — here is the same section formatted as **pure Markdown**, ready to paste directly into your `README.md`:

---

## 🔁 Code Workflow Diagram (Interactive)

This repository includes an interactive workflow diagram that explains the overall code flow.

* File: `code_flow.dio`
* Created using **draw.io**
* Designed to work with the **Draw.io VS Code Extension** and VS Code **Code Link** feature

When opened correctly, you can:

* View the flow diagram alongside the source code
* Click on any diagram box to navigate directly to the corresponding file and line in the code

---

### 📦 Prerequisites

1. Install **Draw.io Integration** extension in VS Code
   Extension ID: `hediet.vscode-drawio`

2. Enable **Code Link** feature

   * Open VS Code
   * Look at the status bar (bottom)
   * Enable **Code Link** (click it if disabled)

---

### 📂 How to Use

1. Open the repository in VS Code
2. Open `code_flow.dio`
3. Open the relevant source folder/file
4. Arrange editor panes side-by-side:

   * Left: `code_flow.dio`
   * Right: Source code
5. Click any box inside the diagram → VS Code navigates to the linked file and line

### 💡 Recommended Workflow

Keeping the diagram and code open side-by-side provides a fast way to:

* Understand system architecture
* Trace execution paths

## 🎯 Using the Application

### 1. First Time Setup
1. Access the application at [http://localhost:8000](http://localhost:8000)
2. Configure your settings:
   - **Model Selection**: Choose between OpenAI or Anthropic models
   - **Memory Strategies**: Select one or more:
     - `SEMANTIC`: Context-aware semantic search
     - `SUMMARY`: Conversation summarization
     - `USER_PREFERENCE`: Track and remember user preferences
   - **Exchange History**: Set how many past exchanges to include

### 2. Memory Strategies Explained

**Semantic Memory**
- Stores conversations as vector embeddings
- Retrieves contextually relevant past exchanges
- Best for: Long-term context retention

**Summary Memory**
- Creates concise summaries of conversation history
- Reduces token usage while maintaining context
- Best for: Long conversations and cost optimization

**User Preference Memory**
- Tracks user-specific preferences and patterns
- Personalizes responses based on user history
- Best for: Personalized experiences and user profiling

### 3. Chat Features
- Type messages naturally in the chat interface
- The agent has access to memory tools for:
  - Retrieving past conversations
  - Storing important information
  - Accessing user preferences
- Previous conversations are automatically saved
- Resume conversations from the chat history panel

## 🛠️ Troubleshooting

### Common Issues

**Port Already in Use**
If ports `8000`, `5532`, or `5051` are occupied, modify `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change host port (left side)
```

**Database Connection Errors**
1. Ensure PostgreSQL container is running:
   ```bash
   docker ps | grep tai_postgres
   ```
2. Check database logs:
   ```bash
   docker logs tai_postgres
   ```
3. Verify `.env` file has correct credentials

**API Key Errors**
- Verify API keys are correctly set in `.env`
- Check for extra spaces or quotes
- Ensure keys have proper permissions and credits

**Container Build Failures**
1. Clean Docker cache:
   ```bash
   docker system prune -a
   ```
2. Rebuild from scratch:
   ```bash
   docker compose down -v
   docker compose up --build
   ```

**Memory/Performance Issues**
- Increase Docker memory allocation (Docker Desktop Settings)
- Monitor resource usage:
  ```bash
  docker stats
  ```

## 🔧 Development

### Running Locally (Without Docker)

1. Install PostgreSQL with pgVector extension
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize database:
   ```bash
   psql -U your_user -d your_db -f init.sql
   ```
5. Run the application:
   ```bash
   chainlit run app.py -w --port 8000
   ```

### Project Configuration

Edit `src/config/settings.py` to modify:
- Available AI models
- Default memory strategies
- Database connection parameters
- Token limits and model settings

## 📊 Database Schema

The application uses several key tables:
- `User`: User profiles and metadata
- `Thread`: Conversation threads
- `Step`: Individual conversation steps
- `Element`: Attachments and media
- `Feedback`: User feedback on responses
- Custom tables for memory storage with vector embeddings

View the complete schema in `init.sql`.

## 📖 Additional Notes

### Memory Management
- Vector embeddings are stored in PostgreSQL with pgVector
- Automatic cleanup of old conversations (configurable)
- Efficient similarity search using HNSW indexes

### Customization
- Modify prompts in `src/prompts/` directory
- Add new memory strategies in `src/strategies/`
- Customize UI theme in `public/theme.json`
- Update welcome message in `chainlit.md`

### Cost Optimization
- Use summary strategy to reduce token usage
- Select appropriate models based on task complexity
- Monitor API usage through provider dashboards
- Limit exchange history to necessary amount

## 🤝 Contributing
Contributions are welcome! Please ensure:
- Code follows project structure
- Add tests for new features
- Update documentation
- Follow existing coding standards

## 📝 License
```
GNU GENERAL PUBLIC LICENSE WITH NON-COMMERCIAL RESTRICTION
Version 1.0, TSI Technologies Pvt. Ltd., 2025
```

This project is licensed under a modified GNU GPL that restricts commercial use. See the LICENSE file for full details.

---

## 🚀 Quick Start Commands

```bash
# Clone and setup
git clone https://github.com/taiconnect/taiconnect-3-workshop
cd taiconnect-3-workshop

# Start application
docker compose up -d --build

# View logs
docker compose logs -f

# Stop application
docker compose down

# Stop and remove volumes (⚠️ deletes data)
docker compose down -v
```

---

**Happy Coding! 🚀**

For questions, issues, or support, please contact TSI Technologies Pvt. Ltd.
