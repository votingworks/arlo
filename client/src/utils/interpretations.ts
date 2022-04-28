import { IBallotInterpretation, IContest } from '../types'

export default function constructEmptyInterpretation(
  contest: IContest
): IBallotInterpretation {
  return {
    contestId: contest.id,
    interpretation: null,
    choiceIds: [],
    comment: null,
  }
}
