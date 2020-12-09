import { useEffect, useState } from 'react'
import { api } from '../../utilities'
import { IAuditSettings } from '../useAuditSettings'

const getSettings = async (
  electionId: string,
  jurisdictionId: string
): Promise<IAuditSettings | null> => {
  return api(`/election/${electionId}/jurisdiction/${jurisdictionId}/settings`)
}

const useAuditSettingsJurisdictionAdmin = (
  electionId: string,
  jurisdictionId: string
): IAuditSettings | null => {
  const [settings, setSettings] = useState<IAuditSettings | null>(null)

  useEffect(() => {
    ;(async () => {
      const newSettings = await getSettings(electionId, jurisdictionId)
      setSettings(newSettings)
    })()
  }, [electionId, jurisdictionId])

  return settings
}

export default useAuditSettingsJurisdictionAdmin
