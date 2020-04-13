import React, { useState, useEffect, useCallback, useContext } from 'react'
import { useRouteMatch, RouteComponentProps } from 'react-router-dom'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { api, checkAndToast } from '../utilities'
import { IAudit, IErrorResponse, ElementType } from '../../types'
import ResetButton from './ResetButton'
import Wrapper from '../Atoms/Wrapper'
import Sidebar from '../Atoms/Sidebar'
import { AuthDataContext } from '../UserContext'
import Setup, { setupStages } from './Setup'
import useSetupMenuItems from './useSetupMenuItems'

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

interface IParams {
  electionId: string
  view: 'setup' | 'progress'
}

const Audit: React.FC<{}> = () => {
  const match: RouteComponentProps<IParams>['match'] | null = useRouteMatch(
    '/election/:electionId/:view?'
  )
  /* istanbul ignore next */
  const viewMatch = match ? match.params.view : undefined
  /* istanbul ignore next */
  const electionId = match ? match.params.electionId : ''

  const { isAuthenticated, meta } = useContext(AuthDataContext)

  const [isLoading, setIsLoading] = useState<boolean>(false)

  const [audit, setAudit] = useState(initialData)

  const getStatus = useCallback(async (): Promise<IAudit> => {
    const auditStatusOrError: IAudit | IErrorResponse = await api(
      `/election/${electionId}/audit/status`
    )
    if (checkAndToast(auditStatusOrError)) {
      return initialData
    }
    return auditStatusOrError
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

  const showSelectBallotsToAudit =
    !audit.isMultiJurisdiction &&
    !!audit.contests.length &&
    audit.rounds[0].contests.every(c => !!c.sampleSizeOptions)
  const showCalculateRiskMeasurement =
    !!audit.rounds.length && audit.rounds[0].contests.every(c => !!c.sampleSize)

  const [stage, setStage] = useState<ElementType<typeof setupStages>>(
    'Participants'
  )

  const [menuItems, refresh] = useSetupMenuItems(stage, setStage, electionId)

  useEffect(() => {
    refresh()
  }, [refresh])

  return (
    <Wrapper className={!isAuthenticated ? 'single-page' : ''}>
      <ResetButton
        electionId={electionId}
        disabled={!audit.contests.length || isLoading}
        updateAudit={updateAudit}
      />

      {isAuthenticated &&
      (viewMatch === 'setup' || viewMatch === 'progress') ? (
        <>
          {meta!.type === 'audit_admin' && (
            <Sidebar title="Audit Setup" menuItems={menuItems} />
          )}
          <Setup stage={stage} menuItems={menuItems} />
        </>
      ) : (
        <>
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
        </>
      )}
    </Wrapper>
  )
}

export default Audit
