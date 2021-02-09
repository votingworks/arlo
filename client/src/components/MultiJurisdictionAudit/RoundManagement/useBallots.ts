import { useEffect, useState } from 'react'
import { api } from '../../utilities'
import { IAuditBoard } from '../useAuditBoards'
import { BallotStatus, IBallotInterpretation } from '../../../types'

export interface IBallot {
  id: string
  status: BallotStatus
  interpretations: IBallotInterpretation[]
  position: number
  batch: {
    id: string
    name: string
    tabulator: string | null
    container: string | null
  }
  auditBoard: Pick<IAuditBoard, 'id' | 'name'> | null
  imprintedId?: string
  contestsOnBallot?: string[]
}

// TODO add pagination to this endpoint and yield a continuous stream of ballots
export const getBallots = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
) => {
  const response = await api<{ ballots: IBallot[] }>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/ballots`
  )
  return response && response.ballots
}

const getBallotCount = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
) => {
  const response = await api<{ count: number }>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/ballots?count=true`
  )
  return response && response.count
}

const useBallotCount = (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): number | null => {
  const [numBallots, setNumBallots] = useState<number | null>(null)

  useEffect(() => {
    ;(async () => {
      setNumBallots(await getBallotCount(electionId, jurisdictionId, roundId))
    })()
  }, [electionId, jurisdictionId, roundId])

  return numBallots
}

export default useBallotCount
