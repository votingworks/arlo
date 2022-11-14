import React, { useEffect, useState } from 'react'
import styled from 'styled-components'
import { Classes } from '@blueprintjs/core'

import BatchDetail from './BatchDetail'
import useContestsJurisdictionAdmin from '../../useContestsJurisdictionAdmin'
import { assert } from '../../../utilities'
import { Confirm, useConfirm } from '../../../Atoms/Confirm'
import {
  IBatch,
  IBatchResultTallySheet,
  useBatches,
  useRecordBatchResults,
} from '../../useBatchResults'
import { IContest } from '../../../../types'
import {
  List,
  ListAndDetail,
  ListItem,
  ListSearchNoResults,
} from '../../../Atoms/ListAndDetail'
import { useDebounce } from '../../../../utils/debounce'

const Container = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;

  .${Classes.CALLOUT} {
    border-radius: 0;
  }
`

interface IProps {
  electionId: string
  jurisdictionId: string
  roundId: string
}

const BatchRoundTallyEntry: React.FC<IProps> = ({
  electionId,
  jurisdictionId,
  roundId,
}) => {
  const batchesQuery = useBatches(electionId, jurisdictionId, roundId)
  const contestsQuery = useContestsJurisdictionAdmin(electionId, jurisdictionId)

  if (!batchesQuery.isSuccess || !contestsQuery.isSuccess) {
    return null
  }

  const { batches, resultsFinalizedAt } = batchesQuery.data
  // Batch comparison audits only support a single contest
  const [contest] = contestsQuery.data

  if (batches.length === 0) {
    return null
  }

  return (
    <BatchRoundTallyEntryContent
      areResultsFinalized={Boolean(resultsFinalizedAt)}
      batches={batches}
      contest={contest}
      electionId={electionId}
      jurisdictionId={jurisdictionId}
      roundId={roundId}
    />
  )
}

interface IBatchRoundTallyEntryContentProps {
  areResultsFinalized: boolean
  batches: IBatch[]
  contest: IContest
  electionId: string
  jurisdictionId: string
  roundId: string
}

const BatchRoundTallyEntryContent: React.FC<IBatchRoundTallyEntryContentProps> = ({
  areResultsFinalized,
  batches,
  contest,
  electionId,
  jurisdictionId,
  roundId,
}) => {
  const recordBatchResults = useRecordBatchResults(
    electionId,
    jurisdictionId,
    roundId
  )
  const { confirm, confirmProps } = useConfirm()

  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearchQuery] = useDebounce(searchQuery)
  const [selectedBatchId, setSelectedBatchId] = useState<IBatch['id']>(
    batches[0].id
  )
  const [isEditing, setIsEditing] = useState(false)

  const filteredBatches = batches.filter(batch =>
    batch.name.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
  )
  const selectedBatch = batches.find(batch => batch.id === selectedBatchId)
  assert(selectedBatch !== undefined)

  // Auto-select first search match
  useEffect(() => {
    if (debouncedSearchQuery && filteredBatches.length > 0 && !isEditing) {
      setSelectedBatchId(filteredBatches[0].id)
    }
  }, [debouncedSearchQuery, filteredBatches, isEditing, setSelectedBatchId])

  const selectBatch = (batchId: string) => {
    if (isEditing) {
      confirm({
        title: 'Unsaved Changes',
        description:
          'You have unsaved changes. ' +
          'Are you sure you want to leave this batch without saving changes?',
        yesButtonLabel: 'Discard Changes',
        yesButtonIntent: 'danger',
        onYesClick: () => {
          setSelectedBatchId(batchId)
          setIsEditing(false)
        },
        noButtonLabel: 'Cancel',
      })
      return
    }
    setSelectedBatchId(batchId)
  }

  return (
    <Container>
      <ListAndDetail>
        <List
          search={{
            onChange: setSearchQuery,
            placeholder: 'Search batches...',
          }}
        >
          {filteredBatches.length === 0 && (
            <ListSearchNoResults>No batches found</ListSearchNoResults>
          )}
          {filteredBatches.map(batch => (
            <ListItem
              key={batch.id}
              onClick={() => selectBatch(batch.id)}
              rightIcon={
                batch.resultTallySheets.length > 0 ? 'tick' : undefined
              }
              selected={batch.id === selectedBatch.id}
            >
              {batch.name}
            </ListItem>
          ))}
        </List>

        <BatchDetail
          areResultsFinalized={areResultsFinalized}
          batch={selectedBatch}
          contest={contest}
          isEditing={isEditing}
          key={selectedBatch.id}
          saveBatchResults={async (
            resultTallySheets: IBatchResultTallySheet[]
          ) => {
            await recordBatchResults.mutateAsync({
              batchId: selectedBatch.id,
              resultTallySheets,
            })
          }}
          setIsEditing={setIsEditing}
        />

        <Confirm {...confirmProps} />
      </ListAndDetail>
    </Container>
  )
}

export default BatchRoundTallyEntry
