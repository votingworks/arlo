import React, { useState, useEffect } from 'react'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { api } from '../utilities'
import { Audit } from '../../types'

const AuditForms = () => {
  const [isLoading, setIsLoading] = useState(false)

  const [audit, setAudit] = useState()

  const getStatus = async (): Promise<Audit> => {
    const audit: any = await api('/audit/status', {})
    return audit
  }

  const updateAudit = async () => {
    const audit = await getStatus()
    setIsLoading(true)
    setAudit(audit)
    setIsLoading(false)
  }

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
