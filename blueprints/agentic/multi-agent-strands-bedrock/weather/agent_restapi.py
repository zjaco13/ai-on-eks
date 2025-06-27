#!/usr/bin/env python3
"""
Weather Agent REST API Server

Provides a REST API interface for the weather agent, allowing HTTP clients
to interact with weather forecast and alert functionality.
"""

import os
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from agent import weather_assistant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherRestAPI:
    """REST API wrapper for the Weather Agent"""

    def __init__(self, host: str = "0.0.0.0", port: int = 3000):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self):
        """Configure Flask routes"""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "service": "weather-agent-rest-api",
                "version": "0.1.0"
            })

        @self.app.route('/chat', methods=['POST'])
        def chat():
            """Chat with the weather assistant"""
            try:
                data = request.get_json()
                if not data or 'query' not in data:
                    return jsonify({
                        "error": "Missing 'query' parameter in request body"
                    }), 400

                query = data['query']
                logger.info(f"Processing chat request: {query}")

                # Use the weather assistant to process the query
                response = weather_assistant(query)

                return jsonify({
                    "query": query,
                    "response": response
                })

            except Exception as e:
                logger.error(f"Error processing chat request: {str(e)}")
                return jsonify({
                    "error": f"Failed to process chat request: {str(e)}"
                }), 500

        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "error": "Endpoint not found",
                "available_endpoints": [
                    "/health",
                    "/chat"
                ]
            }), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                "error": "Internal server error"
            }), 500

    def run(self, debug: bool = False):
        """Start the REST API server"""
        logger.info(f"Starting Weather Agent REST API server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug)


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
