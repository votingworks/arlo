import React from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { ButtonGroup, Button, H2, H3 } from '@blueprintjs/core'
import { Wrapper } from '../Atoms/Wrapper'
import { apiDownload, assert } from '../utilities'
import CreateAuditBoards from './CreateAuditBoards'
import RoundProgress from './RoundProgress'
import {
  downloadPlaceholders,
  downloadLabels,
  downloadAuditBoardCredentials,
} from './generateSheets'
import { IAuditBoard } from '../useAuditBoards'
import QRs from './QRs'
import RoundDataEntry from './RoundDataEntry'
import useAuditSettingsJurisdictionAdmin from './useAuditSettingsJurisdictionAdmin'
import { useAuthDataContext } from '../UserContext'
import { IRound } from '../AuditAdmin/useRoundsAuditAdmin'
import { IAuditSettings } from '../useAuditSettings'
import AsyncButton from '../Atoms/AsyncButton'
import useSampleCount from './useBallots'
import FullHandTallyDataEntry from './FullHandTallyDataEntry'
import BatchRoundSteps from './BatchRoundSteps/BatchRoundSteps'

const PaddedWrapper = styled(Wrapper)`
  flex-direction: column;
  padding: 30px 0;
`

const SpacedDiv = styled.div`
  margin-bottom: 30px;
`

const StrongP = styled.p`
  font-weight: 500;
`

export interface IRoundManagementProps {
  round: IRound
  auditBoards: IAuditBoard[]
  createAuditBoards: (auditBoards: { name: string }[]) => Promise<boolean>
}

const RoundManagement: React.FC<IRoundManagementProps> = ({
  round,
  auditBoards,
  createAuditBoards,
}) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const auth = useAuthDataContext()
  const auditSettings = useAuditSettingsJurisdictionAdmin(
    electionId,
    jurisdictionId
  )
  const auditType = auditSettings && auditSettings.auditType
  const sampleCount = useSampleCount(
    electionId,
    jurisdictionId,
    round.id,
    auditType
  )

  if (!auth?.user || !auditSettings || !sampleCount) return null // Still loading

  assert(auth.user.type === 'jurisdiction_admin')
  const jurisdiction = auth.user.jurisdictions.find(
    j => j.id === jurisdictionId
  )!
  const { roundNum } = round

  if (round.isAuditComplete) {
    return (
      <PaddedWrapper>
        <H2>Congratulations! Your Risk-Limiting Audit is now complete.</H2>
      </PaddedWrapper>
    )
  }

  if (sampleCount.ballots === 0 && !round.isFullHandTally) {
    return (
      <PaddedWrapper>
        <StrongP>
          Your jurisdiction has not been assigned any ballots to audit in this
          round.
        </StrongP>
      </PaddedWrapper>
    )
  }

  if (auditType === 'BATCH_COMPARISON') {
    return (
      <PaddedWrapper>
        <BatchRoundSteps jurisdiction={jurisdiction} round={round} />
      </PaddedWrapper>
    )
  }

  const samplesToAudit = (() => {
    if (round.isFullHandTally)
      return (
        <StrongP>
          Please audit all of the ballots in your jurisdiction (
          {jurisdiction.numBallots} ballots)
        </StrongP>
      )
    return (
      <StrongP>
        Ballots to audit: {sampleCount.ballots.toLocaleString()}
      </StrongP>
    )
  })()

  if (
    auditBoards.length === 0 &&
    auditSettings.auditType !== 'BATCH_COMPARISON'
  ) {
    return (
      <PaddedWrapper>
        <H3>Round {roundNum} Audit Board Setup</H3>
        {samplesToAudit}
        <CreateAuditBoards createAuditBoards={createAuditBoards} />
      </PaddedWrapper>
    )
  }

  return (
    <PaddedWrapper>
      <H3>Round {roundNum} Data Entry</H3>
      {round.isFullHandTally ? (
        samplesToAudit
      ) : (
        <SpacedDiv>
          {samplesToAudit}
          <JAFileDownloadButtons
            electionId={electionId}
            jurisdictionId={jurisdictionId}
            jurisdictionName={jurisdiction.name}
            round={round}
            auditSettings={auditSettings}
            auditBoards={auditBoards}
          />
        </SpacedDiv>
      )}
      <SpacedDiv>
        {auditSettings.online ? (
          <RoundProgress auditBoards={auditBoards} />
        ) : round.isFullHandTally ? (
          <FullHandTallyDataEntry round={round} />
        ) : (
          <RoundDataEntry round={round} />
        )}
      </SpacedDiv>
    </PaddedWrapper>
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
