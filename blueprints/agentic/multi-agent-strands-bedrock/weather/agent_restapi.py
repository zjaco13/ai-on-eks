#!/usr/bin/env python3
"""
Weather Agent REST API Server

Provides a REST API interface for the weather agent, allowing HTTP clients
to interact with weather forecast and alert functionality with session state management.
"""

import os
import logging
import secrets
import time
from typing import Dict, Any, Optional, List
from functools import wraps
from flask import Flask, request, jsonify, session
from agent import get_weather_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherRestAPI:
    """REST API wrapper for the Weather Agent with session state management"""

    def __init__(self, host: str = "0.0.0.0", port: int = 3000):
        self.host = host
        self.port = port
        self.app = Flask(__name__)

        # Configure Flask session
        self.app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

        # API Key configuration (optional)
        self.api_key = os.getenv('API_KEY')
        self.require_api_key = os.getenv('REQUIRE_API_KEY', 'false').lower() == 'true'

        # Session configuration
        self.app.config.update(
            SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true',
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
            PERMANENT_SESSION_LIFETIME=int(os.getenv('SESSION_LIFETIME', '3600'))  # 1 hour default
        )

        # Store agent instances per session
        self.session_agents: Dict[str, Any] = {}

        self._setup_routes()

    def _require_api_key(self, f):
        """Decorator to require API key authentication if enabled"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.require_api_key:
                return f(*args, **kwargs)

            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            if not api_key or api_key != self.api_key:
                logger.warning(f"Invalid API key attempt from {request.remote_addr}")
                return jsonify({
                    "error": "Invalid or missing API key",
                    "message": "Provide API key in X-API-Key header or api_key query parameter"
                }), 401
            return f(*args, **kwargs)
        return decorated_function

    def _get_session_id(self) -> str:
        """Get or create a session ID"""
        if 'session_id' not in session:
            session['session_id'] = secrets.token_hex(16)
            session.permanent = True
            logger.info(f"Created new session: {session['session_id']}")
        return session['session_id']

    def _get_session_agent(self, session_id: str):
        """Get or create an agent for the session"""
        if session_id not in self.session_agents:
            logger.info(f"Creating new agent for session: {session_id}")
            try:
                self.session_agents[session_id] = get_weather_agent()
            except Exception as e:
                logger.error(f"Failed to create agent for session {session_id}: {str(e)}")
                raise
        return self.session_agents[session_id]

    def _get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for the session"""
        if 'conversations' not in session:
            session['conversations'] = []
        return session['conversations']

    def _add_to_conversation_history(self, session_id: str, query: str, response: str):
        """Add a message pair to the conversation history"""
        if 'conversations' not in session:
            session['conversations'] = []

        session['conversations'].append({
            "query": query,
            "response": response,
            "timestamp": time.time()
        })

        # Keep only last 20 exchanges to prevent session from growing too large
        max_history = int(os.getenv('MAX_CONVERSATION_HISTORY', '20'))
        if len(session['conversations']) > max_history:
            session['conversations'] = session['conversations'][-max_history:]

        session.modified = True

    def _build_context_from_history(self, history: List[Dict[str, str]]) -> str:
        """Build context string from conversation history"""
        if not history:
            return ""

        context_window = int(os.getenv('CONTEXT_WINDOW_SIZE', '5'))
        recent_history = history[-context_window:]

        context = "\n\nPrevious conversation context:\n"
        for i, exchange in enumerate(recent_history, 1):
            # Truncate long responses for context
            response_preview = exchange['response'][:100] + "..." if len(exchange['response']) > 100 else exchange['response']
            context += f"{i}. User: {exchange['query']}\n   Assistant: {response_preview}\n"
        context += "\nCurrent question:\n"

        return context

    def _cleanup_old_sessions(self):
        """Clean up old agent instances (basic memory management)"""
        # Simple cleanup: remove agents for sessions that haven't been used recently
        # In production, you might want more sophisticated cleanup
        if len(self.session_agents) > 100:  # Arbitrary threshold
            logger.info(f"Cleaning up old sessions. Current count: {len(self.session_agents)}")
            # Keep only the most recent 50 sessions (simple FIFO)
            session_ids = list(self.session_agents.keys())
            for session_id in session_ids[:-50]:
                del self.session_agents[session_id]
            logger.info(f"Cleaned up sessions. New count: {len(self.session_agents)}")

    def _setup_routes(self):
        """Configure Flask routes"""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "service": "weather-agent-rest-api",
                "version": "0.2.0",
                "features": {
                    "session_management": True,
                    "api_key_auth": self.require_api_key,
                    "conversation_history": True
                },
                "stats": {
                    "active_sessions": len(self.session_agents)
                }
            })

        @self.app.route('/chat', methods=['POST'])
        @self._require_api_key
        def chat():
            """Chat with the weather assistant with session state"""
            try:
                # Validate request
                if not request.is_json:
                    return jsonify({
                        "error": "Content-Type must be application/json"
                    }), 400

                data = request.get_json()
                if not data or 'query' not in data:
                    return jsonify({
                        "error": "Missing 'query' parameter in request body"
                    }), 400

                query = data['query'].strip()
                if not query:
                    return jsonify({
                        "error": "Query cannot be empty"
                    }), 400

                session_id = self._get_session_id()
                logger.info(f"Processing chat request for session {session_id}: {query}")

                # Periodic cleanup
                self._cleanup_old_sessions()

                # Get the agent for this session
                agent = self._get_session_agent(session_id)

                # Get conversation history and build context
                history = self._get_conversation_history(session_id)
                context = self._build_context_from_history(history)

                # Process the query with context
                full_query = f"{context}{query}" if context else query
                response = str(agent(full_query))

                # Add to conversation history
                self._add_to_conversation_history(session_id, query, response)

                return jsonify({
                    "session_id": session_id,
                    "query": query,
                    "response": response,
                    "conversation_length": len(self._get_conversation_history(session_id))
                })

            except Exception as e:
                logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
                return jsonify({
                    "error": "Failed to process chat request",
                    "message": str(e) if os.getenv('DEBUG') else "Internal server error"
                }), 500

        @self.app.route('/chat/history', methods=['GET'])
        @self._require_api_key
        def get_chat_history():
            """Get conversation history for the current session"""
            try:
                session_id = self._get_session_id()
                history = self._get_conversation_history(session_id)

                return jsonify({
                    "session_id": session_id,
                    "conversation_history": history,
                    "total_exchanges": len(history)
                })

            except Exception as e:
                logger.error(f"Error retrieving chat history: {str(e)}")
                return jsonify({
                    "error": "Failed to retrieve chat history"
                }), 500

        @self.app.route('/chat/clear', methods=['POST'])
        @self._require_api_key
        def clear_chat_history():
            """Clear conversation history for the current session"""
            try:
                session_id = self._get_session_id()

                # Clear conversation history
                session['conversations'] = []
                session.modified = True

                # Remove agent from cache to start fresh
                if session_id in self.session_agents:
                    del self.session_agents[session_id]

                logger.info(f"Cleared chat history for session: {session_id}")

                return jsonify({
                    "session_id": session_id,
                    "message": "Chat history cleared successfully"
                })

            except Exception as e:
                logger.error(f"Error clearing chat history: {str(e)}")
                return jsonify({
                    "error": "Failed to clear chat history"
                }), 500

        @self.app.route('/session/info', methods=['GET'])
        @self._require_api_key
        def session_info():
            """Get information about the current session"""
            try:
                session_id = self._get_session_id()
                history = self._get_conversation_history(session_id)

                return jsonify({
                    "session_id": session_id,
                    "conversation_length": len(history),
                    "has_agent": session_id in self.session_agents,
                    "session_data_keys": list(session.keys()),
                    "max_history": int(os.getenv('MAX_CONVERSATION_HISTORY', '20')),
                    "context_window": int(os.getenv('CONTEXT_WINDOW_SIZE', '5'))
                })

            except Exception as e:
                logger.error(f"Error retrieving session info: {str(e)}")
                return jsonify({
                    "error": "Failed to retrieve session info"
                }), 500

        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "error": "Endpoint not found",
                "available_endpoints": [
                    "/health",
                    "/chat",
                    "/chat/history",
                    "/chat/clear",
                    "/session/info"
                ]
            }), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {str(error)}")
            return jsonify({
                "error": "Internal server error"
            }), 500

    def run(self, debug: bool = False):
        """Start the REST API server"""
        auth_status = "enabled" if self.require_api_key else "disabled"
        logger.info(f"Starting Weather Agent REST API server on {self.host}:{self.port}")
        logger.info(f"API Key authentication: {auth_status}")
        logger.info(f"Session management: enabled")
        logger.info(f"Max conversation history: {os.getenv('MAX_CONVERSATION_HISTORY', '20')}")
        logger.info(f"Context window size: {os.getenv('CONTEXT_WINDOW_SIZE', '5')}")

        try:
            self.app.run(host=self.host, port=self.port, debug=debug)
        except Exception as e:
            logger.error(f"Failed to start server: {str(e)}")
            raise


def rest_api_agent():
    """Main entry point for the REST API server"""
    # Get configuration from environment variables
    host = os.getenv("REST_API_HOST", "0.0.0.0")
    port = int(os.getenv("REST_API_PORT", "3000"))
    debug = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")

    # Create and start the server
    server = WeatherRestAPI(host=host, port=port)
    server.run(debug=debug)


if __name__ == "__main__":
    rest_api_agent()
