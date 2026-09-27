import uvicorn
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    print("Starting ATLAS-OPS in LOCAL mode...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
