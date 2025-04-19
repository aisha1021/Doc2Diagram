import React, { useState, useRef } from 'react';
import { Camera, Send, RotateCcw } from 'lucide-react';
import { CameraCaptureProps } from '../types';

const CameraCapture: React.FC<CameraCaptureProps> = ({
  isLoading,
  setIsLoading,
  setError
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      setError('Unable to access the camera.');
    }
  };

  const takePicture = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      setCapturedImage(canvas.toDataURL('image/jpeg'));
    }
  };

  const sendToBackend = async () => {
    if (!capturedImage) return;
    setIsLoading(true);
    try {
      const blob = await fetch(capturedImage).then((res) => res.blob());
      const formData = new FormData();
      formData.append('file', new File([blob], 'capture.jpg', { type: 'image/jpeg' }));
      const response = await fetch('http://localhost:5001/process-camera', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        throw new Error('Upload failed');
      }
      setError('');
    } catch (err) {
      setError('Failed to upload image.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-3xl mx-auto">
      <div className="w-full space-y-6">
        {!capturedImage ? (
          <>
            <div className="relative w-full aspect-video bg-gray-100 rounded-lg overflow-hidden shadow-md">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex justify-center gap-6">
              <button
                onClick={startCamera}
                className="inline-flex items-center px-6 py-3 bg-blue-700 text-white rounded-lg hover:bg-blue-800 transition-colors shadow-sm"
              >
                <Camera className="w-5 h-5 mr-3" />
                Start Camera
              </button>
              <button
                onClick={takePicture}
                className="inline-flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-sm"
              >
                <Camera className="w-5 h-5 mr-3" />
                Capture
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="relative w-full aspect-video bg-gray-100 rounded-lg overflow-hidden shadow-md">
              <img
                src={capturedImage}
                alt="Captured"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex justify-center gap-6">
              <button
                onClick={sendToBackend}
                className="inline-flex items-center px-6 py-3 bg-blue-700 text-white rounded-lg hover:bg-blue-800 transition-colors shadow-sm"
              >
                <Send className="w-5 h-5 mr-3" />
                Process Image
              </button>
              <button
                onClick={() => setCapturedImage(null)}
                className="inline-flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors shadow-sm"
              >
                <RotateCcw className="w-5 h-5 mr-3" />
                Retake
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default CameraCapture;