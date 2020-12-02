import { useEffect, useState } from 'react'
import { api } from '../../utilities'
import { IAuditBoard } from '../useAuditBoards'
import { hashBy } from '../../../utils/array'
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

const getBallots = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): Promise<IBallot[] | null> => {
  const response = await api<{ ballots: IBallot[] }>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/ballots`
  )
  return response && response.ballots
}

const useBallots = (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoards: IAuditBoard[] | null
): IBallot[] | null => {
  const [ballots, setBallots] = useState<IBallot[] | null>(null)

  const auditBoardsHash = hashBy(auditBoards, ab => ab.id)
  useEffect(() => {
    ;(async () => {
      setBallots(await getBallots(electionId, jurisdictionId, roundId))
    })()
  }, [
    electionId,
    jurisdictionId,
    roundId,
    // We need to reload the ballots after we create the audit boards in order
    // to populate ballot.auditBoard
    auditBoardsHash,
  ])

  return ballots
}

export default useBallots
