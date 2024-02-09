
from io import BytesIO
from fastapi import FastAPI
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse , JSONResponse
from gtts import gTTS
from gtts.lang import tts_langs
from google.cloud import vision
from google.cloud.vision_v1 import types
from openai import OpenAI
from pydantic import BaseModel
import shutil

import os
from decouple import config
# Remplacez 'NOM_DE_LA_VARIABLE' par le nom réel de votre variable d'environnement
#cle_api =config("openapi")

clientgpt = OpenAI(api_key= "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" )
client = vision.ImageAnnotatorClient.from_service_account_file("key.json")
#from six.moves import queue


app = FastAPI()
tts_langs = tts_langs()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("record.html", {"request": request, "name": "World"})


@app.get("/tts/{text}")
def tts(text : str):
    lang="en"
    mp3 = BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(mp3)
    mp3.seek(0)
    return StreamingResponse(mp3, media_type="audio/mp3")


@app.post("/generate-audio")
async def ttsp(request: Request):
    form_data = await request.form()
    text = form_data["textaudio"]
    lang = "en"
    mp3 = BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(mp3)
    mp3.seek(0)
    return StreamingResponse(mp3, media_type="audio/mpeg")




class AudioFile(BaseModel):
    file_path: str

@app.post("/upload/")
async def upload_audio(file: UploadFile = File(...)):
    try:
        path = "audio.mp3"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
	text = speechgpt(path)
	print("Hello1")
        text = f"{chat(text)}"
        lang = "en"
        mp3 = BytesIO()
        gTTS(text=text, lang=lang).write_to_fp(mp3)
        mp3.seek(0)
        return StreamingResponse(mp3, media_type="audio/mp3")

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



@app.post("/ocr")
async def ocrtext(request: Request):
    form_data = await request.form()
    file = form_data["image_ocr"]
    path = "im.png"
    try:
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer) 
        
        text=ocr1(path=path) 
        text += localize_objects(path=path) 
        print("fin du text")     
        lang="en"
        mp3 = BytesIO()
        gTTS(text=text, lang=lang).write_to_fp(mp3)
        mp3.seek(0)
        return StreamingResponse(mp3, media_type="audio/mp3")
    
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    

"""import openai 
openai.api_key ="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"

def chat(message):
    messages = [ {"role": "system", "content": 
			"Your name is Vision Plus, a intelligent assistant for blind people."} ] 
    reply = ""
    if message: 
        messages.append( 
			{"role": "user", "content": message}, 
            ) 
        chat = openai.ChatCompletion.create( 
			model="gpt-3.5-turbo", messages=messages 
		) 
    reply = chat.choices[0].message.content 
    return reply
"""

@app.post("/localize")
async def loc(request: Request):
    form_data = await request.form()
    file = form_data["imag_loc"]
    path = "im.png"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer) 
    text=localize_objects(path=path)  
    print("fin du text", text)
        
    lang="en"
    mp3 = BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(mp3)
    mp3.seek(0)
    return StreamingResponse(mp3, media_type="audio/mp3")
    
   

def ocr1(path=None, content=None):
    
    if path:
        with open(path, "rb") as f:
            content=f.read()
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print('Texts:')
    t=""
    #print(texts.keys())
    for text in texts:
        t=f'\n"{text.description}"'

        vertices = ([f'({vertex.x},{vertex.y})'
                    for vertex in text.bounding_poly.vertices])
        break
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    '''for text in texts:
        print(f'\n"{text.description}"')

        vertices = ([f'({vertex.x},{vertex.y})'
                    for vertex in text.bounding_poly.vertices])

        print('bounds: {}'.format(','.join(vertices)))'''
    if t:
        print(t)
        return t
    else:
        return "pas de texte "




def localize_objects(path):
   
    with open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)
    response = client.object_localization(image=image)
    objects = response.localized_object_annotations
    t = ''
    if len(objects):
        t += f"{len(objects)} differents elements find"
        print('Normalized bounding polygon vertices: ')
        for object_ in objects:
            t += f" a {object_.name} ,"
            #print(t)
    else:
        t += "I don't find objects in front of you, if is anormal, please try again"
    return t




def speechgpt(path):
    audio_file= open(path, "rb")
    transcript = clientgpt.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file
    )
    text = transcript.text
    print("text audio: ", text)
    return  text
    

def chat(mes):
    response = clientgpt.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    messages=[ 
        {"role": "system", "content": "You are AI assistant for blind people."},
        {"role": "user", "content": mes}
    ]
    )
    text = response.choices[0].message.content
    return  text

if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8000)
