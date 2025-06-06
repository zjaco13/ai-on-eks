from fastapi import FastAPI
import os
import re
import json
import uuid
from datetime import datetime
from strands import Agent, tool
import requests
import redis
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from typing import List, Dict, Any

from app.weather.schemas import QueryRequest

app = FastAPI(title="Weather and Time Agent with Memory")
geolocator = Nominatim(user_agent="weather-time-agent")
tf = TimezoneFinder()

# Redis connection with error handling
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true'
    )
    redis_client.ping()  # Test connection
    print("Redis connected successfully")
except Exception as e:
    print(f"Redis connection error: {e}")
    redis_client = None

# Memory functions
def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    """Get chat history from Redis"""
    if not redis_client:
        return []
        
    try:
        history_json = redis_client.get(f"chat:{session_id}")
        if history_json:
            return json.loads(history_json)
    except Exception as e:
        print(f"Error getting chat history: {e}")
    return []

def save_chat_message(session_id: str, role: str, content: str) -> bool:
    """Save a message to chat history in Redis"""
    if not redis_client:
        return False
        
    try:
        history = get_chat_history(session_id)
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        redis_client.setex(
            f"chat:{session_id}", 
            86400,  # 24 hours in seconds
            json.dumps(history)
        )
        return True
    except Exception as e:
        print(f"Error saving chat message: {e}")
        return False

@tool
def current_time(location: str) -> str:
    """Get the current time for a location."""
    timezone = get_timezone_for_location(location)
    try:
        tz = pytz.timezone(timezone)
        dt = datetime.now(tz)
        return dt.strftime("%Y-%m-%d %I:%M %p %Z")
    except Exception:
        return str(datetime.now())

@tool
def current_weather(location: str) -> str:
    """Get the current weather for a location."""
    try:
        location_data = geolocator.geocode(location)
        if not location_data:
            return "Location not found."

        lat, lon = location_data.latitude, location_data.longitude

        # Open-Meteo API call
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code"
            "&timezone=auto"
        )

        response = requests.get(url)
        if response.status_code != 200:
            return f"Failed to get weather: {response.status_code}"

        data = response.json()
        temperature = data.get("current", {}).get("temperature_2m", "N/A")
        weather_code = data.get("current", {}).get("weather_code", "N/A")

        weather_desc = weather_code_to_description(weather_code)
        return f"{weather_desc}, {temperature}°C"

    except Exception as e:
        return f"Error fetching weather: {str(e)}"

# WMO weather code mapping (simplified)
def weather_code_to_description(code):
    mapping = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Moderate snow",
        75: "Heavy snow",
        95: "Thunderstorm",
    }
    return mapping.get(code, f"Unknown (code {code})")

def get_timezone_for_location(location):
    try:
        location_data = geolocator.geocode(location)
        if location_data:
            timezone = tf.timezone_at(lng=location_data.longitude, lat=location_data.latitude)
            return timezone or "UTC"
    except Exception:
        pass
    return "UTC"

# Create model configuration
model_config = {
    "api_key": os.getenv('HUGGING_FACE_TOKEN', 'dummy-token'),
    "api_base": os.getenv('MISTRAL_API_BASE', 'http://mistral:8000/v1'),
    "model": os.getenv('MISTRAL_MODEL', 'mistralai/Mistral-7B-Instruct-v0.3'),
    "max_tokens": int(os.getenv('MAX_TOKENS', '1000')),
    "temperature": float(os.getenv('TEMPERATURE', '0.7'))
}

@app.get("/health")
async def health_check():
    if redis_client:
        try:
            redis_client.ping()
            return {"status": "healthy", "redis": "connected"}
        except:
            pass
    return {"status": "healthy", "redis": "disconnected"}

@app.post("/ask")
async def ask_agent(request: QueryRequest):
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get chat history
        history = get_chat_history(session_id)
        
        # Save user query to history
        save_chat_message(session_id, "user", request.query)
        
        # Check for follow-up questions about previous locations
        location = None
        location_match = re.search(r'in\s+([A-Za-z\s]+)', request.query, re.IGNORECASE)
        
        if location_match:
            location = location_match.group(1).strip()
        elif "there" in request.query.lower() and history:
            # Look for previous locations in history
            for msg in reversed(history):
                if msg["role"] == "user":
                    prev_location_match = re.search(r'in\s+([A-Za-z\s]+)', msg["content"], re.IGNORECASE)
                    if prev_location_match:
                        location = prev_location_match.group(1).strip()
                        break
        
        if not location:
            response = "Please specify a location in your query (e.g., 'in Tokyo')"
            save_chat_message(session_id, "assistant", response)
            return {
                "status": "error", 
                "message": response,
                "session_id": session_id
            }
        
        is_time_query = "time" in request.query.lower()
        is_weather_query = "weather" in request.query.lower() or "there" in request.query.lower()
        
        facts = []
        
        if is_time_query:
            time_result = current_time(location)
            facts.append(f"The current time in {location} is {time_result}.")
        
        if is_weather_query:
            weather_result = current_weather(location)
            facts.append(f"The weather in {location} is {weather_result}.")
        
        if facts:
            try:
                # Include chat history in the prompt if available
                context = ""
                if history and len(history) > 1:
                    context = "Previous conversation:\n" + "\n".join([
                        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                        for msg in history[-3:]  # Last 3 messages
                    ]) + "\n\n"
                
                enhanced_prompt = f"""
                {context}Based ONLY on these facts:
                {' '.join(facts)}

                Create a single, natural, conversational response that includes ONLY this information.
                Do not include placeholders like [weather in X] or [time in X].
                If relevant to the conversation history, make references to previous exchanges.
                """
                
                # Create a new model and agent instance for this request
                agent = Agent(
                    system_prompt="You are a helpful assistant that provides information about time and weather. Use the tools to get accurate information. Reference previous conversations when appropriate.",
                    tools=[current_time, current_weather]
                )
                
                result = agent(enhanced_prompt)
                enhanced_response = str(result)

                # Clean up the response
                if "Based on these facts:" in enhanced_response:
                    enhanced_response = enhanced_response.split("Based on these facts:")[0].strip()
                elif "\n\n" in enhanced_response:
                    enhanced_response = enhanced_response.split("\n\n")[0].strip()

                # Remove any quotes
                enhanced_response = enhanced_response.strip('"\'')
                
                # Save assistant response to history
                save_chat_message(session_id, "assistant", enhanced_response)
                
                return {
                    "status": "success", 
                    "response": enhanced_response,
                    "session_id": session_id
                }
            except Exception as e:
                print(f"Error enhancing response: {e}")
                response = " ".join(facts)
                save_chat_message(session_id, "assistant", response)
                return {
                    "status": "success", 
                    "response": response,
                    "session_id": session_id
                }
        else:
            response = "Please ask about time or weather"
            save_chat_message(session_id, "assistant", response)
            return {
                "status": "error", 
                "message": response,
                "session_id": session_id
            }
            
    except Exception as e:
        print(f"Error in ask_agent: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get chat history for a session"""
    history = get_chat_history(session_id)
    return {"session_id": session_id, "history": history}