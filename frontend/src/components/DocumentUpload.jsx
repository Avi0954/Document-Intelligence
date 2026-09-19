import React, { useState, useRef } from 'react';
import { uploadDocument } from '../services/api';

export const DocumentUpload = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const fileInputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;
    
    const ext = file.name.split('.').pop().toLowerCase();
    const allowed = ['pdf', 'docx', 'pptx', 'txt', 'png', 'jpg', 'jpeg'];
    if (!allowed.includes(ext)) {
      setError(`Unsupported file format .${ext}. Allowed formats: PDF, DOCX, PPTX, TXT, PNG, JPG, JPEG.`);
      return;
    }

    setUploading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const doc = await uploadDocument(file);
      setSuccessMsg(`Uploaded "${doc.original_name}".`);
      if (onUploadSuccess) {
        onUploadSuccess(doc);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to upload document.';
      setError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full space-y-4">
      
      {/* Editorial Header */}
      <div>
        <div className="font-mono text-xs text-[#707070] uppercase tracking-widest mb-1">01 / DOCUMENTS</div>
        <h3 className="text-base font-semibold text-white tracking-tight">
          Build a question bank from your documents.
        </h3>
      </div>

      {/* Editorial Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border rounded-sm p-8 text-center cursor-pointer transition-all bg-[#111111] ${
          isDragging
            ? 'border-[#F5F5F5] bg-[#171717]'
            : 'border-[#242424] hover:border-[#2D2D2D] hover:bg-[#151515]'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.pptx,.txt,.png,.jpg,.jpeg"
          onChange={handleChange}
          className="hidden"
        />

        <div className="space-y-3">
          <p className="font-mono text-xs uppercase tracking-widest text-[#A0A0A0]">
            {uploading ? 'Processing upload...' : 'Drop documents here'}
          </p>
          
          <div className="pt-1">
            <button
              type="button"
              className="inline-block px-5 py-2.5 rounded-sm bg-[#F5F5F5] text-[#0B0B0B] text-xs font-semibold uppercase tracking-wider hover:bg-white transition-colors"
            >
              + Add Document
            </button>
          </div>

          <p className="font-mono text-[10px] text-[#707070] tracking-widest uppercase pt-1">
            PDF · DOCX · PPTX · TXT · PNG · JPG · JPEG
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-sm bg-[#151515] border border-[#2D2D2D] font-mono text-xs text-[#F87171]">
          ! {error}
        </div>
      )}

      {successMsg && (
        <div className="p-3 rounded-sm bg-[#151515] border border-[#242424] font-mono text-xs text-[#F5F5F5]">
          ✓ {successMsg}
        </div>
      )}
    </div>
  );
};


