export interface ICandidate {
  name: string
  votes: number
}

export interface IElectionResults {
  candidates: ICandidate[]
  numWinners: number
  totalBallotsCast: number
}

export function constructNewCandidate(): ICandidate {
  return {
    name: '',
    votes: 0,
  }
}

export function constructInitialElectionResults(): IElectionResults {
  return {
    candidates: [constructNewCandidate(), constructNewCandidate()],
    numWinners: 1,
    totalBallotsCast: 0,
  }
}
