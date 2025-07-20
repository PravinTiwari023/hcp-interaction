# Project Plan: AI-First CRM HCP Module

## 1. Project Basic Details

This project aims to develop a module for a Customer Relationship Management (CRM) system specifically designed for the healthcare industry. The core feature is a "Log Interaction Screen" that allows field representatives to log their interactions with Healthcare Professionals (HCPs). This can be done through a traditional form or a conversational AI interface, making the process faster and more intuitive. An AI agent will assist in processing and managing this data.

## 2. Tech Stack

*   **Frontend:** React with Redux for state management.
*   **Backend:** Python with FastAPI.
*   **AI Agent Framework:** LangGraph.
*   **LLM:** Groq API with `gemma2-9b-it` model.
*   **Database:** PostgreSQL.
*   **Font:** Google Inter.

## 3. Feasibility

The project is highly feasible. The chosen technologies are modern, well-documented, and integrate well with each other.
*   **React & FastAPI:** A standard and powerful combination for web applications.
*   **LangGraph:** Provides the necessary structure for building a stateful, multi-tool AI agent.
*   **Groq LLM:** Offers a fast and capable model for natural language understanding and generation tasks.
*   **PostgreSQL:** A robust and scalable database suitable for storing structured interaction data.

The main challenge will be designing the conversational flow and ensuring the AI agent accurately interprets user input and uses its tools correctly.

## 4. Directory Structure

```
/ai-crm-hcp
|-- /frontend
|   |-- /src
|   |   |-- /app
|   |   |   |-- store.js            # Redux store setup
|   |   |-- /components
|   |   |   |-- /common             # Reusable UI components (Button, Input, etc.)
|   |   |   |-- /hcp
|   |   |   |   |-- HCPInteractionForm.js
|   |   |   |   |-- HCPChatInterface.js
|   |   |-- /features
|   |   |   |-- /interactions
|   |   |   |   |-- interactionsSlice.js # Redux slice for interactions
|   |   |-- /pages
|   |   |   |-- LogInteractionPage.js
|   |   |-- /services
|   |   |   |-- api.js              # API integration service
|   |   |-- App.js
|   |   |-- index.js
|   |-- package.json
|
|-- /backend
|   |-- /app
|   |   |-- /api
|   |   |   |-- /v1
|   |   |   |   |-- endpoints.py    # FastAPI routes
|   |   |-- /core
|   |   |   |-- config.py         # Configuration settings
|   |   |-- /db
|   |   |   |-- models.py         # SQLAlchemy models
|   |   |   |-- database.py       # Database session management
|   |   |-- /langgraph_agent
|   |   |   |-- agent.py          # LangGraph agent definition
|   |   |   |-- tools.py          # Agent tools (Log, Edit, etc.)
|   |   |-- main.py               # FastAPI app entry point
|   |-- requirements.txt
|
|-- plan.md
```

## 5. SQL Data Model and ER Diagram

### SQL Data Model (PostgreSQL)

```sql
CREATE TABLE hcp (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    specialty VARCHAR(255),
    institution VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    hcp_id INTEGER NOT NULL REFERENCES hcp(id),
    interaction_date DATE NOT NULL,
    interaction_type VARCHAR(100), -- e.g., 'Call', 'Visit', 'Email'
    summary TEXT,
    key_discussion_points TEXT,
    sentiment VARCHAR(50), -- e.g., 'Positive', 'Neutral', 'Negative'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```



## 6. Backend Development Plan

### FastAPI Routes (`/backend/app/api/v1/endpoints.py`)

*   **`POST /api/v1/interactions/log`**: Receives data from the frontend (either form data or conversational text). If conversational, it invokes the LangGraph agent.
*   **`PUT /api/v1/interactions/{interaction_id}`**: Updates an existing interaction record.
*   **`GET /api/v1/interactions/{hcp_id}`**: Retrieves all interactions for a specific HCP.
*   **`POST /api/v1/chat`**: The main endpoint for the conversational interface. It will manage the conversation state and route requests to the LangGraph agent.
*   **`GET /api/v1/hcp/search`**: Searches for HCPs by name or specialty.

### LangGraph Agent Implementation Plan

The LangGraph agent is the core of the AI functionality. It will be a stateful agent that manages a conversation with the user to log or retrieve information about HCP interactions.

**Agent's Role:**
The agent's primary role is to assist the field representative in managing HCP interaction data efficiently. It acts as a conversational assistant that can understand natural language commands to perform specific sales-related tasks. It will orchestrate the use of various "tools" to fulfill user requests, maintain conversation state, and handle the flow of information between the user, the LLM, and the database.

**Agent Tools (`/backend/app/langgraph_agent/tools.py`):**

1.  **`log_interaction`**:
    *   **Description:** This is the primary tool for creating a new interaction record. It can be triggered by a user's conversational input (e.g., "I just met with Dr. Smith to discuss our new drug").
    *   **Mechanism:**
        1.  It takes the conversational text as input.
        2.  It uses the `gemma2-9b-it` LLM to perform entity extraction (HCP name, date, location) and summarization. The prompt will instruct the LLM to identify key entities and create a concise summary of the discussion.
        3.  The tool then structures this extracted information into a JSON object corresponding to the `interactions` database model.
        4.  Finally, it saves this structured data to the PostgreSQL database.
        5.  It returns a confirmation message to the user, like "Successfully logged your interaction with Dr. Smith."

2.  **`edit_interaction`**:
    *   **Description:** Allows users to modify an existing interaction log using natural language.
    *   **Mechanism:**
        1.  The user might say, "Update my last interaction with Dr. Smith, the meeting was today, not yesterday."
        2.  The agent first needs to identify the target interaction. It may ask clarifying questions if the reference is ambiguous ("I see two interactions with Dr. Smith. Which one do you mean?").
        3.  Once identified, the tool fetches the existing interaction data from the database.
        4.  It then uses the LLM to understand the requested modification and applies the change to the fetched data.
        5.  The updated record is written back to the database.
        6.  A confirmation is sent to the user.

3.  **`search_hcp`**:
    *   **Description:** Finds HCPs in the database.
    *   **Mechanism:** Takes a name or specialty as input (e.g., "Find Dr. Evelyn Reed" or "show me all cardiologists"). It queries the `hcp` table and returns a list of matching professionals.

4.  **`get_interaction_history`**:
    *   **Description:** Retrieves the interaction history for a specific HCP.
    *   **Mechanism:** The user would ask, "What's my history with Dr. Smith?". The tool queries the `interactions` table (joining with `hcp`) and returns a formatted summary of past interactions, ordered by date.

5.  **`summarize_hcp_activity`**:
    *   **Description:** Provides a high-level summary of all interactions with an HCP over a specified period.
    *   **Mechanism:** The user might ask, "Give me a summary of my talks with Dr. Smith this quarter." The tool fetches all relevant interactions from the database and uses the LLM to generate a consolidated summary, highlighting key discussion points, outcomes, and sentiment trends.

## 7. Frontend Development Plan

### React Components (`/frontend/src/components/`)

*   **`LogInteractionPage.js`**: The main container page holding the two interaction methods. It will have a toggle to switch between the form and chat views.
*   **`HCPInteractionForm.js`**: A controlled React form with fields for HCP name (autocomplete search), date, interaction type, and notes.
*   **`HCPChatInterface.js`**: A chat window component. It will display the conversation history with the agent and have an input field for sending new messages.
*   **`Button.js`, `Input.js`, `Select.js`**: Reusable, styled UI components.
*   **`Header.js`**: Top navigation bar.

### Frontend Routes

*   **`/` or `/dashboard`**: Main dashboard (out of scope for this task).
*   **`/log-interaction`**: The primary route for the "Log Interaction Screen."

### API Integration (`/frontend/src/services/api.js`)

*   Use `axios` or `fetch` to create a service layer for all backend communication.
*   Functions will correspond to the FastAPI routes (`logInteraction`, `editInteraction`, `searchHCP`, etc.).
*   Redux Toolkit Query or `createAsyncThunk` will be used to manage API calls, loading states, and caching within the Redux store.

### Performance Optimization

*   **Code Splitting:** Use React.lazy() to load the `HCPInteractionForm` and `HCPChatInterface` components on demand.
*   **Debouncing:** Apply debouncing to the HCP search input to avoid excessive API calls while the user is typing.
*   **Memoization:** Use `React.memo` for presentational components to prevent unnecessary re-renders.
*   **State Management:** Keep the Redux state normalized and use selectors to efficiently derive data.