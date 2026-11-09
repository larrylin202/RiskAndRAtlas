export type RiskLevel = 'low' | 'moderate' | 'elevated';

export interface RiskLevelInfo {
  level: RiskLevel;
  // Short label shown in the row chip
  label: string;
  // Guidance shown in the expanded row
  description: string;
}

// Single source of truth for score thresholds (scores are 0-100), so the row
// chip and the expanded description can never disagree.
export const getRiskLevel = (score: number): RiskLevelInfo => {
  if (score >= 70) {
    return {
      level: 'elevated',
      label: 'Elevated',
      description: 'Elevated risk — review local preparedness guidance.',
    };
  }
  if (score >= 40) {
    return {
      level: 'moderate',
      label: 'Moderate',
      description: 'Moderate risk — stay informed and make a plan.',
    };
  }
  return {
    level: 'low',
    label: 'Low',
    description: 'Lower risk — continue routine preparedness.',
  };
};
