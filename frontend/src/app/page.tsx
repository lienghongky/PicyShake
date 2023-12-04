"use client";
import Image from "next/image";
import DragAndDrop from "./dragdrop/page";
import { useState, useEffect } from "react";
import { json } from "stream/consumers";

export default function Home() {
  const getLocalSelectedModel = () => {
    const selectedModel = localStorage.getItem('selectedModel');
    if (selectedModel) {
      try {
        return JSON.parse(selectedModel);
      } catch (error) {
        // console.error('Error parsing JSON from local storage:', error);
      }
    }
    return {id: -1, name: "Default"};
  }
  const selectModel = (id:string) => {
    fetch(`http://localhost:8000/selectmodel/`+id, {
      method: "POST",
      body: JSON.stringify({id: id}),
    })
      .then((res) => res.json())
      .then((res) => {
        console.log(res);
      })
      .catch((err) => console.log(err));
  }

  const [isToggled, setIsToggled] = useState<boolean>(false);
  const [progress, setProgress] = useState(0);
  const [outputImage, setOutputImage] = useState<string>("");
  const [inputImage, setInputImage] = useState<string>("");
  const [isLoaded, setIsLoaded] = useState<boolean>(false);
  const [models, setModels] = useState<any>([]);
  const [selectedModel, setSelectedModel] = useState(getLocalSelectedModel());
  
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
    <main className="flex min-h-screen flex-col items-center justify-between p-10 bg-black-opactiy-30">
      {/* Side bar */}
      <div className="drawer z-50 fixed top-4 left-4">
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
        className={`z-40 fixed top-1/2 left-4 transform -translate-y-1/2 h-2/3 w-48 bg-gray-900 rounded-xl border border-neutral-600 backdrop-blur-2xl ${
          isToggled ? "block" : "hidden"
        }`}
        onClick={handleToggle}
      ></div>

      {/* main container */}
      <div className=" z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex  black-opactiy-30">
        <div className="mr-8 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          <select value={selectedModel.id} onChange={handleSelectChange} className="bg-zinc-800/30" >
            <option key={-1} value="-1">Default</option>
            {models.map((model: any) => ( <option key={model.id} value={model.id}>{model.name}</option>))}
          </select>
        </div>

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
      <div className="pt-4 w-full">
        <DragAndDrop onUploadResponse={onUploadResponse} />
      </div>

      <div className="w-2/3 mockup-window rounded-b-xl border bg-base-300 my-8">

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

      <footer className="text-xs text-center text-gray-500 mt-4">
        Created on {new Date().toLocaleDateString()} &copy; LIENG HONGKY | VB
        lab @PNU
      </footer>
    </main>
  );
}
