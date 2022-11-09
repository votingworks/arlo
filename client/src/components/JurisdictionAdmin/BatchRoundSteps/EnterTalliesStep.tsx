import React from 'react'
import { Button, Callout, Classes } from '@blueprintjs/core'
import styled from 'styled-components'
import { IJurisdiction } from '../../UserContext'
import { IRound } from '../../AuditAdmin/useRoundsAuditAdmin'
import BatchRoundTallyEntry from './BatchRoundTallyEntry'
import { useBatches, useFinalizeBatchResults } from '../useBatchResults'
import { useConfirm, Confirm } from '../../Atoms/Confirm'
import { StepPanel, StepActions } from '../../Atoms/Steps'
import LinkButton from '../../Atoms/LinkButton'
import { Column, Row } from '../../Atoms/Layout'

const Panel = styled(StepPanel)`
  padding: 0;

  .${Classes.CALLOUT} {
    border-radius: 0;
  }
  height: auto;
`

interface IEnterTalliesStepProps {
  previousStepUrl: string
  jurisdiction: IJurisdiction
  round: IRound
}

const EnterTalliesStep: React.FC<IEnterTalliesStepProps> = ({
  previousStepUrl,
  jurisdiction,
  round,
}) => {
  const batchesQuery = useBatches(
    jurisdiction.election.id,
    jurisdiction.id,
    round.id
  )
  const finalizeResults = useFinalizeBatchResults(
    jurisdiction.election.id,
    jurisdiction.id,
    round.id
  )
  const { confirm, confirmProps } = useConfirm()

  if (!batchesQuery.isSuccess) return null // Still loading

  const { batches, resultsFinalizedAt } = batchesQuery.data
  const areAllBatchesAudited = batches.every(
    batch => batch.resultTallySheets.length > 0
  )

  const onClickFinalize = () => {
    confirm({
      title: 'Are you sure you want to finalize your tallies?',
      description:
        'Before finalizing your tallies, check the tallies you have entered into Arlo against your tally sheets.',
      yesButtonLabel: 'Confirm',
      onYesClick: async () => {
        await finalizeResults.mutateAsync()
      },
    })
  }

  return (
    <>
      <Panel>
        <Column>
          {areAllBatchesAudited && !resultsFinalizedAt && (
            <Callout intent="primary" icon={null}>
              <Row alignItems="center" justifyContent="space-between">
                <div>
                  <strong>All batches audited</strong>
                  <div>
                    Review your tallies and then finalize them when you&rsquo;re
                    ready.
                  </div>
                </div>
                <Button
                  intent="primary"
                  icon="tick"
                  onClick={onClickFinalize}
                  disabled={resultsFinalizedAt !== null}
                >
                  Finalize Tallies
                </Button>
              </Row>
            </Callout>
          )}
          <BatchRoundTallyEntry
            electionId={jurisdiction.election.id}
            jurisdictionId={jurisdiction.id}
            roundId={round.id}
          />
        </Column>
      </Panel>
      <StepActions
        left={
          <LinkButton to={previousStepUrl} icon="chevron-left">
            Back
          </LinkButton>
        }
      />
      <Confirm {...confirmProps} />
    </>
  )
}

export default EnterTalliesStep
