import React, { useState, useEffect, useCallback } from 'react'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
//import { api } from '../utilities'
import { Audit } from '../../types'
import { statusStates } from './_mocks'

const AuditForms = () => {
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const [audit, setAudit] = useState<Audit>(statusStates[0])

  const getStatus = useCallback(async (): Promise<Audit> => {
    //const audit: any = await api('/audit/status', {})
    return statusStates[4]
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
