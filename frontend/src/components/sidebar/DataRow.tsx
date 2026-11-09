import React from 'react';
import type { RiskLevelInfo } from '../../utils/riskLevel';
import { ChevronDownIcon } from './icons';

interface DataRowProps {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
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

// One expandable row in the sidebar: icon, label, optional score + severity
// chip, and a chevron showing whether it is open. Clicking it reveals
// `children` underneath.
export const DataRow: React.FC<DataRowProps> = ({
  icon: Icon,
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
        <Icon className="row-icon" />
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
        <ChevronDownIcon className="row-chevron" />
      </button>
      {/* Always rendered so aria-controls points at a real element */}
      <div className="row-detail" id={detailId} hidden={!isOpen}>
        {children}
      </div>
    </div>
  );
};

export default DataRow;
