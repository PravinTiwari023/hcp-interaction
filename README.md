# HCP Interaction Management System

## Project Overview
A comprehensive Healthcare Professional (HCP) interaction management system designed for pharmaceutical and medical device sales representatives. The system combines AI-powered conversation capabilities with robust data management to streamline the logging, editing, and analysis of healthcare professional interactions.

## Tech Stack

### Frontend
- **React 18** - Modern UI framework
- **Redux Toolkit** - State management
- **CSS3** - Styling and responsive design
- **JavaScript ES6+** - Modern JavaScript features

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Primary database
- **LangGraph** - AI agent workflow management
- **Groq API** - LLM integration for natural language processing

### AI & ML
- **LangChain** - LLM application framework
- **Groq LLM** - Natural language understanding
- **Custom AI Agent** - Specialized HCP interaction processing

## Directory Structure

```
D:\01 Pravin work\
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints.py       # REST API endpoints
│   │   ├── core/
│   │   │   └── config.py             # Configuration management
│   │   ├── db/
│   │   │   ├── database.py           # Database connection
│   │   │   ├── models.py             # SQLAlchemy models
│   │   │   └── schemas.py            # Pydantic schemas
│   │   └── langgraph_agent/
│   │       ├── agent.py              # AI agent workflow
│   │       └── tools.py              # AI agent tools
│   ├── requirements.txt               # Python dependencies
│   └── start_backend.py              # Backend startup script
└── frontend/
    ├── src/
    │   ├── App.js                     # Main React application
    │   ├── index.js                   # React entry point
    │   ├── app/
    │   │   └── store.js              # Redux store configuration
    │   ├── components/
    │   │   └── hcp/
    │   │       ├── AIAssistantChat.js        # AI chat interface
    │   │       ├── AIAssistantChat.css       # Chat styling
    │   │       ├── HCPInteractionForm.js     # Main interaction form
    │   │       └── HCPInteractionForm.css    # Form styling
    │   ├── features/
    │   │   └── interactions/
    │   │       └── interactionsSlice.js      # Redux slice
    │   ├── pages/
    │   │   ├── LogInteractionPage.js         # Main page component
    │   │   └── LogInteractionPage.css        # Page styling
    │   ├── services/
    │   │   └── api.js                # API service layer
    │   └── reportWebVitals.js        # Performance monitoring
    ├── package.json                   # Node.js dependencies
    └── public/
        └── index.html                 # HTML template
```

## Database Schema

### SQL Table: Interactions

```sql
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    hcp_name VARCHAR(255) NOT NULL,
    interaction_date DATE NOT NULL,
    interaction_time VARCHAR(20),
    interaction_type VARCHAR(50) NOT NULL,
    attendees TEXT,
    summary TEXT,
    key_discussion_points TEXT,
    materials_shared TEXT,
    samples_distributed TEXT,
    sentiment VARCHAR(20) DEFAULT 'Neutral',
    follow_up_actions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_interactions_hcp_name ON interactions(hcp_name);
CREATE INDEX idx_interactions_date ON interactions(interaction_date);
CREATE INDEX idx_interactions_type ON interactions(interaction_type);
CREATE INDEX idx_interactions_sentiment ON interactions(sentiment);
```

## Frontend Architecture

### Components Structure

#### 1. AIAssistantChat.js
- **Purpose**: AI-powered chat interface for interaction logging
- **Features**:
  - Command prefix system ("-" for tasks, regular for conversation)
  - Real-time message display with auto-scroll
  - Form field updates via PUT commands
  - Error handling and loading states
  - Natural language processing integration

#### 2. HCPInteractionForm.js
- **Purpose**: Main form for logging HCP interactions
- **Features**:
  - Embedded AI chat assistant
  - Form validation and submission
  - Real-time field updates from AI
  - Voice input integration
  - Comprehensive interaction data capture

#### 3. LogInteractionPage.js
- **Purpose**: Main page layout and component orchestration
- **Features**:
  - Page-level state management
  - Component integration
  - Responsive design layout

### API Integration

#### API Service Layer (api.js)
```javascript
const API_BASE_URL = 'http://localhost:8000';

// Core API functions
- logInteraction(interactionData)     // POST /interactions/log
- updateInteraction(id, data)         // PUT /interactions/{id}  
- getInteractionsForHCP(hcpName)      // GET /interactions/hcp/{hcp_name}
- chatWithAgent(message)              // POST /chat
```

### Redux State Management

#### InteractionsSlice.js
- **State Structure**:
  ```javascript
  {
    interactions: [],
    chatResponse: null,
    status: 'idle',
    error: null
  }
  ```
- **Async Actions**:
  - `logInteractionAsync` - Log new interactions
  - `updateInteractionAsync` - Update existing interactions
  - `getInteractionsForHCPAsync` - Retrieve interaction history
  - `chatWithAgentAsync` - Chat with AI agent

### Frontend Features

#### Command System
- **Chat Mode**: Normal conversation without prefix
- **Task Mode**: Commands with "-" prefix for actions
- **Examples**:
  - `"hello"` → Conversational response
  - `"-Show me history for Dr. Smith"` → Execute task

#### Real-time Updates
- Form field updates via AI commands
- Auto-scroll chat messages
- Loading states and error handling
- Visual feedback for successful operations

## Backend Architecture

### FastAPI Application

#### Main Application (main.py)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router

app = FastAPI(title="HCP Interaction Management API")

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
```

#### REST API Endpoints (endpoints.py)
```python
# Core endpoints
POST   /interactions/log              # Log new interaction
PUT    /interactions/{interaction_id}  # Update existing interaction
GET    /interactions/hcp/{hcp_name}   # Get interactions for HCP
POST   /chat                          # Chat with AI agent
```

### Database Layer

#### Models (models.py)
```python
class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String, nullable=False, index=True)
    interaction_date = Column(Date, nullable=False)
    interaction_time = Column(String)
    interaction_type = Column(String, nullable=False)
    attendees = Column(Text)
    summary = Column(Text)
    key_discussion_points = Column(Text)
    materials_shared = Column(Text)
    samples_distributed = Column(Text)
    sentiment = Column(String, default="Neutral")
    follow_up_actions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

#### Schemas (schemas.py)
```python
# Pydantic models for request/response validation
class InteractionCreate(BaseModel):
    hcp_name: str
    interaction_date: date
    interaction_time: Optional[str] = None
    interaction_type: str
    # ... other fields

class InteractionUpdate(BaseModel):
    hcp_name: Optional[str] = None
    interaction_date: Optional[date] = None
    # ... all fields optional for updates

class Interaction(InteractionCreate):
    id: int
    created_at: datetime
    updated_at: datetime
```

### AI Agent System

#### LangGraph Agent (agent.py)

##### Command Routing System
```python
def determine_intent_and_route(user_input: str) -> dict:
    """
    Routes user input to appropriate tools based on command prefix:
    - Without '-': General conversation
    - With '-': Task execution
    """
    if user_input.startswith("-"):
        return _route_task_command(user_input[1:].strip())
    else:
        return {"tool": "general_conversation", "params": {"user_input": user_input}}
```

##### Conversational AI Features
- Natural language understanding
- Context-aware responses
- Task command parsing
- Error handling and validation

#### AI Agent Tools (tools.py)

##### Core Tools Available
1. **log_interaction** - Log new HCP interactions with LLM entity extraction
2. **edit_interaction** - Edit interactions by ID
3. **edit_interaction_by_name** - Edit interactions by HCP name
4. **update_form_field** - Real-time form field updates
5. **get_interaction_history** - Retrieve interaction history
6. **generate_sales_insights** - AI-powered sales analysis

##### Tool Implementation Example
```python
@tool
def log_interaction(raw_interaction_text: str) -> str:
    """
    Log new HCP interaction with AI-powered entity extraction
    and automatic field population.
    """
    # Extract entities using LLM
    entities = extract_entities_and_summarize(raw_interaction_text)
    
    # Create interaction record
    interaction = Interaction(
        hcp_name=entities.get("hcp_name", "Unknown"),
        interaction_date=parse_date_flexibly(entities.get("interaction_date", "today")),
        interaction_type=entities.get("interaction_type", "Meeting"),
        summary=entities.get("summary", ""),
        sentiment=entities.get("sentiment", "Neutral"),
        # ... other fields
    )
    
    # Save to database
    db.add(interaction)
    db.commit()
    
    return f"✅ Successfully logged interaction with {interaction.hcp_name}"
```

### LLM Integration

#### Groq API Configuration
```python
from langchain_groq import ChatGroq

llm = ChatGroq(
    temperature=0.1,
    model_name="gemma2-9b-it",
    groq_api_key=settings.groq_api_key
)
```

#### Entity Extraction
- Automatic HCP name detection
- Date and time parsing
- Sentiment analysis
- Key discussion points extraction
- Material and sample tracking

## Frontend-Backend Integration

### API Communication Flow

#### 1. Chat Integration
```javascript
// Frontend sends chat message
const response = await dispatch(chatWithAgentAsync(message));

// Backend processes through LangGraph agent
@app.post("/chat")
async def chat_with_agent(request: ChatRequest):
    response = process_user_input(request.message)
    return {"response": response}
```

#### 2. Form Updates
```javascript
// AI can update form fields in real-time
const handleFormUpdate = (field, value) => {
    setFormData(prev => ({
        ...prev,
        [field]: value
    }));
};
```

#### 3. Data Flow
```
User Input → Frontend → API → LangGraph Agent → Tools → Database → Response → Frontend → UI Update
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### State Synchronization
- Redux manages frontend state
- API calls update backend database
- Real-time updates via chat interface
- Form state synced with AI responses

## Key Features

### 1. AI-Powered Interaction Logging
- Natural language input processing
- Automatic entity extraction
- Intelligent field population
- Sentiment analysis

### 2. Dual Command System
- Conversational mode for general chat
- Task mode with "-" prefix for commands
- Context-aware responses
- Error handling and validation

### 3. Real-time Form Updates
- AI can update form fields directly
- PUT command system for field updates
- Visual feedback for changes
- Form validation and submission

### 4. Interaction Management
- CRUD operations for interactions
- Search by HCP name
- History tracking
- Bulk operations support

### 5. Sales Insights
- AI-powered analysis
- Relationship tracking
- Performance metrics
- Trend analysis

## Deployment Considerations

### Backend Requirements
- Python 3.8+
- PostgreSQL database
- Groq API key for LLM access
- Environment variables for configuration

### Frontend Requirements
- Node.js 16+
- React 18 compatible browser
- CORS-enabled backend connection

### Environment Setup
```bash
# Backend
cd backend
pip install -r requirements.txt
python start_backend.py

# Frontend
cd frontend
npm install
npm start
```

## Security Features

### API Security
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy
- Error handling and logging
- CORS configuration

### Data Protection
- No sensitive data logging
- Secure database connections
- Environment-based configuration
- API key management

## Performance Optimization

### Frontend
- Component optimization with React hooks
- Redux state management
- Lazy loading capabilities
- Efficient re-rendering

### Backend
- Database indexing
- Async operations with FastAPI
- Connection pooling
- Caching strategies

## Future Enhancements

### Planned Features
- User authentication system
- Multi-tenant support
- Advanced analytics dashboard
- Mobile application
- Export/import functionality
- Integration with CRM systems

### Technical Improvements
- Microservices architecture
- Container deployment
- API versioning
- Performance monitoring
- Automated testing suite

---

This HCP Interaction Management System provides a comprehensive solution for pharmaceutical and medical device sales representatives to efficiently manage their healthcare professional interactions with the power of AI assistance.