import React, { useEffect, useState } from 'react'

import BatchDetails from './BatchDetails'
import useContestsJurisdictionAdmin from '../useContestsJurisdictionAdmin'
import { Confirm, useConfirm } from '../../Atoms/Confirm'
import {
  Detail,
  List,
  ListAndDetail,
  ListItem,
} from '../../Atoms/ListAndDetail'
import {
  IBatch,
  IBatchResultTallySheet,
  useBatches,
  useRecordBatchResults,
} from '../useBatchResults'
import { useDebounce } from '../../../utils/debounce'

interface IProps {
  electionId: string
  jurisdictionId: string
  roundId: string
}

const BatchRoundDataEntry: React.FC<IProps> = ({
  electionId,
  jurisdictionId,
  roundId,
}) => {
  const batchesQuery = useBatches(electionId, jurisdictionId, roundId)
  const contestsQuery = useContestsJurisdictionAdmin(electionId, jurisdictionId)
  const recordBatchResults = useRecordBatchResults(
    electionId,
    jurisdictionId,
    roundId
  )
  const { confirm, confirmProps } = useConfirm()

  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearchQuery] = useDebounce(searchQuery)
  const [selectedBatchId, setSelectedBatchId] = useState<IBatch['id']>()
  const [areChangesUnsaved, setAreChangesUnsaved] = useState(false)

  const batches = batchesQuery.isSuccess ? batchesQuery.data.batches : []
  const filteredBatches = batches.filter(batch =>
    batch.name.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
  )
  const selectedBatch = batches.find(batch => batch.id === selectedBatchId)

  // Auto-select first batch on initial load
  useEffect(() => {
    if (!selectedBatchId && filteredBatches.length > 0) {
      setSelectedBatchId(filteredBatches[0].id)
    }
  }, [filteredBatches, selectedBatchId, setSelectedBatchId])

  // Auto-select first search match
  useEffect(() => {
    if (
      debouncedSearchQuery &&
      filteredBatches.length > 0 &&
      !areChangesUnsaved
    ) {
      setSelectedBatchId(filteredBatches[0].id)
    }
  }, [
    debouncedSearchQuery,
    filteredBatches,
    areChangesUnsaved,
    setSelectedBatchId,
  ])

  if (!batchesQuery.isSuccess || !contestsQuery.isSuccess) {
    return null
  }

  const areResultsFinalized = Boolean(batchesQuery.data.resultsFinalizedAt)
  // Batch comparison audits only support a single contest
  const [contest] = contestsQuery.data

  const selectBatch = (batchId: string) => {
    if (areChangesUnsaved) {
      confirm({
        title: 'Unsaved Changes',
        description:
          'You have unsaved changes. ' +
          'Are you sure you want to leave this batch without saving changes?',
        yesButtonLabel: 'Discard Changes',
        yesButtonIntent: 'danger',
        onYesClick: () => setSelectedBatchId(batchId),
        noButtonLabel: 'Cancel',
      })
      return
    }
    setSelectedBatchId(batchId)
  }

  return (
    <ListAndDetail>
      <List
        search={{
          placeholder: 'Search batches...',
          setQuery: setSearchQuery,
        }}
      >
        {filteredBatches.map(batch => (
          <ListItem
            key={batch.id}
            onClick={() => selectBatch(batch.id)}
            selected={batch.id === selectedBatchId}
          >
            {batch.name}
          </ListItem>
        ))}
      </List>

      {!selectedBatch ? (
        <Detail>
          <p>Select a batch to enter tallies.</p>
        </Detail>
      ) : (
        <BatchDetails
          areResultsFinalized={areResultsFinalized}
          batch={selectedBatch}
          contest={contest}
          key={selectedBatch.id}
          saveBatchResults={async (
            resultTallySheets: IBatchResultTallySheet[]
          ) => {
            await recordBatchResults.mutateAsync({
              batchId: selectedBatch.id,
              resultTallySheets,
            })
          }}
          setAreChangesUnsaved={setAreChangesUnsaved}
        />
      )}
      <Confirm {...confirmProps} />
    </ListAndDetail>
  )
}

export default BatchRoundDataEntry
