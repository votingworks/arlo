export type ElementType<
  T extends readonly unknown[]
> = T extends readonly (infer ElementType)[] ? ElementType : never

export interface IErrorResponse {
  errors: {
    message: string
  }[]
}

export interface ICandidate {
  id: string
  name: string
  numVotes: number | string
  numVotesCvr?: number
  numVotesNonCvr?: number
}

export interface IContest {
  id: string
  isTargeted: boolean
  name: string
  numWinners: string
  votesAllowed: string
  choices: ICandidate[]
  totalBallotsCast: string
  jurisdictionIds: string[]
}

export enum Interpretation {
  BLANK = 'BLANK',
  CANT_AGREE = 'CANT_AGREE',
  VOTE = 'VOTE',
  CONTEST_NOT_ON_BALLOT = 'CONTEST_NOT_ON_BALLOT',
}

export interface IBallotInterpretation {
  contestId: string
  interpretation: Interpretation | null
  choiceIds: string[]
  comment: string | null
}

export enum BallotStatus {
  NOT_AUDITED = 'NOT_AUDITED',
  AUDITED = 'AUDITED',
  NOT_FOUND = 'NOT_FOUND',
}
