import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { AuthModal } from './components/AuthModal';
import { DocumentUpload } from './components/DocumentUpload';
import { DocumentList } from './components/DocumentList';
import { DocumentChunksModal } from './components/DocumentChunksModal';
import { QuestionFilter } from './components/QuestionFilter';
import { QuestionCard } from './components/QuestionCard';
import { AddQuestionModal } from './components/AddQuestionModal';
import { EditQuestionModal } from './components/EditQuestionModal';
import { AssociateDocumentModal } from './components/AssociateDocumentModal';
import { fetchDocuments, processDocument, deleteDocument, fetchDocumentQuestions, deleteQuestion, getExportUrl } from './services/api';

export function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    return token && savedUser ? JSON.parse(savedUser) : null;
  });

  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [processingDocId, setProcessingDocId] = useState(null);

  // Modals state
  const [chunksModalDoc, setChunksModalDoc] = useState(null);
  const [associateModalDoc, setAssociateModalDoc] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);

  // Filters state
  const [searchQuery, setSearchQuery] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [bloomFilter, setBloomFilter] = useState('');

  // Global Error banner state
  const [errorBanner, setErrorBanner] = useState(null);

  const handleSignOut = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setCurrentUser(null);
    setDocuments([]);
    setSelectedDocId(null);
    setQuestions([]);
  };

  const loadDocuments = async (autoSelectFirst = false) => {
    if (!currentUser) return;
    setLoadingDocs(true);
    try {
      const data = await fetchDocuments();
      setDocuments(data);
      if (data.length > 0) {
        if (autoSelectFirst || !selectedDocId) {
          setSelectedDocId(data[0].id);
        }
      } else {
        setSelectedDocId(null);
        setQuestions([]);
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
      setErrorBanner('Could not connect to service. Please verify backend server is running.');
    } finally {
      setLoadingDocs(false);
    }
  };

  const loadQuestions = async (docId) => {
    if (!docId) return;
    setLoadingQuestions(true);
    setErrorBanner(null);
    try {
      const params = {};
      if (difficultyFilter) params.difficulty = difficultyFilter;
      if (typeFilter) params.question_type = typeFilter;
      if (bloomFilter) params.bloom_taxonomy = bloomFilter;

      const data = await fetchDocumentQuestions(docId, params);
      setQuestions(data);
    } catch (err) {
      console.error('Failed to load questions:', err);
      setErrorBanner('Failed to load questions for this document. Please try again.');
    } finally {
      setLoadingQuestions(false);
    }
  };

  useEffect(() => {
    if (currentUser) {
      loadDocuments(true);
    }
  }, [currentUser]);

  useEffect(() => {
    if (selectedDocId && currentUser) {
      loadQuestions(selectedDocId);
    }
  }, [selectedDocId, difficultyFilter, typeFilter, bloomFilter, currentUser]);

  // Auto-polling for active background processing jobs
  useEffect(() => {
    if (!currentUser) return;
    const hasActiveProcessing = documents.some((d) =>
      ['PENDING', 'PROCESSING', 'EXTRACTING_TEXT', 'EXTRACTING_QUESTIONS'].includes(d.status)
    );

    if (hasActiveProcessing) {
      const interval = setInterval(() => {
        loadDocuments();
        if (selectedDocId) {
          loadQuestions(selectedDocId);
        }
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [documents, selectedDocId, currentUser]);

  const handleProcessDoc = async (docId) => {
    setProcessingDocId(docId);
    setErrorBanner(null);
    try {
      await processDocument(docId);
      await loadDocuments();
      if (selectedDocId === docId) {
        await loadQuestions(docId);
      } else {
        setSelectedDocId(docId);
      }
    } catch (err) {
      console.error('Document processing error:', err);
      setErrorBanner('Processing failed. Could not generate questions for this document.');
      await loadDocuments();
    } finally {
      setProcessingDocId(null);
    }
  };

  const handleDeleteDoc = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document and all its questions?')) return;
    try {
      await deleteDocument(docId);
      if (selectedDocId === docId) {
        setSelectedDocId(null);
      }
      await loadDocuments();
    } catch (err) {
      setErrorBanner('Failed to delete document.');
    }
  };

  const handleDeleteQuestion = async (qId) => {
    if (!window.confirm('Are you sure you want to delete this question?')) return;
    try {
      await deleteQuestion(qId);
      setQuestions(questions.filter((q) => q.id !== qId));
      await loadDocuments();
    } catch (err) {
      setErrorBanner('Failed to delete question.');
    }
  };

  const selectedDocument = documents.find((d) => d.id === selectedDocId);

  // Client-side search filtering
  const filteredQuestions = questions.filter((q) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      q.question_text.toLowerCase().includes(query) ||
      (q.correct_answer && q.correct_answer.toLowerCase().includes(query)) ||
      (q.explanation && q.explanation.toLowerCase().includes(query))
    );
  });

  return (
    <div className="min-h-screen bg-[#0B0B0B] text-[#F5F5F5] flex flex-col font-sans">
      <Navbar user={currentUser} onSignOut={handleSignOut} />

      {!currentUser && (
        <AuthModal
          onAuthSuccess={(userObj) => {
            setCurrentUser(userObj);
          }}
        />
      )}

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-8 py-10 space-y-12">

        {/* Error Banner */}
        {errorBanner && (
          <div className="p-4 rounded-sm bg-[#151515] border border-[#2D2D2D] font-mono text-xs text-[#F5F5F5] flex items-center justify-between gap-3">
            <span>! {errorBanner}</span>
            <button
              onClick={() => setErrorBanner(null)}
              className="text-[#A0A0A0] hover:text-white uppercase font-mono text-[11px]"
            >
              DISMISS
            </button>
          </div>
        )}

        {/* Section 01: Upload & Documents List */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">

          {/* Upload Dropzone */}
          <div className="lg:col-span-5">
            <DocumentUpload onUploadSuccess={() => loadDocuments(true)} />
          </div>

          {/* Document Repository Table */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-mono text-xs text-[#707070] uppercase tracking-widest mb-0.5">02 / EXTRACTION</div>
                <h3 className="text-base font-semibold text-white tracking-tight">
                  Document Repository ({documents.length})
                </h3>
              </div>
              <button
                onClick={() => loadDocuments()}
                className="font-mono text-[11px] uppercase tracking-wider text-[#A0A0A0] hover:text-white transition-colors border border-[#2D2D2D] px-2.5 py-1 rounded-sm bg-[#151515]"
              >
                REFRESH
              </button>
            </div>

            {loadingDocs ? (
              <div className="bg-[#111111] rounded-sm border border-[#242424] p-8 text-center font-mono text-xs text-[#707070]">
                LOADING DOCUMENTS...
              </div>
            ) : (
              <DocumentList
                documents={documents}
                selectedDocId={selectedDocId}
                onSelectDoc={(id) => setSelectedDocId(id)}
                onProcessDoc={handleProcessDoc}
                onDeleteDoc={handleDeleteDoc}
                onViewChunks={(doc) => setChunksModalDoc(doc)}
                onAssociateDoc={(doc) => setAssociateModalDoc(doc)}
                processingDocId={processingDocId}
              />
            )}
          </div>

        </div>

        {/* Section 03: Questions Section */}
        <div className="space-y-6 pt-10 border-t border-[#242424]">

          <div>
            <div className="font-mono text-xs text-[#707070] uppercase tracking-widest mb-1">03 / QUESTIONS</div>
            <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
              <h2 className="text-xl font-semibold text-white tracking-tight">
                {questions.length} QUESTIONS EXTRACTED
              </h2>
              <span className="font-mono text-xs text-[#A0A0A0]">
                {selectedDocument ? selectedDocument.original_name : 'No document selected'}
              </span>
            </div>
          </div>

          {/* Filter Toolbar */}
          <QuestionFilter
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            difficultyFilter={difficultyFilter}
            setDifficultyFilter={setDifficultyFilter}
            typeFilter={typeFilter}
            setTypeFilter={setTypeFilter}
            bloomFilter={bloomFilter}
            setBloomFilter={setBloomFilter}
            onAddQuestion={() => setShowAddModal(true)}
            documentId={selectedDocId}
          />

          {/* Questions Cards List */}
          {loadingQuestions ? (
            <div className="bg-[#111111] rounded-sm border border-[#242424] p-12 text-center font-mono text-xs text-[#707070]">
              LOADING QUESTIONS...
            </div>
          ) : !selectedDocId ? (
            <div className="bg-[#111111] rounded-sm border border-[#242424] p-10 text-center font-mono text-xs text-[#707070]">
              NO DOCUMENT SELECTED. CLICK ON A DOCUMENT ROW IN THE TABLE ABOVE.
            </div>
          ) : filteredQuestions.length === 0 ? (
            <div className="bg-[#111111] rounded-sm border border-[#242424] p-10 text-center font-mono text-xs text-[#707070]">
              {questions.length === 0
                ? 'NO QUESTIONS EXTRACTED YET. CLICK PROCESS ON THIS DOCUMENT.'
                : 'NO QUESTIONS MATCH THE FILTER CRITERIA.'}
            </div>
          ) : (
            <div className="space-y-4">
              {filteredQuestions.map((q, idx) => (
                <QuestionCard
                  key={q.id}
                  question={q}
                  index={idx}
                  onEdit={(qObj) => setEditingQuestion(qObj)}
                  onDelete={handleDeleteQuestion}
                />
              ))}
            </div>
          )}

        </div>

        {/* Section 04: Output / Export Section */}
        {selectedDocId && questions.length > 0 && (
          <div className="space-y-4 pt-10 border-t border-[#242424]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#111111] p-6 rounded-sm border border-[#242424]">
              <div>
                <div className="font-mono text-xs text-[#707070] uppercase tracking-widest mb-1">04 / OUTPUT</div>
                <h3 className="text-base font-semibold text-white tracking-tight">
                  Export Question Bank
                </h3>
                <p className="text-xs text-[#A0A0A0] mt-0.5 font-sans">
                  Export structured examination data for external learning platforms or print formatting.
                </p>
              </div>

              <div className="flex items-center gap-3 font-mono text-xs">
                <a
                  href={getExportUrl(selectedDocId, 'json')}
                  download
                  className="px-4 py-2.5 rounded-sm bg-white hover:bg-[#E5E5E5] text-black font-semibold uppercase tracking-wider transition-colors"
                >
                  EXPORT JSON
                </a>
                <a
                  href={getExportUrl(selectedDocId, 'csv')}
                  download
                  className="px-4 py-2.5 rounded-sm bg-[#151515] hover:bg-[#1C1C1C] text-[#F5F5F5] font-semibold border border-[#2D2D2D] uppercase tracking-wider transition-colors"
                >
                  EXPORT CSV
                </a>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="w-full border-t border-[#242424] py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-8 text-center font-mono text-[11px] text-[#707070]">
          PRAGATI BHARATI — DOCUMENT INTELLIGENCE & QUESTION EXTRACTION STUDIO
        </div>
      </footer>

      {/* Modals */}
      {chunksModalDoc && (
        <DocumentChunksModal
          document={chunksModalDoc}
          onClose={() => setChunksModalDoc(null)}
        />
      )}

      {associateModalDoc && (
        <AssociateDocumentModal
          primaryDoc={associateModalDoc}
          allDocuments={documents}
          onClose={() => setAssociateModalDoc(null)}
          onAssociationSuccess={() => {
            loadDocuments();
          }}
        />
      )}

      {showAddModal && selectedDocId && (
        <AddQuestionModal
          documentId={selectedDocId}
          onClose={() => setShowAddModal(false)}
          onQuestionAdded={() => {
            loadQuestions(selectedDocId);
            loadDocuments();
          }}
        />
      )}

      {editingQuestion && (
        <EditQuestionModal
          question={editingQuestion}
          onClose={() => setEditingQuestion(null)}
          onQuestionUpdated={() => {
            loadQuestions(selectedDocId);
          }}
        />
      )}
    </div>
  );
}
export default App;


