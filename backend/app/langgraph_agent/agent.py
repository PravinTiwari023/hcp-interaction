from langchain_core.messages import BaseMessage, FunctionMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from typing import Literal, TypedDict
from typing_extensions import Annotated
from langgraph.graph.message import add_messages
import json
import re

# Import the 6 core tools
from .tools import (
    log_interaction,           # Tool 1: Log Interaction (with LLM summarization)
    edit_interaction,          # Tool 2: Edit Interaction by ID
    edit_interaction_by_name,  # Tool 2b: Edit Interaction by Name
    update_form_field,         # Tool 3: PUT Form Update
    get_interaction_history,   # Tool 4: Get Interaction History
    generate_sales_insights    # Tool 5: Generate Sales Insights
)
from ..core.config import settings

def _make_response_conversational(tool_result: str, user_input: str, tool_name: str) -> str:
    """
    Convert technical tool responses into more natural, conversational responses.
    """
    # Handle different tool responses
    if tool_name == "log_interaction":
        if "✅" in tool_result:
            return f"Great! I've successfully logged your interaction. {tool_result.replace('✅', '').strip()}"
        elif "❌" in tool_result:
            return f"I encountered an issue while logging your interaction. {tool_result.replace('❌', '').strip()}"
    
    elif tool_name == "edit_interaction" or tool_name == "edit_interaction_by_name":
        if "✅" in tool_result:
            return f"Perfect! I've updated the interaction as requested. {tool_result.replace('✅', '').strip()}"
        elif "Multiple interactions found" in tool_result:
            return f"I found several interactions for that person. Here are your options:\n\n{tool_result}"
        elif "No interactions found" in tool_result:
            return f"I couldn't find any interactions matching your request. {tool_result}"
        elif "❌" in tool_result:
            return f"I had trouble updating the interaction. {tool_result.replace('❌', '').strip()}"
    
    elif tool_name == "update_form_field":
        if "✅" in tool_result:
            return f"Done! I've updated the form field for you. {tool_result.replace('✅', '').strip()}"
        elif "❌" in tool_result:
            return f"I couldn't update that field. {tool_result.replace('❌', '').strip()}"
    
    elif tool_name == "get_interaction_history":
        if "No interactions found" in tool_result:
            return f"I couldn't find any interaction history for that person. {tool_result}"
        elif "❌" in tool_result:
            return f"I had trouble retrieving the interaction history. {tool_result.replace('❌', '').strip()}"
        else:
            return f"Here's the interaction history you requested:\n\n{tool_result}"
    
    elif tool_name == "generate_sales_insights":
        if "❌" in tool_result:
            return f"I couldn't generate the sales insights right now. {tool_result.replace('❌', '').strip()}"
        else:
            return f"Here are the sales insights based on your request:\n\n{tool_result}"
    
    elif tool_name == "error":
        return f"I'm not sure how to help with that. {tool_result.replace('❌', '').strip()}"
    
    # Default: return the original response for any unhandled cases
    return tool_result

def _handle_general_conversation(user_input: str) -> str:
    """
    Handle general conversation like a friendly chatbot.
    """
    user_lower = user_input.lower().strip()
    
    # First check for specific CRM/business questions (higher priority)
    # CRM workflow and functionality questions
    if any(phrase in user_lower for phrase in ["doctor visit", "planned visit", "call planning", "visit planning"]):
        return "Excellent question about visit planning! In HCP CRM systems, planned doctor visits are optimized through:\n\n• Call Planning: Schedule visits based on HCP preferences and availability\n• Pre-visit Preparation: System generates briefing with HCP history, recent interactions, and relevant talking points\n• Content Recommendations: AI suggests materials based on HCP specialty, interests, and previous engagement\n• Territory Management: Optimizes routing and scheduling for maximum efficiency\n• Compliance Checks: Ensures all planned activities meet regulatory requirements\n\nThe system uses AI to analyze HCP profiles, interaction history, and current campaigns to recommend the most relevant approach for each visit. What specific aspect of visit planning interests you most?"
    
    elif any(phrase in user_lower for phrase in ["crm suggest", "content suggest", "recommend content", "suggest content"]):
        return "Great question about content recommendations! The CRM uses AI to suggest relevant content through:\n\n• HCP Profiling: Analyzes specialty, interests, and previous content engagement\n• Interaction History: Reviews past discussions and materials that resonated\n• Campaign Alignment: Matches current marketing campaigns with HCP interests\n• Therapeutic Area Mapping: Suggests content based on HCP's medical specialties\n• Engagement Analytics: Recommends content with highest engagement rates\n• Compliance Filtering: Ensures all suggested content is approved for the specific HCP\n\nFor example, if visiting a cardiologist who previously engaged with heart failure content, the system would suggest the latest cardiac research, product updates, and relevant case studies. Would you like more details about any specific aspect?"
    
    # Specific CRM functionality questions
    elif any(phrase in user_lower for phrase in ["content section", "digital content", "brochures", "pdfs", "content management"]):
        return "Great question about content management! In a typical HCP CRM, the content section manages digital materials like brochures, PDFs, and educational content. Here's how it works:\n\n• Content Library: Stores approved materials by therapeutic area\n• HCP Profiling: Tracks content preferences and engagement\n• Smart Recommendations: Suggests relevant content based on HCP specialty and previous interactions\n• Usage Analytics: Monitors which materials are most effective\n• Compliance: Ensures all content is medically and legally approved\n\nFor planned visits, the system would analyze the HCP's specialty, previous interactions, and current campaigns to suggest the most relevant materials. Would you like to know more about any specific aspect?"
    
    # Then check for simple greetings (lower priority)
    elif any(greeting in user_lower for greeting in ["hello", "hi", "hey"]) and len(user_input.split()) <= 3:
        return "Hi! How are you doing today? 😊"
    
    elif any(greeting in user_lower for greeting in ["good morning"]) and len(user_input.split()) <= 3:
        return "Good morning! Hope you're having a great day! ☀️"
    
    elif any(greeting in user_lower for greeting in ["good afternoon"]) and len(user_input.split()) <= 3:
        return "Good afternoon! How's your day going? 🌤️"
    
    elif any(greeting in user_lower for greeting in ["good evening"]) and len(user_input.split()) <= 3:
        return "Good evening! Hope you had a productive day! 🌙"
    
    # How are you patterns
    elif any(phrase in user_lower for phrase in ["how are you", "how you doing", "what's up", "how's it going"]):
        return "I'm doing great, thanks for asking! I'm here and ready to help with your HCP interactions. How about you? How's your day going?"
    
    # Help patterns
    elif any(help_word in user_lower for help_word in ["help", "what can you do", "how do i", "commands"]):
        return """I can help you with several HCP interaction tasks! Here's what I can do:

• Log new interactions: Use "-" before describing your meeting (e.g., "-I met with Dr. Smith today...")
• Edit interactions: Use "-edit interaction [ID]" or "-edit interaction with [name]"
• Get interaction history: Use "-history for [HCP name]" or "-show me history for [name]"
• Update form fields: Use "-put [field] as [value]"
• Generate insights: Use "-insights for [HCP name]" or "-sales analysis"

The "-" prefix tells me you want to perform a task. Without it, we're just having a regular conversation! 😊

What would you like to do?"""
    
    # Thank you patterns
    elif any(thanks in user_lower for thanks in ["thank you", "thanks", "appreciate"]):
        return "You're so welcome! Always happy to help! 😊 Is there anything else you'd like to chat about or any tasks you need help with?"
    
    # Personal questions
    elif any(question in user_lower for question in ["who are you", "what are you", "tell me about yourself"]):
        return "I'm your friendly HCP interaction assistant! I help manage healthcare professional interactions in your CRM system. I can be both a chatbot for casual conversation and a powerful tool for managing your sales interactions. Just use '-' before any task you want me to perform!"
    
    # Specific HCP-related questions
    elif any(question in user_lower for question in ["what is hcp", "what are hcp", "what does hcp mean", "define hcp"]):
        return "HCP stands for Healthcare Professional! These are medical professionals like doctors, nurses, specialists, and other healthcare providers. In the context of pharmaceutical and medical device sales, HCPs are the key people that sales representatives interact with to discuss products, share medical information, and build professional relationships. They're essentially the healthcare experts who make treatment decisions for patients."
    
    elif any(question in user_lower for question in ["who are hcp", "who is hcp", "who are healthcare professionals"]):
        return "Healthcare Professionals (HCPs) are the medical experts you work with! This includes:\n\n• Doctors - Primary care physicians, specialists, surgeons\n• Nurses - Registered nurses, nurse practitioners, clinical staff\n• Hospital Staff - Department heads, administrators, pharmacists\n• Researchers - Clinical researchers, medical researchers\n• Specialists - Cardiologists, oncologists, neurologists, etc.\n\nBasically, anyone in the healthcare field who might be interested in your medical products or services!"
    
    elif any(term in user_lower for term in ["crm", "customer relationship management"]):
        return "A CRM (Customer Relationship Management) system helps manage all your interactions with healthcare professionals! It's like a digital assistant that keeps track of your meetings, calls, emails, and follow-ups with doctors and other medical professionals. Think of it as your organized notebook that remembers everything about your professional relationships."
    
    elif any(term in user_lower for term in ["interaction", "sales interaction", "medical sales"]):
        return "Sales interactions are all the ways you connect with healthcare professionals! This could be:\n\n• Face-to-face meetings - Office visits, hospital meetings\n• Phone calls - Check-ins, product discussions\n• Emails - Follow-ups, information sharing\n• Conferences - Medical conferences, trade shows\n• Educational events - Training sessions, product demos\n\nEach interaction is valuable for building relationships and sharing important medical information!"
    
    # Weather/casual conversation
    elif any(word in user_lower for word in ["weather", "today", "weekend"]):
        return "I wish I could check the weather for you, but I'm focused on helping with HCP interactions! How's your day going though? Any interesting meetings or calls with healthcare professionals?"
    
    # Jokes/fun
    elif any(word in user_lower for word in ["joke", "funny", "laugh"]):
        return "Haha, I'm better at managing HCP interactions than telling jokes! But here's one: Why did the sales rep bring a ladder to the meeting? Because they wanted to reach new heights with their HCP relationships! 😄"
    
    # Compliments
    elif any(word in user_lower for word in ["good job", "great", "awesome", "nice"]):
        return "Aww, thank you! That really makes my day! 😊 I love helping with HCP interactions. Is there anything else you'd like to chat about?"
    
    # Work-related questions
    elif any(phrase in user_lower for phrase in ["how was work", "how's work", "busy day", "long day"]):
        return "I hope your work day is going well! Are you managing lots of HCP interactions today? I'm here if you need help logging any meetings or calls with healthcare professionals."
    
    # Product/pharma related questions
    elif any(word in user_lower for word in ["pharmaceutical", "pharma", "medicine", "drug", "medical device"]):
        return "Pharmaceutical and medical device sales are fascinating fields! You're helping bring important treatments to healthcare professionals who can improve patient lives. That's really meaningful work. Are you working with any specific therapeutic areas?"
    
    # Specific CRM functionality questions
    elif any(phrase in user_lower for phrase in ["content section", "digital content", "brochures", "pdfs", "content management"]):
        return "Great question about content management! In a typical HCP CRM, the content section manages digital materials like brochures, PDFs, and educational content. Here's how it works:\n\n• Content Library: Stores approved materials by therapeutic area\n• HCP Profiling: Tracks content preferences and engagement\n• Smart Recommendations: Suggests relevant content based on HCP specialty and previous interactions\n• Usage Analytics: Monitors which materials are most effective\n• Compliance: Ensures all content is medically and legally approved\n\nFor planned visits, the system would analyze the HCP's specialty, previous interactions, and current campaigns to suggest the most relevant materials. Would you like to know more about any specific aspect?"
    
    # Questions about the system
    elif any(phrase in user_lower for phrase in ["how does this work", "how do you work", "explain this system"]):
        return "I'm designed to make your HCP interaction management super easy! I can work in two ways:\n\n• Chat mode (like right now) - Just talk to me normally\n• Task mode - Use '-' before commands to log interactions, edit data, get history, etc.\n\nI'm powered by AI to understand natural language and help you stay organized with your healthcare professional relationships!"
    
    
    # Specific question patterns
    elif user_lower.startswith("what") and ("do" in user_lower or "can" in user_lower):
        return "Great question! I can help you manage your relationships with healthcare professionals. I can log your meetings and calls, help you edit interaction details, retrieve history for specific HCPs, and generate insights about your sales activities. What specific task interests you?"
    
    elif user_lower.startswith("how") and ("use" in user_lower or "work" in user_lower):
        return "It's really simple! For casual conversation, just talk to me normally (like you're doing now). When you want me to do something specific, just add a '-' at the beginning. For example:\n\n• Normal: \"How are you?\"\n• Task: \"-Show me history for Dr. Smith\"\n\nTry it out - what would you like to do?"
    
    # Fallback for general conversation
    else:
        return "That's interesting! I'm here to chat or help with HCP interaction tasks. Feel free to tell me more about what's on your mind, or if you need help with any sales interactions, just add a '-' before your request!"

def _parse_field_updates(updates_text: str) -> dict:
    """
    Parse field updates from natural language text.
    
    Handles patterns like:
    - "change time to 02:45"
    - "set sentiment to positive"
    - "update interaction type to Meeting"
    - "time 02:45"
    """
    if not updates_text:
        return {}
    
    params = {}
    text_lower = updates_text.lower().strip()
    
    # Field mapping
    field_patterns = {
        r"(?:change|set|update)?\s*(?:the\s+)?time\s+(?:to\s+)?(.+)": "interaction_time",
        r"(?:change|set|update)?\s*(?:the\s+)?date\s+(?:to\s+)?(.+)": "interaction_date", 
        r"(?:change|set|update)?\s*(?:the\s+)?sentiment\s+(?:to\s+)?(.+)": "sentiment",
        r"(?:change|set|update)?\s*(?:the\s+)?(?:interaction\s+)?type\s+(?:to\s+)?(.+)": "interaction_type",
        r"(?:change|set|update)?\s*(?:the\s+)?attendees\s+(?:to\s+)?(.+)": "attendees",
        r"(?:change|set|update)?\s*(?:the\s+)?summary\s+(?:to\s+)?(.+)": "summary",
        r"(?:change|set|update)?\s*(?:the\s+)?(?:key\s+)?discussion\s+(?:points\s+)?(?:to\s+)?(.+)": "key_discussion_points",
        r"(?:change|set|update)?\s*(?:the\s+)?materials\s+(?:shared\s+)?(?:to\s+)?(.+)": "materials_shared",
        r"(?:change|set|update)?\s*(?:the\s+)?samples\s+(?:distributed\s+)?(?:to\s+)?(.+)": "samples_distributed",
        r"(?:change|set|update)?\s*(?:the\s+)?follow\s*up\s+(?:actions\s+)?(?:to\s+)?(.+)": "follow_up_actions"
    }
    
    for pattern, field_name in field_patterns.items():
        match = re.search(pattern, text_lower)
        if match:
            value = match.group(1).strip()
            # Clean up common prefixes/suffixes
            value = re.sub(r'^(as|to)\s+', '', value)
            value = value.strip('"\'')
            params[field_name] = value
            break
    
    return params

def determine_intent_and_route(user_input: str) -> dict:
    """
    Command prefix system: '-' indicates task command, otherwise conversational response.
    Returns the appropriate tool and parsed parameters.
    """
    user_input = user_input.strip()
    
    # Check if this is a task command (starts with -)
    if user_input.startswith("-"):
        # Remove the - prefix and process as a task command
        task_input = user_input[1:].strip()
        return _route_task_command(task_input)
    else:
        # Handle as general conversation
        return {
            "tool": "general_conversation",
            "params": {"user_input": user_input}
        }

def _route_task_command(user_input: str) -> dict:
    """
    Route task commands (without the - prefix) to appropriate tools.
    """
    user_lower = user_input.lower().strip()
    
    # Tool 3: PUT Form Update - handle "put [field] as [value]" commands
    if user_lower.startswith("put "):
        # Extract field and value from "put [field] as [value]"
        put_pattern = r"put\s+(.+?)\s+as\s+(.+)"
        match = re.search(put_pattern, user_input, re.IGNORECASE)
        if match:
            field_name = match.group(1).strip()
            field_value = match.group(2).strip()
            return {
                "tool": "update_form_field",
                "params": {"field_name": field_name, "field_value": field_value}
            }
        else:
            return {"tool": "error", "message": "Invalid PUT format. Use: 'put [field] as [value]'"}
    
    # Tool 2: Edit Interaction - handle both ID and name-based editing
    elif "edit interaction" in user_lower:
        # First try to match by ID pattern: "edit interaction [id]"
        edit_id_pattern = r"edit\s+interaction\s+(\d+)"
        id_match = re.search(edit_id_pattern, user_input, re.IGNORECASE)
        
        if id_match:
            interaction_id = int(id_match.group(1))
            remaining_text = user_input[id_match.end():].strip()
            return {
                "tool": "edit_interaction", 
                "params": {"interaction_id": interaction_id, "updates": remaining_text}
            }
        else:
            # Try to match by name pattern: "edit interaction with [name]" 
            # Only match patterns that clearly indicate name-based editing
            edit_name_patterns = [
                r"edit\s+interaction\s+with\s+(.+?)(?:\s+change\s+(.+))?$",
                r"edit\s+interaction\s+for\s+(.+?)(?:\s+change\s+(.+))?$"
            ]
            
            for pattern in edit_name_patterns:
                name_match = re.search(pattern, user_input, re.IGNORECASE)
                if name_match:
                    hcp_name = name_match.group(1).strip()
                    updates = name_match.group(2).strip() if name_match.group(2) else ""
                    return {
                        "tool": "edit_interaction_by_name",
                        "params": {"hcp_name_search": hcp_name, "updates": updates}
                    }
            
            return {"tool": "error", "message": "Invalid edit format. Use: 'edit interaction [id]' or 'edit interaction with [name]' or 'edit interaction for [name]'"}
    
    # Tool 4: Get Interaction History - handle "history for [hcp_name]" or "get history [hcp_name]"
    elif "history" in user_lower:
        # Extract HCP name from various history command formats
        history_patterns = [
            r"history\s+for\s+(.+)",
            r"get\s+history\s+(.+)",
            r"show\s+history\s+(.+)",
            r"show\s+me\s+(?:the\s+)?history\s+for\s+(.+)",
            r"show\s+me\s+(?:the\s+)?history\s+(?:of\s+)?(.+)",
            r"get\s+me\s+(?:the\s+)?history\s+for\s+(.+)",
            r"(.+)\s+history"
        ]
        
        for pattern in history_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                hcp_name = match.group(1).strip()
                return {
                    "tool": "get_interaction_history",
                    "params": {"hcp_name": hcp_name}
                }
        
        return {"tool": "error", "message": "Please specify HCP name for history. Use: 'history for [HCP name]'"}
    
    # Tool 5: Generate Sales Insights - handle specific insight request commands
    elif any(user_lower.startswith(keyword) for keyword in ["insights", "analyze", "generate insights", "generate sales", "sales report", "pipeline report"]) or \
         any(keyword in user_lower for keyword in ["generate insights", "analyze pipeline", "sales analysis", "pipeline analysis"]):
        # Check if specific HCP is mentioned
        hcp_pattern = r"(?:for|about)\s+(.+?)(?:\s+(?:last|past)\s+(\d+)\s+days?)?$"
        match = re.search(hcp_pattern, user_input, re.IGNORECASE)
        
        if match:
            hcp_name = match.group(1).strip()
            period_days = int(match.group(2)) if match.group(2) else 30
            return {
                "tool": "generate_sales_insights",
                "params": {"hcp_name": hcp_name, "period_days": period_days}
            }
        else:
            # Check for period without specific HCP
            period_match = re.search(r"(?:last|past)\s+(\d+)\s+days?", user_input, re.IGNORECASE)
            period_days = int(period_match.group(1)) if period_match else 30
            return {
                "tool": "generate_sales_insights", 
                "params": {"hcp_name": "", "period_days": period_days}
            }
    
    # Tool 1: Log Interaction - default for everything else (natural language interaction logging)
    else:
        return {
            "tool": "log_interaction",
            "params": {"raw_interaction_text": user_input}
        }

# Define the 6 core tools available to the agent
tools = [
    log_interaction,           # Tool 1: Log Interaction (with LLM summarization)
    edit_interaction,          # Tool 2: Edit Interaction by ID
    edit_interaction_by_name,  # Tool 2b: Edit Interaction by Name
    update_form_field,         # Tool 3: PUT Form Update  
    get_interaction_history,   # Tool 4: Get Interaction History
    generate_sales_insights    # Tool 5: Generate Sales Insights
]

# Tool name to function mapping
tool_map = {
    "log_interaction": log_interaction,
    "edit_interaction": edit_interaction,
    "edit_interaction_by_name": edit_interaction_by_name,
    "update_form_field": update_form_field,
    "get_interaction_history": get_interaction_history,
    "generate_sales_insights": generate_sales_insights
}

# Initialize LLM (we still need it for complex routing decisions if needed)
try:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured. Please set it in the .env file.")
    
    llm = ChatGroq(
        temperature=0.1, 
        model_name="gemma2-9b-it", 
        groq_api_key=settings.groq_api_key
    )
    print(f"✅ Simplified LangGraph Agent initialized successfully")
except Exception as e:
    print(f"❌ Error initializing Simplified LangGraph Agent: {e}")
    raise

# Define the graph state
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_input: str
    tool_result: str

# Define the nodes
def route_and_execute(state: AgentState):
    """
    Main routing node that determines intent and executes the appropriate tool.
    This replaces the complex LLM-based routing with simple keyword detection.
    """
    user_input = state["messages"][-1].content if state["messages"] else ""
    
    # Determine intent and get routing information
    routing_info = determine_intent_and_route(user_input)
    
    if routing_info["tool"] == "error":
        result = _make_response_conversational(routing_info['message'], user_input, "error")
    elif routing_info["tool"] == "general_conversation":
        result = _handle_general_conversation(user_input)
    else:
        try:
            # Get the tool function
            tool_func = tool_map[routing_info["tool"]]
            
            # Execute the tool with parameters
            if routing_info["tool"] == "update_form_field":
                raw_result = tool_func.invoke(routing_info["params"])
                result = _make_response_conversational(raw_result, user_input, "update_form_field")
            elif routing_info["tool"] == "edit_interaction":
                # Parse field updates from the command
                interaction_id = routing_info["params"]["interaction_id"]
                updates_text = routing_info["params"]["updates"]
                params = {"interaction_id": interaction_id}
                
                # Parse field updates from natural language
                params.update(_parse_field_updates(updates_text))
                raw_result = tool_func.invoke(params)
                result = _make_response_conversational(raw_result, user_input, "edit_interaction")
            elif routing_info["tool"] == "edit_interaction_by_name":
                # Parse field updates for name-based editing
                hcp_name = routing_info["params"]["hcp_name_search"]
                updates_text = routing_info["params"]["updates"]
                params = {"hcp_name_search": hcp_name}
                
                # Parse field updates from natural language
                params.update(_parse_field_updates(updates_text))
                raw_result = tool_func.invoke(params)
                result = _make_response_conversational(raw_result, user_input, "edit_interaction_by_name")
            else:
                raw_result = tool_func.invoke(routing_info["params"])
                result = _make_response_conversational(raw_result, user_input, routing_info["tool"])
                
        except Exception as e:
            error_msg = f"❌ Error executing {routing_info['tool']}: {str(e)}"
            result = _make_response_conversational(error_msg, user_input, "error")
    
    return {
        "messages": state["messages"] + [FunctionMessage(content=result, name="agent_response")],
        "user_input": user_input,
        "tool_result": result
    }

# Create the simplified workflow
workflow = StateGraph(AgentState)

# Add single node for routing and execution
workflow.add_node("route_and_execute", route_and_execute)

# Set entry point and end
workflow.set_entry_point("route_and_execute")
workflow.add_edge("route_and_execute", END)

# Compile the workflow
app = workflow.compile()

def process_user_input(user_input: str) -> str:
    """
    Process user input through the conversational LangGraph agent with command prefix system.
    
    Command System:
    - Messages WITHOUT '-' prefix: Handled as general conversation (chatbot-like responses)
    - Messages WITH '-' prefix: Processed as task commands using the tools
    
    Task Commands (with '-' prefix):
    1. Log interactions: "-Today I met with Dr. Smith..."
    2. Edit interactions: "-edit interaction 123 change time to 02:45"
    3. Get history: "-history for Dr. Johnson" or "-show me history for Dr. Smith"
    4. Update form fields: "-put sentiment as positive"
    5. Generate insights: "-generate insights for Dr. Smith"
    
    General Conversation (without '-' prefix):
    - Greetings, casual chat, questions, help requests
    - Friendly, ChatGPT-like responses with personality
    """
    try:
        # Create initial state
        from langchain_core.messages import HumanMessage
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_input": user_input,
            "tool_result": ""
        }
        
        # Process through the workflow
        result = app.invoke(initial_state)
        
        # Return the tool result
        return result.get("tool_result", "No result generated")
        
    except Exception as e:
        return f"❌ Error processing request: {str(e)}"

# Agent description for documentation
AGENT_DESCRIPTION = """
# LangGraph AI Agent for HCP Interaction Management

## Role
The LangGraph agent manages Healthcare Professional (HCP) interactions through intelligent routing 
and automated data processing. It simplifies complex sales workflows by providing natural language 
interfaces for common tasks.

## Core Tools (6 Total)

### Tool 1: Log Interaction
- **Purpose**: Captures new HCP interactions from natural language descriptions
- **LLM Features**: 
  - Entity extraction (HCP names, dates, interaction types)
  - Automatic summarization of conversation content
  - Sentiment analysis and classification
- **Example**: "I met with Dr. Sarah Johnson today. She was very interested in our cardiology solutions."

### Tool 2: Edit Interaction by ID
- **Purpose**: Modifies existing interaction records in the database using interaction ID
- **Features**: Updates any field of previously logged interactions
- **Example**: "edit interaction 123 change time to 02:45"

### Tool 2b: Edit Interaction by Name
- **Purpose**: Modifies the most recent interaction for an HCP by name
- **Features**: 
  - Finds interactions by HCP name (partial matching)
  - Updates the most recent interaction automatically
  - Shows disambiguation when multiple matches found
- **Example**: "edit interaction with Neha Singh change time to 02:45" or "edit interaction for Neha Singh change time to 02:45"

### Tool 3: PUT Form Update
- **Purpose**: Updates frontend form fields in real-time during data entry
- **Features**: 
  - Field mapping and normalization
  - Value validation and transformation
  - Real-time UI updates
- **Example**: "put sentiment as positive", "put interaction type as call"

### Tool 4: Get Interaction History
- **Purpose**: Retrieves comprehensive interaction history for specific HCPs
- **Features**: 
  - Chronological interaction summaries
  - Sentiment trends and patterns
  - Formatted output for sales analysis
- **Example**: "history for Dr. Johnson", "show interactions with Dr. Smith"

### Tool 5: Generate Sales Insights
- **Purpose**: Provides AI-powered strategic analysis and recommendations
- **LLM Features**:
  - Relationship trend analysis
  - Opportunity scoring and identification  
  - Strategic recommendations generation
  - Success metrics calculation
- **Example**: "generate insights for Dr. Johnson", "analyze pipeline last 30 days"

## Workflow Benefits
1. **Simplified Routing**: Keyword-based intent detection eliminates complex LLM routing overhead
2. **Consistent Performance**: Direct tool invocation ensures reliable response times
3. **Maintainable Architecture**: Clear separation of concerns between routing and execution
4. **Scalable Design**: Easy to add new tools or modify existing functionality
"""