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
  timesSampled: number
  auditBoard?: Pick<IAuditBoard, 'id' | 'name'>
  status: 'AUDITED' | null
  vote: 'YES' | 'NO' | 'NO_CONSENSUS' | 'NO_VOTE' | null
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
  riskLimit: string
  randomSeed: string
  contests: IContest[]
  jurisdictions: IJurisdiction[]
  rounds: IRound[]
}
