export interface Candidate {
  id: string
  name: string
  numVotes: number
}

export interface Contest {
  id: string
  name: string
  choices: Candidate[]
  totalBallotsCast: number
}

export interface AuditBoard {
  id: string
  members: any[]
}

export interface BallotManifest {
  filename: string
  numBallots: number
  numBatches: number
}

export interface Jurisdiction {
  id: string
  name: string
  contests: string[]
  auditBoards: AuditBoard[]
  ballotManifest?: BallotManifest
}

// export interface Round {
// look this up
//}

export interface Audit {
  name: string
  riskLimit: number
  randomSeed: number
  contests: Contest[]
  jurisdictions: Jurisdiction[]
  rounds?: any[]
}
