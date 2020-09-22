import { useEffect, useState } from 'react'
import { api } from '../../utilities'
import { IAuditSettings, IAuditSettingsPossNull } from '../../../types'

const getSettings = async (
  electionId: string,
  jurisdictionId: string
): Promise<IAuditSettings | null> => {
  return api(`/election/${electionId}/jurisdiction/${jurisdictionId}/settings`)
}

const useAuditSettingsJurisdictionAdmin = (
  electionId: string,
  jurisdictionId: string
): IAuditSettingsPossNull => {
  const [settings, setSettings] = useState<IAuditSettingsPossNull>(null)

  useEffect(() => {
    ;(async () => {
      const newSettings = await getSettings(electionId, jurisdictionId)
      setSettings(newSettings)
    })()
  }, [electionId, jurisdictionId])

  return settings
}

export default useAuditSettingsJurisdictionAdmin
