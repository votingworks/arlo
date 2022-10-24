import React from 'react'
import { H5, UL } from '@blueprintjs/core'
import { IJurisdiction } from '../../UserContext'
import { IRound } from '../../AuditAdmin/useRoundsAuditAdmin'
import { StepPanel, StepPanelColumn, StepActions } from '../../Atoms/Steps'
import DownloadBatchTallySheetsButton from './DownloadBatchTallySheetsButton'
import LinkButton from '../../Atoms/LinkButton'
import DownloadBatchRetrievalListButton from './DownloadBatchRetrievalListButton'

interface IPrepareBatchesStepProps {
  nextStepUrl: string
  jurisdiction: IJurisdiction
  round: IRound
}

const PrepareBatchesStep: React.FC<IPrepareBatchesStepProps> = ({
  nextStepUrl,
  jurisdiction,
  round,
}) => (
  <>
    <StepPanel>
      <StepPanelColumn>
        <H5>Retrieve Batches from Storage</H5>
        <p>
          <DownloadBatchRetrievalListButton
            electionId={jurisdiction.election.id}
            jurisdictionId={jurisdiction.id}
            roundId={round.id}
            intent="primary"
          />
        </p>
        <span>For each batch in the retrieval list:</span>
        <UL>
          <li>Find the container in storage</li>
          <li>Perform the required chain of custody verification steps</li>
          <li>Take the batch of ballots out of the container and stack them</li>
        </UL>
      </StepPanelColumn>
      <StepPanelColumn>
        <H5>Print Batch Tally Sheets</H5>
        <p>
          <DownloadBatchTallySheetsButton
            electionId={jurisdiction.election.id}
            auditName={jurisdiction.election.auditName}
            jurisdictionId={jurisdiction.id}
            jurisdictionName={jurisdiction.name}
            roundId={round.id}
            intent="primary"
          />
        </p>
        <p>
          There will be one tally sheet for each batch. Use these tally sheets
          when recording the audited votes in each batch.
        </p>
      </StepPanelColumn>
    </StepPanel>
    <StepActions
      right={
        <LinkButton to={nextStepUrl} intent="primary" rightIcon="chevron-right">
          Continue
        </LinkButton>
      }
    />
  </>
)

export default PrepareBatchesStep
