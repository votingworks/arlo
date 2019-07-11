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

export interface Jurisdiction {
  id: string
  name: string
  contests: string[]
  auditBoards: AuditBoard[]
}

export interface Audit {
  name: string
  riskLimit: number
  randomSeed: number
  contests: Contest[]
}
