import React, { useState, useEffect } from 'react'
import { useParams, Redirect } from 'react-router-dom'
import uuidv4 from 'uuidv4'
import { Spinner, H3, Intent } from '@blueprintjs/core'
import useRoundsAuditAdmin, {
  isAuditStarted,
  isDrawSampleComplete,
  drawSampleError,
} from './useRoundsAuditAdmin'
import { useJurisdictions } from '../useJurisdictions'
import useContests from '../useContests'
import useAuditSettings from '../useAuditSettings'
import { ElementType } from '../../types'
import useSetupMenuItems from './useSetupMenuItems/useSetupMenuItems'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import { AuditAdminStatusBox } from '../Atoms/StatusBox'
import Sidebar from '../Atoms/Sidebar'
import { RefreshTag } from '../Atoms/RefreshTag'
import Setup, { setupStages } from './Setup/Setup'
import Progress from './Progress/Progress'

interface IParams {
  electionId: string
  view: 'setup' | 'progress' | ''
}

const AuditAdminView: React.FC = () => {
  const { electionId, view } = useParams<IParams>()
  const [refreshId, setRefreshId] = useState(uuidv4())

  const [rounds, startNextRound, undoRoundStart] = useRoundsAuditAdmin(
    electionId,
    refreshId
  )
  const jurisdictionsQuery = useJurisdictions(electionId) // TODO incorporate refresh
  const [contests] = useContests(electionId, undefined, refreshId)
  const [auditSettings] = useAuditSettings(electionId, refreshId)

  const isBallotComparison =
    auditSettings !== null && auditSettings.auditType === 'BALLOT_COMPARISON'
  const isHybrid =
    auditSettings !== null && auditSettings.auditType === 'HYBRID'
  const [stage, setStage] = useState<ElementType<typeof setupStages>>(
    'participants'
  )
  const [menuItems, refresh] = useSetupMenuItems(
    stage,
    setStage,
    electionId,
    !!isBallotComparison,
    !!isHybrid,
    setRefreshId
  )

  useEffect(refresh, [
    refresh,
    isBallotComparison,
    isHybrid,
    rounds !== null && isAuditStarted(rounds),
  ])

  if (!jurisdictionsQuery.isSuccess || !contests || !rounds || !auditSettings)
    return null // Still loading
  const jurisdictions = jurisdictionsQuery.data

  // TODO support multiple contests in batch comparison audits
  const isBatch = auditSettings.auditType === 'BATCH_COMPARISON'
  const filteredMenuItems = menuItems.filter(({ id }) => {
    switch (id as ElementType<typeof setupStages>) {
      case 'opportunistic-contests':
        return !isBatch
      default:
        return true
    }
  })

  if (rounds.length > 0 && !isDrawSampleComplete(rounds)) {
    return (
      <Wrapper>
        <Inner>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              marginTop: '100px',
            }}
          >
            <div style={{ marginBottom: '20px' }}>
              <Spinner size={Spinner.SIZE_LARGE} intent={Intent.PRIMARY} />
            </div>
            <H3>Drawing a random sample of ballots...</H3>
            <p>For large elections, this can take a couple of minutes.</p>
          </div>
        </Inner>
      </Wrapper>
    )
  }

  switch (view) {
    case 'setup':
      return (
        <Wrapper>
          <AuditAdminStatusBox
            rounds={rounds}
            startNextRound={startNextRound}
            undoRoundStart={undoRoundStart}
            jurisdictions={jurisdictions}
            contests={contests}
            auditSettings={auditSettings}
          >
            <RefreshTag refresh={refresh} />
          </AuditAdminStatusBox>
          <Inner>
            <Sidebar title="Audit Setup" menuItems={filteredMenuItems} />
            <Setup
              stage={stage}
              refresh={refresh}
              menuItems={menuItems}
              auditType={auditSettings.auditType}
              startNextRound={startNextRound}
            />
          </Inner>
        </Wrapper>
      )
    case 'progress':
      return (
        <Wrapper>
          <AuditAdminStatusBox
            rounds={rounds}
            startNextRound={startNextRound}
            undoRoundStart={undoRoundStart}
            jurisdictions={jurisdictions}
            contests={contests}
            auditSettings={auditSettings}
          >
            <RefreshTag refresh={refresh} />
          </AuditAdminStatusBox>
          {!drawSampleError(rounds) && (
            <Inner>
              <Progress
                jurisdictions={jurisdictions}
                auditSettings={auditSettings}
                round={rounds[rounds.length - 1]}
              />
            </Inner>
          )}
        </Wrapper>
      )
    default:
      return (
        <Redirect
          to={
            rounds.length > 0
              ? `/election/${electionId}/progress`
              : `/election/${electionId}/setup`
          }
        />
      )
  }
}

export default AuditAdminView
