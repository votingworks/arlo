import { IBallotInterpretation, Interpretation } from '../../types'

export const INVALID_WRITE_IN = 'INVALID_WRITE_IN'

/**
 * A modified representation of a ballot interpretation, optimized for the audit board form
 */
export interface IBallotInterpretationFormRepresentation {
  choiceIds: string[]
  comment: string | null
  contestId: string
  isBlankVoteChecked: boolean
  isContestNotOnBallotChecked: boolean
  isInvalidWriteInChecked: boolean
}

/**
 * Converts an IBallotInterpretation to an IBallotInterpretationFormRepresentation
 */
export function ballotInterpretationToFormRepresentation({
  choiceIds,
  comment,
  contestId,
  hasInvalidWriteIn,
  interpretation,
}: IBallotInterpretation): IBallotInterpretationFormRepresentation {
  return {
    choiceIds,
    comment,
    contestId,
    isBlankVoteChecked:
      interpretation === Interpretation.BLANK && !hasInvalidWriteIn,
    isContestNotOnBallotChecked:
      interpretation === Interpretation.CONTEST_NOT_ON_BALLOT,
    isInvalidWriteInChecked: hasInvalidWriteIn,
  }
}

/**
 * Converts an IBallotInterpretationFormRepresentation to an IBallotInterpretation
 */
export function ballotInterpretationFromFormRepresentation({
  choiceIds,
  comment,
  contestId,
  isBlankVoteChecked,
  isContestNotOnBallotChecked,
  isInvalidWriteInChecked,
}: IBallotInterpretationFormRepresentation): IBallotInterpretation {
  let interpretation: Interpretation | null = null
  if (choiceIds.length > 0) {
    interpretation = Interpretation.VOTE
  } else if (isBlankVoteChecked || isInvalidWriteInChecked) {
    interpretation = Interpretation.BLANK
  } else if (isContestNotOnBallotChecked) {
    interpretation = Interpretation.CONTEST_NOT_ON_BALLOT
  }
  return {
    contestId,
    interpretation,
    choiceIds,
    comment,
    hasInvalidWriteIn: isInvalidWriteInChecked,
  }
}
