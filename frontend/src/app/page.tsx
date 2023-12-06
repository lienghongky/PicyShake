"use client";
import Image from "next/image";
import DragAndDrop from "./dragdrop/page";
import { useState, useEffect } from "react";
import { json } from "stream/consumers";

export default function Home() {

  const getLocalSelectedModel = () => {
    if (typeof window !== 'undefined') {
      const selectedModel = window.localStorage.getItem('selectedModel');
      if (selectedModel) {
        try {
          return JSON.parse(selectedModel);
        } catch (error) {
          return {id: -1, name: "Default Model"};
          // console.error('Error parsing JSON from local storage:', error);
        }
      }
    }else {
      return {id: -1, name: "Default Model"};
    }
  }

  const selectModel = (id:string) => {
    fetch(`http://localhost:8000/selectmodel/`+id, {
      method: "POST",
      body: JSON.stringify({id: id}),
    })
      .then((res) => res.json())
      .then((json) => {
        console.log(json.alert);
        if (json.alert) {
          handleAlertMessage(json.alert);
        }
      })
      .catch((err) => console.log(err));
  }

 

  const [isToggled, setIsToggled] = useState<boolean>(true);
  const [progress, setProgress] = useState(0);
  const [outputImage, setOutputImage] = useState<string>("");
  const [inputImage, setInputImage] = useState<string>("");
  const [isLoaded, setIsLoaded] = useState<boolean>(false);
  const [models, setModels] = useState<any>([]);
  const [selectedModel, setSelectedModel] = useState(getLocalSelectedModel());
  const [alert, setAlert] = useState<any>();
  const [isBatch, setIsBatch] = useState<boolean>(false);

  const handleAlertMessage = (message:any) => {
    if (message) {
      setAlert(message);
      setTimeout(() => {
        setAlert(null);
      }, 2000);
    }
  }
  useEffect(() => {
    selectModel(selectedModel.id);
    localStorage.setItem('selectedModel', selectedModel.toString());

  }, [selectedModel]);
  
  useEffect(() => {
    getModels();
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onmessage = (event) => {
      console.log(event.data);
      var json = JSON.parse(event.data);
      if (json.progress) {
        console.log("Progress", json.progress);
        setProgress(Math.round(parseFloat(json.progress) * 100));
      } else if (json.result) {
        console.log("Result", json.result);
        setOutputImage(`http://localhost:8000/result/${json.result.url}`);
        setIsLoaded(true);
      } else if (json.error) {
        console.log("Error", json.error);
      } else if (json.message) {
        if (json.message && json.message.type === "alert") {
          handleAlertMessage(json.message);
        }
        console.log("Message", json.message);
      } else if (json.connected) {
        console.log("Connected", json.connected);
      } else {
        console.log("Unknown", json);
      }
    };

    return () => {
      ws.close();
    };
  }, []);
  const handleToggle = () => {
    setIsToggled(!isToggled);
  };
  const onUploadResponse = (response: any) => {
    console.log(response);
    setIsLoaded(false);
    setInputImage(`http://localhost:8000/input/${response.files[0].input}`);
  };

  const getModels = () => {
    fetch("http://localhost:8000/models", {
      method: "GET",
    })
      .then((res) => res.json())
      .then((res) => {
        console.log(res);
        setModels(res.models);
      })
      .catch((err) => console.log(err));
  };

  const handleSelectChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedModel(models[event.target.value]);
  };
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-4 bg-black-opactiy-30">
      
      {/* Side bar */}
      <div className="drawer z-50 fixed top-4 left-4">
        {
         alert && 
         <div role="alert" className={`alert alert-${alert.type} absolute left-0 right-0 mx-auto w-fit`}>
          <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <span dangerouslySetInnerHTML={{ __html: alert.message }}></span>
         </div>
        }
        <button
          onClick={handleToggle}
          className="btn btn-circle btn-outline absolute"
        >
          <svg
            className="h-6 w-6"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M3 5.75C3 5.33579 3.33579 5 3.75 5H20.25C20.6642 5 21 5.33579 21 5.75C21 6.16421 20.6642 6.5 20.25 6.5H3.75C3.33579 6.5 3 6.16421 3 5.75Z"
              fill="currentColor"
            />
            <path
              d="M3 11.75C3 11.3358 3.33579 11 3.75 11H20.25C20.6642 11 21 11.3358 21 11.75C21 12.1642 20.6642 12.5 20.25 12.5H3.75C3.33579 12.5 3 12.1642 3 11.75Z"
              fill="currentColor"
            />
            <path
              d="M3 17.75C3 17.3358 3.33579 17 3.75 17H20.25C20.6642 17 21 17.3358 21 17.75C21 18.1642 20.6642 18.5 20.25 18.5H3.75C3.33579 18.5 3 18.1642 3 17.75Z"
              fill="currentColor"
            />
          </svg>
        </button>
      </div>

      {/* Side bar */}
      <div
        className={`transition-2 transition-all z-40 w-80 fixed top-1/2 left-4 transform -translate-y-1/2 h-2/3 bg-gray-900 rounded-xl border border-neutral-600 backdrop-blur-2xl ${
          isToggled ? "block translate-x-0" : " -translate-x-full"
        }`}
      >
        <div className="p-4 w-full">
          <DragAndDrop onUploadResponse={onUploadResponse} />
        </div>
        <div className="flex w-full justify-center p-4">
          <select value={selectedModel.id} onChange={handleSelectChange} className="select select-success w-full max-w-xs " >
            <option key={-1} value="-1">Default Model</option>
            {models.map((model: any) => ( <option key={model.id} value={model.id}>{model.name}</option>))}
          </select>
        </div>
        <div className="m-4 ">
          <label className="cursor-pointer label">
          <span className="label-text">Enbale batch process</span> 
          <input checked={isBatch} type="checkbox" className="toggle toggle-success" onChange={(e)=>setIsBatch(e.target.checked)}/>
          </label>
          <label className="cursor-pointer label">
          <span className="label-text">Enbale paches</span> 
          <input checked={isBatch} type="checkbox" className="toggle toggle-success" onChange={(e)=>setIsBatch(e.target.checked)}/>
          </label>
          <label className="cursor-pointer label">
          <span className="label-text">Enbale scale</span> 
          <input checked={isBatch} type="checkbox" className="toggle toggle-success" onChange={(e)=>setIsBatch(e.target.checked)}/>
          </label>
        </div>

      </div>
      {/* main container */}
      <div className=" z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex  black-opactiy-30">
        <div className="w-full"></div>

        <div className="fixed bottom-0 left-0 flex h-48 w-full items-end justify-center bg-gradient-to-t from-white via-white dark:from-black dark:via-black lg:static lg:h-auto lg:w-auto lg:bg-none">
          <a
            className="pointer-events-none flex place-items-center gap-2 p-8 lg:pointer-events-auto lg:p-0"
            href="https://vb.pusan.ac.kr/visbic/index..do"
            target="_blank"
            rel="noopener noreferrer"
          >
            By{" "}
            <Image
              src="/logo.png"
              alt="Vercel Logo"
              className=""
              width={100}
              height={24}
              priority
            />
          </a>
        </div>
      </div>
    

      <div className={isToggled ? "w-full flex justify-end" :"w-full flex justify-center"}>
        <div className="w-2/3 mockup-window rounded-b-xl border bg-base-300 my-8 transition-all duration-100">

          <div className="w-full">
            <div className="diff aspect-[16/9]">
              <div className="diff-item-1">
                <img
                  className={isLoaded ? "" : "blur-lg"}
                  src={isLoaded ? outputImage : inputImage}
                />
              </div>
              <div className="diff-item-2">
                <img 
                  src={inputImage} />
              </div>
              <div className="diff-resizer"></div>
            </div>
          </div>
          <div className="flex items-center">
            <p className="text-xd text-teal-500 p-1">{`${progress}%`}</p>
            <progress
              className="progress progress-accent w-full"
              value={progress}
              max="100"
            ></progress>
          </div>
        </div>
      </div>

      <footer className="text-xs text-center dark:text-gray-200 mt-4">
        Created on {new Date().toLocaleDateString()} &copy; <strong>LIENG HONGKY</strong> | VB
        lab @PNU
      </footer>
    </main>
  );
}
