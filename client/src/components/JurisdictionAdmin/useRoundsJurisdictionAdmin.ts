import { useState, useEffect } from 'react'
import { api } from '../utilities'
import { IRound } from '../AuditAdmin/useRoundsAuditAdmin'

const useRoundsJurisdictionAdmin = (
  electionId: string,
  jurisdictionId: string
) => {
  const [rounds, setRounds] = useState<IRound[] | null>(null)

  useEffect(() => {
    ;(async () => {
      const response = await api<{ rounds: IRound[] }>(
        `/election/${electionId}/jurisdiction/${jurisdictionId}/round`
      )
      if (!response) return
      setRounds(response.rounds)
    })()
  }, [electionId, jurisdictionId])

  return rounds
}

export default useRoundsJurisdictionAdmin
