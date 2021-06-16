import { useEffect, useState } from 'react'
import { api } from '../utilities'
import { hashBy } from '../../utils/array'
import { IRound, isAuditStarted } from './useRoundsAuditAdmin'

export interface IAuditBoardMember {
  name: string
  affiliation: string
}

export interface IAuditBoard {
  id: string
  name: string
  signedOffAt: string | null
  passphrase: string
  currentRoundStatus: {
    numSampledBallots: number
    numAuditedBallots: number
  }
}

const getAuditBoards = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string
): Promise<IAuditBoard[] | null> => {
  const response = await api<{ auditBoards: IAuditBoard[] }>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board`
  )
  if (!response) return null
  return response.auditBoards
}

const postAuditBoards = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoards: { name: string }[]
): Promise<boolean> => {
  const response = await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(auditBoards),
    }
  )
  return !!response
}

const useAuditBoards = (
  electionId: string,
  jurisdictionId: string,
  rounds: IRound[] | null
): [
  IAuditBoard[] | null,
  (auditBoards: { name: string }[]) => Promise<boolean>
] => {
  const [auditBoards, setAuditBoards] = useState<IAuditBoard[] | null>(null)

  const roundsHash = hashBy(rounds, r => r.id)
  useEffect(() => {
    ;(async () => {
      if (!rounds) return setAuditBoards(null)
      if (!isAuditStarted(rounds)) return setAuditBoards([])
      const roundId = rounds[rounds.length - 1].id
      return setAuditBoards(
        await getAuditBoards(electionId, jurisdictionId, roundId)
      )
    })()
  }, [electionId, jurisdictionId, roundsHash]) // eslint-disable-line react-hooks/exhaustive-deps

  const createAuditBoards = async (
    boards: { name: string }[]
  ): Promise<boolean> => {
    if (rounds && rounds.length > 0) {
      const roundId = rounds[rounds.length - 1].id
      if (await postAuditBoards(electionId, jurisdictionId, roundId, boards)) {
        setAuditBoards(
          await getAuditBoards(electionId, jurisdictionId, roundId)
        )
        return true
      }
    }
    return false
  }

  return [auditBoards, createAuditBoards]
}

export default useAuditBoards
