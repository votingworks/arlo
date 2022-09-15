export interface ICandidateFormState {
  name: string
  votes: number | null
}

export interface IElectionResultsFormState {
  candidates: ICandidateFormState[]
  numWinners: number | null
  totalBallotsCast: number | null
}

export function constructNewCandidate(): ICandidateFormState {
  return {
    name: '',
    votes: null,
  }
}

export function constructInitialElectionResults(): IElectionResultsFormState {
  return {
    candidates: [constructNewCandidate(), constructNewCandidate()],
    numWinners: 1,
    totalBallotsCast: null,
  }
}
