#!/bin/bash

# Create tables if they don't exist
python -c "from api.database import create_tables; create_tables()"

# Start the FastAPI application
uvicorn api.fastapi_app:app --host 0.0.0.0 --port $PORT