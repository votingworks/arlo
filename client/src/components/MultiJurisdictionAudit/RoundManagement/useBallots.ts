import { useEffect, useState } from 'react'
import { api } from '../../utilities'
import { IAuditBoard } from '../useAuditBoards'
import { BallotStatus, IBallotInterpretation } from '../../../types'
import { IAuditSettings } from '../useAuditSettings'
import { getBatches } from './useBatchResults'

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

const useBallotOrBatchCount = (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditType: IAuditSettings['auditType'] | null
): number | null => {
  const [count, setCount] = useState<number | null>(null)

  useEffect(() => {
    ;(async () => {
      if (auditType === null) return
      if (auditType === 'BATCH_COMPARISON') {
        const batches = await getBatches(electionId, jurisdictionId, roundId)
        setCount(batches && batches.length)
      } else {
        setCount(await getBallotCount(electionId, jurisdictionId, roundId))
      }
    })()
  }, [electionId, jurisdictionId, roundId, auditType])

  return count
}

export default useBallotOrBatchCount
