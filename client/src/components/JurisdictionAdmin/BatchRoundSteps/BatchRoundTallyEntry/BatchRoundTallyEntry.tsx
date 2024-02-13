import React, { useEffect, useState } from 'react'

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
  const contests = contestsQuery.data

  if (batches.length === 0) {
    return null
  }

  return (
    <BatchRoundTallyEntryContent
      areResultsFinalized={Boolean(resultsFinalizedAt)}
      batches={batches}
      contests={contests}
      electionId={electionId}
      jurisdictionId={jurisdictionId}
      roundId={roundId}
    />
  )
}

interface IBatchRoundTallyEntryContentProps {
  areResultsFinalized: boolean
  batches: IBatch[]
  contests: IContest[]
  electionId: string
  jurisdictionId: string
  roundId: string
}

const BatchRoundTallyEntryContent: React.FC<IBatchRoundTallyEntryContentProps> = ({
  areResultsFinalized,
  batches,
  contests,
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
            rightIcon={batch.resultTallySheets.length > 0 ? 'tick' : undefined}
            selected={batch.id === selectedBatch.id}
          >
            {batch.name}
          </ListItem>
        ))}
      </List>

      <BatchDetail
        areResultsFinalized={areResultsFinalized}
        batch={selectedBatch}
        contests={contests}
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
  )
}

export default BatchRoundTallyEntry
