from typing import Literal, List, Dict, Optional
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
import json
import re
from ..db.database import SessionLocal
from ..db import models
from ..core.config import settings

def get_db_session():
    """Helper function to get database session"""
    return SessionLocal()

def parse_time_intelligently(time_text: str) -> str:
    """
    Comprehensive time parsing function that handles various time expressions:
    - Exact times: "9:15", "4:10 PM", "14:30"
    - Approximate times: "around 9", "about 3 PM"
    - Time periods: "morning", "afternoon", "evening", "night"
    - Specific periods: "early morning", "late afternoon", "mid-morning"
    - Special times: "midnight", "noon", "lunch time", "dinner time"
    - Combined expressions: "yesterday morning at 9:15", "this evening around 6"
    
    Returns 24-hour format HH:MM string suitable for HTML time input
    """
    if not time_text:
        return ""
    
    time_text = time_text.lower().strip()
    
    # Time period mappings to approximate times
    time_periods = {
        # Early periods
        'early morning': '07:00',
        'dawn': '06:00',
        'sunrise': '06:30',
        
        # Morning periods
        'morning': '09:00',
        'mid morning': '10:30',
        'mid-morning': '10:30',
        'late morning': '11:30',
        
        # Noon and lunch
        'noon': '12:00',
        'midday': '12:00',
        'lunch': '12:30',
        'lunch time': '12:30',
        'lunchtime': '12:30',
        
        # Afternoon periods
        'afternoon': '14:00',
        'early afternoon': '13:30',
        'mid afternoon': '15:00',
        'mid-afternoon': '15:00',
        'late afternoon': '16:30',
        
        # Evening periods
        'evening': '18:00',
        'early evening': '17:30',
        'late evening': '20:00',
        'dinner': '19:00',
        'dinner time': '19:00',
        'dinnertime': '19:00',
        
        # Night periods
        'night': '21:00',
        'late night': '23:00',
        'midnight': '00:00',
        'mid night': '00:00',
        'mid-night': '00:00',
        
        # Work periods
        'start of day': '08:00',
        'end of day': '17:00',
        'close of business': '17:00',
        'business hours': '14:00'
    }
    
    # Check for exact period matches first (sort by length to match longest first)
    sorted_periods = sorted(time_periods.items(), key=lambda x: len(x[0]), reverse=True)
    
    for period, default_time in sorted_periods:
        if period in time_text:
            # Look for specific times mentioned with the period
            time_patterns = [
                r'(\d{1,2}):(\d{2})\s*(am|pm)?',
                r'(\d{1,2})\s*(am|pm)',
                r'around\s+(\d{1,2})',
                r'about\s+(\d{1,2})',
                r'at\s+(\d{1,2})'
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, time_text)
                if match:
                    if ':' in match.group(0):
                        # Handle HH:MM format
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        am_pm = match.group(3) if len(match.groups()) >= 3 and match.group(3) else None
                    else:
                        # Handle single hour
                        hour = int(match.group(1))
                        minute = 0
                        am_pm = match.group(2) if len(match.groups()) >= 2 and match.group(2) else None
                    
                    # Apply AM/PM conversion
                    if am_pm:
                        if am_pm.lower() == 'pm' and hour != 12:
                            hour += 12
                        elif am_pm.lower() == 'am' and hour == 12:
                            hour = 0
                    else:
                        # Infer AM/PM based on period context
                        if period in ['morning', 'early morning', 'dawn', 'sunrise', 'mid morning', 'mid-morning', 'late morning']:
                            if hour > 12:
                                hour = hour - 12  # Convert from 24h if needed
                        elif period in ['afternoon', 'early afternoon', 'mid afternoon', 'mid-afternoon', 'late afternoon', 'evening', 'early evening', 'late evening', 'night', 'late night', 'dinner', 'dinner time', 'dinnertime'] and hour < 12:
                            hour += 12
                    
                    return f"{hour:02d}:{minute:02d}"
            
            # No specific time found, return default for period
            return default_time
    
    # Handle standalone time expressions without period context
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)?',  # 9:15, 4:10 PM
        r'(\d{1,2})\s*(am|pm)',          # 9 AM, 4 PM
        r'around\s+(\d{1,2})',           # around 9
        r'about\s+(\d{1,2})',            # about 3
        r'at\s+(\d{1,2})',               # at 9
        r'^(\d{1,2})$'                   # just "9"
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, time_text)
        if match:
            if ':' in match.group(0):
                # Handle HH:MM format
                hour = int(match.group(1))
                minute = int(match.group(2))
                am_pm = match.group(3) if len(match.groups()) >= 3 else None
            else:
                # Handle single hour
                hour = int(match.group(1))
                minute = 0
                am_pm = match.group(2) if len(match.groups()) >= 2 else None
            
            # Apply AM/PM conversion
            if am_pm:
                if am_pm.lower() == 'pm' and hour != 12:
                    hour += 12
                elif am_pm.lower() == 'am' and hour == 12:
                    hour = 0
            
            return f"{hour:02d}:{minute:02d}"
    
    # If no patterns match, return empty string
    return ""

def parse_date_flexibly(date_input: str) -> date:
    """Parse date input in various formats, handling natural language dates"""
    if not date_input:
        return datetime.now().date()
    
    date_str = date_input.lower().strip()
    
    # Handle common natural language dates
    if date_str in ['today', 'now']:
        return datetime.now().date()
    elif date_str == 'yesterday':
        return datetime.now().date() - timedelta(days=1)
    elif date_str == 'tomorrow':
        return datetime.now().date() + timedelta(days=1)
    
    # Try different date formats
    formats = [
        "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S",
        "%B %d, %Y", "%b %d, %Y", "%d-%m-%Y", "%m-%d-%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # If no format matches, return today
    print(f"Warning: Could not parse date '{date_input}', using today's date")
    return datetime.now().date()

def get_llm():
    """Initialize LLM for agent tools"""
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured. Please set it in the .env file.")
    
    try:
        llm = ChatGroq(
            temperature=0.1, 
            model_name="gemma2-9b-it", 
            groq_api_key=settings.groq_api_key
        )
        return llm
    except Exception as e:
        print(f"❌ Error initializing LLM: {e}")
        raise

def extract_entities_and_summarize(raw_text: str) -> Dict[str, str]:
    """Use LLM to extract entities and create summary from raw interaction text"""
    llm = get_llm()
    
    # Extract HCP names using simple pattern matching as backup
    import re
    hcp_names = re.findall(r'Dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', raw_text)
    primary_hcp = hcp_names[0] if hcp_names else ""
    
    extraction_prompt = f"""
    Analyze this sales interaction text and extract information. Return ONLY a valid JSON object:
    
    Text: "{raw_text[:1000]}..."
    
    {{
        "hcp_name": "Primary HCP name (e.g., Dr. Sarah Mitchell)",
        "interaction_type": "Meeting, Call, Email, Visit, or Conference",
        "interaction_date": "today",
        "interaction_time": "Extract complete time expression including periods like 'morning at 9:15', '4:10 PM', 'evening around 6', 'noon', 'midnight', etc.",
        "attendees": "Other attendees mentioned",
        "summary": "Brief 1-2 sentence summary of key outcomes",
        "key_discussion_points": "Main topics discussed",
        "materials_shared": "Materials provided",
        "samples_distributed": "Samples given",
        "sentiment": "Positive, Neutral, or Negative",
        "follow_up_actions": "Next steps mentioned"
    }}
    
    For interaction_time, capture the full time context including:
    - Exact times: "9:15", "4:10 PM", "14:30"
    - Time periods: "morning", "afternoon", "evening", "night"
    - Combined: "morning at 9:15", "evening around 6", "late afternoon"
    - Special times: "noon", "midnight", "lunch time", "dinner time"
    
    Return only the JSON object, no explanations.
    """
    
    try:
        response = llm.invoke(extraction_prompt)
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
        
        extracted_data = json.loads(content)
        
        # Ensure we have an HCP name
        if not extracted_data.get("hcp_name") and primary_hcp:
            extracted_data["hcp_name"] = f"Dr. {primary_hcp}"
        
        return extracted_data
        
    except Exception as e:
        print(f"Error in entity extraction: {e}")
        # Enhanced fallback with pattern matching
        return {
            "hcp_name": f"Dr. {primary_hcp}" if primary_hcp else "",
            "interaction_type": "Meeting" if "meeting" in raw_text.lower() else "Other",
            "interaction_date": "today",
            "interaction_time": "",
            "attendees": ", ".join([f"Dr. {name}" for name in hcp_names[1:3]]) if len(hcp_names) > 1 else "",
            "summary": raw_text[:200] + "..." if len(raw_text) > 200 else raw_text,
            "key_discussion_points": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
            "materials_shared": "clinical materials" if "material" in raw_text.lower() else "",
            "samples_distributed": "sample kits" if "sample" in raw_text.lower() else "",
            "sentiment": "Positive" if any(word in raw_text.lower() for word in ["excited", "positive", "successful", "agreed"]) else "Neutral",
            "follow_up_actions": ""
        }

@tool
def log_interaction(raw_interaction_text: str) -> str:
    """
    Tool 1: Log Interaction (Form Population)
    
    Analyzes interaction text and populates the form fields instead of saving to database.
    Uses LLM to extract entities, summarize content, and determine sentiment automatically.
    This is the primary tool for capturing interaction data from natural language input.
    
    Example: "I met with Dr. Sarah Johnson today at City Hospital. We discussed the new 
    cardiology treatment protocol and she seemed very interested in the efficacy data."
    """
    try:
        # Use LLM to extract structured data from raw text
        extracted_data = extract_entities_and_summarize(raw_interaction_text)
        
        # Get HCP name from extracted data
        hcp_name = extracted_data.get("hcp_name", "").strip()
        if not hcp_name:
            return json.dumps({
                "response_type": "ERROR",
                "message": "Could not identify HCP from the interaction text. Please specify the HCP name more clearly."
            })
        
        # Create field updates for form population
        field_updates = []
        
        # Map extracted data to form fields
        if hcp_name:
            field_updates.append({
                "field": "hcp_name",
                "value": hcp_name
            })
        
        if extracted_data.get("interaction_type"):
            field_updates.append({
                "field": "interaction_type",
                "value": extracted_data["interaction_type"]
            })
        
        if extracted_data.get("sentiment"):
            field_updates.append({
                "field": "sentiment",
                "value": extracted_data["sentiment"]
            })
        
        # Handle date
        extracted_date = extracted_data.get('interaction_date', 'today')
        if extracted_date:
            parsed_date = parse_date_flexibly(extracted_date)
            field_updates.append({
                "field": "date",
                "value": parsed_date.strftime('%Y-%m-%d')
            })
        
        if extracted_data.get("interaction_time"):
            # Use the comprehensive time parsing function
            time_value = parse_time_intelligently(extracted_data["interaction_time"])
            
            if time_value:  # Only add if we successfully parsed a time
                field_updates.append({
                    "field": "time",
                    "value": time_value
                })
        
        if extracted_data.get("attendees"):
            field_updates.append({
                "field": "attendees",
                "value": extracted_data["attendees"]
            })
        
        if extracted_data.get("key_discussion_points"):
            field_updates.append({
                "field": "key_discussion_points",
                "value": extracted_data["key_discussion_points"]
            })
        
        if extracted_data.get("materials_shared"):
            field_updates.append({
                "field": "materials_shared",
                "value": extracted_data["materials_shared"]
            })
        
        if extracted_data.get("samples_distributed"):
            field_updates.append({
                "field": "samples_distributed",
                "value": extracted_data["samples_distributed"]
            })
        
        if extracted_data.get("summary"):
            field_updates.append({
                "field": "summary",
                "value": extracted_data["summary"]
            })
        
        if extracted_data.get("follow_up_actions"):
            field_updates.append({
                "field": "follow_up_actions",
                "value": extracted_data["follow_up_actions"]
            })
        
        # Return JSON response for form population
        return json.dumps({
            "response_type": "FORM_POPULATE",
            "field_updates": field_updates,
            "message": f"Perfect! I've populated the form with information about your interaction with {hcp_name}. Please review and submit when ready."
        })
        
    except Exception as e:
        return json.dumps({
            "response_type": "ERROR",
            "message": f"❌ Error analyzing interaction: {str(e)}"
        })

@tool
def edit_interaction(
    interaction_id: int,
    hcp_name: str = None,
    interaction_date: str = None,
    interaction_time: str = None,
    interaction_type: Literal["Call", "Visit", "Email", "Meeting", "Conference", "Other"] = None,
    attendees: str = None,
    summary: str = None,
    key_discussion_points: str = None,
    materials_shared: str = None,
    samples_distributed: str = None,
    sentiment: Literal["Positive", "Neutral", "Negative"] = None,
    follow_up_actions: str = None,
) -> str:
    """
    Tool 2: Edit Interaction by ID
    
    Edits an existing interaction record with a Healthcare Professional (HCP).
    This tool allows modification of previously logged interaction details using the interaction ID.
    """
    db = get_db_session()
    try:
        interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
        if not interaction:
            return f"Interaction with ID {interaction_id} not found."
        
        # Update fields if provided
        if hcp_name:
            interaction.hcp_name = hcp_name
        if interaction_date:
            interaction.interaction_date = parse_date_flexibly(interaction_date)
        if interaction_time:
            interaction.interaction_time = interaction_time
        if interaction_type:
            interaction.interaction_type = interaction_type
        if attendees:
            interaction.attendees = attendees
        if summary:
            interaction.summary = summary
        if key_discussion_points:
            interaction.key_discussion_points = key_discussion_points
        if materials_shared:
            interaction.materials_shared = materials_shared
        if samples_distributed:
            interaction.samples_distributed = samples_distributed
        if sentiment:
            interaction.sentiment = sentiment
        if follow_up_actions:
            interaction.follow_up_actions = follow_up_actions
        
        db.commit()
        return f"✅ Successfully updated interaction ID {interaction_id}"
    except Exception as e:
        db.rollback()
        return f"❌ Error updating interaction: {str(e)}"
    finally:
        db.close()

@tool
def edit_interaction_by_name(
    hcp_name_search: str,
    interaction_date: str = None,
    interaction_time: str = None,
    interaction_type: Literal["Call", "Visit", "Email", "Meeting", "Conference", "Other"] = None,
    attendees: str = None,
    summary: str = None,
    key_discussion_points: str = None,
    materials_shared: str = None,
    samples_distributed: str = None,
    sentiment: Literal["Positive", "Neutral", "Negative"] = None,
    follow_up_actions: str = None,
) -> str:
    """
    Tool 2b: Edit Interaction by HCP Name
    
    Edits the most recent interaction record for a Healthcare Professional (HCP) by name.
    This tool finds interactions by HCP name and allows modification of the most recent one.
    """
    db = get_db_session()
    try:
        # Search for interactions with the HCP name (case-insensitive partial match)
        interactions = db.query(models.Interaction).filter(
            models.Interaction.hcp_name.ilike(f"%{hcp_name_search}%")
        ).order_by(models.Interaction.created_at.desc()).all()
        
        if not interactions:
            return f"No interactions found for HCP name containing '{hcp_name_search}'."
        
        if len(interactions) > 1:
            # Show available interactions and ask for ID selection
            interaction_list = "\n".join([
                f"  - ID {int.id}: {int.hcp_name} on {int.interaction_date} at {int.interaction_time or 'N/A'}"
                for int in interactions[:10]  # Show first 10
            ])
            return f"Multiple interactions found for '{hcp_name_search}':\n{interaction_list}\n\nPlease use 'edit interaction [ID]' to specify which interaction to edit."
        
        # Update the single matching interaction
        interaction = interactions[0]
        
        # Update fields if provided
        if interaction_date:
            interaction.interaction_date = parse_date_flexibly(interaction_date)
        if interaction_time:
            interaction.interaction_time = interaction_time
        if interaction_type:
            interaction.interaction_type = interaction_type
        if attendees:
            interaction.attendees = attendees
        if summary:
            interaction.summary = summary
        if key_discussion_points:
            interaction.key_discussion_points = key_discussion_points
        if materials_shared:
            interaction.materials_shared = materials_shared
        if samples_distributed:
            interaction.samples_distributed = samples_distributed
        if sentiment:
            interaction.sentiment = sentiment
        if follow_up_actions:
            interaction.follow_up_actions = follow_up_actions
        
        db.commit()
        return f"✅ Successfully updated interaction for {interaction.hcp_name} (ID {interaction.id})"
    except Exception as e:
        db.rollback()
        return f"❌ Error updating interaction: {str(e)}"
    finally:
        db.close()

@tool
def update_form_field(field_name: str, field_value: str) -> str:
    """
    Tool 3: PUT Form Update
    
    Updates form fields on the frontend. This tool handles PUT commands like 
    "put sentiment as positive" by returning structured data for the frontend form.
    
    Supported fields: sentiment, interaction_type, summary, key_discussion_points,
    materials_shared, samples_distributed, follow_up_actions, attendees, date, time, hcp_name
    """
    try:
        # Field mapping and normalization (must match frontend exactly)
        field_mapping = {
            # Primary field mappings
            'sentiment': 'hcpSentiment',
            'interaction_type': 'interactionType',
            'summary': 'outcomes',
            'key_discussion_points': 'topicsDiscussed',
            'materials_shared': 'materialsShared',
            'samples_distributed': 'samplesDistributed',
            'follow_up_actions': 'followUpActions',
            'attendees': 'attendees',
            'date': 'date',
            'time': 'time',
            'hcp_name': 'hcpName',
            
            # Alternative field names (for different PUT command variations)
            'materials': 'materialsShared',
            'samples': 'samplesDistributed',
            'follow_up': 'followUpActions',
            'topics': 'topicsDiscussed',
            'discussion': 'topicsDiscussed',
            'outcomes': 'outcomes',
            'results': 'outcomes',
            'type': 'interactionType',
            'interaction_date': 'date',
            'interaction_time': 'time',
            'name': 'hcpName',
            'doctor': 'hcpName',
            'hcp': 'hcpName',
            
            # Sentiment variations
            'feeling': 'hcpSentiment',
            'mood': 'hcpSentiment',
            'reaction': 'hcpSentiment',
            
            # Date/time variations
            'when': 'date',
            'meeting_date': 'date',
            'meeting_time': 'time'
        }
        
        # Handle both space-separated and underscore-separated field names
        field_key = field_name.lower()
        form_field = field_mapping.get(field_key, field_mapping.get(field_key.replace(' ', '_'), field_name))
        
        # Normalize values (must match frontend exactly)
        if form_field == 'hcpSentiment':
            sentiment_map = {
                'positive': 'Positive', 'good': 'Positive', 'happy': 'Positive',
                'pleased': 'Positive', 'satisfied': 'Positive',
                'neutral': 'Neutral', 'okay': 'Neutral', 'fine': 'Neutral', 'average': 'Neutral',
                'negative': 'Negative', 'bad': 'Negative', 'unhappy': 'Negative',
                'dissatisfied': 'Negative', 'concerned': 'Negative'
            }
            field_value = sentiment_map.get(field_value.lower(), field_value)
        
        if form_field == 'interactionType':
            type_map = {
                'meeting': 'Meeting', 'call': 'Call', 'phone': 'Call',
                'email': 'Email', 'visit': 'Visit', 'conference': 'Conference', 'other': 'Other'
            }
            field_value = type_map.get(field_value.lower(), field_value)
        
        return json.dumps({
            "field": form_field,
            "value": field_value,
            "response_type": "FORM_UPDATE",
            "message": f"✅ Updated {field_name} to '{field_value}'"
        })
        
    except Exception as e:
        return json.dumps({
            "error": f"Error updating form field: {str(e)}",
            "response_type": "ERROR",
            "message": "❌ Error updating form field"
        })

@tool
def get_interaction_history(hcp_name: str) -> str:
    """
    Tool 4: Get Interaction History
    
    Retrieves the interaction history for a specific Healthcare Professional (HCP).
    Returns a formatted summary of past interactions including dates, types, and sentiments.
    """
    db = get_db_session()
    try:
        # Improve search logic for better HCP name matching
        search_terms = [hcp_name]
        
        # If searching for "Dr. LastName", also try just "LastName"
        if hcp_name.startswith("Dr. ") and len(hcp_name.split()) == 2:
            last_name = hcp_name.split()[1]
            search_terms.append(last_name)
        
        # Try each search term until we find matches
        interactions = []
        for term in search_terms:
            interactions = db.query(models.Interaction).filter(
                models.Interaction.hcp_name.ilike(f"%{term}%")
            ).order_by(models.Interaction.interaction_date.desc()).all()
            if interactions:
                break
        
        if not interactions:
            return f"No interactions found for {hcp_name}."
        
        results = []
        for interaction in interactions:
            results.append(
                f"📅 {interaction.interaction_date} | 📞 {interaction.interaction_type} | "
                f"😊 {interaction.sentiment} | 📝 {interaction.summary[:100]}..."
            )
        
        return f"📋 Interaction history for {hcp_name} ({len(interactions)} interactions):\n\n" + "\n".join(results)
    except Exception as e:
        return f"❌ Error retrieving interaction history: {str(e)}"
    finally:
        db.close()

@tool
def generate_sales_insights(hcp_name: str = "", period_days: int = 30) -> str:
    """
    Tool 5: Generate Sales Insights
    
    Uses LLM to generate strategic sales insights and recommendations based on interaction data.
    Can analyze a specific HCP or provide overall sales pipeline insights.
    """
    db = get_db_session()
    try:
        # Build query based on parameters with improved search logic
        query = db.query(models.Interaction)
        if hcp_name:
            # Try multiple search terms for better matching
            search_terms = [hcp_name]
            
            # If searching for "Dr. LastName", also try just "LastName"
            if hcp_name.startswith("Dr. ") and len(hcp_name.split()) == 2:
                last_name = hcp_name.split()[1]
                search_terms.append(last_name)
            
            # Use OR conditions for multiple search terms
            from sqlalchemy import or_
            conditions = [models.Interaction.hcp_name.ilike(f"%{term}%") for term in search_terms]
            query = query.filter(or_(*conditions))
        
        # Filter by time period
        cutoff_date = datetime.now().date() - timedelta(days=period_days)
        interactions = query.filter(models.Interaction.interaction_date >= cutoff_date).all()
        
        if not interactions:
            target = hcp_name if hcp_name else "your sales activities"
            return f"No recent interactions found for {target} in the last {period_days} days."
        
        # Prepare data for LLM analysis
        interaction_data = []
        for interaction in interactions:
            interaction_data.append({
                'hcp_name': interaction.hcp_name,
                'date': str(interaction.interaction_date),
                'type': interaction.interaction_type,
                'summary': interaction.summary,
                'sentiment': interaction.sentiment
            })
        
        llm = get_llm()
        
        insights_prompt = f"""
        Analyze the following sales interaction data and provide strategic insights:
        
        Target: {hcp_name if hcp_name else 'Overall Sales Pipeline'}
        Period: Last {period_days} days
        Total Interactions: {len(interactions)}
        
        Interaction Data:
        {json.dumps(interaction_data, indent=2)}
        
        Provide analysis in JSON format with these fields:
        - engagement_summary: Overall engagement assessment
        - sentiment_analysis: Breakdown of positive/neutral/negative interactions
        - top_opportunities: List of high-potential HCPs or opportunities
        - relationship_trends: Key trends in HCP relationships
        - strategic_recommendations: Specific actionable recommendations
        - success_metrics: Key performance indicators
        
        Return only valid JSON format.
        """
        
        response = llm.invoke(insights_prompt)
        content = response.content.strip()
        
        # Clean the response to extract JSON
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        insights_data = json.loads(content)
        
        # Format the result for display
        target_label = hcp_name if hcp_name else "Sales Pipeline"
        result = f"🧠 Sales Insights - {target_label} (Last {period_days} days):\n\n"
        result += f"📊 Engagement Summary: {insights_data.get('engagement_summary', 'N/A')}\n\n"
        result += f"💭 Sentiment Analysis: {insights_data.get('sentiment_analysis', 'N/A')}\n\n"
        result += f"🎯 Top Opportunities:\n"
        opportunities = insights_data.get('top_opportunities', [])
        for i, opp in enumerate(opportunities, 1):
            result += f"  {i}. {opp}\n"
        
        result += f"\n📈 Relationship Trends: {insights_data.get('relationship_trends', 'N/A')}\n\n"
        result += f"🚀 Strategic Recommendations:\n"
        recommendations = insights_data.get('strategic_recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            result += f"  {i}. {rec}\n"
        
        result += f"\n📊 Success Metrics: {insights_data.get('success_metrics', 'N/A')}"
        
        return result
        
    except Exception as e:
        return f"❌ Error generating sales insights: {str(e)}"
    finally:
        db.close()

@tool
def form_information_tool(form_data: str) -> str:
    """
    Tool 6: Form Information Tool
    
    Analyzes the current form data and provides a summary to the user.
    This tool helps the AI assistant understand what information is currently
    filled in the HCP interaction form and can provide insights or summaries.
    
    The form_data parameter should contain the current form state as JSON string.
    """
    try:
        # Parse the form data
        form_info = json.loads(form_data) if form_data else {}
        
        # Extract form fields
        hcp_name = form_info.get('hcpName', '').strip()
        interaction_type = form_info.get('interactionType', '').strip()
        date = form_info.get('date', '').strip()
        time = form_info.get('time', '').strip()
        attendees = form_info.get('attendees', '').strip()
        topics_discussed = form_info.get('topicsDiscussed', '').strip()
        materials_shared = form_info.get('materialsShared', '').strip()
        samples_distributed = form_info.get('samplesDistributed', '').strip()
        hcp_sentiment = form_info.get('hcpSentiment', '').strip()
        outcomes = form_info.get('outcomes', '').strip()
        follow_up_actions = form_info.get('followUpActions', '').strip()
        
        # Create a comprehensive summary
        summary_parts = []
        
        # Basic interaction details
        if hcp_name:
            summary_parts.append(f"👤 HCP: {hcp_name}")
        else:
            summary_parts.append("👤 HCP: Not specified")
        
        if interaction_type:
            summary_parts.append(f"📞 Type: {interaction_type}")
        else:
            summary_parts.append("📞 Type: Not specified")
        
        if date:
            summary_parts.append(f"📅 Date: {date}")
        else:
            summary_parts.append("📅 Date: Not specified")
        
        if time:
            summary_parts.append(f"⏰ Time: {time}")
        else:
            summary_parts.append("⏰ Time: Not specified")
        
        # Additional details
        if attendees:
            summary_parts.append(f"👥 Attendees: {attendees}")
        
        if topics_discussed:
            summary_parts.append(f"💬 Topics: {topics_discussed[:100]}{'...' if len(topics_discussed) > 100 else ''}")
        
        if materials_shared:
            summary_parts.append(f"📄 Materials: {materials_shared}")
        
        if samples_distributed:
            summary_parts.append(f"🧪 Samples: {samples_distributed}")
        
        if hcp_sentiment:
            sentiment_emoji = "😊" if hcp_sentiment == "Positive" else "😐" if hcp_sentiment == "Neutral" else "😞"
            summary_parts.append(f"{sentiment_emoji} Sentiment: {hcp_sentiment}")
        
        if outcomes:
            summary_parts.append(f"🎯 Outcomes: {outcomes[:100]}{'...' if len(outcomes) > 100 else ''}")
        
        if follow_up_actions:
            summary_parts.append(f"📋 Follow-up: {follow_up_actions[:100]}{'...' if len(follow_up_actions) > 100 else ''}")
        
        # Check completeness
        required_fields = ['hcpName', 'interactionType', 'date']
        filled_required = sum(1 for field in required_fields if form_info.get(field, '').strip())
        completeness = (filled_required / len(required_fields)) * 100
        
        # Count total filled fields
        all_fields = ['hcpName', 'interactionType', 'date', 'time', 'attendees', 'topicsDiscussed', 
                     'materialsShared', 'samplesDistributed', 'hcpSentiment', 'outcomes', 'followUpActions']
        filled_fields = sum(1 for field in all_fields if form_info.get(field, '').strip())
        
        # Create final summary
        result = "📋 **Current Form Summary**\n\n"
        result += "\n".join(summary_parts)
        result += f"\n\n📊 **Form Status:**\n"
        result += f"• Required fields completed: {filled_required}/{len(required_fields)} ({completeness:.0f}%)\n"
        result += f"• Total fields filled: {filled_fields}/{len(all_fields)}\n"
        
        if completeness >= 100:
            result += f"✅ Form is ready for submission!"
        elif completeness >= 66:
            result += f"⚠️ Form is mostly complete - consider adding more details"
        else:
            result += f"❌ Form needs more information before submission"
        
        return result
        
    except json.JSONDecodeError:
        return "❌ Error: Invalid form data format. Please provide valid JSON."
    except Exception as e:
        return f"❌ Error analyzing form: {str(e)}"