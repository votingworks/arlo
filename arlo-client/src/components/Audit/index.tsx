import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  useContext,
} from 'react'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { api, checkAndToast } from '../utilities'
import {
  IAudit,
  ICreateAuditParams,
  IErrorResponse,
  ElementType,
} from '../../types'
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

interface IProps {
  match: {
    params: ICreateAuditParams
  }
}

const Audit: React.FC<IProps> = ({
  match: {
    params: { electionId },
  },
}: IProps) => {
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

  const menuItems = useMemo(
    () =>
      setupStages.map(
        (s: ElementType<typeof setupStages>): ISidebarMenuItem => ({
          title: s,
          active: s === stage,
          action: () => setStage(s),
        })
      ),
    [stage]
  )

  return (
    <Wrapper className={!isAuthenticated ? 'single-page' : ''}>
      <ResetButton
        electionId={electionId}
        disabled={!audit.contests.length || isLoading}
        updateAudit={updateAudit}
      />

      {isAuthenticated ? (
        <>
          {meta!.type === 'audit_admin' && (
            <Sidebar title="Audit Setup" menuItems={menuItems} />
          )}
          <Setup stage={stage} audit={audit} setStage={setStage} />
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
