import constructEmptyInterpretation from './interpretations'
import { IContest } from '../types'

describe('constructEmptyInterpretation', () => {
  it('constructs an empty interpretation for a contest', () => {
    const contest: IContest = {
      id: 'id',
      isTargeted: true,
      name: 'name',
      numWinners: '1',
      votesAllowed: '1',
      choices: [],
      totalBallotsCast: '100',
      jurisdictionIds: [],
    }

    expect(constructEmptyInterpretation(contest)).toStrictEqual({
      contestId: 'id',
      interpretation: null,
      choiceIds: [],
      comment: null,
    })
  })
})
