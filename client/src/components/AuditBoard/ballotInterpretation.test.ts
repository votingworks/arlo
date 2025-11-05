import { expect, test } from 'vitest'
import {
  ballotInterpretationFromFormState,
  ballotInterpretationToFormState,
  IBallotInterpretationFormState,
} from './ballotInterpretation'
import { IBallotInterpretation, Interpretation } from '../../types'

const testCases: [
  string, // Description
  IBallotInterpretation,
  IBallotInterpretationFormState
][] = [
  [
    'no interpretation',
    {
      choiceIds: [],
      comment: 'comment',
      contestId: 'contestId',
      hasInvalidWriteIn: false,
      interpretation: null,
    },
    {
      choiceIds: [],
      comment: 'comment',
      contestId: 'contestId',
      isBlankVoteChecked: false,
      isContestNotOnBallotChecked: false,
      isInvalidWriteInChecked: false,
    },
  ],
  [
    'blank',
    {
      choiceIds: [],
      comment: 'comment',
      contestId: 'contestId',
      hasInvalidWriteIn: false,
      interpretation: Interpretation.BLANK,
    },
    {
      choiceIds: [],
      comment: 'comment',
      contestId: 'contestId',
      isBlankVoteChecked: true,
      isContestNotOnBallotChecked: false,
      isInvalidWriteInChecked: false,
    },
  ],
  [
    'invalid write-in',
    {
      choiceIds: [],
      comment: 'comment',
      contestId: 'contestId',
      hasInvalidWriteIn: true,
      interpretation: Interpretation.BLANK,
    },
    {
      choiceIds: [],
      comment: 'comment',
      contestId: 'contestId',
      isBlankVoteChecked: false,
      isContestNotOnBallotChecked: false,
      isInvalidWriteInChecked: true,
    },
  ],
  [
    'vote',
    {
      choiceIds: ['choiceId1', 'choiceId2'],
      comment: 'comment',
      contestId: 'contestId',
      hasInvalidWriteIn: false,
      interpretation: Interpretation.VOTE,
    },
    {
      choiceIds: ['choiceId1', 'choiceId2'],
      comment: 'comment',
      contestId: 'contestId',
      isBlankVoteChecked: false,
      isContestNotOnBallotChecked: false,
      isInvalidWriteInChecked: false,
    },
  ],
  [
    'vote with invalid write-in',
    {
      choiceIds: ['choiceId1', 'choiceId2'],
      comment: 'comment',
      contestId: 'contestId',
      hasInvalidWriteIn: true,
      interpretation: Interpretation.VOTE,
    },
    {
      choiceIds: ['choiceId1', 'choiceId2'],
      comment: 'comment',
      contestId: 'contestId',
      isBlankVoteChecked: false,
      isContestNotOnBallotChecked: false,
      isInvalidWriteInChecked: true,
    },
  ],
  [
    'contest not on ballot',
    {
      choiceIds: [],
      comment: 'comment',
      contestId: 'contestId',
      hasInvalidWriteIn: false,
      interpretation: Interpretation.CONTEST_NOT_ON_BALLOT,
    },
    {
      choiceIds: [],
      comment: 'comment',
      contestId: 'contestId',
      isBlankVoteChecked: false,
      isContestNotOnBallotChecked: true,
      isInvalidWriteInChecked: false,
    },
  ],
]
test.each(testCases)(
  'ballotInterpretation transformations (%s)',
  (_description, ballotInterpretation, ballotInterpretationFormState) => {
    expect(ballotInterpretationToFormState(ballotInterpretation)).toEqual(
      ballotInterpretationFormState
    )
    expect(
      ballotInterpretationFromFormState(ballotInterpretationFormState)
    ).toEqual(ballotInterpretation)
  }
)
