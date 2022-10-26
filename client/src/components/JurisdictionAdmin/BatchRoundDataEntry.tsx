import classnames from 'classnames'
import React, {
  BaseSyntheticEvent,
  ChangeEvent,
  useEffect,
  useState,
} from 'react'
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
  ButtonGroup,
  Classes,
  Colors,
  FormGroup,
  H4,
  HTMLTable,
  InputGroup,
  Menu,
  MenuItem,
  Popover,
  Tab,
  Tabs,
} from '@blueprintjs/core'

import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import { ButtonRow, Row } from '../Atoms/Layout'
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

const RenameSheetPanel = styled('div')`
  min-height: 70px; // Match the height of the additional sheet actions menu
  padding: 8px;

  .${Classes.FORM_GROUP} {
    margin-bottom: 0;
  }

  .${Classes.INPUT_GROUP} {
    margin-right: 4px;
  }
`

const BatchResultTallySheetTable = styled(HTMLTable).attrs({
  bordered: true,
  striped: true,
})`
  &.${Classes.HTML_TABLE} {
    border: 1px solid ${Colors.LIGHT_GRAY1};
    margin-bottom: 16px;
    table-layout: fixed;
    width: 100%;
  }

  &.${Classes.HTML_TABLE} tbody tr {
    height: 56px;
  }

  &.${Classes.HTML_TABLE} td {
    vertical-align: middle;
  }
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
  const [
    areAdditionalSheetActionsOpen,
    setAreAdditionalSheetActionsOpen,
  ] = useState(false)
  const [isRenamingSheet, setIsRenamingSheet] = useState(false)
  const [draftSheetName, setDraftSheetName] = useState('')
  const [
    autoSelectLastTabOnceNumSheetsIs,
    setAutoSelectLastTabOnceNumSheetsIs,
  ] = useState<number>()

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
  // BEWARE! You have to access properties on the formState to subscribe to it:
  // https://github.com/react-hook-form/react-hook-form/issues/9002
  const { isDirty, isSubmitting } = formState
  const sheetFieldArrayMethods = useFieldArray<IBatchResultTallySheet>({
    control,
    name: 'resultTallySheets',
  })
  const sheetFields = sheetFieldArrayMethods.fields

  const currentSheetIndex = sheetFields.findIndex(s => s.id === selectedTabId)

  const selectVoteTotalsTab = () => {
    setSelectedTabId(VOTE_TOTALS_TAB_ID)
  }

  const selectTabWithSheetIndex = (sheetIndex: number) => {
    setSelectedTabId(sheetFields[sheetIndex].id || '')
  }

  const resetFormState = () => {
    reset({ resultTallySheets: initialResultTallySheets })
    selectVoteTotalsTab()
    setIsEditing(false)
  }

  // Reset state whenever a new batch is selected. Use an effect instead of the tabs onChange
  // handler since actions other than tab clicks can result in tab changes, e.g. searching
  useEffect(() => {
    resetFormState()
  }, [selectedBatchId])

  // Auto-select first batch on initial load
  useEffect(() => {
    if (!selectedBatchId && filteredBatches.length > 0) {
      setSelectedBatchId(filteredBatches[0].id)
    }
  }, [filteredBatches, selectedBatchId, setSelectedBatchId])

  // Auto-select first search match
  useEffect(() => {
    if (debouncedSearchQuery && filteredBatches.length > 0 && !isDirty) {
      setSelectedBatchId(filteredBatches[0].id)
    }
  }, [debouncedSearchQuery, filteredBatches, isDirty, setSelectedBatchId])

  // Auto-select new sheets
  useEffect(() => {
    if (
      autoSelectLastTabOnceNumSheetsIs !== undefined &&
      sheetFields.length === autoSelectLastTabOnceNumSheetsIs
    ) {
      selectTabWithSheetIndex(sheetFields.length - 1)
      setAutoSelectLastTabOnceNumSheetsIs(undefined)
    }
  }, [
    autoSelectLastTabOnceNumSheetsIs,
    selectTabWithSheetIndex,
    setAutoSelectLastTabOnceNumSheetsIs,
    sheetFields,
  ])

  if (!batchesQuery.isSuccess || !contestsQuery.isSuccess) {
    return null
  }

  const areResultsFinalized = Boolean(batchesQuery.data.resultsFinalizedAt)
  // Batch comparison audits only support a single contest
  const [contest] = contestsQuery.data

  // ---------- Handlers (START) ----------

  const selectBatch = (batchId: string) => {
    if (isDirty) {
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

  const enableEditing = () => {
    setIsEditing(true)

    // Open the first editable sheet if not already on an editable sheet
    if (sheetFields.length > 1 && selectedTabId === VOTE_TOTALS_TAB_ID) {
      selectTabWithSheetIndex(0)
    }
  }

  const addSheet = () => {
    let newSheetName = defaultResultTallySheetName(sheetFields.length)
    function doesNewSheetNameConflict() {
      return sheetFields.some(
        (_, i) => getValues(`resultTallySheets[${i}].name`) === newSheetName
      )
    }

    let incrementToAvoidConflict = 0
    while (doesNewSheetNameConflict()) {
      incrementToAvoidConflict += 1
      newSheetName = defaultResultTallySheetName(
        sheetFields.length + incrementToAvoidConflict
      )
    }

    sheetFieldArrayMethods.append({
      name: newSheetName,
      results: {},
    })
    // We want to auto-select the new sheet but don't yet have the react-hook-form useFieldArray ID
    // to select it, so we do so via a useEffect hook
    setAutoSelectLastTabOnceNumSheetsIs(sheetFields.length + 1)
  }

  const openAdditionalSheetActions = () => {
    setAreAdditionalSheetActionsOpen(true)
  }

  const closeAdditionalSheetActions = () => {
    setAreAdditionalSheetActionsOpen(false)
  }

  const initiateSheetRename = () => {
    setDraftSheetName(getValues(`resultTallySheets[${currentSheetIndex}].name`))
    setIsRenamingSheet(true)
  }

  const confirmSheetRename = () => {
    setValue(`resultTallySheets[${currentSheetIndex}].name`, draftSheetName, {
      shouldDirty: true,
    })
    setIsRenamingSheet(false)
    setAreAdditionalSheetActionsOpen(false)
    setDraftSheetName('')
  }

  const cancelSheetRename = () => {
    setIsRenamingSheet(false)
    setAreAdditionalSheetActionsOpen(true)
    setDraftSheetName('')
  }

  const removeSheet = () => {
    const numSheetsAfterDeletion = sheetFields.length - 1

    if (numSheetsAfterDeletion === 1 || currentSheetIndex === 0) {
      selectVoteTotalsTab()
    } else {
      // Open the sheet before the to-be-deleted sheet
      selectTabWithSheetIndex(Math.max(currentSheetIndex - 1, 0))
    }

    // If we drop back down to 1 sheet, rename that sheet "Sheet 1" under the hood
    if (numSheetsAfterDeletion === 1) {
      const remainingIndex = currentSheetIndex === 1 ? 0 : 1
      setValue(`resultTallySheets[${remainingIndex}].name`, 'Sheet 1')
    }

    sheetFieldArrayMethods.remove(currentSheetIndex)
    setAreAdditionalSheetActionsOpen(false)
  }

  const onValidSubmit: SubmitHandler<IBatchRoundDataEntryFormState> = async ({
    resultTallySheets,
  }) => {
    if (!selectedBatch) {
      return
    }
    try {
      await recordBatchResults.mutateAsync({
        batchId: selectedBatch.id,
        resultTallySheets,
      })
    } catch {
      // Errors are automatically toasted by the queryClient
      setIsEditing(true)
      return
    }
    selectVoteTotalsTab()
    // Reset the form's isDirty value back to false
    reset({ resultTallySheets })
    setIsEditing(false)
  }

  const onInvalidSubmit: SubmitErrorHandler<IBatchRoundDataEntryFormState> = errors => {
    // Open the first sheet with a validation error
    if (sheetFields.length > 1) {
      const sheetWithErrorIndex = (errors.resultTallySheets || []).findIndex(
        Boolean
      )
      if (sheetWithErrorIndex !== -1) {
        selectTabWithSheetIndex(sheetWithErrorIndex)
      }
    }
  }

  const saveResults = (e: BaseSyntheticEvent) => {
    handleSubmit(onValidSubmit, onInvalidSubmit)(e)
  }

  const discardChanges = () => {
    resetFormState()
  }

  // ---------- Handlers (END) ----------

  const currentSheetName = watch(`resultTallySheets[${currentSheetIndex}].name`)

  const draftSheetNameError = (() => {
    if (!isRenamingSheet) {
      return ''
    }
    if (!draftSheetName) {
      return 'Required'
    }
    const sheetNames = sheetFields.map((_, i) =>
      i === currentSheetIndex
        ? draftSheetName
        : watch(`resultTallySheets[${i}].name`)
    )
    if (new Set(sheetNames).size < sheetNames.length) {
      return 'Must be unique'
    }
    return ''
  })()

  const sheetActions = (
    <ButtonGroup>
      <Button
        disabled={isSubmitting || isRenamingSheet}
        icon="add"
        minimal
        onClick={addSheet}
      >
        {sheetFields.length > 1 ? 'Add Sheet' : 'Use Multiple Tally Sheets'}
      </Button>
      {sheetFields.length > 1 && selectedTabId !== VOTE_TOTALS_TAB_ID && (
        <Popover
          content={
            isRenamingSheet ? (
              <RenameSheetPanel>
                <FormGroup
                  helperText={draftSheetNameError}
                  intent={draftSheetNameError ? 'danger' : undefined}
                >
                  <Row>
                    <InputGroup
                      aria-label="New Sheet Name"
                      disabled={isSubmitting}
                      intent={draftSheetNameError ? 'danger' : undefined}
                      onChange={(e: ChangeEvent<HTMLInputElement>) =>
                        setDraftSheetName(e.target.value)
                      }
                      placeholder="New sheet name"
                      value={draftSheetName}
                    />
                    <Button
                      aria-label="Rename Sheet"
                      disabled={Boolean(draftSheetNameError)}
                      icon="tick"
                      minimal
                      onClick={confirmSheetRename}
                    />
                    <Button
                      aria-label="Cancel"
                      icon="delete"
                      minimal
                      onClick={cancelSheetRename}
                    />
                  </Row>
                </FormGroup>
              </RenameSheetPanel>
            ) : (
              <Menu>
                <MenuItem
                  icon="edit"
                  onClick={initiateSheetRename}
                  text={`Rename ${currentSheetName}`}
                />
                <MenuItem
                  icon="remove"
                  onClick={removeSheet}
                  text={`Remove ${currentSheetName}`}
                />
              </Menu>
            )
          }
          isOpen={areAdditionalSheetActionsOpen || isRenamingSheet}
          onClose={closeAdditionalSheetActions}
          position="bottom"
        >
          <Button
            aria-label="Additional Actions"
            disabled={isSubmitting}
            icon="caret-down"
            minimal
            onClick={openAdditionalSheetActions}
          />
        </Popover>
      )}
    </ButtonGroup>
  )

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
        <Detail>
          <H4>{selectedBatch.name}</H4>

          <Tabs
            id={selectedBatch.name}
            onChange={(newTabId: string) => {
              setSelectedTabId(newTabId)
            }}
            // Defaults to false but noting explicitly for clarity. Rendering all tabs at all times
            // is important for react-hook-form's state management
            renderActiveTabPanelOnly={false}
            selectedTabId={selectedTabId}
          >
            <Tab
              disabled={isRenamingSheet}
              id={VOTE_TOTALS_TAB_ID}
              panel={
                <BatchResultTallySheet
                  contest={contest}
                  formMethods={formMethods}
                  index={0}
                  isEditing={isEditing}
                  isTotalsSheet={sheetFields.length > 1}
                  key={
                    sheetFields.length === 1
                      ? sheetFields[0].id || ''
                      : VOTE_TOTALS_TAB_ID
                  }
                  savedResults={
                    selectedBatch.resultTallySheets[0]?.results || {}
                  }
                  sheetFields={sheetFields}
                />
              }
            >
              Vote Totals
            </Tab>
            {sheetFields.length > 1 &&
              sheetFields.map((sheetField, i) => (
                <Tab
                  disabled={isRenamingSheet}
                  id={sheetField.id}
                  key={sheetField.id}
                  panel={
                    <BatchResultTallySheet
                      contest={contest}
                      formMethods={formMethods}
                      index={i}
                      isEditing={isEditing}
                      key={sheetField.id || ''}
                      savedResults={
                        selectedBatch.resultTallySheets[i]?.results || {}
                      }
                      sheetFields={sheetFields}
                    />
                  }
                >
                  {watch(`resultTallySheets[${i}].name`)}
                </Tab>
              ))}
            <Tabs.Expander />
            {isEditing && sheetActions}
          </Tabs>

          <ButtonRow justifyContent="end">
            {isEditing ? (
              <>
                <Button
                  disabled={isSubmitting || isRenamingSheet}
                  icon="delete"
                  intent="danger"
                  minimal
                  onClick={discardChanges}
                >
                  Discard Changes
                </Button>
                <Button
                  disabled={isRenamingSheet}
                  icon="tick"
                  intent="primary"
                  loading={isSubmitting}
                  onClick={saveResults}
                >
                  Save Tallies
                </Button>
              </>
            ) : (
              <Button
                disabled={areResultsFinalized}
                icon="edit"
                onClick={enableEditing}
              >
                Edit Tallies
              </Button>
            )}
          </ButtonRow>
        </Detail>
      )}
      <Confirm {...confirmProps} />
    </ListAndDetail>
  )
}

interface IBatchResultTallySheetProps {
  contest: IContest
  formMethods: UseFormMethods<IBatchRoundDataEntryFormState>
  index: number
  isEditing: boolean
  isTotalsSheet?: boolean
  // Require a key to ensure that inputs within this component re-render in response to
  // useFieldArray updates
  key: string // eslint-disable-line react/no-unused-prop-types
  savedResults: { [choiceId: string]: number }
  sheetFields: Partial<ArrayField<IBatchResultTallySheet, 'id'>>[]
}

const BatchResultTallySheet: React.FC<IBatchResultTallySheetProps> = ({
  contest,
  formMethods,
  index,
  isEditing,
  isTotalsSheet,
  savedResults,
  sheetFields,
}) => {
  const { errors, formState, register, watch } = formMethods
  // BEWARE! You have to access properties on the formState to subscribe to it:
  // https://github.com/react-hook-form/react-hook-form/issues/9002
  const { isSubmitting } = formState

  return (
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
                    sheetFields.map(
                      (_, i) =>
                        watch(
                          `resultTallySheets[${i}].results[${choice.id}]`
                        ) || 0
                    )
                  )}
                </span>
              ) : isEditing ? (
                <>
                  <input
                    aria-label={`${choice.name} Votes`}
                    className={classnames(
                      Classes.INPUT,
                      errors.resultTallySheets?.[index]?.results?.[choice.id] &&
                        Classes.INTENT_DANGER
                    )}
                    defaultValue={`${sheetFields[index]?.results?.[choice.id] ||
                      0}`}
                    name={`resultTallySheets[${index}].results[${choice.id}]`}
                    readOnly={isSubmitting}
                    ref={register({
                      min: 0,
                      required: true,
                      valueAsNumber: true,
                    })}
                    type="number"
                  />
                  {/* We include a hidden input for name so that it's registered in the
                    react-hook-form state */}
                  <input
                    defaultValue={sheetFields[index].name}
                    name={`resultTallySheets[${index}].name`}
                    ref={register()}
                    style={{ display: 'none' }}
                  />
                </>
              ) : (
                <span>{savedResults[choice.id] || 0}</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </BatchResultTallySheetTable>
  )
}

export default BatchRoundDataEntry
