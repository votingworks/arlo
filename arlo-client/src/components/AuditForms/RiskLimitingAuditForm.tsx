import React, { useState, useEffect, useCallback } from 'react'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { api } from '../utilities'
import { Audit } from '../../types'

const blankAudit: Audit = {
  name: '',
  riskLimit: '',
  randomSeed: '',

  contests: [
    {
      id: '',
      name: '',

      choices: [
        {
          id: '',
          name: '',
          numVotes: '',
        },
        {
          id: '',
          name: '',
          numVotes: '',
        },
      ],

      totalBallotsCast: '',
    },
  ],

  jurisdictions: [
    {
      id: '',
      name: '',
      contests: [],
      auditBoards: [
        //{
        //  id: '',
        // members: []
        //}
      ],
      ballotManifest: {
        filename: '',
        numBallots: '',
        numBatches: '',
        uploadedAt: '',
      },
    },
  ],

  rounds: [
    {
      startedAt: '',
      endedAt: '',
      contests: [
        {
          id: '',
          endMeasurements: {
            //pvalue: 0.085,
            isComplete: false,
          },
          results: {
            //"candidate-1": 55,
            //"candidate-2": 35
          },
          sampleSize: '',
        },
      ],
      jurisdictions: {
        //"adams-county": {
        //  numBallots: 15,
        //}
      },
    },
  ],
}

const AuditForms = () => {
  const [isLoading, setIsLoading] = useState(false)

  const [audit, setAudit] = useState(blankAudit)

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
