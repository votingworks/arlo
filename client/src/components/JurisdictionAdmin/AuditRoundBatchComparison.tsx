import React from 'react'
import { Button, Callout, H5 } from '@blueprintjs/core'
import { IRound } from '../AuditAdmin/useRoundsAuditAdmin'
import {
  StepListItem,
  StepPanel,
  Steps,
  StepList,
  StepActions,
} from '../Atoms/Steps'
import DownloadBatchTallySheetsButton from './DownloadBatchTallySheetsButton'
import { IJurisdiction } from '../UserContext'
import { jurisdictionErrorFile } from '../AuditAdmin/Setup/Participants/_mocks'

interface IProps {
  jurisdiction: IJurisdiction
  round: IRound
  sampleCount: ISampleCount
}

const AuditRoundBatchComparison: React.FC<IProps> = ({
  jurisdiction,
  round,
  sampleCount,
}) => {
  return (
    <Steps>
      <StepList>
        <StepListItem current>Prepare Batches</StepListItem>
        <StepListItem>Set Up Audit Boards</StepListItem>
        <StepListItem>Audit Batches</StepListItem>
      </StepList>
      <StepPanel style={{ alignItems: 'stretch' }}>
        <Callout style={{ padding: '20px' }}>
          <H5>Retrieve Batches from Storage</H5>
          <p>
            For each batch in the retrieval list:
            <ul>
              <li>Find the container in storage</li>
              <li>Perform the required chain of custody verification steps</li>
              <li>
                Take the batch of ballots out of the container and stack them
              </li>
            </ul>
          </p>
          <p>
            <Button
              icon="download"
              large
              intent="primary"
              onClick={
                /* istanbul ignore next */ // tested in generateSheets.test.tsx
                () =>
                  apiDownload(
                    `/election/${jurisdiction.election.id}/jurisdiction/${jurisdiction.id}/round/${round.id}/batches/retrieval-list`
                  )
              }
            >
              Download Batch Retrieval List
            </Button>
          </p>
        </Callout>
        <Callout style={{ padding: '20px' }}>
          <H5>Print Batch Tally Sheets</H5>
          <p>
            There will be one tally sheet for each batch. Use these tally sheets
            when recording the audited votes in each batch.
          </p>
          <p>
            <DownloadBatchTallySheetsButton
              electionId={jurisdiction.election.id}
              jurisdictionId={jurisdiction.id}
              jurisdictionName={jurisdiction.name}
              roundId={round.id}
            />
          </p>
        </Callout>
      </StepPanel>
      <StepActions
        right={
          <Button intent="primary" rightIcon="chevron-right">
            Continue
          </Button>
        }
      />
    </Steps>
  )
}

export default AuditRoundBatchComparison
