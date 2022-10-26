import classnames from 'classnames'
import React, { BaseSyntheticEvent, useEffect, useState } from 'react'
import styled from 'styled-components'
import {
  ArrayField,
  SubmitErrorHandler,
  SubmitHandler,
  useFieldArray,
  useForm,
  UseFormMethods,
} from 'react-hook-form'
import {
  Button,
  Classes,
  Colors,
  H4,
  HTMLTable,
  Tab,
  Tabs,
} from '@blueprintjs/core'
import { ErrorMessage } from '@hookform/error-message'

import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import { Confirm, useConfirm } from '../Atoms/Confirm'
import { Detail, List, ListAndDetail, ListItem } from '../Atoms/ListAndDetail'
import {
  IBatch,
  IBatchResultTallySheet,
  useBatches,
  useRecordBatchResults,
} from './useBatchResults'
import { IContest } from '../../types'
import { sum } from '../../utils/number'
import { useDebounce } from '../../utils/debounce'

const HIDDEN_INPUT_CLASS_NAME = 'hidden-input'

const BatchResultTallySheetTable = styled(HTMLTable).attrs({
  bordered: true,
  striped: true,
})`
  &.${Classes.HTML_TABLE} {
    border: 1px solid ${Colors.LIGHT_GRAY1};
    table-layout: fixed;
    width: 100%;
  }

  &.${Classes.HTML_TABLE} tbody tr {
    height: 56px;
  }

  &.${Classes.HTML_TABLE} td {
    vertical-align: middle;
  }

  .${Classes.INPUT}.${HIDDEN_INPUT_CLASS_NAME} {
    display: none;
  }
`

const Actions = styled('div')`
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-top: 16px;

  .${Classes.INPUT}.${HIDDEN_INPUT_CLASS_NAME} {
    display: none;
  }
`

const SheetActions = styled('div')`
  align-items: center;
  display: flex;
`

const ConfirmSheetRenameButton = styled(Button)`
  margin-left: 8px;
`

const SheetRenameErrorMessage = styled('span').attrs({
  className: Classes.TEXT_SMALL,
})`
  color: ${Colors.RED2};
  margin-left: 8px;
`

const Spacer = styled('div')`
  flex-grow: 1;
`

interface IBatchRoundDataEntryFormState {
  resultTallySheets: IBatchResultTallySheet[]
}

const VOTE_TOTALS_TAB_ID = 'vote-totals'

function defaultResultTallySheetName(index: number) {
  return `Sheet ${index + 1}`
}

function constructEmptyResultTallySheet(index: number): IBatchResultTallySheet {
  return {
    name: defaultResultTallySheetName(index),
    results: {},
  }
}

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
  const [selectedTabId, setSelectedTabId] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [isRenamingSheet, setIsRenamingSheet] = useState(false)
  const [sheetNameBeforeRename, setSheetNameBeforeRename] = useState<{
    index: number
    name: string
  }>()

  const batches = batchesQuery.isSuccess ? batchesQuery.data.batches : []
  const filteredBatches = batches.filter(batch =>
    batch.name.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
  )
  const selectedBatch = batches.find(batch => batch.id === selectedBatchId)

  const initialResultTallySheets = selectedBatch?.resultTallySheets.length
    ? selectedBatch.resultTallySheets
    : [constructEmptyResultTallySheet(0)]
  const formMethods = useForm<IBatchRoundDataEntryFormState>({
    defaultValues: {
      resultTallySheets: initialResultTallySheets,
    },
  })
  const {
    control,
    formState,
    getValues,
    handleSubmit,
    reset,
    setValue,
    watch,
  } = formMethods
  const {
    append: appendSheet,
    fields: sheets,
    remove: removeSheet,
  } = useFieldArray<IBatchResultTallySheet>({
    control,
    name: 'resultTallySheets',
  })

  // Reset state whenever a new batch is selected
  useEffect(() => {
    reset({ resultTallySheets: initialResultTallySheets })
    setSelectedTabId(VOTE_TOTALS_TAB_ID)
    setIsEditing(false)
  }, [selectedBatchId])

  // Auto-select first search match
  useEffect(() => {
    if (
      debouncedSearchQuery &&
      filteredBatches.length > 0 &&
      !formState.isDirty
    ) {
      setSelectedBatchId(filteredBatches[0].id)
    }
  }, [debouncedSearchQuery])

  if (!batchesQuery.isSuccess || !contestsQuery.isSuccess) {
    return null
  }

  const areResultsFinalized = Boolean(batchesQuery.data.resultsFinalizedAt)
  // Batch comparison audits only support a single contest
  const [contest] = contestsQuery.data

  // ---------- Handlers (START) ----------

  const selectBatch = (batchId: string) => {
    if (formState.isDirty) {
      confirm({
        title: 'Unsaved Changes',
        description:
          'You have unsaved changes. ' +
          'Are you sure you want to leave this batch without saving changes?',
        yesButtonLabel: 'Yes, Leave Batch without Saving',
        onYesClick: () => {
          setSelectedBatchId(batchId)
        },
        noButtonLabel: 'Return to Batch',
      })
      return
    }
    setSelectedBatchId(batchId)
  }

  const enableEditing = () => {
    setIsEditing(true)

    // Open the first editable sheet if not already on an editable sheet
    if (sheets.length > 1 && selectedTabId === VOTE_TOTALS_TAB_ID) {
      setSelectedTabId(getValues(`resultTallySheets[0].name`))
    }
  }

  const onValidSubmit: SubmitHandler<IBatchRoundDataEntryFormState> = async ({
    resultTallySheets,
  }) => {
    if (!selectedBatch) {
      return
    }
    try {
      setSelectedTabId(VOTE_TOTALS_TAB_ID)
      await recordBatchResults.mutateAsync({
        batchId: selectedBatch.id,
        resultTallySheets,
      })
      // Reset the form's isDirty value back to false
      reset({ resultTallySheets })
    } catch {
      // Errors are automatically toasted by the queryClient
      setIsEditing(true)
    }
  }

  const onInvalidSubmit: SubmitErrorHandler<IBatchRoundDataEntryFormState> = errors => {
    // Open the first sheet with a validation error
    if (sheets.length > 1) {
      const index = (errors.resultTallySheets || []).findIndex(Boolean)
      if (index !== -1) {
        setSelectedTabId(getValues(`resultTallySheets[${index}].name`))
      }
    }

    setIsEditing(true)
  }

  const initiateSheetRename = (index: number) => {
    setIsRenamingSheet(true)
    setSheetNameBeforeRename({
      index,
      name: getValues(`resultTallySheets[${index}].name`),
    })
  }

  const confirmSheetRename = () => {
    setIsRenamingSheet(false)
    setSheetNameBeforeRename(undefined)
  }

  const cancelSheetRename = () => {
    setIsRenamingSheet(false)
    if (sheetNameBeforeRename) {
      const { index, name } = sheetNameBeforeRename
      setValue(`resultTallySheets[${index}].name`, name)
      setSheetNameBeforeRename(undefined)
    }
  }

  const addSheet = () => {
    let newSheetName = defaultResultTallySheetName(sheets.length)
    function doesNewSheetNameConflict() {
      return sheets.some(
        (_, i) => getValues(`resultTallySheets[${i}].name`) === newSheetName
      )
    }

    let incrementToAvoidConflict = 0
    while (doesNewSheetNameConflict()) {
      incrementToAvoidConflict += 1
      newSheetName = defaultResultTallySheetName(
        sheets.length + incrementToAvoidConflict
      )
    }

    appendSheet({
      name: newSheetName,
      results: {},
    })
    setSelectedTabId(newSheetName)
  }

  const deleteSheet = (index: number) => {
    const numSheetsAfterDeletion = sheets.length - 1

    if (numSheetsAfterDeletion === 1 || index === 0) {
      setSelectedTabId(VOTE_TOTALS_TAB_ID)
    } else {
      // Open the sheet before the to-be-deleted sheet
      setSelectedTabId(
        getValues(`resultTallySheets[${Math.max(index - 1, 0)}].name`)
      )
    }

    // If we drop back down to 1 sheet, rename that sheet "Sheet 1" under the hood
    if (numSheetsAfterDeletion === 1) {
      const remainingIndex = index === 1 ? 0 : 1
      setValue(`resultTallySheets[${remainingIndex}].name`, 'Sheet 1')
    }

    removeSheet(index)
  }

  const saveResults = (e: BaseSyntheticEvent) => {
    cancelSheetRename()
    setIsEditing(false)
    handleSubmit(onValidSubmit, onInvalidSubmit)(e)
  }

  // ---------- Handlers (END) ----------

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

      <Detail>
        {!selectedBatch ? (
          <p>Select a batch to enter audit results.</p>
        ) : (
          <>
            <H4>{selectedBatch.name}</H4>
            <Tabs
              id={selectedBatch.name}
              onChange={(newTabId: string) => {
                cancelSheetRename()
                setSelectedTabId(newTabId)
              }}
              // Defaults to false but noting explicitly for clarity. Rendering all tabs at all
              // times is important for react-hook-form's state management
              renderActiveTabPanelOnly={false}
              selectedTabId={selectedTabId}
            >
              <Tab
                id={VOTE_TOTALS_TAB_ID}
                panel={
                  <BatchResultTallySheet
                    areResultsFinalized={areResultsFinalized}
                    cancelSheetRename={cancelSheetRename}
                    confirmSheetRename={confirmSheetRename}
                    contest={contest}
                    deleteSheet={() => deleteSheet(0)}
                    enableEditing={enableEditing}
                    formMethods={formMethods}
                    index={0}
                    initiateSheetRename={() => initiateSheetRename(0)}
                    isEditing={isEditing}
                    isRenamingSheet={isRenamingSheet}
                    isTotalsSheet={sheets.length > 1}
                    key={
                      sheets.length === 1
                        ? sheets[0].id || ''
                        : VOTE_TOTALS_TAB_ID
                    }
                    savedResults={
                      selectedBatch.resultTallySheets[0]?.results || {}
                    }
                    saveResults={saveResults}
                    sheets={sheets}
                  />
                }
              >
                Vote Totals
              </Tab>
              {sheets.length > 1 &&
                sheets.map((sheet, i) => (
                  <Tab
                    id={sheet.name}
                    key={sheet.id}
                    panel={
                      <BatchResultTallySheet
                        areResultsFinalized={areResultsFinalized}
                        cancelSheetRename={cancelSheetRename}
                        confirmSheetRename={confirmSheetRename}
                        contest={contest}
                        deleteSheet={() => deleteSheet(i)}
                        enableEditing={enableEditing}
                        formMethods={formMethods}
                        index={i}
                        initiateSheetRename={() => initiateSheetRename(i)}
                        isEditing={isEditing}
                        isRenamingSheet={isRenamingSheet}
                        key={sheet.id || ''}
                        savedResults={
                          selectedBatch.resultTallySheets[i]?.results || {}
                        }
                        saveResults={saveResults}
                        sheets={sheets}
                      />
                    }
                  >
                    {sheetNameBeforeRename && sheetNameBeforeRename.index === i
                      ? sheetNameBeforeRename.name
                      : watch(`resultTallySheets[${i}].name`)}
                  </Tab>
                ))}

              <Tabs.Expander />

              {isEditing && (
                <Button
                  disabled={isRenamingSheet}
                  icon="add"
                  minimal
                  onClick={addSheet}
                >
                  {sheets.length > 1
                    ? 'Add sheet'
                    : 'Use multiple tally sheets'}
                </Button>
              )}
            </Tabs>
          </>
        )}
      </Detail>
      <Confirm {...confirmProps} />
    </ListAndDetail>
  )
}

interface IBatchResultTallySheetProps {
  areResultsFinalized: boolean
  cancelSheetRename: () => void
  confirmSheetRename: () => void
  contest: IContest
  deleteSheet: () => void
  enableEditing: () => void
  formMethods: UseFormMethods<IBatchRoundDataEntryFormState>
  index: number
  initiateSheetRename: () => void
  isEditing: boolean
  isRenamingSheet: boolean
  isTotalsSheet?: boolean
  // Require a key to ensure that inputs within this component re-render in response to
  // useFieldArray updates
  key: string // eslint-disable-line react/no-unused-prop-types
  savedResults: { [choiceId: string]: number }
  saveResults: (e: BaseSyntheticEvent) => void
  sheets: Partial<ArrayField<IBatchResultTallySheet, 'id'>>[]
}

const BatchResultTallySheet: React.FC<IBatchResultTallySheetProps> = ({
  areResultsFinalized,
  cancelSheetRename,
  confirmSheetRename,
  contest,
  deleteSheet,
  enableEditing,
  formMethods,
  index,
  initiateSheetRename,
  isEditing,
  isRenamingSheet,
  isTotalsSheet,
  savedResults,
  saveResults,
  sheets,
}) => {
  const { errors, formState, getValues, register, trigger, watch } = formMethods

  return (
    <>
      <BatchResultTallySheetTable>
        <thead>
          <tr>
            <th>Choice</th>
            <th>Votes</th>
          </tr>
        </thead>
        <tbody>
          {contest.choices.map(choice => (
            <tr key={choice.id}>
              <td>{choice.name}</td>
              <td>
                {isTotalsSheet ? (
                  <span>
                    {sum(
                      sheets.map(
                        (_, i) =>
                          watch(
                            `resultTallySheets[${i}].results[${choice.id}]`
                          ) || 0
                      )
                    )}
                  </span>
                ) : (
                  <>
                    <input
                      aria-label={`${choice.name} Votes`}
                      className={classnames(
                        Classes.INPUT,
                        errors.resultTallySheets?.[index]?.results?.[
                          choice.id
                        ] && Classes.INTENT_DANGER,
                        // Visually hide this input instead of completely unmounting it to avoid
                        // interfering with react-hook-form's state management
                        !isEditing &&
                          !formState.isSubmitting &&
                          HIDDEN_INPUT_CLASS_NAME
                      )}
                      defaultValue={`${sheets[index]?.results?.[choice.id] ||
                        0}`}
                      disabled={formState.isSubmitting}
                      name={`resultTallySheets[${index}].results[${choice.id}]`}
                      ref={register({
                        min: 0,
                        required: true,
                        valueAsNumber: true,
                      })}
                      type="number"
                    />
                    {!isEditing && !formState.isSubmitting && (
                      <span>{savedResults[choice.id] || 0}</span>
                    )}
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </BatchResultTallySheetTable>

      <Actions>
        {!isTotalsSheet && (
          <SheetActions>
            {isEditing && sheets.length > 1 && !isRenamingSheet && (
              <>
                <Button icon="edit" minimal onClick={initiateSheetRename}>
                  Rename sheet
                </Button>
                <Button
                  icon="delete"
                  intent="danger"
                  minimal
                  onClick={deleteSheet}
                >
                  Delete sheet
                </Button>
              </>
            )}
            <input
              className={classnames(
                Classes.INPUT,
                Classes.SMALL,
                errors.resultTallySheets?.[index]?.name &&
                  Classes.INTENT_DANGER,
                // Visually hide this input instead of completely unmounting it to avoid
                // interfering with react-hook-form's state management
                !isRenamingSheet && HIDDEN_INPUT_CLASS_NAME
              )}
              defaultValue={sheets[index].name}
              name={`resultTallySheets[${index}].name`}
              onChange={() => trigger(`resultTallySheets[${index}].name`)}
              ref={register({
                required: true,
                validate: () => {
                  const sheetNames = sheets.map((_, i) =>
                    getValues(`resultTallySheets[${i}].name`)
                  )
                  if (new Set(sheetNames).size < sheetNames.length) {
                    return 'Must be unique'
                  }
                  return true
                },
              })}
            />
            {isRenamingSheet && (
              <>
                <ConfirmSheetRenameButton
                  disabled={Boolean(errors.resultTallySheets?.[index]?.name)}
                  icon="tick"
                  minimal
                  onClick={confirmSheetRename}
                >
                  Done
                </ConfirmSheetRenameButton>
                <Button icon="delete" minimal onClick={cancelSheetRename}>
                  Cancel
                </Button>
                <ErrorMessage
                  errors={errors}
                  name={`resultTallySheets[${index}].name`}
                  render={({ message }) => (
                    <SheetRenameErrorMessage>{message}</SheetRenameErrorMessage>
                  )}
                />
              </>
            )}
          </SheetActions>
        )}

        <Spacer />

        {isEditing || formState.isSubmitting ? (
          <Button
            disabled={isRenamingSheet}
            icon="tick"
            intent="primary"
            loading={formState.isSubmitting}
            onClick={saveResults}
          >
            Save Results
          </Button>
        ) : (
          <Button
            disabled={areResultsFinalized}
            icon="edit"
            onClick={enableEditing}
          >
            Edit Results
          </Button>
        )}
      </Actions>
    </>
  )
}

export default BatchRoundDataEntry
