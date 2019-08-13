export interface Candidate {
  id: string
  name: string
  numVotes: number | ''
}

export interface SampleSizeOption {
  size: number | string
  prob?: string | number
  type?: string
}

export interface Contest {
  id: string
  name: string
  choices: Candidate[]
  totalBallotsCast: number | ''
  sampleSizeOptions?: SampleSizeOption[]
}

export interface AuditBoard {
  id: string
  name: string
  members: any[]
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
  sampleSize: number
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
  riskLimit: number | string
  randomSeed: string
  contests: Contest[]
  jurisdictions: Jurisdiction[]
  rounds: Round[]
}
