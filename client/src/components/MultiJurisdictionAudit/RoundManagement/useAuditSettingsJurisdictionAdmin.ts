import { useEffect, useState } from 'react'
import { api } from '../../utilities'
import { IAuditSettings } from '../../../types'

const defaultValues: IAuditSettings = {
  state: null,
  electionName: null,
  online: null,
  randomSeed: null,
  riskLimit: null,
  auditType: 'BALLOT_POLLING',
}

const getSettings = async (
  electionId: string,
  jurisdictionId: string
): Promise<IAuditSettings | null> => {
  const response = await api<IAuditSettings>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/settings`
  )
  if (!response) return null
  return response
}

const useAuditSettingsJurisdictionAdmin = (
  electionId: string,
  jurisdictionId: string
): IAuditSettings => {
  const [settings, setSettings] = useState<IAuditSettings>(defaultValues)

  useEffect(() => {
    ;(async () => {
      const newSettings = await getSettings(electionId, jurisdictionId)
      setSettings(newSettings || defaultValues)
    })()
  }, [electionId, jurisdictionId])

  return settings
}

export default useAuditSettingsJurisdictionAdmin
