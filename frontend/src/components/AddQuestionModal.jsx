import React, { useState } from 'react';
import { addCustomQuestion } from '../services/api';

export const AddQuestionModal = ({ documentId, onClose, onQuestionAdded }) => {
  const [questionText, setQuestionText] = useState('');
  const [questionType, setQuestionType] = useState('MCQ');
  const [optionsStr, setOptionsStr] = useState('A. Option 1\nB. Option 2\nC. Option 3\nD. Option 4');
  const [correctAnswer, setCorrectAnswer] = useState('');
  const [explanation, setExplanation] = useState('');
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [bloomTaxonomy, setBloomTaxonomy] = useState('UNDERSTAND');
  const [pageReference, setPageReference] = useState('');
  
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!questionText.trim()) {
      setError('Question text is required.');
      return;
    }
    if (!correctAnswer.trim()) {
      setError('Correct answer is required.');
      return;
    }

    setSubmitting(true);
    setError(null);

    let options = null;
    if (questionType === 'MCQ') {
      options = optionsStr.split('\n').map((opt) => opt.trim()).filter(Boolean);
    }

    try {
      const newQuestion = await addCustomQuestion(documentId, {
        question_text: questionText,
        question_type: questionType,
        options: options,
        correct_answer: correctAnswer,
        explanation: explanation,
        difficulty: difficulty,
        bloom_taxonomy: bloomTaxonomy,
        page_reference: pageReference ? parseInt(pageReference, 10) : null
      });

      if (onQuestionAdded) {
        onQuestionAdded(newQuestion);
      }
      onClose();
    } catch (err) {
      console.error('Add question error:', err);
      setError('Failed to add question. Please check inputs and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75">
      <div className="w-full max-w-xl bg-[#151515] border border-[#2D2D2D] rounded-sm shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#242424]">
          <h3 className="font-mono text-sm font-semibold uppercase tracking-wider text-white">CREATE QUESTION</h3>
          <button
            onClick={onClose}
            className="font-mono text-xs text-[#707070] hover:text-white uppercase tracking-wider transition-colors"
          >
            CANCEL
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4 flex-1 text-xs">
          {error && (
            <div className="p-3 rounded-sm bg-[#111111] border border-[#2D2D2D] font-mono text-[#F87171]">
              ! {error}
            </div>
          )}

          <div>
            <label className="block font-mono text-[11px] uppercase tracking-wider text-[#A0A0A0] mb-1">QUESTION STATEMENT *</label>
            <textarea
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              rows={3}
              required
              placeholder="Enter the question statement..."
              className="w-full bg-[#111111] border border-[#2D2D2D] rounded-sm p-3 text-xs text-[#F5F5F5] placeholder-[#707070] focus:outline-none focus:border-[#707070]"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono">
            <div>
              <label className="block text-[11px] uppercase tracking-wider text-[#A0A0A0] mb-1">QUESTION TYPE</label>
              <select
                value={questionType}
                onChange={(e) => setQuestionType(e.target.value)}
                className="w-full bg-[#111111] border border-[#2D2D2D] rounded-sm p-2 text-xs text-[#F5F5F5] focus:outline-none focus:border-[#707070] cursor-pointer uppercase"
              >
                <option value="MCQ">MCQ</option>
                <option value="SHORT_ANSWER">SHORT ANSWER</option>
                <option value="LONG_ANSWER">LONG ANSWER</option>
                <option value="TRUE_FALSE">TRUE / FALSE</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] uppercase tracking-wider text-[#A0A0A0] mb-1">DIFFICULTY</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full bg-[#111111] border border-[#2D2D2D] rounded-sm p-2 text-xs text-[#F5F5F5] focus:outline-none focus:border-[#707070] cursor-pointer uppercase"
              >
                <option value="EASY">EASY</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HARD">HARD</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] uppercase tracking-wider text-[#A0A0A0] mb-1">BLOOM'S TAXONOMY</label>
              <select
                value={bloomTaxonomy}
                onChange={(e) => setBloomTaxonomy(e.target.value)}
                className="w-full bg-[#111111] border border-[#2D2D2D] rounded-sm p-2 text-xs text-[#F5F5F5] focus:outline-none focus:border-[#707070] cursor-pointer uppercase"
              >
                <option value="REMEMBER">REMEMBER</option>
                <option value="UNDERSTAND">UNDERSTAND</option>
                <option value="APPLY">APPLY</option>
                <option value="ANALYZE">ANALYZE</option>
                <option value="EVALUATE">EVALUATE</option>
                <option value="CREATE">CREATE</option>
              </select>
            </div>
          </div>

          {questionType === 'MCQ' && (
            <div>
              <label className="block font-mono text-[11px] uppercase tracking-wider text-[#A0A0A0] mb-1">OPTIONS (ONE PER LINE)</label>
              <textarea
                value={optionsStr}
                onChange={(e) => setOptionsStr(e.target.value)}
                rows={4}
                className="w-full bg-[#111111] border border-[#2D2D2D] rounded-sm p-3 text-xs text-[#F5F5F5] placeholder-[#707070] focus:outline-none focus:border-[#707070] font-mono"
              />
            </div>
          )}

          <div>
            <label className="block font-mono text-[11px] uppercase tracking-wider text-[#A0A0A0] mb-1">CORRECT ANSWER *</label>
            <input
              type="text"
              value={correctAnswer}
              onChange={(e) => setCorrectAnswer(e.target.value)}
              required
              placeholder="e.g. A. Option 1"
              className="w-full bg-[#111111] border border-[#2D2D2D] rounded-sm p-2.5 text-xs text-[#F5F5F5] placeholder-[#707070] focus:outline-none focus:border-[#707070]"
            />
          </div>

          <div>
            <label className="block font-mono text-[11px] uppercase tracking-wider text-[#A0A0A0] mb-1">RATIONALE / EXPLANATION</label>
            <textarea
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              rows={2}
              placeholder="Explain why this answer is correct..."
              className="w-full bg-[#111111] border border-[#2D2D2D] rounded-sm p-3 text-xs text-[#F5F5F5] placeholder-[#707070] focus:outline-none focus:border-[#707070]"
            />
          </div>

          <div>
            <label className="block font-mono text-[11px] uppercase tracking-wider text-[#A0A0A0] mb-1">PAGE REFERENCE</label>
            <input
              type="number"
              value={pageReference}
              onChange={(e) => setPageReference(e.target.value)}
              placeholder="e.g. 1"
              className="w-full font-mono bg-[#111111] border border-[#2D2D2D] rounded-sm p-2.5 text-xs text-[#F5F5F5] placeholder-[#707070] focus:outline-none focus:border-[#707070]"
            />
          </div>

          {/* Footer Buttons */}
          <div className="flex items-center justify-end gap-2 pt-4 border-t border-[#242424] font-mono text-xs">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-sm uppercase tracking-wider bg-[#151515] text-[#A0A0A0] border border-[#2D2D2D] hover:text-white hover:bg-[#1C1C1C] transition-colors"
            >
              CANCEL
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-sm bg-white hover:bg-[#E5E5E5] text-black font-semibold uppercase tracking-wider transition-colors disabled:bg-[#242424] disabled:text-[#707070]"
            >
              {submitting ? 'SAVING...' : 'SAVE QUESTION'}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};


