import React, { ReactElement } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Callout, H3, H4 } from '@blueprintjs/core'
import { toast } from 'react-toastify'
import { apiDownload } from '../utilities'
import { Inner } from './Wrapper'
import { IJurisdiction, JurisdictionRoundStatus } from '../useJurisdictions'
import { FileProcessingStatus, IFileInfo } from '../useCSV'
import { IAuditSettings } from '../useAuditSettings'
import {
  IRound,
  drawSampleError,
  ISampleSizes,
} from '../AuditAdmin/useRoundsAuditAdmin'
import { IContest } from '../../types'
import useSampleSizes from '../AuditAdmin/Setup/Review/useSampleSizes'
import { mapValues } from '../../utils/objects'
import AsyncButton from './AsyncButton'

const SpacedH3 = styled(H3)`
  &.bp3-heading {
    margin-bottom: 20px;
  }
`

const Wrapper = styled(Callout)`
  display: flex;
  padding: 30px 0;
  .text {
    flex-grow: 1;
    p {
      margin-bottom: 0;
    }
  }
`

interface IStatusBoxProps {
  headline: string
  details: string[]
  auditName: string
  action?: ReactElement
  children?: ReactElement
}

const StatusBox: React.FC<IStatusBoxProps> = ({
  headline,
  details,
  auditName,
  action,
  children,
}: IStatusBoxProps) => {
  return (
    <Wrapper icon={null}>
      <Inner>
        <div className="text">
          <SpacedH3>{auditName}</SpacedH3>
          <H4>{headline}</H4>
          {details.map(detail => (
            <p key={detail}>{detail}</p>
          ))}
          {children}
        </div>
        <div>{action}</div>
      </Inner>
    </Wrapper>
  )
}

export const allCvrsUploaded = (jurisdictions: IJurisdiction[]): boolean =>
  jurisdictions.every(
    ({ cvrs }) =>
      cvrs &&
      cvrs.processing &&
      cvrs.processing.status === FileProcessingStatus.PROCESSED
  )

export const isSetupComplete = (
  jurisdictions: IJurisdiction[],
  contests: IContest[],
  auditSettings: IAuditSettings
): boolean => {
  if (jurisdictions.length === 0) return false

  if (!contests.some(c => c.isTargeted)) return false

  if (Object.values(auditSettings).some(v => v === null)) return false

  const participatingJurisdictions = jurisdictions.filter(({ id }) =>
    contests.some(c => c.jurisdictionIds.includes(id))
  )

  // In batch comparison audits, all jurisdictions must upload batch tallies
  if (auditSettings.auditType === 'BATCH_COMPARISON') {
    if (
      !participatingJurisdictions.every(
        ({ batchTallies }) =>
          batchTallies &&
          batchTallies.processing &&
          batchTallies.processing.status === FileProcessingStatus.PROCESSED
      )
    )
      return false
  }

  // In ballot comparison/hybrid audits, all jurisdictions must upload CVRs
  if (['BALLOT_COMPARISON', 'HYBRID'].includes(auditSettings.auditType)) {
    if (!allCvrsUploaded(participatingJurisdictions)) return false
  }

  return true
}

interface IAuditAdminProps {
  rounds: IRound[]
  startNextRound: (sampleSizes: ISampleSizes) => Promise<boolean>
  finishRound: () => Promise<void>
  undoRoundStart: () => Promise<void>
  jurisdictions: IJurisdiction[]
  contests: IContest[]
  auditSettings: IAuditSettings
  children?: ReactElement
}

export const AuditAdminStatusBox: React.FC<IAuditAdminProps> = ({
  rounds,
  startNextRound,
  finishRound,
  undoRoundStart,
  jurisdictions,
  contests,
  auditSettings,
  children,
}: IAuditAdminProps) => {
  const { electionId } = useParams<{ electionId: string }>()

  // Audit setup
  if (rounds.length === 0) {
    const details = [
      isSetupComplete(jurisdictions, contests, auditSettings)
        ? 'Audit setup is complete.'
        : 'Audit setup is not complete.',
    ]
    if (jurisdictions.length > 0) {
      const numUploaded = jurisdictions.filter(
        ({ ballotManifest, batchTallies, cvrs }) => {
          const files: IFileInfo['processing'][] = [ballotManifest.processing]
          if (batchTallies) files.push(batchTallies.processing)
          if (cvrs) files.push(cvrs.processing)
          return files.every(
            f => f && f.status === FileProcessingStatus.PROCESSED
          )
        }
      ).length
      details.push(
        `${numUploaded} of ${jurisdictions.length}` +
          ' jurisdictions have completed file uploads.'
      )
    }
    return (
      <StatusBox
        headline="The audit has not started."
        details={details}
        auditName={auditSettings.auditName}
      >
        {children}
      </StatusBox>
    )
  }

  if (drawSampleError(rounds)) {
    return (
      <StatusBox
        headline="Arlo could not draw the sample"
        details={[
          'Please contact our support team for help resolving this issue.',
          `Error: ${drawSampleError(rounds)}`,
        ]}
        auditName={auditSettings.auditName}
        action={
          rounds.length === 1 ? (
            <AsyncButton onClick={undoRoundStart} intent="primary">
              Undo Audit Launch
            </AsyncButton>
          ) : (
            undefined
          )
        }
      >
        {children}
      </StatusBox>
    )
  }

  const {
    roundNum,
    endedAt,
    isAuditComplete,
    needsFullHandTally,
    isFullHandTally,
  } = rounds[rounds.length - 1]

  // Round in progress
  if (!endedAt) {
    const numCompleted = jurisdictions.filter(
      ({ currentRoundStatus }) =>
        currentRoundStatus &&
        currentRoundStatus.status === JurisdictionRoundStatus.COMPLETE
    ).length

    const canFinishRound = numCompleted === jurisdictions.length

    const canUndoLaunch =
      roundNum === 1 &&
      jurisdictions.every(
        ({ currentRoundStatus }) =>
          currentRoundStatus &&
          currentRoundStatus.status !== JurisdictionRoundStatus.IN_PROGRESS
      )

    return (
      <StatusBox
        headline={`Round ${roundNum} of the audit is in progress`}
        details={[
          `${numCompleted} of ${jurisdictions.length} jurisdictions` +
            ` have completed round ${roundNum}`,
        ]}
        auditName={auditSettings.auditName}
        action={
          canFinishRound ? (
            <AsyncButton onClick={finishRound} intent="primary">
              Finish Round {roundNum}
            </AsyncButton>
          ) : canUndoLaunch ? (
            <AsyncButton onClick={undoRoundStart}>
              Undo Audit Launch
            </AsyncButton>
          ) : (
            undefined
          )
        }
      >
        <>
          {/* Special case: when a sample size has been drawn that requires a full hand tally
     but the audit isn't in full hand tally mode (e.g. in a second round) */}
          {needsFullHandTally && !isFullHandTally && (
            <Callout intent="warning" style={{ marginTop: '15px' }}>
              <strong>Full hand tally required</strong>
              <p>
                One or more target contests require a full hand tally to
                complete the audit.
              </p>
            </Callout>
          )}
          {children}
        </>
      </StatusBox>
    )
  }

  // Round complete, need another round
  if (!isAuditComplete) {
    return (
      <AuditAdminAnotherRoundStatusBox
        electionId={electionId}
        auditSettings={auditSettings}
        contests={contests}
        roundNum={roundNum}
        startNextRound={startNextRound}
      />
    )
  }

  // Round complete, audit complete
  return (
    <StatusBox
      auditName={auditSettings.auditName}
      headline="Congratulations - the audit is complete!"
      details={[]}
      action={
        <AsyncButton
          intent="primary"
          onClick={() => apiDownload(`/election/${electionId}/report`)}
        >
          Download Audit Report
        </AsyncButton>
      }
    >
      {children}
    </StatusBox>
  )
}

interface IAuditAdminAnotherRoundStatusBoxProps {
  electionId: string
  auditSettings: IAuditSettings
  contests: IContest[]
  roundNum: number
  startNextRound: (sampleSizes: ISampleSizes) => Promise<boolean>
  children?: ReactElement
}

const AuditAdminAnotherRoundStatusBox = ({
  electionId,
  auditSettings,
  contests,
  roundNum,
  startNextRound,
  children,
}: IAuditAdminAnotherRoundStatusBoxProps) => {
  const sampleSizesQuery = useSampleSizes(electionId, roundNum + 1, {
    refetchInterval: sampleSizesResponse =>
      sampleSizesResponse?.task.completedAt === null ? 1000 : false,
  })
  // The server should autoselect one option per contest, so we pick the first
  // item in the options array for each contest
  const sampleSizes =
    sampleSizesQuery.data?.sampleSizes &&
    mapValues(sampleSizesQuery.data.sampleSizes, options => options[0])
  const ballotsOrBatches =
    auditSettings.auditType === 'BATCH_COMPARISON' ? 'batches' : 'ballots'

  return (
    <StatusBox
      auditName={auditSettings.auditName}
      headline={`Round ${roundNum} of the audit is complete - another round is needed`}
      details={(() => {
        if (!sampleSizesQuery.data?.task.completedAt)
          return ['Loading sample sizes...']
        if (sampleSizesQuery.data.task.error !== null)
          return [
            `Error computing sample sizes: ${sampleSizesQuery.data.task.error}`,
          ]
        return [
          `Round ${roundNum + 1} Sample Sizes`,
          ...Object.entries(sampleSizes!).map(([contestId, option]) => {
            const contestName = contests.find(
              contest => contest.id === contestId
            )!.name
            return `• ${contestName}: ${option.size} ${ballotsOrBatches}`
          }),
        ]
      })()}
      action={
        <AsyncButton
          intent="primary"
          onClick={async () => {
            if (!sampleSizes) {
              toast.info('Sample sizes are still loading')
            } else {
              await startNextRound(sampleSizes)
            }
          }}
        >
          Start Round {roundNum + 1}
        </AsyncButton>
      }
    >
      {children}
    </StatusBox>
  )
}
