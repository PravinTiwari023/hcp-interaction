from langchain_core.messages import BaseMessage, FunctionMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from typing import Literal, TypedDict, Dict, Any, List, Tuple
from typing_extensions import Annotated
from langgraph.graph.message import add_messages
import json
import re
from datetime import datetime, timedelta

# Import tools
from .tools import (
    log_interaction,
    edit_interaction,
    edit_interaction_by_name,
    update_form_field,
    get_interaction_history,
    generate_sales_insights,
    form_information_tool
)
from ..core.config import settings

class IntelligentAgentState(TypedDict):
    """State for the intelligent AI agent with LLM-based decision making"""
    messages: Annotated[list[BaseMessage], add_messages]
    user_query: str
    query_analysis: Dict[str, Any]
    selected_tool: str
    tool_parameters: Dict[str, Any]
    tool_result: str
    form_data: Dict[str, Any]

class LLMQueryAnalyzer:
    """Uses LLM to analyze user queries and make intelligent tool selection decisions"""
    
    def __init__(self, llm):
        self.llm = llm
        self.tool_descriptions = {
            "log_interaction": {
                "purpose": "Use when user is describing a NEW interaction they had with an HCP (Healthcare Professional)",
                "examples": [
                    "I met with Dr. Smith today",
                    "Had a call with Dr. Johnson about cardiology",
                    "Visited Dr. Brown this morning at the hospital",
                    "Dr. Martinez seemed interested in our new product"
                ]
            },
            "edit_interaction": {
                "purpose": "Use when user wants to MODIFY or UPDATE an existing interaction",
                "examples": [
                    "Update the meeting with Dr. Smith to positive sentiment",
                    "Change the interaction type to call",
                    "Edit the notes for Dr. Johnson's visit",
                    "Modify the sentiment of yesterday's meeting"
                ]
            },
            "get_interaction_history": {
                "purpose": "Use when user wants to SEE PAST interactions or history with an HCP",
                "examples": [
                    "Show me interactions with Dr. Smith",
                    "What's the history with Dr. Johnson?",
                    "Get all meetings with Dr. Brown",
                    "Display past interactions with Dr. Martinez"
                ]
            },
            "generate_sales_insights": {
                "purpose": "Use when user wants ANALYSIS, INSIGHTS, or REPORTS about interactions",
                "examples": [
                    "Analyze my performance this month",
                    "Generate insights for Dr. Smith",
                    "Show me sales analytics",
                    "What are the trends in my interactions?"
                ]
            },
            "form_information_tool": {
                "purpose": "Use when user wants to CHECK or REVIEW current form data",
                "examples": [
                    "What's currently in the form?",
                    "Show me the form summary",
                    "Check the form status",
                    "What information do I have filled in?"
                ]
            },
            "general_conversation": {
                "purpose": "Use when user is asking GENERAL QUESTIONS, seeking EXPLANATIONS, or having CASUAL CONVERSATION not related to specific database tasks",
                "examples": [
                    "How does the HCP module help pharma reps?",
                    "What is customer relationship management?",
                    "How do I improve my sales performance?",
                    "What are best practices for HCP engagement?"
                ]
            }
        }
    
    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        """Use LLM to analyze the user query and determine the best tool to use"""
        
        analysis_prompt = f"""
        You are an AI assistant that helps healthcare sales representatives manage their interactions with Healthcare Professionals (HCPs).

        Analyze this user query and determine which tool would be best to handle it:

        USER QUERY: "{user_query}"

        AVAILABLE TOOLS:
        1. log_interaction - Use when user is describing a NEW interaction they had with an HCP
           Examples: "I met with Dr. Smith today", "Had a call with Dr. Johnson"
        
        2. edit_interaction - Use when user wants to MODIFY/UPDATE an existing interaction
           Examples: "Update the meeting with Dr. Smith", "Change the sentiment to positive"
        
        3. get_interaction_history - Use when user wants to SEE PAST interactions with an HCP
           Examples: "Show me interactions with Dr. Smith", "Get history for Dr. Johnson"
        
        4. generate_sales_insights - Use when user wants ANALYSIS/INSIGHTS/REPORTS
           Examples: "Analyze my performance", "Generate insights for Dr. Smith"
        
        5. form_information_tool - Use when user wants to CHECK/REVIEW current form data
           Examples: "What's in the form?", "Show form summary", "Check form status"

        6. general_conversation - Use when user is asking GENERAL QUESTIONS, seeking EXPLANATIONS, or having CASUAL CONVERSATION not related to specific database tasks
           Examples: "How does the HCP module help pharma reps?", "What is customer relationship management?", "How do I improve my sales performance?", "What are best practices for HCP engagement?"

        Think step by step:
        1. What is the user trying to accomplish?
        2. Are they describing a new interaction, wanting to modify an existing one, requesting history, asking for analysis, or asking general questions?
        3. Which tool best matches their intent?

        IMPORTANT: If the user is asking general questions about concepts, explanations, or casual conversation NOT related to specific database operations, use "general_conversation".

        Return your analysis in JSON format:
        {{
            "user_intent": "Brief description of what user wants to do",
            "reasoning": "Your step-by-step reasoning for tool selection",
            "selected_tool": "log_interaction|edit_interaction|get_interaction_history|generate_sales_insights|form_information_tool|general_conversation",
            "confidence": "high|medium|low",
            "extracted_entities": {{
                "hcp_name": "HCP name if mentioned (e.g., 'Dr. Smith', 'Neha Singh')",
                "interaction_type": "meeting|call|email|visit|conference if mentioned",
                "sentiment": "positive|negative|neutral if mentioned",
                "date": "date if mentioned (e.g., 'today', '2024-01-15')",
                "time": "time if mentioned (e.g., '14:50', '2:30 PM', '10:00')",
                "materials": "materials if mentioned",
                "samples": "samples if mentioned",
                "topics": "topics discussed if mentioned",
                "specific_requests": "any specific modifications or requests"
            }}
        }}

        Return only valid JSON, no explanations.
        """
        
        try:
            response = self.llm.invoke(analysis_prompt)
            content = response.content.strip()
            
            # Clean the response to extract JSON
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            # Find JSON boundaries
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                content = content[start:end]
            
            analysis = json.loads(content)
            return analysis
            
        except Exception as e:
            print(f"Error in LLM query analysis: {e}")
            # Fallback to simple pattern matching
            return self._fallback_analysis(user_query)
    
    def _fallback_analysis(self, user_query: str) -> Dict[str, Any]:
        """Fallback analysis using simple pattern matching"""
        user_lower = user_query.lower()
        
        # Simple pattern matching as fallback
        if any(phrase in user_lower for phrase in ["met with", "had a call", "visited", "spoke with", "discussed with"]):
            return {
                "user_intent": "User is describing a new interaction",
                "reasoning": "Pattern matching detected new interaction keywords",
                "selected_tool": "log_interaction",
                "confidence": "medium",
                "extracted_entities": {}
            }
        elif any(phrase in user_lower for phrase in ["update", "edit", "change", "modify", "correct"]):
            return {
                "user_intent": "User wants to modify existing interaction",
                "reasoning": "Pattern matching detected modification keywords",
                "selected_tool": "edit_interaction",
                "confidence": "medium",
                "extracted_entities": {}
            }
        elif any(phrase in user_lower for phrase in ["show", "history", "past", "previous", "interactions with"]):
            return {
                "user_intent": "User wants to see interaction history",
                "reasoning": "Pattern matching detected history keywords",
                "selected_tool": "get_interaction_history",
                "confidence": "medium",
                "extracted_entities": {}
            }
        elif any(phrase in user_lower for phrase in ["analyze", "insights", "report", "analytics", "performance"]):
            return {
                "user_intent": "User wants analysis or insights",
                "reasoning": "Pattern matching detected analysis keywords",
                "selected_tool": "generate_sales_insights",
                "confidence": "medium",
                "extracted_entities": {}
            }
        elif any(phrase in user_lower for phrase in ["how does", "what is", "what are", "how do", "explain", "help me understand", "best practices"]):
            return {
                "user_intent": "User is asking general questions",
                "reasoning": "Pattern matching detected general question keywords",
                "selected_tool": "general_conversation",
                "confidence": "medium",
                "extracted_entities": {}
            }
        else:
            return {
                "user_intent": "Default to logging new interaction",
                "reasoning": "No clear pattern matched, defaulting to log_interaction",
                "selected_tool": "log_interaction",
                "confidence": "low",
                "extracted_entities": {}
            }

class IntelligentToolExecutor:
    """Executes tools based on LLM analysis and extracted parameters"""
    
    def __init__(self, llm):
        self.llm = llm
        self.tools = {
            'log_interaction': log_interaction,
            'edit_interaction': edit_interaction,
            'edit_interaction_by_name': edit_interaction_by_name,
            'update_form_field': update_form_field,
            'get_interaction_history': get_interaction_history,
            'generate_sales_insights': generate_sales_insights,
            'form_information_tool': form_information_tool,
            'general_conversation': self.handle_general_conversation
        }
    
    def prepare_parameters(self, tool_name: str, query_analysis: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        """Prepare parameters for the selected tool based on LLM analysis"""
        
        entities = query_analysis.get('extracted_entities', {})
        
        if tool_name == 'log_interaction':
            return {
                'raw_interaction_text': user_query
            }
        
        elif tool_name == 'edit_interaction':
            # Check if specific HCP name is mentioned for name-based editing
            if entities.get('hcp_name'):
                params = {
                    'hcp_name_search': entities['hcp_name']
                }
                # Add any specific field updates
                if entities.get('sentiment'):
                    params['sentiment'] = entities['sentiment'].title()
                if entities.get('interaction_type'):
                    params['interaction_type'] = entities['interaction_type'].title()
                if entities.get('time'):
                    params['interaction_time'] = entities['time']
                if entities.get('date'):
                    params['interaction_date'] = entities['date']
                if entities.get('materials'):
                    params['materials_shared'] = entities['materials']
                if entities.get('samples'):
                    params['samples_distributed'] = entities['samples']
                if entities.get('topics'):
                    params['key_discussion_points'] = entities['topics']
                
                return params
            else:
                # Default to editing interaction ID 1 if no specific HCP mentioned
                return {
                    'interaction_id': 1,
                    'summary': entities.get('specific_requests', user_query)
                }
        
        elif tool_name == 'get_interaction_history':
            return {
                'hcp_name': entities.get('hcp_name', '')
            }
        
        elif tool_name == 'generate_sales_insights':
            return {
                'hcp_name': entities.get('hcp_name', ''),
                'period_days': 30
            }
        
        elif tool_name == 'form_information_tool':
            return {
                'form_data': '{}'  # This will be populated by the frontend
            }
        
        elif tool_name == 'general_conversation':
            return {
                'user_query': user_query
            }
        
        return {}
    
    def handle_general_conversation(self, parameters: Dict[str, Any]) -> str:
        """Handle general conversation questions with human-like responses"""
        user_query = parameters.get('user_query', '')
        
        conversation_prompt = f"""
        You are a helpful AI assistant for healthcare sales representatives. The user is asking a general question about healthcare sales, CRM, or related topics. 
        
        USER QUESTION: "{user_query}"
        
        Provide a helpful, informative, and conversational response. Be natural and human-like in your response. 
        This is NOT a database operation - just answer their question directly as if you were having a conversation.
        
        Keep your response concise but informative. Use a friendly, professional tone.
        """
        
        try:
            response = self.llm.invoke(conversation_prompt)
            return response.content.strip()
        except Exception as e:
            print(f"Error in general conversation: {e}")
            return self._get_fallback_response(user_query)
    
    def _get_fallback_response(self, user_query: str) -> str:
        """Fallback responses for general questions"""
        user_lower = user_query.lower()
        
        if "hcp" in user_lower and "help" in user_lower:
            return "HCP (Healthcare Professional) interaction management helps pharma reps track their engagements with doctors, build stronger relationships, and plan more effective follow-ups. It enables personalized communication and better understanding of each doctor's needs and preferences."
        elif "crm" in user_lower:
            return "Customer Relationship Management (CRM) in healthcare sales helps organize and track all interactions with healthcare professionals, manage contact information, schedule follow-ups, and analyze engagement patterns to improve sales effectiveness."
        elif "sales performance" in user_lower:
            return "To improve sales performance with HCPs, focus on: 1) Building genuine relationships, 2) Understanding their specific needs, 3) Providing valuable medical information, 4) Following up consistently, 5) Tracking interaction history to personalize future engagements."
        elif "best practices" in user_lower:
            return "Best practices for HCP engagement include: being respectful of their time, providing scientifically accurate information, following compliance guidelines, maintaining detailed interaction records, and focusing on patient outcomes rather than just product features."
        else:
            return "I'm here to help with questions about healthcare sales, HCP engagement, and interaction management. Feel free to ask about best practices, strategies, or how our tools can support your work with healthcare professionals."
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute the selected tool with prepared parameters"""
        
        try:
            tool_func = self.tools[tool_name]
            
            # Handle different tool execution methods
            if tool_name == 'edit_interaction' and 'hcp_name_search' in parameters:
                # Use name-based editing
                tool_func = self.tools['edit_interaction_by_name']
                print(f"DEBUG - Using edit_interaction_by_name with parameters: {parameters}")
            
            # Handle general conversation differently (it's a method, not a tool)
            if tool_name == 'general_conversation':
                result = tool_func(parameters)
            else:
                result = tool_func.invoke(parameters)
            
            print(f"DEBUG - Tool {tool_name} executed with result: {result}")
            return result
            
        except Exception as e:
            print(f"DEBUG - Tool execution error: {str(e)}")
            return f"Error executing {tool_name}: {str(e)}"

# Initialize LLM
try:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured. Please set it in the .env file.")
    
    llm = ChatGroq(
        temperature=0.1,
        model_name="gemma2-9b-it",
        groq_api_key=settings.groq_api_key
    )
    print("✅ Intelligent LangGraph Agent initialized successfully")
except Exception as e:
    print(f"❌ Error initializing Intelligent LangGraph Agent: {e}")
    raise

# Initialize services
query_analyzer = LLMQueryAnalyzer(llm)
tool_executor = IntelligentToolExecutor(llm)

# Define the intelligent workflow nodes
def analyze_query_node(state: IntelligentAgentState) -> IntelligentAgentState:
    """Use LLM to analyze user query and determine best tool"""
    user_query = state["messages"][-1].content if state["messages"] else ""
    
    # Use LLM to analyze the query
    analysis = query_analyzer.analyze_query(user_query)
    
    return {
        **state,
        "user_query": user_query,
        "query_analysis": analysis
    }

def select_tool_node(state: IntelligentAgentState) -> IntelligentAgentState:
    """Select tool and prepare parameters based on LLM analysis"""
    analysis = state["query_analysis"]
    selected_tool = analysis.get("selected_tool", "log_interaction")
    
    # Prepare parameters for the selected tool
    parameters = tool_executor.prepare_parameters(selected_tool, analysis, state["user_query"])
    
    print(f"DEBUG - Selected tool: {selected_tool}")
    print(f"DEBUG - Prepared parameters: {parameters}")
    print(f"DEBUG - Extracted entities: {analysis.get('extracted_entities', {})}")
    
    return {
        **state,
        "selected_tool": selected_tool,
        "tool_parameters": parameters
    }

def execute_tool_node(state: IntelligentAgentState) -> IntelligentAgentState:
    """Execute the selected tool with prepared parameters"""
    
    # If using form information tool, pass the form data
    if state["selected_tool"] == "form_information_tool":
        import json
        form_data_str = json.dumps(state.get("form_data", {}))
        state["tool_parameters"]["form_data"] = form_data_str
    
    # Execute the tool
    result = tool_executor.execute_tool(state["selected_tool"], state["tool_parameters"])
    
    # Create user-friendly response
    analysis = state["query_analysis"]
    friendly_response = _create_intelligent_response(result, state["selected_tool"], analysis)
    
    return {
        **state,
        "tool_result": friendly_response
    }

def _create_intelligent_response(tool_result: str, tool_name: str, analysis: Dict[str, Any]) -> str:
    """Create intelligent, context-aware responses based on tool results"""
    
    user_intent = analysis.get("user_intent", "")
    confidence = analysis.get("confidence", "medium")
    
    # Add confidence indicator for low confidence
    confidence_note = ""
    if confidence == "low":
        confidence_note = " (I'm not entirely sure about this interpretation - please let me know if this isn't what you wanted)"
    
    if tool_name == 'log_interaction':
        # Handle JSON response from form population
        try:
            import json
            result_data = json.loads(tool_result)
            if result_data.get("response_type") == "FORM_POPULATE":
                # Return the JSON response directly for form population
                return tool_result
            elif result_data.get("response_type") == "ERROR":
                return f"I understood you were describing a new interaction, but {result_data.get('message', 'encountered an error')}{confidence_note}"
            else:
                return f"Perfect! I understood you were describing a new interaction. {result_data.get('message', 'Interaction processed successfully')}{confidence_note}"
        except (json.JSONDecodeError, KeyError):
            if "✅" in tool_result:
                return f"Perfect! I understood you were describing a new interaction. {tool_result.replace('✅', '').strip()}{confidence_note}"
            else:
                return f"I tried to log your interaction but encountered an issue: {tool_result}{confidence_note}"
    
    elif tool_name == 'edit_interaction' or tool_name == 'edit_interaction_by_name':
        if "✅" in tool_result:
            return f"Done! I understood you wanted to modify an existing interaction. {tool_result.replace('✅', '').strip()}{confidence_note}"
        else:
            return f"I tried to update the interaction but: {tool_result}{confidence_note}"
    
    elif tool_name == 'get_interaction_history':
        if "No interactions found" in tool_result:
            return f"I understood you wanted to see interaction history, but {tool_result.lower()}{confidence_note}"
        else:
            return f"I understood you wanted to see interaction history. {tool_result}{confidence_note}"
    
    elif tool_name == 'generate_sales_insights':
        if "❌" in tool_result:
            return f"I understood you wanted analysis and insights, but {tool_result.replace('❌', '').strip()}{confidence_note}"
        else:
            return f"I understood you wanted analysis and insights. {tool_result}{confidence_note}"
    
    elif tool_name == 'form_information_tool':
        if "❌" in tool_result:
            return f"I understood you wanted to check the form information, but {tool_result.replace('❌', '').strip()}{confidence_note}"
        else:
            return f"I understood you wanted to check the current form information. {tool_result}{confidence_note}"
    
    elif tool_name == 'general_conversation':
        # Return the conversational response directly without tool-specific formatting
        return tool_result
    
    return f"I analyzed your request as: {user_intent}. {tool_result}{confidence_note}"

# Create the intelligent workflow
intelligent_workflow = StateGraph(IntelligentAgentState)

# Add nodes
intelligent_workflow.add_node("analyze_query", analyze_query_node)
intelligent_workflow.add_node("select_tool", select_tool_node)
intelligent_workflow.add_node("execute_tool", execute_tool_node)

# Define the workflow
intelligent_workflow.set_entry_point("analyze_query")
intelligent_workflow.add_edge("analyze_query", "select_tool")
intelligent_workflow.add_edge("select_tool", "execute_tool")
intelligent_workflow.add_edge("execute_tool", END)

# Compile the intelligent workflow
intelligent_app = intelligent_workflow.compile()

def process_intelligent_user_input(user_input: str, form_data: dict = None) -> str:
    """
    Process user input through the intelligent AI agent with LLM-based decision making.
    
    This agent:
    1. Uses LLM to analyze and understand user queries
    2. Makes intelligent decisions about which tool to use
    3. Extracts relevant parameters for the selected tool
    4. Provides context-aware responses
    
    The agent understands natural language and thinks before acting!
    """
    try:
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
            "query_analysis": {},
            "selected_tool": "",
            "tool_parameters": {},
            "tool_result": "",
            "form_data": form_data or {}
        }
        
        # Process through the intelligent workflow
        result = intelligent_app.invoke(initial_state)
        
        # Debug output
        print(f"DEBUG - Input: {user_input}")
        print(f"DEBUG - Analysis: {result.get('query_analysis', {})}")
        print(f"DEBUG - Selected Tool: {result.get('selected_tool', 'unknown')}")
        print(f"DEBUG - Parameters: {result.get('tool_parameters', {})}")
        print(f"DEBUG - Tool Result: {result.get('tool_result', 'no result')}")
        
        # Return the tool result
        return result.get("tool_result", "I'm not sure how to help with that request.")
        
    except Exception as e:
        print(f"DEBUG - Error: {str(e)}")
        return f"I encountered an error while processing your request: {str(e)}"

# Intelligent agent description
INTELLIGENT_AGENT_DESCRIPTION = """
# Intelligent AI Agent for HCP Interaction Management

## Key Features

### 1. LLM-Based Decision Making
- Uses advanced language model to understand user queries
- Thinks before acting - analyzes intent and context
- Makes intelligent decisions about which tool to use

### 2. Natural Language Understanding
- Understands complex, conversational queries
- Extracts relevant information automatically
- Handles ambiguous requests intelligently

### 3. Tool Selection Intelligence
- **log_interaction**: Detects when user describes new interactions
- **edit_interaction**: Identifies requests to modify existing interactions
- **get_interaction_history**: Recognizes requests for past interaction data
- **generate_sales_insights**: Understands requests for analysis and insights

### 4. Context-Aware Responses
- Provides responses that acknowledge what the user intended
- Includes confidence indicators for uncertain interpretations
- Offers helpful feedback and clarifications

### 5. Example Interactions
- "I met with Dr. Smith today" → Uses log_interaction
- "Update Dr. Johnson's meeting to positive" → Uses edit_interaction
- "Show me all interactions with Dr. Brown" → Uses get_interaction_history
- "Analyze my performance this month" → Uses generate_sales_insights

## Architecture
- Query Analysis (LLM) → Tool Selection → Parameter Preparation → Tool Execution
- Advanced reasoning and decision making
- Context-aware response generation
- Intelligent fallback mechanisms
"""