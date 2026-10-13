from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field
from keras.models import load_model
from contextlib import asynccontextmanager
import numpy as np
from keras.preprocessing.sequence import pad_sequences
import pickle
import re

model_path = 'Artifacts/BiGRU_model.keras'

tokenizer_path = 'Artifacts/tokenizer.pkl'

max_sequence_length = 50

emotion_labels = ["sadness", "joy", "love", "anger", "fear", "surprise"]

EMOTION_EMOJIS = {
    "sadness": "😢",
    "joy": "😄",
    "love": "❤️",
    "anger": "😠",
    "fear": "😨",
    "surprise": "😲",
}

#Preprocess

def preprocess_text(text:str) -> str:
    text = text.lower()
    text = re.sub(r"'","",text)
    text = re.sub(r"[^a-z0-9\s]"," ",text)
    text = re.sub(r"\s+"," ",text).strip()
    return text

#Pydantic

class TextInput(BaseModel):
    text : str = Field(...,
    min_length = 1,
    description = "Input text for emotion detection",
    json_schema_extra = {"example": "I am feeling very happy today!"}
    )

class PredictionResponse(BaseModel):
   text : str
   prediction_emotion :str
   confidence : float
   all_probabilites: dict[str, float] 

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool

#Model Loading
dl_model = {}

@asynccontextmanager
async def lifespan(app:FastAPI):
    print('Loading the model and tokenizer...')
    dl_model["BiGRU_model"] = load_model(model_path)
    with open(tokenizer_path,'rb') as f:
        dl_model["Tokenizer"] = pickle.load(f)
    print('Model are loaded successfully...') 
    
    yield

    dl_model.clear()

#Web App Initialization
app = FastAPI(
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount('/static', StaticFiles(directory="static"), name="static")

#Endpoints

@app.get("/",include_in_schema=False)
def server_ui():
    return FileResponse('static/index.html')

@app.get("/health",response_model=HealthResponse)
def HealthCheck():
    return HealthResponse(status="OK", model_loaded=bool(dl_model))

@app.post("/predict",response_model=PredictionResponse)
def predict_emotion(text_input:TextInput):
    BiGRU_model = dl_model.get("BiGRU_model")
    Tokenizer_model = dl_model.get("Tokenizer")

    if BiGRU_model is None or Tokenizer_model is None:
        raise HTTPException(status_code=500, detail={"error": "Model or tokenizer not loaded."})

    cleaned_text = preprocess_text(text_input.text)

    tokenized_text = Tokenizer_model.texts_to_sequences([cleaned_text])

    padded_sequences = pad_sequences(
        tokenized_text,
        maxlen=max_sequence_length,
        padding='post',
        truncating='post'
    )

    probabilities = BiGRU_model.predict(padded_sequences)[0]

    top_emotion_index = int(np.argmax(probabilities))

    all_probabilities =  {
        label: float(prob) for prob ,label in zip(probabilities, emotion_labels)
        }

    return PredictionResponse(
        text = text_input.text,
        prediction_emotion = emotion_labels[top_emotion_index],
        confidence = float(probabilities[top_emotion_index]),
        all_probabilites = all_probabilities
    )
        