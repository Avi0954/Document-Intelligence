import React from 'react';

export const StatusBadge = ({ status, errorMessage }) => {
  switch (status) {
    case 'COMPLETED':
      return (
        <span className="font-mono text-xs text-white">
          ✓ PROCESSED
        </span>
      );
    case 'EXTRACTING_TEXT':
    case 'EXTRACTING_QUESTIONS':
    case 'PROCESSING':
      return (
        <span className="font-mono text-xs text-[#A0A0A0] inline-flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#A0A0A0] animate-pulse"></span>
          PROCESSING
        </span>
      );
    case 'FAILED':
      return (
        <span className="font-mono text-xs text-[#F87171] font-semibold" title={errorMessage || 'Processing failed'}>
          ! FAILED
        </span>
      );
    case 'PENDING':
    default:
      return (
        <span className="font-mono text-xs text-[#707070]">
          QUEUED
        </span>
      );
  }
};


