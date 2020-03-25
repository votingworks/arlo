import { useEffect, useCallback, useState } from 'react'
import { api, checkAndToast } from '../../utilities'
import { IAuditSettings, IErrorResponse } from '../../../types'

const defaultValues: IAuditSettings = {
  state: null,
  electionName: null,
  online: null,
  randomSeed: null,
  riskLimit: null,
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
  electionId: string
): [IAuditSettings, (arg0: TNewSettings) => Promise<boolean>] => {
  const [settings, setSettings] = useState(defaultValues)

  const getSettings = useCallback(async (): Promise<IAuditSettings> => {
    const settingsOrError: IAuditSettings | IErrorResponse = await api(
      `/election/${electionId}/settings`
    )
    if (checkAndToast(settingsOrError)) {
      return defaultValues
    }
    return settingsOrError
  }, [electionId])

  const updateSettings = async (
    newSettings: TNewSettings
  ): Promise<boolean> => {
    const oldSettings = await getSettings()
    const mergedSettings = {
      ...oldSettings,
      ...newSettings,
    }
    const response: IErrorResponse = await api(
      `/election/${electionId}/settings`,
      {
        method: 'PUT',
        body: JSON.stringify(mergedSettings),
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
    if (checkAndToast(response)) {
      return false
    }
    setSettings(mergedSettings)
    return true
  }

  useEffect(() => {
    ;(async () => {
      const newSettings = await getSettings()
      setSettings(newSettings)
    })()
  }, [getSettings])
  return [settings, updateSettings]
}

export default useAuditSettings
