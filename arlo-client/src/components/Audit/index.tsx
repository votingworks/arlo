import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  useContext,
} from 'react'
import { useRouteMatch, RouteComponentProps } from 'react-router-dom'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { api, checkAndToast } from '../utilities'
import { IAudit, IErrorResponse, ElementType } from '../../types'
import ResetButton from './ResetButton'
import Wrapper from '../Atoms/Wrapper'
import Sidebar, { ISidebarMenuItem } from '../Atoms/Sidebar'
import { AuthDataContext } from '../UserContext'
import Setup, { setupStages } from './Setup'

const initialData: IAudit = {
  name: '',
  frozenAt: null,
  online: true,
  riskLimit: '',
  randomSeed: '',
  contests: [],
  jurisdictions: [],
  rounds: [],
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
    !!audit.contests.length &&
    audit.rounds[0].contests.every(c => !!c.sampleSizeOptions)
  const showCalculateRiskMeasurement =
    !!audit.rounds.length && audit.rounds[0].contests.every(c => !!c.sampleSize)

  const [stage, setStage] = useState<ElementType<typeof setupStages>>(
    'Participants'
  )

  const menuItems: ISidebarMenuItem[] = useMemo(
    () =>
      setupStages.map((s: ElementType<typeof setupStages>) => {
        const state = (() => {
          switch (s) {
            case 'Participants':
              return 'live'
            case 'Target Contests':
              return 'live'
            case 'Opportunistic Contests':
              return 'live'
            case 'Audit Settings':
              return 'live'
            case 'Review & Launch':
              return 'live'
            /* istanbul ignore next */
            default:
              return 'locked'
          }
        })()
        return {
          title: s,
          active: s === stage,
          activate: (_, force = false) => {
            if (state === 'live') {
              if (!force) {
                // launch confirm dialog
              }
              setStage(s)
            }
          },
          state,
        }
      }),
    [stage, setupStages]
  )

  const activeStage = menuItems.find(m => m.title === stage)
  const nextStage = menuItems[menuItems.indexOf(activeStage!) + 1]
  const prevStage = menuItems[menuItems.indexOf(activeStage!) - 1]

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
          <Setup
            stage={stage}
            audit={audit}
            nextStage={nextStage}
            prevStage={prevStage}
          />
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
