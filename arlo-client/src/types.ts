export type ElementType<
  T extends readonly unknown[]
> = T extends readonly (infer ElementType)[] ? ElementType : never

export interface IErrorResponse {
  errors: {
    message: string
  }[]
}

export interface ICreateAuditParams {
  electionId: string
}

export interface IAuditFlowParams extends ICreateAuditParams {
  token: string
  roundId?: string
  ballotId?: string
}

export interface ICandidate {
  id: string
  name: string
  numVotes: number | string
}

export interface ISampleSizeOption {
  size: number | string
  prob: number | null
  type: string | null
}

export interface IContest {
  id: string
  isTargeted: boolean
  name: string
  numWinners: string
  votesAllowed: string
  choices: ICandidate[]
  totalBallotsCast: string
}

export interface IBallot {
  timesSampled: number
  auditBoard?: Pick<IAuditBoard, 'id' | 'name'>
  status: 'AUDITED' | null
  vote: string
  comment: string
  position: number
  batch: {
    id: string
    name: string
    tabulator: string | null
  }
}

export interface IAuditBoardMember {
  name: string
  affiliation: string
}

export interface IReview {
  vote: IBallot['vote']
  comment: IBallot['comment']
}

export interface IAuditBoard {
  id: string
  name: string
  members: IAuditBoardMember[]
  passphrase?: string
  ballots?: IBallot[] // TODO remove
}

export interface IBallotManifest {
  filename: string | null
  numBallots: number | '' | null
  numBatches: number | '' | null
  uploadedAt: string | null
}

export interface IBatch {
  id: string
  name: string
  numBallots: number
  storageLocation: null | string
  tabulator: null | string
}

export interface IJurisdiction {
  id: string
  name: string
  contests: string[]
  auditBoards: IAuditBoard[]
  ballotManifest?: IBallotManifest
  batches?: IBatch[] // optional until I'm ready to update everything
}

export interface IRoundContest {
  id: string
  results: {
    [key: string]: number
  }
  sampleSizeOptions: ISampleSizeOption[] | null
  sampleSize: number | null
  endMeasurements: {
    isComplete: null | boolean
    pvalue: null | number
  }
}

export interface IRound {
  id: string
  name?: string
  randomSeed?: string
  riskLimit?: number
  contests: IRoundContest[]
  startedAt: string
  endedAt: string | null
  jurisdictions?: {
    [key: string]: {
      numBallots: number
    }
  }
}

export interface IAudit {
  name: string
  online: boolean
  riskLimit: string
  randomSeed: string
  contests: IContest[]
  jurisdictions: IJurisdiction[]
  rounds: IRound[]
  frozenAt: string | null
}

export interface IElectionMeta {
  id: string
  name: string
  state: string
  electionDate: string
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
}

export interface IUserMeta {
  name: string
  email: string
  type: 'audit_admin' | 'jurisdiction_admin'
  organizations: IOrganizationMeta[]
  jurisdictions: IJurisdictionMeta[]
}

export interface IAuthData {
  isAuthenticated: boolean
  meta?: IUserMeta
}
