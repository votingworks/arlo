import { useEffect, useCallback, useState } from 'react'
import { api } from '../utilities'
import { IAuditSettings } from '../../types'

const defaultValues: IAuditSettings = {
  state: null,
  electionName: null,
  online: null,
  randomSeed: null,
  riskLimit: null,
  auditType: 'BALLOT_POLLING',
}

type TNewSettings =
  | {
      state: IAuditSettings['state']
    }
  | {
      electionName: IAuditSettings['electionName']
      online: IAuditSettings['online']
      randomSeed: IAuditSettings['randomSeed']
      riskLimit: IAuditSettings['riskLimit']
    }

const useAuditSettings = (
  electionId: string,
  refreshId?: string
): [IAuditSettings, (arg0: TNewSettings) => Promise<boolean>] => {
  const [settings, setSettings] = useState(defaultValues)

  const getSettings = useCallback(async (): Promise<IAuditSettings> => {
    const response = await api<IAuditSettings>(
      `/election/${electionId}/settings`
    )
    if (!response) {
      return defaultValues
    }
    return response
  }, [electionId])

  const updateSettings = async (
    newSettings: TNewSettings
  ): Promise<boolean> => {
    const oldSettings = await getSettings()
    const mergedSettings = {
      ...oldSettings,
      ...newSettings,
    }
    const response = await api(`/election/${electionId}/settings`, {
      method: 'PUT',
      body: JSON.stringify(mergedSettings),
      headers: {
        'Content-Type': 'application/json',
      },
    })
    return !!response
  }

  useEffect(() => {
    ;(async () => {
      const newSettings = await getSettings()
      setSettings(newSettings)
    })()
  }, [getSettings, refreshId])
  return [settings, updateSettings]
}

export default useAuditSettings
