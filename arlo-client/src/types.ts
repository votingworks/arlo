export interface Candidate {
  id?: string
  name: string
  numVotes: number | ''
}

export interface Contest {
  id: string
  name: string
  choices: Candidate[]
  totalBallotsCast: number | ''
  sampleSizeOptions?: {
    size: number
    prob?: string | number
    type?: 'ASN'
  }[]
}

export interface AuditBoard {
  id: string
  members: any[]
}

export interface BallotManifest {
  filename: string
  numBallots: number | ''
  numBatches: number | ''
  uploadedAt: string
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
    [one: string]: number
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
  randomSeed: number | string
  contests: Contest[] | []
  jurisdictions: Jurisdiction[] | []
  rounds: Round[] | []
}
