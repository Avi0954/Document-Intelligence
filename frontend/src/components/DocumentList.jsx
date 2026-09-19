import React from 'react';
import { StatusBadge } from './StatusBadge';

export const DocumentList = ({
  documents,
  selectedDocId,
  onSelectDoc,
  onProcessDoc,
  onDeleteDoc,
  onViewChunks,
  onAssociateDoc,
  processingDocId
}) => {
  if (documents.length === 0) {
    return (
      <div className="bg-[#111111] rounded-sm border border-[#242424] p-8 text-center text-[#707070] font-mono text-xs">
        NO DOCUMENTS UPLOADED YET. UPLOAD A FILE TO BEGIN.
      </div>
    );
  }

  return (
    <div className="bg-[#111111] rounded-sm border border-[#242424] overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-[#151515] border-b border-[#242424] text-[#A0A0A0] font-mono uppercase tracking-wider text-[11px]">
              <th className="py-3 px-4">DOCUMENT</th>
              <th className="py-3 px-3">TYPE</th>
              <th className="py-3 px-3">STATUS</th>
              <th className="py-3 px-3">QUESTIONS</th>
              <th className="py-3 px-4 text-right">ACTIONS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#242424]">
            {documents.map((doc) => {
              const isSelected = doc.id === selectedDocId;
              const isProcessing = processingDocId === doc.id || ['EXTRACTING_TEXT', 'EXTRACTING_QUESTIONS'].includes(doc.status);

              const fileTypeUpper = (doc.file_type || doc.original_name.split('.').pop() || 'PDF').toUpperCase();

              return (
                <tr
                  key={doc.id}
                  onClick={() => onSelectDoc(doc.id)}
                  className={`cursor-pointer transition-colors ${
                    isSelected ? 'bg-[#181818] font-medium' : 'bg-[#111111] hover:bg-[#151515]'
                  }`}
                >
                  {/* Document Name */}
                  <td className="py-3.5 px-4 text-white font-medium max-w-xs">
                    <div className="truncate">{doc.original_name}</div>
                    {doc.related_document_id && (
                      <div className="text-[10px] font-mono text-[#707070] uppercase mt-0.5">
                        [Answer Key Attached]
                      </div>
                    )}
                    {doc.status === 'FAILED' && doc.error_message && (
                      <div className="text-[10px] font-mono text-[#F87171] mt-0.5 max-w-xs truncate" title={doc.error_message}>
                        ! {doc.error_message}
                      </div>
                    )}
                  </td>

                  {/* Document Type */}
                  <td className="py-3.5 px-3">
                    <span className="font-mono text-[#A0A0A0] text-[10px] uppercase">
                      {fileTypeUpper}
                    </span>
                  </td>

                  {/* Status Badge */}
                  <td className="py-3.5 px-3 whitespace-nowrap">
                    <StatusBadge status={doc.status} errorMessage={doc.error_message} />
                  </td>

                  {/* Question Count */}
                  <td className="py-3.5 px-3 text-white font-mono text-xs">
                    {doc.question_count > 0 ? doc.question_count : '—'}
                  </td>

                  {/* Actions */}
                  <td className="py-3.5 px-4 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-2 font-mono text-[11px]">
                      {doc.chunk_count > 0 && (
                        <button
                          onClick={() => onViewChunks(doc)}
                          className="px-2.5 py-1 rounded-sm text-[#A0A0A0] hover:text-white border border-[#2D2D2D] bg-[#151515] hover:bg-[#1C1C1C] transition-colors uppercase tracking-wider"
                        >
                          View Content
                        </button>
                      )}

                      <button
                        onClick={() => onAssociateDoc(doc)}
                        className="px-2.5 py-1 rounded-sm text-[#A0A0A0] hover:text-white border border-[#2D2D2D] bg-[#151515] hover:bg-[#1C1C1C] transition-colors uppercase tracking-wider"
                        title="Associate document"
                      >
                        Associate
                      </button>

                      <button
                        onClick={() => onProcessDoc(doc.id)}
                        disabled={isProcessing}
                        className={`px-3 py-1 rounded-sm uppercase tracking-wider font-semibold transition-colors ${
                          isProcessing
                            ? 'bg-[#242424] text-[#707070] cursor-not-allowed'
                            : doc.status === 'FAILED'
                            ? 'bg-[#F87171] text-black hover:bg-[#ef4444]'
                            : 'bg-white text-black hover:bg-[#E5E5E5]'
                        }`}
                      >
                        {isProcessing ? 'Processing' : (doc.status === 'COMPLETED' ? 'Reprocess' : doc.status === 'FAILED' ? 'Retry' : 'Process')}
                      </button>

                      <button
                        onClick={() => onDeleteDoc(doc.id)}
                        className="px-2 py-1 rounded-sm text-[#707070] hover:text-[#F87171] hover:bg-[#1C1C1C] transition-colors uppercase tracking-wider"
                        title="Delete Document"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};


