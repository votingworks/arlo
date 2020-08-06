import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api } from '../../utilities'
import { IAuditSettings } from '../../../types'

const defaultValues: IAuditSettings = {
  state: null,
  electionName: null,
  online: null,
  randomSeed: null,
  riskLimit: null,
}

const getSettings = async (
  electionId: string,
  jurisdictionId: string
): Promise<IAuditSettings | null> => {
  try {
    const response: IAuditSettings = await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/settings`
    )
    return response
  } catch (err) {
    toast.error(err.message)
    return null
  }
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
