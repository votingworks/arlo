import React, { useState, useEffect, useCallback } from 'react'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { api } from '../utilities'
import { Audit } from '../../types'
import ResetButton from './ResetButton'

const initialData = {
  name: '',
  riskLimit: '',
  randomSeed: '',
  contests: [],
  jurisdictions: [],
  rounds: [],
}

const AuditForms = () => {
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const [audit, setAudit] = useState<Audit>(initialData)

  const getStatus = useCallback(async (): Promise<Audit> => {
    const audit: any = await api('/audit/status', {})
    return audit
  }, [])

  const updateAudit = useCallback(async () => {
    const audit = await getStatus()
    setIsLoading(true)
    setAudit(audit)
    setIsLoading(false)
  }, [getStatus])

  useEffect(() => {
    updateAudit()
  }, [updateAudit])

  return (
    <React.Fragment>
      <ResetButton updateAudit={updateAudit} />

      <EstimateSampleSize
        audit={audit}
        isLoading={isLoading}
        setIsLoading={setIsLoading}
        updateAudit={updateAudit}
      />

      {!!audit.contests.length && (
        <SelectBallotsToAudit
          audit={audit}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
          updateAudit={updateAudit}
          getStatus={getStatus}
        />
      )}

      {!!audit.rounds.length && (
        <CalculateRiskMeasurement
          audit={audit}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
          updateAudit={updateAudit}
        />
      )}
    </React.Fragment>
  )
}

export default AuditForms
