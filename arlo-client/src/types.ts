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
  name: string
  winners: string
  choices: ICandidate[]
  totalBallotsCast: string
}

export interface IAuditMember {
  name: string
  affiliation: 'DEM' | 'REP' | 'LIB' | 'IND' | ''
}

export interface IBallot {
  id: string
  tabulator: string
  batch: string
  position: string
  status: 'AUDITED' | 'NOT_AUDITED'
  vote: 'YES' | 'NO' | 'NO_CONSENSUS' | 'NO_VOTE' | null
  comment: string
}

export interface IReview {
  vote: IBallot['vote']
  comment: IBallot['comment']
}

export interface IAuditBoard {
  id: string
  name: string
  members: [IAuditMember, IAuditMember] | []
  ballots?: IBallot[]
}

export interface IBallotManifest {
  filename: string | null
  numBallots: number | '' | null
  numBatches: number | '' | null
  uploadedAt: string | null
}

export interface IJurisdiction {
  id: string
  name: string
  contests: string[]
  auditBoards: IAuditBoard[]
  ballotManifest?: IBallotManifest
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
  riskLimit: string
  randomSeed: string
  contests: IContest[]
  jurisdictions: IJurisdiction[]
  rounds: IRound[]
}
