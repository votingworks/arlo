export type ElementType<
  T extends readonly unknown[]
> = T extends readonly (infer ElementType)[] ? ElementType : never

export interface IErrorResponse {
  errors: {
    message: string
  }[]
}

export interface IChoice {
  id: string
  name: string
  numVotes: number
  numVotesCvr?: number
  numVotesNonCvr?: number
}

export interface IContest {
  id: string
  isTargeted: boolean
  name: string
  numWinners: number
  votesAllowed: number
  choices: IChoice[]
  totalBallotsCast: number
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
  /**
   * If a ballot has an invalid write-in with no other selections, the corresponding interpretation
   * will be BLANK. If a ballot for a vote-for-n contest has an invalid write-in alongside a valid
   * selection, the corresponding interpretation will be VOTE.
   */
  hasInvalidWriteIn: boolean
}

export enum BallotStatus {
  NOT_AUDITED = 'NOT_AUDITED',
  AUDITED = 'AUDITED',
  NOT_FOUND = 'NOT_FOUND',
}
