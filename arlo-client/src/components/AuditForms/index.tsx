import React, { useState, useEffect, useCallback } from 'react'
import styled from 'styled-components'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { api } from '../utilities'
import { Audit, Params } from '../../types'
import ResetButton from './ResetButton'

const Wrapper = styled.div`
  flex-grow: 1;
  margin-top: 20px;
  margin-right: auto;
  margin-left: auto;
  width: 100%;
  max-width: 1020px;
  padding-right: 15px;
  padding-left: 15px;
`

const initialData: Audit = {
  name: '',
  riskLimit: '',
  randomSeed: '',
  contests: [],
  jurisdictions: [],
  rounds: [],
}

interface Props {
  match: {
    params: Params
  }
}

const AuditForms: React.FC<Props> = ({
  match: {
    params: { electionId },
  },
}: Props) => {
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const [audit, setAudit] = useState(initialData)

  const getStatus = useCallback(async (): Promise<Audit> => {
    const audit: Audit = await api('/audit/status', { electionId })
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
    <Wrapper>
      <ResetButton
        electionId={electionId}
        disabled={!audit.contests.length}
        updateAudit={updateAudit}
      />

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
    </Wrapper>
  )
}

export default AuditForms
