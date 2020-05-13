import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { api } from '../utilities'

export interface IRound {
  id: string
  roundNum: number
  startedAt: string
  endedAt: string
  isAuditComplete: boolean
}

const useRoundsAuditAdmin = (electionId: string, refreshId?: string) => {
  const [rounds, setRounds] = useState<IRound[] | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const response: { rounds: IRound[] } = await api(
          `/election/${electionId}/round`
        )
        setRounds(response.rounds)
      } catch (err) {
        toast.error(err.message)
      }
    })()
  }, [electionId, refreshId])

  return rounds
}

export default useRoundsAuditAdmin
