import { useEffect, useCallback, useState } from 'react'
import { api } from '../utilities'
import { IAuditSettings } from '../../types'

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
): [IAuditSettings | null, (arg0: TNewSettings) => Promise<boolean>] => {
  const [settings, setSettings] = useState<IAuditSettings | null>(null)

  const getSettings = useCallback(async (): Promise<IAuditSettings | null> => {
    return api<IAuditSettings>(`/election/${electionId}/settings`)
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
