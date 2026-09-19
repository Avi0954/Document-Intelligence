import React, { useState } from 'react';

export const QuestionCard = ({ question, index, onEdit, onDelete }) => {
  const [showAnswer, setShowAnswer] = useState(false);

  const formattedNum = String(index + 1).padStart(2, '0');
  const typeLabel = question.question_type === 'MCQ' ? 'MCQ' :
                    question.question_type === 'SHORT_ANSWER' ? 'SHORT ANSWER' :
                    question.question_type === 'LONG_ANSWER' ? 'LONG ANSWER' :
                    question.question_type === 'TRUE_FALSE' ? 'TRUE / FALSE' : question.question_type;

  const statusLabel = question.answer_status === 'VERIFIED' ? 'VERIFIED' :
                      question.answer_status === 'UNCERTAIN' ? 'UNCERTAIN' : 'NOT FOUND';

  return (
    <div className="bg-[#111111] p-6 rounded-sm border border-[#242424] space-y-5 hover:border-[#2D2D2D] transition-colors">
      
      {/* Editorial Question Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-baseline gap-4">
          <span className="font-mono text-3xl font-light text-[#404040]">
            {formattedNum}
          </span>
          {question.page_reference && (
            <span className="font-mono text-[11px] text-[#707070] uppercase tracking-wider">
              PAGE {String(question.page_reference).padStart(2, '0')}
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 font-mono text-[11px] uppercase tracking-wider">
          <button
            onClick={() => onEdit(question)}
            className="text-[#A0A0A0] hover:text-white transition-colors"
          >
            Edit
          </button>
          <span className="text-[#404040]">·</span>
          <button
            onClick={() => onDelete(question.id)}
            className="text-[#707070] hover:text-[#F87171] transition-colors"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Question Text */}
      <h4 className="text-base sm:text-lg font-medium text-[#F5F5F5] leading-relaxed">
        {question.question_text}
      </h4>

      {/* Thin Editorial Divider */}
      <div className="border-t border-[#242424]"></div>

      {/* MCQ Options */}
      {question.question_type === 'MCQ' && Array.isArray(question.options) && question.options.length > 0 && (
        <div className="space-y-2 text-xs font-sans">
          {question.options.map((option, optIdx) => {
            const isCorrect = showAnswer && question.correct_answer && (
              option.toLowerCase().includes(question.correct_answer.toLowerCase()) ||
              question.correct_answer.toLowerCase().includes(option.toLowerCase())
            );
            return (
              <div
                key={optIdx}
                className={`p-3 rounded-sm border transition-colors ${
                  isCorrect
                    ? 'bg-white border-white text-black font-semibold'
                    : 'bg-[#151515] border-[#242424] text-[#F5F5F5]'
                }`}
              >
                {option}
              </div>
            );
          })}
        </div>
      )}

      {/* Answer & Metadata Drawer */}
      <div className="pt-2">
        <button
          onClick={() => setShowAnswer(!showAnswer)}
          className="font-mono text-xs text-[#A0A0A0] hover:text-white uppercase tracking-wider transition-colors"
        >
          {showAnswer ? '— Hide Answer & Metadata' : '+ View Answer & Metadata'}
        </button>

        {showAnswer && (
          <div className="mt-4 p-5 rounded-sm bg-[#151515] border border-[#242424] space-y-4 text-xs font-mono">
            {/* Correct Answer */}
            <div>
              <span className="text-[#707070] uppercase tracking-widest text-[10px] block">ANSWER</span>
              <p className="font-sans font-semibold text-white text-sm mt-1">
                {question.correct_answer ? question.correct_answer : <span className="text-[#707070] italic">No answer found</span>}
              </p>
            </div>

            {/* Rationale */}
            {question.explanation && (
              <div className="pt-3 border-t border-[#242424]">
                <span className="text-[#707070] uppercase tracking-widest text-[10px] block">RATIONALE</span>
                <p className="font-sans text-[#A0A0A0] text-xs mt-1 leading-relaxed">{question.explanation}</p>
              </div>
            )}

            {/* Structured Metadata Grid */}
            <div className="pt-3 border-t border-[#242424] grid grid-cols-2 sm:grid-cols-5 gap-3 text-[11px] uppercase tracking-wider">
              <div>
                <span className="text-[#707070] block text-[9px]">TYPE</span>
                <span className="text-[#F5F5F5]">{typeLabel}</span>
              </div>
              <div>
                <span className="text-[#707070] block text-[9px]">DIFFICULTY</span>
                <span className="text-[#F5F5F5]">{question.difficulty || 'MEDIUM'}</span>
              </div>
              <div>
                <span className="text-[#707070] block text-[9px]">BLOOM</span>
                <span className="text-[#F5F5F5]">{question.bloom_taxonomy || 'UNDERSTAND'}</span>
              </div>
              <div>
                <span className="text-[#707070] block text-[9px]">SOURCE</span>
                <span className="text-[#F5F5F5]">{question.page_reference ? `PAGE ${question.page_reference}` : 'N/A'}</span>
              </div>
              <div>
                <span className="text-[#707070] block text-[9px]">STATUS</span>
                <span className="text-[#F5F5F5]">{statusLabel}</span>
              </div>
            </div>

          </div>
        )}
      </div>

    </div>
  );
};


