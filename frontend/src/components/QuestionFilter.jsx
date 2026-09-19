import React from 'react';

export const QuestionFilter = ({
  searchQuery,
  setSearchQuery,
  difficultyFilter,
  setDifficultyFilter,
  typeFilter,
  setTypeFilter,
  bloomFilter,
  setBloomFilter,
  onAddQuestion,
  documentId
}) => {
  return (
    <div className="bg-[#111111] p-4 rounded-sm border border-[#242424] flex flex-wrap items-center justify-between gap-3">
      
      {/* Search Input */}
      <div className="w-full sm:w-72">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="SEARCH QUESTIONS..."
          className="w-full bg-[#151515] border border-[#2D2D2D] rounded-sm px-3 py-2 text-xs font-mono text-[#F5F5F5] placeholder-[#707070] focus:outline-none focus:border-[#707070] transition-colors"
        />
      </div>

      {/* Filter Dropdowns & Actions */}
      <div className="flex items-center gap-2 flex-wrap w-full sm:w-auto font-mono text-xs">
        
        {/* Difficulty */}
        <select
          value={difficultyFilter}
          onChange={(e) => setDifficultyFilter(e.target.value)}
          className="bg-[#151515] border border-[#2D2D2D] rounded-sm px-3 py-2 text-[11px] text-[#A0A0A0] uppercase focus:outline-none focus:border-[#707070] cursor-pointer"
        >
          <option value="">DIFFICULTY: ALL</option>
          <option value="EASY">EASY</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="HARD">HARD</option>
        </select>

        {/* Type */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="bg-[#151515] border border-[#2D2D2D] rounded-sm px-3 py-2 text-[11px] text-[#A0A0A0] uppercase focus:outline-none focus:border-[#707070] cursor-pointer"
        >
          <option value="">TYPE: ALL</option>
          <option value="MCQ">MCQ</option>
          <option value="SHORT_ANSWER">SHORT ANSWER</option>
          <option value="LONG_ANSWER">LONG ANSWER</option>
          <option value="TRUE_FALSE">TRUE / FALSE</option>
        </select>

        {/* Bloom */}
        <select
          value={bloomFilter}
          onChange={(e) => setBloomFilter(e.target.value)}
          className="bg-[#151515] border border-[#2D2D2D] rounded-sm px-3 py-2 text-[11px] text-[#A0A0A0] uppercase focus:outline-none focus:border-[#707070] cursor-pointer"
        >
          <option value="">BLOOM: ALL</option>
          <option value="REMEMBER">REMEMBER</option>
          <option value="UNDERSTAND">UNDERSTAND</option>
          <option value="APPLY">APPLY</option>
          <option value="ANALYZE">ANALYZE</option>
          <option value="EVALUATE">EVALUATE</option>
          <option value="CREATE">CREATE</option>
        </select>

        {/* Add Question */}
        {documentId && (
          <button
            onClick={onAddQuestion}
            className="px-4 py-2 rounded-sm bg-white hover:bg-[#E5E5E5] text-black text-xs font-semibold uppercase tracking-wider transition-colors"
          >
            + Add Question
          </button>
        )}

      </div>
    </div>
  );
};


