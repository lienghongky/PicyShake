
import React, { useState, MouseEvent } from "react";

interface HistoryProps {
    history: any;
    isMagnify: boolean
}

export default function History({history,isMagnify }: HistoryProps) {


 // Constants for magnifier size and zoom level
 const MAGNIFIER_SIZE = 120;
 const ZOOM_LEVEL = 2.5;

// ImageEffect component

 // State variables
 const [zoomable, setZoomable] = useState(true);
 const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
 const [position, setPosition] = useState({ x: 100, y: 100, mouseX: 0, mouseY: 0 });
 const [imageAspectRatio, setImageAspectRatio] = useState<string>("4/3");

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

    return (
        
        <div className={`w-full flex justify-center ${isMagnify ? 'cursor-none' : 'cursor-pointer'}`}>
                <div
                    className={`w-1/2 diff aspect-[${imageAspectRatio}]`}
                    style={{ ["aspectRatio" as any]: `${imageAspectRatio}` }}
                    onMouseLeave={handleMouseLeave}
                    onMouseEnter={handleMouseEnter}
                    onMouseMove={handleMouseMove}
                >
                    <div className="diff-item-1">
                        <img
                            src={history.outputImage ?? "https://storage.googleapis.com/proudcity/mebanenc/uploads/2021/03/placeholder-image.png"}
                        />
                    </div>
                    <div className="diff-item-2">
                        <img
                            src={history.inputImage ? history.inputImage : "https://storage.googleapis.com/proudcity/mebanenc/uploads/2021/03/placeholder-image.png"}
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
                                } else {
                                    setImageAspectRatio("4/3");
                                }
                            }}
                        />
                    </div>
                    <div className="diff-resizer cursor-col-resize"></div>
                    <div
                        style={{
                            backgroundPosition: `${position.x}px ${position.y}px`,
                            backgroundImage: `url(${history.inputImage})`,
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
                            backgroundImage: `url(${history.outputImage === "" ? history.debugImage : history.outputImage})`,
                            backgroundSize: `${imageSize.width * ZOOM_LEVEL}px ${imageSize.height * ZOOM_LEVEL}px`,
                            backgroundRepeat: 'no-repeat',
                            display: isMagnify ? zoomable ? 'block' : 'none' : 'none',
                            top: `${position.mouseY}px`,
                            left: `${position.mouseX + (MAGNIFIER_SIZE * (position.mouseX > imageSize.width - 2 * MAGNIFIER_SIZE ? -1 : 1))}px`,
                            width: `${MAGNIFIER_SIZE}px`,
                            height: `${MAGNIFIER_SIZE}px`,
                        }}
                        className={`z-50 border-2 pointer-events-none absolute border-green-500`}
                    />
                </div>
            </div>
    )
}