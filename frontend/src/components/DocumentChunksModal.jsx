import React, { useEffect, useState } from 'react';
import { fetchDocumentChunks } from '../services/api';

export const DocumentChunksModal = ({ document, onClose }) => {
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadChunks = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchDocumentChunks(document.id);
        setChunks(data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load document text chunks.');
      } finally {
        setLoading(false);
      }
    };

    if (document) {
      loadChunks();
    }
  }, [document]);

  if (!document) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75">
      <div className="w-full max-w-3xl bg-[#151515] border border-[#2D2D2D] rounded-sm shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#242424]">
          <div>
            <div className="font-mono text-xs text-[#707070] uppercase tracking-widest">DOCUMENT READER</div>
            <h3 className="text-sm font-semibold text-white mt-0.5">{document.original_name}</h3>
          </div>
          <button
            onClick={onClose}
            className="font-mono text-xs uppercase tracking-wider text-[#A0A0A0] hover:text-white px-2.5 py-1 rounded-sm border border-[#2D2D2D] hover:bg-[#1C1C1C] transition-colors"
          >
            CLOSE
          </button>
        </div>

        {/* Editorial Content Body */}
        <div className="p-8 overflow-y-auto space-y-6 flex-1 font-sans text-xs">
          {loading ? (
            <div className="text-center py-12 font-mono text-[#707070] text-xs">
              LOADING EXTRACTED CONTENT...
            </div>
          ) : error ? (
            <div className="p-3 rounded-sm bg-[#151515] border border-[#2D2D2D] font-mono text-[#F87171] text-xs">
              ! {error}
            </div>
          ) : chunks.length === 0 ? (
            <div className="text-center py-12 font-mono text-[#707070] text-xs">
              NO EXTRACTED TEXT FOUND. PROCESS DOCUMENT FIRST.
            </div>
          ) : (
            chunks.map((chunk, idx) => (
              <div
                key={chunk.id}
                className="space-y-3"
              >
                <div className="flex items-center gap-3 font-mono text-[11px] text-[#A0A0A0] uppercase tracking-widest">
                  <span>{chunk.page_number ? `PAGE ${String(chunk.page_number).padStart(2, '0')}` : `SECTION ${String(idx + 1).padStart(2, '0')}`}</span>
                  <div className="flex-1 border-t border-[#242424]"></div>
                </div>

                <p className="text-sm text-[#F5F5F5] whitespace-pre-wrap leading-relaxed font-normal p-4 bg-[#111111] rounded-sm border border-[#242424]">
                  {chunk.content}
                </p>
              </div>
            ))
          )}
        </div>

      </div>
    </div>
  );
};


