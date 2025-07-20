from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ...db.database import get_db
from ...db import models, schemas
from ...langgraph_agent.intelligent_agent import process_intelligent_user_input # Import the intelligent agent function

router = APIRouter()

class ChatInput(BaseModel):
    message: str
    form_data: dict = None  # Optional form data for form information tool

@router.post("/interactions/log", response_model=schemas.Interaction)
def log_interaction(interaction: schemas.InteractionCreate, db: Session = Depends(get_db)):
    print(f"Received interaction data: {interaction.dict()}")
    try:
        db_interaction = models.Interaction(**interaction.dict())
        db.add(db_interaction)
        db.commit()
        db.refresh(db_interaction)
        print(f"Successfully added interaction with ID: {db_interaction.id}")
        return db_interaction
    except Exception as e:
        db.rollback()
        print(f"Error logging interaction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log interaction: {str(e)}")

@router.put("/interactions/{interaction_id}", response_model=schemas.Interaction)
def update_interaction(interaction_id: int, interaction: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    db_interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not db_interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    for key, value in interaction.dict(exclude_unset=True).items():
        setattr(db_interaction, key, value)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

@router.get("/interactions/hcp/{hcp_name}", response_model=List[schemas.Interaction])
def get_interactions_for_hcp(hcp_name: str, db: Session = Depends(get_db)):
    interactions = db.query(models.Interaction).filter(models.Interaction.hcp_name.ilike(f"%{hcp_name}%")).all()
    return interactions

@router.post("/chat")
async def chat_with_agent(chat_input: ChatInput, db: Session = Depends(get_db)):
    """
    Intelligent chat endpoint using LLM-based decision making.
    
    The agent uses advanced language models to:
    1. UNDERSTAND user queries and intent
    2. THINK about which tool is best for the task
    3. EXTRACT relevant parameters automatically
    4. EXECUTE the appropriate tool with context
    
    Available tools:
    - log_interaction: When describing new HCP interactions
    - edit_interaction: When modifying existing interactions  
    - get_interaction_history: When requesting past interaction data
    - generate_sales_insights: When asking for analysis or insights
    - form_information_tool: When checking current form data or summary
    
    The agent thinks before acting - just describe what you want naturally!
    """
    try:
        # Use the intelligent agent function with form data
        result = process_intelligent_user_input(chat_input.message, chat_input.form_data)
        
        print(f"DEBUG - Backend API received result: {result}")
        
        # Try to parse the result as JSON first (from intelligent agent)
        try:
            import json
            result_data = json.loads(result)
            
            print(f"DEBUG - Parsed JSON result: {result_data}")
            
            if result_data.get("response_type") == "FORM_POPULATE":
                response = {
                    "response_type": "FORM_POPULATE",
                    "field_updates": result_data.get("field_updates", []),
                    "message": result_data.get("message", "Form populated successfully")
                }
                print(f"DEBUG - Returning FORM_POPULATE response: {response}")
                return response
            elif result_data.get("response_type") == "FORM_UPDATE":
                return {
                    "response_type": "FORM_UPDATE",
                    "field": result_data.get("field"),
                    "value": result_data.get("value"),
                    "message": result_data.get("message")
                }
        except (json.JSONDecodeError, KeyError) as e:
            print(f"DEBUG - JSON parsing failed: {e}")
            # Not a JSON response, continue with string matching
            pass
        
        # Check if this is a form populate response
        if "Perfect! I've populated the form" in result or "Great! I've populated the form" in result:
            # This is a form populate response, return special response type
            return {
                "response_type": "FORM_POPULATE",
                "message": result
            }
        
        # Check if this is a form update response (looking for specific patterns)
        if "Perfect! I've updated the" in result and "in the form" in result:
            # This is a form update response, try to extract the field and value
            try:
                import re
                match = re.search(r"updated the (\w+) to '([^']+)' in the form", result)
                if match:
                    return {
                        "response_type": "FORM_UPDATE",
                        "field": match.group(1),
                        "value": match.group(2),
                        "message": result
                    }
            except:
                pass
        
        # Return the agent's response
        return {"message": result}
        
    except Exception as e:
        print(f"Error in intelligent LangGraph agent: {e}")
        # Fallback to basic response if agent fails
        return {
            "message": "I'm your Intelligent AI Sales Assistant with LLM-based decision making:\n\n"
                      "🧠 LLM Understanding - I analyze your queries before acting\n"
                      "🤔 Intelligent Thinking - I decide which tool is best for your task\n"
                      "📝 Smart Interaction Logging - Just describe your meetings naturally\n"
                      "✏️ Context-Aware Editing - I understand when you want to modify things\n"
                      "📊 Intelligent Insights - I know when you want analysis\n\n"
                      "Examples (just talk naturally!):\n"
                      "• 'I met with Dr. Johnson today about cardiology'\n"
                      "• 'Update Dr. Smith's meeting to positive sentiment'\n"
                      "• 'Show me all interactions with Dr. Brown'\n"
                      "• 'Analyze my performance this month'\n"
                      "• 'What's currently in the form?'\n"
                      "• 'I had a great call with Dr. Martinez yesterday'"
        }