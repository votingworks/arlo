import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api } from '../utilities'
import { IRound } from './useRoundsJurisdictionAdmin'

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
  try {
    const { auditBoards } = await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board`
    )
    return auditBoards
  } catch (err) {
    toast.error(err.message)
    return null
  }
}

const postAuditBoards = async (
  electionId: string,
  jurisdictionId: string,
  roundId: string,
  auditBoards: { name: string }[]
): Promise<boolean> => {
  try {
    await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(auditBoards),
      }
    )
    return true
  } catch (err) {
    toast.error(err.message)
    return false
  }
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

  useEffect(() => {
    ;(async () => {
      if (!rounds) return setAuditBoards(null)
      if (rounds.length === 0) return setAuditBoards([])
      const roundId = rounds[rounds.length - 1].id
      return setAuditBoards(
        await getAuditBoards(electionId, jurisdictionId, roundId)
      )
    })()
  }, [electionId, jurisdictionId, rounds])

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
