import React from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { ButtonGroup, Button, H2, H3 } from '@blueprintjs/core'
import { Wrapper } from '../../Atoms/Wrapper'
import { apiDownload } from '../../utilities'
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
import BatchRoundDataEntry from './BatchRoundDataEntry'
import { useAuthDataContext, IJurisdictionAdmin } from '../../UserContext'
import useBallotCount from './useBallots'
import { IRound } from '../useRoundsAuditAdmin'
import OfflineBatchRoundDataEntry from './OfflineBatchRoundDataEntry'
import { IAuditSettings } from '../useAuditSettings'
import AsyncButton from '../../Atoms/AsyncButton'

const PaddedWrapper = styled(Wrapper)`
  flex-direction: column;
  align-items: flex-start;
  padding: 30px 0;
`
// TODO
// width: 510px;

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

const RoundManagement = ({
  round,
  auditBoards,
  createAuditBoards,
}: IRoundManagementProps) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const auth = useAuthDataContext()
  const numBallots = useBallotCount(electionId, jurisdictionId, round.id)
  const auditSettings = useAuditSettingsJurisdictionAdmin(
    electionId,
    jurisdictionId
  )

  if (!auth || !auth.user || numBallots === null || !auditSettings) return null // Still loading

  const jurisdiction = (auth.user as IJurisdictionAdmin).jurisdictions.find(
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

  const ballotsToAudit = round.sampledAllBallots ? (
    <StrongP>
      Please audit all of the ballots in your jurisdiction (
      {jurisdiction.numBallots} ballots)
    </StrongP>
  ) : (
    <StrongP>
      {numBallots.toLocaleString()} ballots to audit in Round {roundNum}
    </StrongP>
  )

  if (auditBoards.length === 0) {
    return (
      <PaddedWrapper>
        <H3>Round {roundNum} Audit Board Setup</H3>
        {ballotsToAudit}
        <CreateAuditBoards createAuditBoards={createAuditBoards} />
      </PaddedWrapper>
    )
  }

  return (
    <PaddedWrapper>
      <H3>Round {roundNum} Data Entry</H3>
      {round.sampledAllBallots ? (
        ballotsToAudit
      ) : (
        <SpacedDiv>
          {ballotsToAudit}
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
        {auditSettings.auditType === 'BATCH_COMPARISON' ? (
          <BatchRoundDataEntry round={round} />
        ) : auditSettings.online ? (
          <RoundProgress auditBoards={auditBoards} />
        ) : round.sampledAllBallots ? (
          <OfflineBatchRoundDataEntry round={round} />
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

export const JAFileDownloadButtons = ({
  electionId,
  jurisdictionId,
  jurisdictionName,
  round,
  auditSettings,
  auditBoards,
}: IJAFileDownloadButtonsProps) => (
  <ButtonGroup vertical alignText="left">
    <Button
      icon="th"
      onClick={
        /* istanbul ignore next */ // tested in generateSheets.test.tsx
        () =>
          apiDownload(
            `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${
              round.id
            }/${
              auditSettings.auditType === 'BATCH_COMPARISON'
                ? 'batches'
                : 'ballots'
            }/retrieval-list`
          ).catch(err => {
            // eslint-disable-next-line no-console
            console.error(err)
          })
      }
    >
      Download Aggregated{' '}
      {auditSettings.auditType === 'BATCH_COMPARISON' ? 'Batch' : 'Ballot'}{' '}
      Retrieval List
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
