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
import BallotManifest from './Setup/BallotManifest'

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
    if (
      isAuthenticated &&
      viewMatch === 'setup' &&
      meta!.type === 'audit_admin'
    )
      refresh()
  }, [refresh, isAuthenticated, viewMatch, meta])

  const progressSidebar = (
    <Sidebar
      title="Audit Progress"
      menuItems={[
        {
          title: 'Jurisdictions',
          active: true,
          state: 'live',
        },
      ]}
    />
  )
  const aaSetupSidebar = <Sidebar title="Audit Setup" menuItems={menuItems} />
  const jaSetupSidebar = (
    <Sidebar
      title="Audit Setup"
      menuItems={[
        {
          title: 'Upload Ballot Manifest',
          active: true,
          state: 'live',
        },
      ]}
    />
  )

  if (isAuthenticated)
    return (
      <Wrapper>
        <ResetButton
          electionId={electionId}
          disabled={!audit.contests.length || isLoading}
          updateAudit={updateAudit}
        />
        {viewMatch === 'setup' && meta!.type === 'audit_admin' && (
          <>
            {aaSetupSidebar}
            <Setup stage={stage} refresh={refresh} menuItems={menuItems} />
          </>
        )}
        {viewMatch === 'setup' && meta!.type === 'jurisdiction_admin' && (
          <>
            {jaSetupSidebar}
            <BallotManifest />
          </>
        )}
        {viewMatch === 'progress' && (
          <>
            {progressSidebar}
            <p>Progress view</p>
          </>
        )}
        {viewMatch !== 'setup' && viewMatch !== 'progress' && (
          <p>Round management view</p>
        )}
      </Wrapper>
    )
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

export default Audit
