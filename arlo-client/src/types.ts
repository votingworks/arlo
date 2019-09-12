export interface CreateAuditParams {
  electionId: string
}

export interface AuditFlowParams extends CreateAuditParams {
  token: string
  round?: string
  ballot?: string
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
  choices: Candidate[]
  totalBallotsCast: string
}

export interface AuditMember {
  name: string
  affiliation: 'DEM' | 'REP' | 'LIB' | 'IND' | ''
}

export interface Ballot {
  tabulator: string
  batch: string
  record: string
  status: 'AUDITED' | 'NOT_AUDITED'
  vote: 'YES' | 'NO' | 'NO_CONSENSUS' | 'NO_VOTE' | null
}

export interface AuditBoard {
  id: string
  name: string
  members: [AuditMember, AuditMember] | []
  ballots?: Ballot[]
}

export interface BallotManifest {
  filename: string | null
  numBallots: number | '' | null
  numBatches: number | '' | null
  uploadedAt: string | null
}

export interface Jurisdiction {
  id: string
  name: string
  contests: string[]
  auditBoards: AuditBoard[]
  ballotManifest?: BallotManifest
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
