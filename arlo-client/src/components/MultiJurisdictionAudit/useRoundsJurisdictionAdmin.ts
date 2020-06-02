import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { api } from '../utilities'

export interface IRound {
  id: string
  roundNum: number
  startedAt: string
  endedAt: string | null
  isAuditComplete: boolean
}

const useRoundsJurisdictionAdmin = (
  electionId: string,
  jurisdictionId: string
) => {
  const [rounds, setRounds] = useState<IRound[] | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const response: { rounds: IRound[] } = await api(
          `/election/${electionId}/jurisdiction/${jurisdictionId}/round`
        )
        setRounds(response.rounds)
      } catch (err) {
        toast.error(err.message)
      }
    })()
  }, [electionId, jurisdictionId])

  return rounds
}

export default useRoundsJurisdictionAdmin
