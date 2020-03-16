export interface IChoiceValues {
  id?: string
  name: string
  numVotes: string | number
}

export interface IContestValues {
  name: string
  isTargeted: boolean
  totalBallotsCast: string
  numWinners: string
  votesAllowed: string
  choices: IChoiceValues[]
}

export interface IValues {
  contests: IContestValues[]
}
