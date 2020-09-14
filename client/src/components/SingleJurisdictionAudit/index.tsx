import React, { useState, useEffect, useCallback } from 'react'
import { Redirect, useParams } from 'react-router-dom'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { api } from '../utilities'
import { IAudit } from '../../types'
import ResetButton from '../ResetButton'
import { Wrapper } from '../Atoms/Wrapper'

interface IParams {
  electionId: string
  view: 'setup' | 'progress' | ''
}

const initialData: IAudit = {
  name: '',
  frozenAt: null,
  online: true,
  riskLimit: '',
  randomSeed: '',
  contests: [],
  jurisdictions: [],
  rounds: [],
  isMultiJurisdiction: false,
}

const SingleJurisdictionAudit: React.FC = () => {
  const { electionId } = useParams<IParams>()
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [audit, setAudit] = useState(initialData)

  const getStatus = useCallback(async (): Promise<IAudit> => {
    const response = await api<IAudit>(`/election/${electionId}/audit/status`)
    if (!response) return initialData
    return response
  }, [electionId])

  const updateAudit = useCallback(async () => {
    const auditStatus = await getStatus()
    setIsLoading(true)
    setAudit(auditStatus)
    setIsLoading(false)
  }, [getStatus])

  useEffect(() => {
    updateAudit()
  }, [updateAudit])

  if (audit.isMultiJurisdiction) {
    return <Redirect to="/" />
  }

  const showSelectBallotsToAudit =
    !!audit.contests.length &&
    audit.rounds[0].contests.every(c => !!c.sampleSizeOptions)
  const showCalculateRiskMeasurement =
    !!audit.rounds.length && audit.rounds[0].contests.every(c => !!c.sampleSize)

  return (
    <Wrapper className="single-page">
      <ResetButton
        electionId={electionId}
        disabled={!audit.contests.length || isLoading}
        updateAudit={updateAudit}
      />
      <EstimateSampleSize
        audit={audit}
        isLoading={isLoading && !showSelectBallotsToAudit}
        setIsLoading={setIsLoading}
        updateAudit={updateAudit}
        getStatus={getStatus}
        electionId={electionId}
      />
      {showSelectBallotsToAudit && (
        <SelectBallotsToAudit
          audit={audit}
          isLoading={isLoading && !showCalculateRiskMeasurement}
          setIsLoading={setIsLoading}
          updateAudit={updateAudit}
          getStatus={getStatus}
          electionId={electionId}
        />
      )}
      {showCalculateRiskMeasurement && (
        <CalculateRiskMeasurement
          audit={audit}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
          updateAudit={updateAudit}
          getStatus={getStatus}
          electionId={electionId}
        />
      )}
    </Wrapper>
  )
}

export default SingleJurisdictionAudit
