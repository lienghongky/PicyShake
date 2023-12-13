"use client";
import Image from "next/image";
import DragAndDrop from "./dragdrop/page";
import History from "./history";
import { useState, useEffect } from "react";
import { json } from "stream/consumers";
import { getIpAddress } from "@/hoc/withIpAddress";



 function Home({ipAddress}: {ipAddress: string}) {
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

  
 // Constants for magnifier size and zoom level
    const MAGNIFIER_SIZE = 120;
    const ZOOM_LEVEL = 2.5;

// ImageEffect component

    // State variables
    const [zoomable, setZoomable] = useState(true);
    const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
    const [position, setPosition] = useState({ x: 100, y: 100, mouseX: 0, mouseY: 0 });

    // Event handlers
    const handleMouseEnter = (e: MouseEvent) => {
        let element = e.currentTarget;
        let { width, height } = element.getBoundingClientRect();
        setImageSize({ width, height });
        setZoomable(true);
        updatePosition(e);
    };

    const handleMouseLeave = (e: MouseEvent) => {
        setZoomable(false);
        updatePosition(e);
    };

    const handleMouseMove = (e: MouseEvent) => {
        updatePosition(e);
    };

    const updatePosition = (e: MouseEvent) => {
        const { left, top } = e.currentTarget.getBoundingClientRect();
        let x = e.clientX - left;
        let y = e.clientY - top;
        setPosition({
            x: -x * ZOOM_LEVEL + (MAGNIFIER_SIZE / 2),
            y: -y * ZOOM_LEVEL + (MAGNIFIER_SIZE / 2),
            mouseX: x - (MAGNIFIER_SIZE / 2),
            mouseY: y - (MAGNIFIER_SIZE / 2),
        });
    };

 
  const [baseURL, setBaseURL] = useState<string>("http://localhost:8000");
  const [isToggled, setIsToggled] = useState<boolean>(true);
  const [isShowDebug, setIsShowDebug] = useState<boolean>(false);
  const [progress, setProgress] = useState(0);
  const [outputImage, setOutputImage] = useState<string>("");
  const [inputImage, setInputImage] = useState<string>("");
  const [debugImage, setDebugImage] = useState<string>("");
  const [histories, setHistories] = useState<any[]>([]);
  const [isLoaded, setIsLoaded] = useState<boolean>(false);
  const [models, setModels] = useState<any>([]);
  const [selectedModel, setSelectedModel] = useState(getLocalSelectedModel());
  const [selectedMode, setSelectedMode] = useState<any>(1);
  const [alert, setAlert] = useState<any>();
  const [isOriginalAspectRatio, setIsOriginalAspectRatio] = useState<boolean>(false);
  const [isloading, setIsloading] = useState<boolean>(false);
  const [isConnected, setIsConnected] = useState<boolean|null>(null);
  const [imageAspectRatio, setImageAspectRatio] = useState<string>("4/3");
  const [debugImageAspectRatio, setDebugImageAspectRatio] = useState<string>("4/3");
  const [zoom, setZoom] = useState<number>(50);
  const [isMagnify, setIsMagnify] = useState<boolean>(false);
  const [customBaseURL, setCustomBaseURL] = useState<string>("http://");

  const handleAlertMessage = (message:any) => {
    if (message) {
      setAlert(message);
      setTimeout(() => {
        setAlert(null);
      }, 2000);
    }
  }
  useEffect(() => {
    const selectModel = (id:string) => {
      setIsloading(true);
      fetch(`${baseURL}/selectmodel/`+id, {
        method: "POST",
        body: JSON.stringify({id: id}),
      })
        .then((res) => res.json())
        .then((json) => {
          console.log(json.alert);
          if (json.alert) {
            handleAlertMessage(json.alert);
          }
          setIsloading(false);
        })
        .catch((err) => console.log(err));
    }
    if (!selectedModel) return;
    selectModel(selectedModel.id);
    localStorage.setItem('selectedModel', selectedModel.toString());

  }, [selectedModel]);
  
  useEffect(() => {
    getModels();
    const connect = () => {
      const ws = new WebSocket(`${baseURL.replace("http","ws")}/ws`);
      
      // onconnected 
      ws.onopen = () => {
        console.log("connected");
        setIsConnected(true);
      };
      // onclose
      ws.onclose = () => {
        console.log("disconnected");
        setIsConnected(false);
        // try to reconnect in 5 seconds
        setTimeout(connect, 2000);
      };
      ws.onmessage = (event) => {
        console.log(event.data);
        var json = JSON.parse(event.data);
        if (json.progress) {
          console.log("Progress", json.progress);
          setProgress(Math.round(parseFloat(json.progress) * 100));
        } else if (json.result) {
          console.log("Result", json.result);
          setOutputImage(`${baseURL}/result/${json.result.url}`);
          setIsLoaded(true);
          setIsloading(false);
          setHistories(prv => { 
            console.log("previous",prv)
           return [...prv,{
            id:json.id,
            inputImage: `${baseURL}/result/${json.result.input}`,
            outputImage: `${baseURL}/result/${json.result.url}`,
            debugImage: `${baseURL}/result/${json.result.debug}`,
          }]});
          
        }else if (json.debug) {
          console.log("Debug", json.debug);
          setDebugImage(`${baseURL}/result/${json.debug.url}`);
        }else if (json.error) {
          console.log("Error", json.error);
        } else if (json.message) {
          if (json.message && json.message.type === "alert") {
            handleAlertMessage(json.message);
            if(json.message.model_id) {
              setSelectedModel(json.message.model_id);
            }
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
    }
    connect();
  }, [baseURL]);
  const handleToggle = () => {
    setIsToggled(!isToggled);
  };
  const onFileSubmit = (files: []) => {
    if (files.length === 0) {
      // no file has been submitted
    } else {
      setProgress(0); 
      // upload the files to the server path: /files
      const formData = new FormData();
      files.forEach((file: any) => {
        formData.append("files", file);
        formData.append("mode", selectedMode);
      });
      fetch(`${baseURL}/uploadfiles`, {
        method: "POST",
        body: formData,
      })
        .then((res) => res.json())
        .then((res) => {
          console.log(res);
          setIsLoaded(false);
          setInputImage(`${baseURL}/input/${res.files[0].input}`);
          setDebugImage(`${baseURL}/input/${res.files[0].input}`)
          setOutputImage("");
          setIsloading(true);
        })
        .catch((err) => console.log(err));
    }
    
  };

  const getModels = () => {
    setIsloading(true);
    fetch(`${baseURL}/models`, {
      method: "GET",
    })
      .then((res) => res.json())
      .then((res) => {
        console.log(res);
        setModels(res.models);
        setIsloading(false)
      })
      .catch((err) => console.log(err));
  };
  

  const handleSelectChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedModel(models[event.target.value]);
  };
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-4 bg-black-opactiy-30">
      {/* Drawer */}
      <div className="drawer z-50 fixed top-4 left-4">
        {

         alert && 
         <div role="alert" className={`bg-green-500 text-white alert alert-${alert.type} absolute left-0 right-0 mx-auto w-fit`}>
          <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <span dangerouslySetInnerHTML={{ __html: alert.message }}></span>
         </div>
        }
        {
          isloading &&
          <span className="loading loading-infinity loading-lg absolute left-0 right-0 mx-auto"></span>
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
        <div className="fixed -right-48 -mb-8 w-80 transform rotate-180 translate-y-64  ">
          <div className="flex items-center justify-center transform rotate-90 ">
          <strong>- </strong>
            <input type="range" min={0} max="100" value={zoom} onChange={e=>setZoom(parseInt(e.target.value))}  className="w-64 bg-gray-700 range range-primary " />
          <strong> +</strong>
          <div className="px-4">
          <button className={`btn btn-primary btn-circle  magnify ${isMagnify ? '' : 'btn-outline'}`} onClick={() => setIsMagnify(!isMagnify)}>
            <svg
              className="h-6 w-6"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4ZM12 18C8.68629 18 6 15.3137 6 12C6 8.68629 8.68629 6 12 6C15.3137 6 18 8.68629 18 12C18 15.3137 15.3137 18 12 18Z"
                fill="currentColor"
              />
              <path
                d="M12 8C10.3431 8 9 9.34315 9 11C9 12.6569 10.3431 14 12 14C13.6569 14 15 12.6569 15 11C15 9.34315 13.6569 8 12 8ZM12 12C11.4477 12 11 11.5523 11 11C11 10.4477 11.4477 10 12 10C12.5523 10 13 10.4477 13 11C13 11.5523 12.5523 12 12 12Z"
                fill="currentColor"
              />
            </svg>
          </button>
          </div>
          </div>
        </div>
        <div className="fixed left-0 right-0 top-0 bottom-0 overflow-y-scroll overflow-visible custom-scrollbar">
          <div className="p-4 w-full">
            <DragAndDrop onFileSubmit={onFileSubmit} />
            <div className="items-center px-2">
              <progress
                className="progress progress-success w-full"
                value={progress}
                max="100"
              ></progress>
              <div className="flex justify-between">
              <p className="text-xs text-right text-teal-400 px-1">Porgess:</p>
              <p className="text-xs text-right text-teal-400 px-1">{`${progress}%`}</p>
              </div>
            </div>
          </div>
          <div className="flex w-full justify-center px-4">
            <select value={selectedModel ? selectedModel.id : -1} onChange={handleSelectChange} className="select select-success w-full max-w-xs " >
              <option key={-1} value="-1">Default Model</option>
              {models.map((model: any) => ( <option key={model.id} value={model.id}>{model.name}</option>))}
            </select>
          </div>
          <label className="form-control w-full max-w-xs p-4">
            <div className="label">
              <span className="label-text">Denois Mode</span>
            </div>
            <select value={selectedMode} onChange={e=>setSelectedMode(e.target.value)}  className="select select-bordered">
              <option disabled value={-1}>Default</option>
              <option value={1}>Iterate</option>
              <option value={2}>Batch</option>
              <option value={3}>Overlapping</option>
              <option value={4}>Smooth Blending</option>
              <option value={5}>Resizing</option>
            </select>
          </label>
          <div className="m-4 ">
            <label className="cursor-pointer label">
            <span className="label-text">Original Aspect ratio</span> 
            <input checked={isOriginalAspectRatio} type="checkbox" className="toggle toggle-success" onChange={(e)=>setIsOriginalAspectRatio(e.target.checked)}/>
            </label>
          
            <label className="cursor-pointer label">
            <span className="label-text">Show Debug</span> 
            <input checked={isShowDebug} type="checkbox" className="toggle toggle-success" onChange={(e)=>setIsShowDebug(e.target.checked)}/>
            </label>
          </div>
        
          <div className="w-full p-1 grid grid-cols-2 border-t-2 border-dashed border-gray-600">
            {
              histories.map((history: any, index: number) => (
                <img 
                onClick={
                   ()=>{
                    setInputImage(history.inputImage);
                    setOutputImage(isShowDebug ? history.debugImage : history.outputImage);
                    setDebugImage(history.debugImage);
                   }

                } 
                className="p-1 aspect-square rounded-sm hover:border-2 border-green-500" 
                key={index} src={history.outputImage} alt="" />
              ))
            }
          </div>
        </div>
        
      </div>
      {/* main container */}
      <div className=" z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex  black-opactiy-30">
        <div className="w-full px-4">
            <select value={baseURL} onChange={(e)=>setBaseURL(e.target.value)} className="select select-primary select-sm max-w-xs " >
            
            <option key={0} value="http://localhost:8000">http://localhost:8000</option>
            <option key={1} value="http://10.125.35.23:8000">http://10.125.35.23:8000</option>
            <option key={2} value={customBaseURL}>{customBaseURL}</option>
          </select>
          <input type="text" placeholder="Type here" className="ml-2 input input-bordered input-sm input-primary  max-w-xs" value={customBaseURL} onChange={(e)=>setCustomBaseURL(e.target.value)} />
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
        <span className="relative flex h-3 w-3">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${isConnected == null ? "bg-zinc-200" : isConnected ? "bg-sky-200":"bg-pink-200"} opacity-75`}></span>
          <span className={`relative inline-flex rounded-full h-3 w-3 ${isConnected == null ? "bg-amber-600" : isConnected ? "bg-green-600":"bg-red-600"}`}></span>
        </span>
      </div>
      <div  style={  {["paddingLeft" as any]:isToggled ? `${Math.min(Math.max(20* zoom/65,10),20)}rem` : "0%"}} 
            className={"w-full flex justify-center items-center"}>
        <div style={{["width" as any]:`${zoom}%`}} className={`max-w-2/3 mockup-window rounded-b-xl border bg-base-300 my-8 transition-all duration-100`}>
        
          <div className={`${isMagnify ? 'cursor-none': 'cursor-pointer'}`}>
            <div className={`diff aspect-[${(isShowDebug) ? debugImageAspectRatio :imageAspectRatio}]`} style={{["aspectRatio" as any]:`${(isShowDebug) ? debugImageAspectRatio :imageAspectRatio}`}}
            onMouseLeave={handleMouseLeave}
            onMouseEnter={handleMouseEnter}
            onMouseMove={handleMouseMove}
            >
              
              <div className="diff-item-1">
                <img
                  className={(isShowDebug) ? "object-contain" : ""}
                  src={isLoaded ? outputImage : debugImage ? debugImage : "https://storage.googleapis.com/proudcity/mebanenc/uploads/2021/03/placeholder-image.png"}
                  onLoad={(e) => {
                    
                    const element = e.target as HTMLImageElement;
                    var width = element.naturalWidth;
                    var height = element.naturalHeight;
                    var viewPortHeight = window.innerHeight;
                    var ratio = width / height;
                    var elementWidth = viewPortHeight * ratio;
                    var elementHeight = viewPortHeight;
                    if (isShowDebug && elementWidth && elementHeight) {
                      setDebugImageAspectRatio(`${elementWidth}/${elementHeight}`);
                    }
                  }}
                />
              </div>
              <div className="diff-item-2">
                <img 
                  src={inputImage ? inputImage : "https://storage.googleapis.com/proudcity/mebanenc/uploads/2021/03/placeholder-image.png"} 
                  onLoad={(e) => {
                    
                    const element = e.target as HTMLImageElement;
                    var width = element.naturalWidth;
                    var height = element.naturalHeight;
                    var viewPortHeight = window.innerHeight;
                    var ratio = width / height;
                    var elementWidth = viewPortHeight * ratio;
                    var elementHeight = viewPortHeight;
                    if (elementWidth && elementHeight) {
                      setImageAspectRatio(`${elementWidth}/${elementHeight}`);
                    }else {
                      setImageAspectRatio("4/3");
                    }
                  }}
                  />
              </div>
              <div className="diff-resizer cursor-col-resize"></div>
              <div
                  key={inputImage}
                    style={{
                        backgroundPosition: `${position.x}px ${position.y}px`,
                        backgroundImage: `url(${inputImage})`,
                        backgroundSize: `${imageSize.width * ZOOM_LEVEL}px ${imageSize.height * ZOOM_LEVEL}px`,
                        backgroundRepeat: 'no-repeat',
                        display: isMagnify ? zoomable ? 'block' : 'none' : 'none',
                        top: `${position.mouseY}px`,
                        left: `${position.mouseX}px`,
                        width: `${MAGNIFIER_SIZE}px`,
                        height: `${MAGNIFIER_SIZE}px`,
                    }}
                    className={`z-50 border pointer-events-none absolute border-gray-500`}
                />
                <div
                    style={{
                        backgroundPosition: `${position.x}px ${position.y}px`,
                        backgroundImage: `url(${outputImage === "" ? debugImage : outputImage})`,
                        backgroundSize: `${imageSize.width * ZOOM_LEVEL}px ${imageSize.height * ZOOM_LEVEL}px`,
                        backgroundRepeat: 'no-repeat',
                        display: isMagnify ? zoomable ? 'block' : 'none' : 'none',
                        top: `${position.mouseY}px`,
                        left: `${position.mouseX+(MAGNIFIER_SIZE * (position.mouseX > imageSize.width-2*MAGNIFIER_SIZE ? -1 : 1))}px`,
                        width: `${MAGNIFIER_SIZE}px`,
                        height: `${MAGNIFIER_SIZE}px`,
                        
                    }}
                    className={`z-50 border-2 pointer-events-none absolute border-green-500`}
                />
            </div>
          </div>
          
        </div>
      </div>
      {/* <div className="w-full h-screen overflow-scroll block bg-gray-600">
        <h1>HISTORY</h1>
      {
          histories.map((history: any, index: number) => (
            <History className="block w-full" key={index} history={history} isMagnify={isMagnify} />
          ))
      }
      </div> */}
      <footer className="text-xs text-center dark:text-gray-200 mt-4">
        Created on {new Date().toLocaleDateString()} &copy; <strong>LIENG HONGKY</strong> | VB
        lab @PNU
      </footer>
    </main>
  );
}
Home.getinitialProps = async (ctx: any) => {
  const ipAddress = getIpAddress();
  console.log("ipAddress: ",ipAddress);
  return { ipAddress: ipAddress };
}
export default Home;
// export default withIpAddress(Home);