import React from 'react';
import { Upload } from 'lucide-react';
import { FileUploadProps } from '../types';

const FileUpload: React.FC<FileUploadProps> = ({
  isLoading,
  setIsLoading,
  setError
}) => {
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setIsLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://localhost:5001/process-document', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to process document');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'workflow.png';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process document');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <input
          type="file"
          onChange={handleFileUpload}
          accept=".pdf,.docx,.png,.jpg,.jpeg"
          className="hidden"
          id="file-upload"
          disabled={isLoading}
        />
        <label
          htmlFor="file-upload"
          className="cursor-pointer inline-flex flex-col items-center"
        >
          <Upload className="w-12 h-12 text-blue-700 mb-4" />
          <span className="text-lg font-medium text-gray-900">Choose a file</span>
          <br />
          <span className="text-sm text-gray-500 mt-1">
            or drag and drop it here
          </span>
        </label>
      </div>
    </div>
  );
};

export default FileUpload;