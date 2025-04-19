import React, { useState } from 'react';
import { Upload, Camera, RefreshCw } from 'lucide-react';
import FileUpload from './components/FileUpload';
import CameraCapture from './components/CameraCapture';

const App: React.FC = () => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'upload' | 'camera'>('upload');

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-blue-700 text-white py-6 px-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold">Cognizant Document Processor</h1>
          <p className="mt-2 text-blue-100">Upload documents or capture images for processing</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto mt-8 px-4">
        <div className="flex border-b border-gray-200 mb-8">
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex items-center px-6 py-3 border-b-2 ${
              activeTab === 'upload'
                ? 'border-blue-700 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Upload className="w-5 h-5 mr-2" />
            File Upload
          </button>
          <button
            onClick={() => setActiveTab('camera')}
            className={`flex items-center px-6 py-3 border-b-2 ${
              activeTab === 'camera'
                ? 'border-blue-700 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Camera className="w-5 h-5 mr-2" />
            Camera Capture
          </button>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          {activeTab === 'upload' ? (
            <FileUpload
              isLoading={isLoading}
              setIsLoading={setIsLoading}
              error={error}
              setError={setError}
            />
          ) : (
            <CameraCapture
              isLoading={isLoading}
              setIsLoading={setIsLoading}
              error={error}
              setError={setError}
            />
          )}

          {isLoading && (
            <div className="mt-6 flex items-center justify-center text-gray-600">
              <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
              Processing...
            </div>
          )}

          {error && (
            <div className="mt-6 p-4 bg-red-50 text-red-700 rounded-lg">
              {error}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default App;