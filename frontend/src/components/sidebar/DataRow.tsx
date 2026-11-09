import React from 'react';
import infoIcon from '../../assets/sidebar/info.svg';

interface DataRowProps {
  icon: string;
  label: string;
  // Color of the strip on the right edge of the row
  accent?: string;
  // Omit for rows without a score column (facilities)
  score?: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

// One expandable row in the sidebar: icon, label, optional score, info icon.
// Clicking it reveals `children` underneath.
export const DataRow: React.FC<DataRowProps> = ({
  icon,
  label,
  accent,
  score,
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
        {hasScore && <strong className="risk-score">{score}</strong>}
        <img src={infoIcon} alt="" className="info-icon" />
      </button>
      {/* Always rendered so aria-controls points at a real element */}
      <div className="row-detail" id={detailId} hidden={!isOpen}>
        {children}
      </div>
    </div>
  );
};

export default DataRow;
