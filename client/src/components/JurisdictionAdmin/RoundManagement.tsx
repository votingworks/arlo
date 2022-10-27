import React from 'react'
import styled from 'styled-components'
import { ButtonGroup, Button, H2, H3, Card, Icon } from '@blueprintjs/core'
import { Inner as InnerAtom } from '../Atoms/Wrapper'
import { apiDownload } from '../utilities'
import CreateAuditBoards from './CreateAuditBoards'
import RoundProgress from './RoundProgress'
import {
  downloadPlaceholders,
  downloadLabels,
  downloadAuditBoardCredentials,
} from './generateSheets'
import useAuditBoards, { IAuditBoard } from '../useAuditBoards'
import QRs from './QRs'
import RoundDataEntry from './RoundDataEntry'
import useAuditSettingsJurisdictionAdmin from './useAuditSettingsJurisdictionAdmin'
import { IJurisdiction } from '../UserContext'
import { IRound } from '../AuditAdmin/useRoundsAuditAdmin'
import { IAuditSettings } from '../useAuditSettings'
import AsyncButton from '../Atoms/AsyncButton'
import useSampleCount from './useBallots'
import FullHandTallyDataEntry from './FullHandTallyDataEntry'
import BatchRoundSteps from './BatchRoundSteps/BatchRoundSteps'
import { StatusBar, AuditHeading } from '../Atoms/StatusBar'
import BatchRoundProgress from './BatchRoundProgress'
import { Row, Column } from '../Atoms/Layout'

const Inner = styled(InnerAtom).attrs({ flexDirection: 'column' })``

const Panel = styled(Card).attrs({ elevation: 1 })`
  margin-bottom: 30px;
`

const StrongP = styled.p`
  font-weight: 500;
`

export interface IRoundManagementProps {
  jurisdiction: IJurisdiction
  round: IRound
}

const RoundManagement: React.FC<IRoundManagementProps> = ({
  jurisdiction,
  round,
}) => {
  const { election } = jurisdiction
  const [auditBoards, createAuditBoards] = useAuditBoards(
    election.id,
    jurisdiction.id,
    [round]
  )
  const auditSettings = useAuditSettingsJurisdictionAdmin(
    election.id,
    jurisdiction.id
  )
  const auditType = auditSettings && auditSettings.auditType
  const sampleCount = useSampleCount(
    election.id,
    jurisdiction.id,
    round.id,
    auditType
  )

  if (!auditBoards || !auditSettings || !sampleCount) return null // Still loading

  const { roundNum } = round

  if (round.isAuditComplete) {
    return (
      <Inner>
        <StatusBar>
          <AuditHeading
            auditName={election.auditName}
            jurisdictionName={jurisdiction.name}
          />
        </StatusBar>
        <Card>
          <Column alignItems="center" gap="30px" style={{ padding: '100px 0' }}>
            <Icon icon="tick-circle" intent="primary" iconSize={100} />
            <Column alignItems="center" gap="10px">
              <H2>Audit Complete</H2>
              <AsyncButton
                intent="primary"
                onClick={() =>
                  apiDownload(
                    `/election/${election.id}/jurisdiction/${jurisdiction.id}/report`
                  )
                }
              >
                Download Audit Report
              </AsyncButton>
            </Column>
          </Column>
        </Card>
      </Inner>
    )
  }

  const auditHeading = (
    <AuditHeading
      auditName={election.auditName}
      jurisdictionName={jurisdiction.name}
      auditStage={`Round ${roundNum}`}
    />
  )

  if (sampleCount.ballots === 0 && !round.isFullHandTally) {
    return (
      <Inner>
        <StatusBar>{auditHeading}</StatusBar>
        <Card>
          <Column alignItems="center" gap="30px" style={{ padding: '100px 0' }}>
            <Column alignItems="center" gap="10px">
              <H2>No ballots to audit</H2>
              <p>
                Your jurisdiction has not been assigned any ballots to audit in
                this round.
              </p>
            </Column>
          </Column>
        </Card>
      </Inner>
    )
  }

  if (auditType === 'BATCH_COMPARISON') {
    return (
      <Inner>
        <StatusBar>
          {auditHeading}
          <BatchRoundProgress
            electionId={election.id}
            jurisdictionId={jurisdiction.id}
            roundId={round.id}
          />
        </StatusBar>
        <BatchRoundSteps jurisdiction={jurisdiction} round={round} />
      </Inner>
    )
  }

  const samplesToAudit = (
    <StrongP>Ballots to audit: {sampleCount.ballots.toLocaleString()}</StrongP>
  )

  if (auditBoards.length === 0) {
    return (
      <Inner>
        <StatusBar>{auditHeading}</StatusBar>
        <Card>
          <H3>Set Up Audit Boards</H3>
          {samplesToAudit}
          <CreateAuditBoards createAuditBoards={createAuditBoards} />
        </Card>
      </Inner>
    )
  }

  if (round.isFullHandTally) {
    return (
      <Inner>
        <StatusBar>{auditHeading}</StatusBar>
        <hr style={{ margin: 0, marginBottom: '20px' }} />
        <StrongP>
          Please audit all of the ballots in your jurisdiction (
          {jurisdiction.numBallots} ballots)
        </StrongP>
        <FullHandTallyDataEntry round={round} />
      </Inner>
    )
  }

  return (
    <Inner>
      <StatusBar>{auditHeading}</StatusBar>
      <Row gap="15px">
        <Panel>
          <H3>Prepare Ballots</H3>
          {samplesToAudit}
          <JAFileDownloadButtons
            electionId={election.id}
            jurisdictionId={jurisdiction.id}
            jurisdictionName={jurisdiction.name}
            round={round}
            auditSettings={auditSettings}
            auditBoards={auditBoards}
          />
        </Panel>
        <Panel style={{ flex: 1 }}>
          {auditSettings.online ? (
            <RoundProgress auditBoards={auditBoards} />
          ) : (
            <RoundDataEntry round={round} />
          )}
        </Panel>
      </Row>
    </Inner>
  )
}

export interface IJAFileDownloadButtonsProps {
  electionId: string
  jurisdictionId: string
  jurisdictionName: string
  round: IRound
  auditSettings: IAuditSettings
  auditBoards: IAuditBoard[]
}

export const JAFileDownloadButtons: React.FC<IJAFileDownloadButtonsProps> = ({
  electionId,
  jurisdictionId,
  jurisdictionName,
  round,
  auditSettings,
  auditBoards,
}) => (
  <ButtonGroup vertical alignText="left">
    <Button
      icon="th"
      onClick={() =>
        apiDownload(
          `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${round.id}/ballots/retrieval-list`
        )
      }
    >
      Download Ballot Retrieval List
    </Button>
    <AsyncButton
      icon="document"
      onClick={() =>
        downloadPlaceholders(
          electionId,
          jurisdictionId,
          round,
          jurisdictionName,
          auditSettings.auditName
        )
      }
    >
      Download Placeholder Sheets
    </AsyncButton>
    <AsyncButton
      icon="label"
      onClick={() =>
        downloadLabels(
          electionId,
          jurisdictionId,
          round,
          jurisdictionName,
          auditSettings.auditName
        )
      }
    >
      Download Ballot Labels
    </AsyncButton>
    {auditSettings.online && (
      <>
        <AsyncButton
          icon="key"
          onClick={() =>
            downloadAuditBoardCredentials(
              auditBoards,
              jurisdictionName,
              auditSettings.auditName
            )
          }
        >
          Download Audit Board Credentials
        </AsyncButton>
        <QRs passphrases={auditBoards.map(b => b.passphrase)} />
      </>
    )}
  </ButtonGroup>
)

export default RoundManagement
