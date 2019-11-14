export interface Params {
  electionId: string
}

export interface Candidate {
  id: string
  name: string
  numVotes: number | string
}

export interface SampleSizeOption {
  size: number | string
  prob: number | null
  type: string | null
}

export interface Contest {
  id: string
  name: string
  winners: string
  choices: Candidate[]
  totalBallotsCast: string
}

export interface Ballot {
  timesSampled: number
  auditBoard?: Pick<AuditBoard, 'id' | 'name'>
  status: 'AUDITED' | null
  vote: 'YES' | 'NO' | 'NO_CONSENSUS' | 'NO_VOTE' | null
  comment: string
  position: string
  batch: {
    id: string
    name: string
    tabulator: string | null
  }
}

export interface AuditBoardMember {
  name: string
  affiliation: string
}

export interface AuditBoard {
  id: string
  name: string
  members: AuditBoardMember[]
  ballots?: Ballot[] // TODO remove
}

export interface BallotManifest {
  filename: string | null
  numBallots: number | '' | null
  numBatches: number | '' | null
  uploadedAt: string | null
}

export interface Batch {
  id: string
  name: string
  numBallots: number
  storageLocation: null | string
  tabulator: null | string
}

export interface Jurisdiction {
  id: string
  name: string
  contests: string[]
  auditBoards: AuditBoard[]
  ballotManifest?: BallotManifest
  batches?: Batch[] // TODO make not optional
}

export interface RoundContest {
  id: string
  results: {
    [key: string]: number
  }
  sampleSizeOptions: SampleSizeOption[] | null
  sampleSize: number | null
  endMeasurements: {
    isComplete: null | boolean
    pvalue: null | number
  }
}

export interface Round {
  id: string
  name?: string
  randomSeed?: string
  riskLimit?: number
  contests: RoundContest[]
  startedAt: string
  endedAt: string | null
  jurisdictions?: {
    [key: string]: {
      numBallots: number
    }
  }
}

export interface Audit {
  name: string
  riskLimit: string
  randomSeed: string
  contests: Contest[]
  jurisdictions: Jurisdiction[]
  rounds: Round[]
}
