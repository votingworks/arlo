import React, { useState, useEffect, useCallback } from 'react'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { api } from '../utilities'
import { Audit } from '../../types'

const AuditForms = () => {
  const [isLoading, setIsLoading] = useState(false)

  const [audit, setAudit] = useState()

  async function getStatus(): Promise<Audit> {
    const audit: any = await api('/audit/status', {})
    return audit
  }

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

      <SelectBallotsToAudit
        audit={audit}
        isLoading={isLoading}
        setIsLoading={setIsLoading}
        updateAudit={updateAudit}
        getStatus={getStatus}
      />

      <CalculateRiskMeasurement
        audit={audit}
        isLoading={isLoading}
        setIsLoading={setIsLoading}
        updateAudit={updateAudit}
      />
    </React.Fragment>
  )
}

export default AuditForms
