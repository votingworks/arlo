export interface ICandidate {
  name: string
  votes: number
}

export interface IElectionResults {
  candidates: ICandidate[]
  numWinners: number
  totalBallotsCast: number
}

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

export function assertIsElectionResults(
  electionResultsFormState: IElectionResultsFormState
): asserts electionResultsFormState is IElectionResults {
  const { candidates, numWinners, totalBallotsCast } = electionResultsFormState
  if (
    candidates.some(candidate => candidate.votes === null) ||
    numWinners === null ||
    totalBallotsCast === null
  ) {
    throw new Error('Required field is null')
  }
}
