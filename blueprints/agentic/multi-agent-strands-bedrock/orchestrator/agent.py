import json
import datetime
from boto3 import Session
from strands import Agent, tool
from strands.models import BedrockModel

sess = Session()

class TravelPlannerAgent():
    """
    An orchestration agent that coordinates between a weather agent and an itinerary agent
    to create weather-optimized travel plans.
    """

    def __init__(self):

        SYSTEM_INSTRUCTION = f"""
            You are a specialized assistant for travel planning. 
            Your sole purpose is to use the  tool to answer questions about conversions. 
            If the user asks about anything other than mathematical conversions,
            politely state that you cannot help with that topic and can only assist with math conversion-related queries. 
            Do not attempt to answer unrelated questions or use tools for other purposes.
            Set response status to input_required if the user needs to provide more information.
            Set response status to error if there is an error while processing the request.
            Set response status to completed if the request is complete.
        """
        self.model = BedrockModel(
            model_id='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
            boto_session=sess,
            temperature=0.01,
        )
        self.agent = Agent(
            system_prompt=SYSTEM_INSTRUCTION, model=self.model, tools=[calculator]
        )

    def invoke(self, query, context) -> str:
        return self.get_agent_response(query)

    def get_agent_response(self, query):
        result = self.agent(query)
        response_text = result.message["content"][0]["text"]
        
        # Extract JSON from between <json_out> tags
        json_pattern = r'<json_out>(.*?)</json_out>'
        json_match = re.search(json_pattern, response_text, re.DOTALL)
        
        if json_match:
            json_content = json_match.group(1).strip()
            try:
                response_data = json.loads(json_content)
                structured_response = ResponseFormat(**response_data)
            except (json.JSONDecodeError, ValidationError) as e:
                print(f"Parsing error: {e}")
                structured_response = ResponseFormat(
                    status="error", message="Unable to process response format"
                )
        else:
            print("No <json_out> tags found in response")
            structured_response = ResponseFormat(
                status="error", message="No JSON output tags found in response"
            )

        # Use the structured_response instead of undefined current_state
        if structured_response.status == "input_required":
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "content": structured_response.message,
            }
        if structured_response.status == "error":
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "content": structured_response.message,
            }
        if structured_response.status == "completed":
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": structured_response.message,
            }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",
        }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def register_tools(self):
        """Register the tools this agent can use."""

        @tool
        def get_weather_forecast(location: str, start_date: str, end_date: str) -> Dict[str, Any]:
            """
            Get weather forecast for a location during a specific date range by communicating with the WeatherAgent.
            """
            # Create a message to send to the WeatherAgent
            message = Message(
                content=f"Get weather forecast for {location} from {start_date} to {end_date}",
                metadata={
                    "location": location,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )

            # Send message to WeatherAgent using A2A communication
            response = self.send_message_to_agent("WeatherAgent", message)

            # Parse and return the weather data
            return json.loads(response.content)

        @tool
        def get_location_itinerary(location: str, interests: List[str], duration_days: int) -> Dict[str, Any]:
            """
            Get an itinerary for a location based on interests by communicating with the ItineraryAgent.
            """
            # Create a message to send to the ItineraryAgent
            message = Message(
                content=f"Create an itinerary for {location} focused on {', '.join(interests)} for {duration_days} days",
                metadata={
                    "location": location,
                    "interests": interests,
                    "duration_days": duration_days
                }
            )

            # Send message to ItineraryAgent using A2A communication
            response = self.send_message_to_agent("ItineraryAgent", message)

            # Parse and return the itinerary data
            return json.loads(response.content)

        @tool
        def create_weather_optimized_plan(location: str, start_date: str, duration_days: int, interests: List[str]) -> Dict[str, Any]:
            """
            Create a travel plan optimized for weather conditions.
            """
            # Calculate end date
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end = start + datetime.timedelta(days=duration_days-1)
            end_date = end.strftime("%Y-%m-%d")

            # Get weather forecast
            weather_data = self.get_weather_forecast(location, start_date, end_date)

            # Get basic itinerary
            itinerary_data = self.get_location_itinerary(location, interests, duration_days)

            # Optimize itinerary based on weather
            optimized_plan = self._optimize_itinerary_for_weather(weather_data, itinerary_data)

            return optimized_plan

    def _optimize_itinerary_for_weather(self, weather_data: Dict[str, Any], itinerary_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize an itinerary based on weather conditions.
        """
        optimized_plan = {
            "location": itinerary_data["location"],
            "duration_days": itinerary_data["duration_days"],
            "weather_summary": self._generate_weather_summary(weather_data),
            "daily_plan": [],
            "recommendations": []
        }

        # Extract activities from itinerary
        all_activities = []
        for day in itinerary_data["daily_plan"]:
            all_activities.extend(day["activities"])

        # Categorize activities as indoor or outdoor
        indoor_activities = [a for a in all_activities if a.get("type") == "indoor"]
        outdoor_activities = [a for a in all_activities if a.get("type") == "outdoor"]
        other_activities = [a for a in all_activities if a.get("type") not in ["indoor", "outdoor"]]

        # Sort days by weather quality (best to worst)
        weather_days = weather_data["daily"]
        weather_quality = []

        for i, day in enumerate(weather_days):
            # Calculate a weather score (higher is better weather)
            score = 100
            if "rain" in day["description"].lower():
                score -= 50
            if "storm" in day["description"].lower():
                score -= 70
            if "snow" in day["description"].lower():
                score -= 40
            if "cloud" in day["description"].lower():
                score -= 20

            # Adjust for temperature (assume ideal is around 75°F/24°C)
            temp = day["temperature"]["average"]
            temp_diff = abs(temp - 75)
            score -= temp_diff

            weather_quality.append({"day_index": i, "score": score, "weather": day})

        # Sort days by weather quality
        weather_quality.sort(key=lambda x: x["score"], reverse=True)

        # Assign activities to days based on weather
        days_plan = []
        for _ in range(len(weather_days)):
            days_plan.append({"activities": []})

        # Assign outdoor activities to best weather days
        outdoor_index = 0
        for day_info in weather_quality:
            day_index = day_info["day_index"]

            if outdoor_index < len(outdoor_activities):
                days_plan[day_index]["activities"].append(outdoor_activities[outdoor_index])
                outdoor_index += 1

        # Fill remaining days with indoor and other activities
        activity_index = 0
        combined_activities = indoor_activities + other_activities

        for day_index in range(len(days_plan)):
            # Add 2-3 activities per day
            while len(days_plan[day_index]["activities"]) < 3 and activity_index < len(combined_activities):
                days_plan[day_index]["activities"].append(combined_activities[activity_index])
                activity_index += 1

        # Format the daily plan with weather information
        for day_index, day_plan in enumerate(days_plan):
            day_weather = weather_days[day_index]
            date = datetime.datetime.strptime(day_weather["date"], "%Y-%m-%d")

            optimized_plan["daily_plan"].append({
                "day": day_index + 1,
                "date": day_weather["date"],
                "day_of_week": date.strftime("%A"),
                "weather": {
                    "description": day_weather["description"],
                    "temperature": day_weather["temperature"],
                    "precipitation_chance": day_weather.get("precipitation_chance", 0)
                },
                "activities": day_plan["activities"],
                "weather_notes": self._generate_weather_notes(day_weather)
            })

        # Add overall recommendations
        optimized_plan["recommendations"] = self._generate_recommendations(weather_data, itinerary_data)

        return optimized_plan

    def _generate_weather_summary(self, weather_data: Dict[str, Any]) -> str:
        """Generate a summary of the weather for the trip duration."""
        conditions = [day["description"] for day in weather_data["daily"]]
        temps = [day["temperature"]["average"] for day in weather_data["daily"]]

        avg_temp = sum(temps) / len(temps)
        condition_counts = {}
        for condition in conditions:
            condition_counts[condition] = condition_counts.get(condition, 0) + 1

        most_common = max(condition_counts.items(), key=lambda x: x[1])

        return f"Average temperature will be {avg_temp:.1f}°F with mostly {most_common[0].lower()} conditions."

    def _generate_weather_notes(self, day_weather: Dict[str, Any]) -> str:
        """Generate weather-specific notes for a day."""
        notes = []
        desc = day_weather["description"].lower()
        temp = day_weather["temperature"]["average"]

        if "rain" in desc or "shower" in desc:
            notes.append("Bring an umbrella and waterproof clothing.")
        if "snow" in desc:
            notes.append("Dress warmly with waterproof boots.")
        if temp > 85:
            notes.append("Stay hydrated and use sun protection.")
        if temp < 50:
            notes.append("Dress in warm layers.")

        return " ".join(notes) if notes else "Weather conditions are favorable."

    def _generate_recommendations(self, weather_data: Dict[str, Any], itinerary_data: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations based on weather and itinerary."""
        recommendations = []

        # Check for extreme weather
        has_rain = any("rain" in day["description"].lower() for day in weather_data["daily"])
        has_extreme_heat = any(day["temperature"]["high"] > 90 for day in weather_data["daily"])
        has_extreme_cold = any(day["temperature"]["low"] < 32 for day in weather_data["daily"])

        if has_rain:
            recommendations.append("Pack waterproof clothing and an umbrella.")
        if has_extreme_heat:
            recommendations.append("Bring lightweight clothing, sun protection, and stay hydrated.")
        if has_extreme_cold:
            recommendations.append("Pack warm clothing, gloves, and a hat.")

        # Add activity-based recommendations
        all_activities = []
        for day in itinerary_data["daily_plan"]:
            all_activities.extend(day["activities"])

        activity_types = set(a.get("category", "") for a in all_activities)

        if "hiking" in activity_types:
            recommendations.append("Bring comfortable hiking shoes and appropriate outdoor gear.")
        if "beach" in activity_types:
            recommendations.append("Don't forget swimwear and beach essentials.")
        if "museum" in activity_types:
            recommendations.append("Check museum hours and consider booking tickets in advance.")

        return recommendations

    def process_message(self, message: Message) -> Message:
        """
        Process incoming messages and generate travel plans.
        """
        try:
            # Extract request details from the message
            content = message.content
            metadata = message.metadata or {}

            location = metadata.get("location", "")
            start_date = metadata.get("start_date", "")
            duration_days = metadata.get("duration_days", 3)
            interests = metadata.get("interests", ["sightseeing", "food", "culture"])

            # Create a weather-optimized travel plan
            travel_plan = self.create_weather_optimized_plan(
                location=location,
                start_date=start_date,
                duration_days=duration_days,
                interests=interests
            )

            # Format the response
            response_content = json.dumps(travel_plan, indent=2)

            return Message(
                content=f"Here's your weather-optimized travel plan for {location}:\n\n{response_content}",
                metadata={"travel_plan": travel_plan}
            )

        except Exception as e:
            return Message(
                content=f"Error creating travel plan: {str(e)}",
                metadata={"error": str(e)}
            )
    def send_message_to_agent(self, agent_name: str, message: Message) -> Message:
        """
        Send a message to another agent.
        """
        # Find the agent in the list of agents
        agent = next((a for a in self.agents if a.name == agent_name), None)

        if agent is None:
            raise ValueError(f"Agent '{agent_name}' not found")

        # Send the message to the agent
        return agent.process_message(message)
