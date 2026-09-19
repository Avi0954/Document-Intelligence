import React, { useState } from 'react';
import { associateDocument } from '../services/api';

export function AssociateDocumentModal({ primaryDoc, allDocuments, onClose, onAssociationSuccess }) {
  const [selectedRelatedId, setSelectedRelatedId] = useState(primaryDoc.related_document_id || '');
  const [relationshipType, setRelationshipType] = useState('ANSWER_KEY');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Filter available documents to exclude the current primary document
  const availableDocs = allDocuments.filter((d) => d.id !== primaryDoc.id);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await associateDocument(
        primaryDoc.id,
        selectedRelatedId || null,
        relationshipType
      );
      onAssociationSuccess();
      onClose();
    } catch (err) {
      console.error('Failed to associate documents:', err);
      const msg = err.response?.data?.detail || 'Failed to update document relationship.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 font-mono text-xs">
      <div className="bg-[#151515] rounded-sm border border-[#2D2D2D] max-w-md w-full p-6 shadow-2xl space-y-5">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#242424]">
          <div>
            <div className="text-[10px] text-[#707070] uppercase tracking-widest">DOCUMENT ASSOCIATION</div>
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider mt-0.5">ASSOCIATE ANSWER KEY</h3>
          </div>
          <button
            onClick={onClose}
            className="text-xs font-semibold text-[#707070] hover:text-white"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="p-3 bg-[#111111] border border-[#2D2D2D] text-[#F87171] text-xs rounded-sm">
            ! {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          <div>
            <label className="block text-[11px] uppercase tracking-wider text-[#A0A0A0] mb-1">
              QUESTION PAPER
            </label>
            <input
              type="text"
              disabled
              value={primaryDoc.original_name}
              className="w-full text-xs px-3 py-2 bg-[#111111] border border-[#242424] rounded-sm text-[#707070]"
            />
          </div>

          <div>
            <label className="block text-[11px] uppercase tracking-wider text-[#A0A0A0] mb-1">
              RELATIONSHIP TYPE
            </label>
            <select
              value={relationshipType}
              onChange={(e) => setRelationshipType(e.target.value)}
              className="w-full text-xs px-3 py-2 bg-[#111111] border border-[#2D2D2D] text-[#F5F5F5] rounded-sm focus:outline-none focus:border-[#707070] uppercase"
            >
              <option value="ANSWER_KEY">ANSWER KEY</option>
              <option value="SUPPLEMENT">SUPPLEMENT / REFERENCE</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] uppercase tracking-wider text-[#A0A0A0] mb-1">
              ANSWER KEY DOCUMENT
            </label>
            <select
              value={selectedRelatedId}
              onChange={(e) => setSelectedRelatedId(e.target.value)}
              className="w-full text-xs px-3 py-2 bg-[#111111] border border-[#2D2D2D] text-[#F5F5F5] rounded-sm focus:outline-none focus:border-[#707070] uppercase"
            >
              <option value="">-- NO RELATIONSHIP (STANDALONE) --</option>
              {availableDocs.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.original_name} ({(doc.file_type || 'DOC').toUpperCase()})
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-[#242424]">
            <button
              type="button"
              onClick={onClose}
              className="text-xs uppercase tracking-wider px-4 py-2 border border-[#2D2D2D] bg-[#151515] rounded-sm text-[#A0A0A0] hover:text-white hover:bg-[#1C1C1C]"
            >
              CANCEL
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="text-xs font-semibold uppercase tracking-wider px-4 py-2 bg-white text-black rounded-sm hover:bg-[#E5E5E5] disabled:bg-[#242424] disabled:text-[#707070]"
            >
              {submitting ? 'SAVING...' : 'ASSOCIATE'}
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}


