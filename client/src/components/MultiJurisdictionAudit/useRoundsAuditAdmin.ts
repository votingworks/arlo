import { useState, useEffect } from 'react'
import { api } from '../utilities'

export interface IRound {
  id: string
  roundNum: number
  startedAt: string
  endedAt: string | null
  isAuditComplete: boolean
  sampledAllBallots: boolean
}

const useRoundsAuditAdmin = (electionId: string, refreshId?: string) => {
  const [rounds, setRounds] = useState<IRound[] | null>(null)

  useEffect(() => {
    ;(async () => {
      const response = await api<{ rounds: IRound[] }>(
        `/election/${electionId}/round`
      )
      if (!response) return
      setRounds(response.rounds)
    })()
  }, [electionId, refreshId])

  return rounds
}

export default useRoundsAuditAdmin
