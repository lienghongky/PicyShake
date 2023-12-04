from typing import Union, Annotated
from fastapi import FastAPI, WebSocket, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os
import datetime as dt
import asyncio
from ModelClass.Inference import Inference
import threading
from fastapi.responses import FileResponse
import blurhash
import numpy as np
import PIL
app = FastAPI()

inference = Inference()
inference.initialize()
inference.load_model()




origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:

    last_message = ""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = super(ConnectionManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self) -> None:
        self.connections  = {}
        self.connection_callback = None
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket
        await self.send_on_connected(["0"], True)
        self.connection_callback()
    async def disconnect(self, user_id):
        websocket: WebSocket = self.connections[user_id]
        await websocket.close()
        del self.connections[user_id]

    async def send_messages(self, user_ids, message):
        for user_id in user_ids:
            websocket: WebSocket = self.connections[user_id]
            print( websocket.client_state )
            await websocket.send_json({"message": message})
    #send message with event name
    async def send_result(self, user_ids, message):
        print("send result")
        print(self.connections)
        for user_id in user_ids:
            websocket: WebSocket = self.connections[user_id]
            await websocket.send_json({"result": message})
    #send progress  
    async def send_progress(self, user_ids, message):
        for user_id in user_ids:
            websocket: WebSocket = self.connections[user_id]
            await websocket.send_json({"progress": message})
    # send on connected 
    async def send_on_connected(self, user_ids, message):
        for user_id in user_ids:
            websocket: WebSocket = self.connections[user_id]
            await websocket.send_json({"connected": message})
async def on_connected():
    try:
        await handle_models()
    except Exception as e:
        print("error",e)
manager = ConnectionManager()
manager.connection_callback = on_connected
modelThread = None

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.post("/files/")
async def create_files(
    files: Annotated[list[bytes], File(description="Multiple files as bytes")],
):
    save_directory = "./files/images"
    os.makedirs(save_directory, exist_ok=True)
    
    file_sizes = []
    return {"file_sizes": file_sizes}


@app.post("/uploadfiles/")
async def create_upload_files(
    files: Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],

):
    print(files)
    filenames = []
    for i, file in enumerate(files):
        current_time = dt.datetime.now().strftime("%Y%m%d%H%M%S%f")
        file_location = f"files/{current_time}_{i}_{file.filename}"
        print(file_location)
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        # generate blurhash
        blurhash_str = "rOpGG-oBUNG,qRj2so|=eE1w^n4S5NH"
                
        filenames.append({"input":file_location.replace("files/", ""), "blurhash": blurhash_str})
        # Run denoising process in background thread
        modelThread = threading.Thread(target=denoise_image, args=(file_location,))
        modelThread.start()
    return {"files": filenames}
# handle Models list request 
@app.get("/models")
async def handle_models():
    return {"models": getModels()}
# handle select model request
@app.post("/selectmodel/{model_id}")
async def select_model(model_id: int):
    model_name = getModels()[model_id]["name"]
    if model_name != inference.model_name:
        inference.load_model(model_name)
    return {"message": "loaded"}
# handle image request
@app.get("/result/{image_id}")
async def get_image(image_id: str):
    image_path = inference.output_dir + "/" + image_id
    return FileResponse(image_path)
# handle image request
@app.get("/input/{image_id}")
async def get_image(image_id: str):
    image_path = "./files/" + image_id
    return FileResponse(image_path)
# handle image request
@app.get("/ping")
async def ping():
    await manager.send_messages(["0"], "pong")
    return {"message": "pong"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect("0", websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_messages(["0"], data)
            if data == "models":
                await manager.send_messages(["0"], {"models": get_models()})
    except:
        await manager.disconnect("0")
# progress callback function
async def progress_callback(progress):
    print(progress)
    await manager.send_progress(["0"], progress)
# update progress in second model thread
async def updateProgess():
    while inference.is_in_progress:
        if inference.is_in_progress:
           await manager.send_progress(["0"], inference.progress+0.1)
        asyncio.sleep(1)
        

# denoise image and return the denoised image
def denoise_image(image_path):
    threading.Thread(target=updateProgess).start()
    denoised_image_name, save_path, (psnr, ssim) = inference.predict(image_path)
    # Send the denoised image to the client
    asyncio.run(manager.send_result(["0"], {"url": denoised_image_name, "psnr": float(psnr), "ssim": float(ssim)}))
    return denoised_image_name, save_path, (psnr, ssim)

def getModels():
    models = []
    for i, filename in enumerate(os.listdir("./models")):
        models.append({"id":i, "name":filename})
    return models
