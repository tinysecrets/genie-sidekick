# Here are your Instructions
# 1. Install Ollama (once) — https://ollama.com/download

# 2. Load his Dolphin GGUF into Ollama. In a folder with his
#    Dolphin3.0-Llama3.1-8B-Q4_K_S.gguf file, make a file called "Modelfile":
FROM ./Dolphin3.0-Llama3.1-8B-Q4_K_S.gguf

# 3. Register it with the name "dolphin3" (must match OLLAMA_MODEL in .env):
ollama create dolphin3 -f Modelfile

# 4. Make sure Ollama is running:
ollama serve

# 5. Start MongoDB, then start the backend:
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001

# 6. Start the frontend in a second terminal:
cd frontend
yarn install
yarn start
