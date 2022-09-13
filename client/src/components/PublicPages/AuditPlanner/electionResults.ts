import { sum } from '../../../utils/number'

export interface ICandidate {
  id: string
  name: string
  votes: number
}

export interface IElectionResults {
  candidates: ICandidate[]
  numWinners: number
  totalBallotsCast: number
}

export function constructNewCandidate(index: number): ICandidate {
  return {
    id: `candidate-${index}`,
    name: '',
    votes: 0,
  }
}

export function constructInitialElectionResults(): IElectionResults {
  return {
    candidates: [constructNewCandidate(0), constructNewCandidate(1)],
    numWinners: 1,
    totalBallotsCast: 0,
  }
}

export function validateElectionResults({
  candidates,
  numWinners,
  totalBallotsCast,
}: IElectionResults): void {
  if (candidates.length < 2) {
    throw new Error('At least 2 candidates must be specified.')
  }
  if (candidates.some(candidate => !candidate.name)) {
    throw new Error('A name must be provided for all candidates.')
  }
  if (candidates.every(candidate => candidate.votes === 0)) {
    throw new Error('At least 1 candidate must have greater than 0 votes.')
  }
  if (candidates.some(candidate => candidate.votes < 0)) {
    throw new Error('Candidate vote counts cannot be less than 0.')
  }
  if (numWinners < 1) {
    throw new Error('Number of winners must be at least 1.')
  }
  if (numWinners > candidates.length) {
    throw new Error(
      'Number of winners cannot be greater than the number of candidates.'
    )
  }
  if (totalBallotsCast < sum(candidates.map(candidate => candidate.votes))) {
    throw new Error(
      'Total ballots cast cannot be less than the sum of votes for candidates.'
    )
  }
}
