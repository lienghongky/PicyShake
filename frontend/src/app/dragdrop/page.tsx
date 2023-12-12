"use client";
import { on } from "events";
import { use, useRef, useState,useEffect } from "react";

export interface DragAndDropProps {
  onFileSubmit?: (files: []) => void;
}

export default function DragAndDrop({ onFileSubmit }: DragAndDropProps) {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const inputRef = useRef<any>(null);
  const [files, setFiles] = useState<any>([]);
  
  useEffect(() => {
      // handle paste event check if is image file and add to files
  document.addEventListener("paste", function (e: ClipboardEvent) {
    // Clear the previous timeout if it exists
    const items = e.clipboardData?.items;
    console.log(items);
    if (items) {
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") !== -1) {
          const blob = items[i].getAsFile();
          console.log(blob);
          setFiles((prevState: any) => [blob]);
        }
      }
    }
  });
  }, []);
  


  function handleChange(e: any) {
    e.preventDefault();
    console.log("File has been added");
    if (e.target.files && e.target.files[0]) {
      console.log(e.target.files);
      for (let i = 0; i < e.target.files["length"]; i++) {
        setFiles((prevState: any) => [...prevState, e.target.files[i]]);
      }
    }
  }

  function handleSubmitFile(e: any) {
    onFileSubmit && onFileSubmit(files);
  }

  function handleDrop(e: any) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      for (let i = 0; i < e.dataTransfer.files["length"]; i++) {
        setFiles((prevState: any) => [...prevState, e.dataTransfer.files[i]]);
      }
    }
  }

  function handleDragLeave(e: any) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }

  function handleDragOver(e: any) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }

  function handleDragEnter(e: any) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }

  function removeFile(fileName: any, idx: any) {
    const newArr = [...files];
    newArr.splice(idx, 1);
    setFiles([]);
    setFiles(newArr);
  }

  function openFileExplorer() {
    inputRef.current.value = "";
    inputRef.current.click();
  }

  return (
    <div className="flex items-center justify-center w-full m-0 p-0">
      <form
       action="/files/" encType="multipart/form-data" method="post"
        className={`${
          dragActive ? "bg-gray-400" : "bg-gray-900 bg-opacity-70"
        }  p-4 w-full rounded-lg  min-h-[10rem] text-center flex flex-col items-center justify-center border-separate border-4 border-dashed border-gray-600`}
        onDragEnter={handleDragEnter}
        onSubmit={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
      >
        {/* this input element allows us to select files for upload. We make it hidden so we can activate it when the user clicks select files */}
        <input
          placeholder="fileInput"
          className="hidden"
          ref={inputRef}
          type="file"
          multiple={true}
          onChange={handleChange}
          accept="image/*"
        />

        <p className="text-gray-700 font-bold text-sm">
          Drag & Drop files or<br/>{" "}
          <span
            className="font-bold text-blue-600 cursor-pointer"
            onClick={openFileExplorer}
          >
            <u>Select files</u>
          </span>{" "}
          to upload
        </p>

        {/* <div className="w-full flex flex-col items-center p-3">
          {files.map((file: any, idx: any) => (
            <div key={idx} className="bg-zinc-700/50 rounded-lg p-2 border border-zinc-700/50 w-full flex flex-row space-x-5 whitespace-nowrap">
              <p className="text-ellipsis truncate">{file.name}</p>
              <span
                className="text-red-500 cursor-pointer"
                onClick={() => removeFile(file.name, idx)}
              >
                remove
              </span>
            </div>
          ))}
        </div> */}

        <button
          className="bg-black rounded-lg p-2 mt-3 w-auto"
          onClick={handleSubmitFile}
        >
          <span className="p-2 text-white">Submit</span>
        </button>
      </form>
    </div>
  );
}