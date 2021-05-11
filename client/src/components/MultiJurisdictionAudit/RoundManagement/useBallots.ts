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

// TODO add pagination to this endpoint and yield a continuous stream of ballots
export const getBallots = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
) => {
  const total = await getBallotCount(electionId, jurisdictionId, roundId)
  const totalBallots = total || 0
  const threshold = 2000
  const count = Math.ceil(totalBallots / threshold)
  const response = []
  for (let index = 1; index <= count; index += 1) {
    const offset = threshold * index - threshold
    const limit = threshold * index
    // eslint-disable-next-line no-await-in-loop
    const ballotsResponse = await api<{ ballots: IBallot[] }>(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/ballots?offset=${offset}&limit=${limit}`
    )
    response.push(...ballotsResponse!.ballots)
  }

  return response
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
