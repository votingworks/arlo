import React from 'react'
import { toast } from 'react-toastify'
import { Button } from '@blueprintjs/core'
import styled from 'styled-components'
import { IJurisdiction } from '../../UserContext'
import { IRound } from '../../AuditAdmin/useRoundsAuditAdmin'
import BatchRoundTallyEntry from './BatchRoundTallyEntry'
import { useBatches, useFinalizeBatchResults } from '../useBatchResults'
import { useConfirm, Confirm } from '../../Atoms/Confirm'
import { StepPanel, StepActions } from '../../Atoms/Steps'
import LinkButton from '../../Atoms/LinkButton'

const Panel = styled(StepPanel)`
  padding: 0;
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

  const onClickFinalize = () => {
    if (batches.some(batch => batch.resultTallySheets.length === 0)) {
      toast.error('Please enter tallies for all batches before finalizing.')
    } else {
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
  }

  return (
    <>
      <Panel>
        <BatchRoundTallyEntry
          electionId={jurisdiction.election.id}
          jurisdictionId={jurisdiction.id}
          roundId={round.id}
        />
      </Panel>
      <StepActions
        left={
          <LinkButton to={previousStepUrl} icon="chevron-left">
            Back
          </LinkButton>
        }
        right={
          <Button
            intent="primary"
            onClick={onClickFinalize}
            disabled={resultsFinalizedAt !== null}
          >
            Finalize Tallies
          </Button>
        }
      />
      <Confirm {...confirmProps} />
    </>
  )
}

export default EnterTalliesStep
