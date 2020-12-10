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

export interface IAuditBoardMember {
  name: string
  affiliation: string | null
}

export interface IAuditBoard {
  id: string
  name: string
  jurisdictionId: string
  jurisdictionName: string
  roundId: string
  members: IAuditBoardMember[]
  signedOffAt: string | null
  passphrase?: string
}

export interface ISampleSizeOption {
  size: number | string
  prob: number | null
  key: string
}

export interface IElectionMeta {
  id: string
  auditName: string
  electionName: string
  state: string
}

export interface IOrganizationMeta {
  id: string
  name: string
  elections: IElectionMeta[]
}

export interface IJurisdictionMeta {
  id: string
  name: string
  election: IElectionMeta
  numBallots: number | null
}

export interface IUserMeta {
  name: string
  email: string
  type: 'audit_admin' | 'jurisdiction_admin' | 'audit_board'
  organizations: IOrganizationMeta[]
  jurisdictions: IJurisdictionMeta[]
}

export interface IAuthData {
  isAuthenticated: boolean | null
  meta?: IUserMeta
}
