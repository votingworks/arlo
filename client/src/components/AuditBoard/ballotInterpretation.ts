import { IBallotInterpretation, Interpretation } from '../../types'

export const INVALID_WRITE_IN = 'INVALID_WRITE_IN'

/**
 * A modified representation of a ballot interpretation, optimized for the audit board form
 */
export interface IBallotInterpretationFormState {
  choiceIds: string[]
  comment: string | null
  contestId: string
  isBlankVoteChecked: boolean
  isContestNotOnBallotChecked: boolean
  isInvalidWriteInChecked: boolean
}

/**
 * Converts an IBallotInterpretation to an IBallotInterpretationFormState
 */
export function ballotInterpretationToFormState({
  choiceIds,
  comment,
  contestId,
  hasInvalidWriteIn,
  interpretation,
}: IBallotInterpretation): IBallotInterpretationFormState {
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
 * Converts an IBallotInterpretationFormState to an IBallotInterpretation
 */
export function ballotInterpretationFromFormState({
  choiceIds,
  comment,
  contestId,
  isBlankVoteChecked,
  isContestNotOnBallotChecked,
  isInvalidWriteInChecked,
}: IBallotInterpretationFormState): IBallotInterpretation {
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
