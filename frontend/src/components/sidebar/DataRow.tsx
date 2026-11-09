import React from 'react';
import type { RiskLevelInfo } from '../../utils/riskLevel';

interface DataRowProps {
  icon: string;
  label: string;
  // Color of the strip on the right edge of the row (identifies the hazard type)
  accent?: string;
  // Omit for rows without a score column (facilities)
  score?: string;
  // Severity chip shown next to the score; omit when there is no real score
  level?: RiskLevelInfo | null;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

const Chevron: React.FC = () => (
  <svg
    className="row-chevron"
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    aria-hidden="true"
    focusable="false"
  >
    <path
      d="M4 6l4 4 4-4"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

// One expandable row in the sidebar: icon, label, optional score + severity
// chip, and a chevron showing whether it is open. Clicking it reveals
// `children` underneath.
export const DataRow: React.FC<DataRowProps> = ({
  icon,
  label,
  accent,
  score,
  level,
  isOpen,
  onToggle,
  children,
}) => {
  const detailId = `row-detail-${label.toLowerCase().replace(/\W+/g, '-')}`;
  const hasScore = score !== undefined;

  return (
    <div className="interactive-row-wrap">
      <button
        type="button"
        className={hasScore ? 'data-row' : 'data-row data-row--no-score'}
        style={accent ? ({ '--accent': accent } as React.CSSProperties) : undefined}
        aria-expanded={isOpen}
        aria-controls={detailId}
        onClick={onToggle}
      >
        <img src={icon} alt="" className="row-icon" />
        <span className="row-label">{label}</span>
        {hasScore && (
          <>
            <strong className="risk-score">{score}</strong>
            <span className="risk-level-cell">
              {level && (
                <span className={`risk-chip risk-chip--${level.level}`}>{level.label}</span>
              )}
            </span>
          </>
        )}
        <Chevron />
      </button>
      {/* Always rendered so aria-controls points at a real element */}
      <div className="row-detail" id={detailId} hidden={!isOpen}>
        {children}
      </div>
    </div>
  );
};

export default DataRow;
