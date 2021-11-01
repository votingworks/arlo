import { useEffect, useState } from 'react'
import { api } from '../../utilities'
import { IAuditBoard } from '../useAuditBoards'
import { BallotStatus, IBallotInterpretation } from '../../../types'
import { IAuditSettings } from '../useAuditSettings'
import { sum } from '../../../utils/number'
import { IBatch } from './useBatchResults'

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

export const getBatches = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
) => {
  const response = await api<{ batches: IBatch[] }>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches`
  )
  return response && response.batches
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

interface ISampleCount {
  ballots: number
  batches?: number
}

const useSampleCount = (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditType: IAuditSettings['auditType'] | null
): ISampleCount | null => {
  const [sampleCount, setSampleCount] = useState<ISampleCount | null>(null)

  useEffect(() => {
    ;(async () => {
      if (auditType === null) return
      if (auditType === 'BATCH_COMPARISON') {
        const batches = await getBatches(electionId, jurisdictionId, roundId)
        setSampleCount(
          batches && {
            batches: batches.length,
            ballots: sum(batches.map(batch => batch.numBallots)),
          }
        )
      } else {
        const ballotCount = await getBallotCount(
          electionId,
          jurisdictionId,
          roundId
        )
        setSampleCount(ballotCount !== null ? { ballots: ballotCount } : null)
      }
    })()
  }, [electionId, jurisdictionId, roundId, auditType])

  return sampleCount
}

export default useSampleCount
