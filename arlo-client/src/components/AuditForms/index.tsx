import React, { useState, useEffect, useCallback } from 'react'
import { RouteComponentProps } from 'react-router-dom'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { api } from '../utilities'
import { Audit, Params } from '../../types'
import { statusStates } from './_mocks'

const AuditForms = ({
  match: {
    params: { electionId },
  },
}: RouteComponentProps<Params>) => {
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const [audit, setAudit] = useState<Audit>(statusStates[0])

  const getStatus = useCallback(async (): Promise<Audit> => {
    const audit: any = await api('/audit/status', { electionId })
    return audit
  }, [electionId])

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
        electionId={electionId}
      />

      {!!audit.contests.length && (
        <SelectBallotsToAudit
          audit={audit}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
          updateAudit={updateAudit}
          getStatus={getStatus}
          electionId={electionId}
        />
      )}

      {!!audit.rounds.length && (
        <CalculateRiskMeasurement
          audit={audit}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
          updateAudit={updateAudit}
          electionId={electionId}
        />
      )}
    </React.Fragment>
  )
}

export default AuditForms
