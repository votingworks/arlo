import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { api } from '../../utilities'

export type IJurisdictions = {
  id: string
  name: string
}[]

const useParticipantsApi = (electionId: string) => {
  const [jurisdictions, setJurisdictions] = useState<IJurisdictions>([])
  useEffect(() => {
    ;(async () => {
      try {
        const response: { jurisdictions: IJurisdictions } = await api(
          `/election/${electionId}/jurisdiction`
        )
        setJurisdictions(response.jurisdictions)
      } catch (err) {
        toast.error(err.message)
      }
    })()
  }, [electionId])
  return jurisdictions
}

export default useParticipantsApi
