import classnames from 'classnames'
import React, { useState } from 'react'
import styled from 'styled-components'
import uuidv4 from 'uuidv4'
import {
  Button,
  ButtonGroup,
  Classes,
  Colors,
  H4,
  HTMLTable,
  Menu,
  MenuItem,
  Popover,
  Spinner,
  Tab,
  Tabs,
} from '@blueprintjs/core'
import { SubmitHandler, useForm } from 'react-hook-form'

import { ButtonRow } from '../../../Atoms/Layout'
import { Detail } from '../../../Atoms/ListAndDetail'
import { IBatch, IBatchResultTallySheet } from '../../useBatchResults'
import { IContest } from '../../../../types'
import { sum } from '../../../../utils/number'

const BatchName = styled(H4)`
  &.${Classes.HEADING} {
    // Match the height of the batch search bar such that the batch name and search bar are
    // vertically middle aligned
    line-height: 30px;
  }
`

interface ITabsWrapperProps {
  isAnimationEnabled?: boolean
}

// More on why this is needed can be found below, where it's used
const TabsWrapper = styled.div<ITabsWrapperProps>`
  .${Classes.TAB_INDICATOR_WRAPPER} {
    transition-duration: ${({ isAnimationEnabled = true }) =>
      !isAnimationEnabled ? '0ms' : undefined};
  }
`

const BatchResultTallySheetTable = styled(HTMLTable).attrs({
  bordered: true,
  striped: true,
})`
  &.${Classes.HTML_TABLE} {
    border: 1px solid ${Colors.LIGHT_GRAY1};
    margin-bottom: 16px;
    margin-top: 16px;
    table-layout: fixed;
    width: 100%;
  }

  &.${Classes.HTML_TABLE} tbody tr {
    height: 56px;
  }

  &.${Classes.HTML_TABLE} td {
    vertical-align: middle;
  }

  // Hide arrows/spinners from number inputs
  // Reference: https://www.w3schools.com/howto/howto_css_hide_arrow_number.asp
  // Chrome, Edge, Safari
  &.${Classes.HTML_TABLE} input::-webkit-inner-spin-button,
  &.${Classes.HTML_TABLE} input::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }
  // Firefox
  &.${Classes.HTML_TABLE} input[type='number'] {
    -moz-appearance: textfield;
  }
`

const BatchResultTallySheetButtonRow = styled(ButtonRow).attrs({
  alignItems: 'center',
})`
  min-height: 30px;
`

const RowSpacer = styled.div`
  flex-grow: 1;
`

const VOTE_TOTALS_TAB_ID = 'vote-totals'

// Sheet names are unique but not static. If we were to use sheet names as the IDs and keys
// assigned to tabs and panels, renaming a sheet would cause components to unexpectedly unmount,
// remount, and reset state. So we add and use our own stable client-side IDs.
// TODO: Add and use DB-persisted IDs instead
interface IBatchResultTallySheetStateEntry extends IBatchResultTallySheet {
  id: string
}

interface ITab {
  id: string
  name: string
}

function sheetToSheetStateEntry(
  sheet: IBatchResultTallySheet
): IBatchResultTallySheetStateEntry {
  return { ...sheet, id: uuidv4() }
}

function sheetStateEntryToSheet(
  sheetStateEntry: IBatchResultTallySheetStateEntry
): IBatchResultTallySheet {
  return {
    name: sheetStateEntry.name,
    results: sheetStateEntry.results,
  }
}

function defaultSheetName(sheetNumber: number) {
  return `Sheet ${sheetNumber}`
}

function constructEmptySheet(sheetName: string): IBatchResultTallySheet {
  return {
    name: sheetName,
    results: {},
  }
}

function tabsFromSheets(sheets: IBatchResultTallySheetStateEntry[]): ITab[] {
  if (sheets.length === 1) {
    return [{ id: sheets[0].id, name: 'Vote Totals' }]
  }
  return [
    { id: VOTE_TOTALS_TAB_ID, name: 'Vote Totals' },
    ...sheets.map(sheet => ({ id: sheet.id, name: sheet.name })),
  ]
}

interface IBatchDetailProps {
  areResultsFinalized: boolean
  batch: IBatch
  contest: IContest
  isEditing: boolean
  saveBatchResults: (
    resultTallySheets: IBatchResultTallySheet[]
  ) => Promise<void>
  setIsEditing: (isEditing: boolean) => void

  // Require a key to ensure that the state within this component resets when a different batch is
  // selected
  key: string // eslint-disable-line react/no-unused-prop-types
}

const BatchDetail: React.FC<IBatchDetailProps> = ({
  areResultsFinalized,
  batch,
  contest,
  isEditing,
  saveBatchResults,
  setIsEditing,
}) => {
  const [sheets, setSheets] = useState<IBatchResultTallySheetStateEntry[]>(
    (batch.resultTallySheets.length === 0
      ? [constructEmptySheet(defaultSheetName(1))]
      : batch.resultTallySheets
    ).map(sheetToSheetStateEntry)
  )
  const [newAndUnsavedSheetId, setNewAndUnsavedSheetId] = useState<
    string | null
  >(null)
  const tabs = tabsFromSheets(sheets)
  const [selectedTabId, setSelectedTabId] = useState(tabs[0].id)
  const [isTabsAnimationEnabled, setIsTabsAnimationEnabled] = useState(true)
  const [areAdditionalActionsOpen, setAreAdditionalActionsOpen] = useState(
    false
  )
  const [isRemovingSheet, setIsRemovingSheet] = useState(false)

  const currentSheetIndex = sheets.findIndex(
    sheet => sheet.id === selectedTabId
  )

  // ---------- Handlers (start) ----------

  const addSheet = async () => {
    const isSheetNameAlreadyTaken = (sheetName: string) =>
      sheets.some(sheet => sheet.name === sheetName)

    let incrementToAvoidNamingConflict = 0
    let newSheetName = defaultSheetName(sheets.length + 1)
    while (isSheetNameAlreadyTaken(newSheetName)) {
      incrementToAvoidNamingConflict += 1
      newSheetName = defaultSheetName(
        sheets.length + 1 + incrementToAvoidNamingConflict
      )
    }
    const newSheet = sheetToSheetStateEntry(constructEmptySheet(newSheetName))
    const updatedSheets = [...sheets, newSheet]

    // Update client-side state but don't save the new sheet to the backend until tallies are
    // entered
    setSheets(updatedSheets)
    setNewAndUnsavedSheetId(newSheet.id)
    setSelectedTabId(
      // If we've just switched from a single sheet to multiple sheets, select the first sheet
      // instead of the second
      updatedSheets.length === 2 ? updatedSheets[0].id : newSheet.id
    )
    setIsEditing(true)
  }

  const updateCurrentSheet = async (updatedSheet: IBatchResultTallySheet) => {
    const updatedSheets = sheets.map((sheet, i) =>
      i === currentSheetIndex ? { ...updatedSheet, id: sheet.id } : sheet
    )

    const isSwitchingFromSingleSheetToMultipleSheets =
      sheets.length === 2 &&
      currentSheetIndex === 0 &&
      newAndUnsavedSheetId === sheets[1].id
    if (isSwitchingFromSingleSheetToMultipleSheets) {
      // When switching from a single sheet to multiple sheets, we open the first sheet in edit
      // mode. We need to auto-populate the second sheet with 0s behind the scenes to avoid errors
      // upon saving the first sheet
      const secondSheetResults: { [choiceId: string]: number } = {}
      contest.choices.forEach(choice => {
        secondSheetResults[choice.id] = 0
      })
      updatedSheets[1] = { ...sheets[1], results: secondSheetResults }
    }

    await saveBatchResults(updatedSheets.map(sheetStateEntryToSheet))
    setSheets(updatedSheets)
    setNewAndUnsavedSheetId(null)
  }

  const removeCurrentSheet = async () => {
    setIsRemovingSheet(true)

    let updatedSheets = sheets.filter((_, i) => i !== currentSheetIndex)
    if (updatedSheets.length === 1) {
      // If we're dropping back to 1 sheet, reset the name of that sheet back to the default
      updatedSheets = [{ ...updatedSheets[0], name: defaultSheetName(1) }]
    }

    await saveBatchResults(updatedSheets.map(sheetStateEntryToSheet))
    setSheets(updatedSheets)
    setSelectedTabId(
      // Auto-select the next sheet (or last sheet if none)
      updatedSheets[Math.min(currentSheetIndex, updatedSheets.length - 1)].id
    )
    setIsRemovingSheet(false)
    setAreAdditionalActionsOpen(false)
  }

  const discardNewAndUnsavedSheets = () => {
    const updatedSheets = sheets.filter(
      sheet => newAndUnsavedSheetId !== sheet.id
    )

    setSheets(updatedSheets)
    setSelectedTabId(
      // Auto-select the next sheet (or last sheet if none)
      updatedSheets[Math.min(currentSheetIndex, updatedSheets.length - 1)].id
    )
  }

  const enableEditing = () => {
    setIsEditing(true)
  }

  const disableEditing = () => {
    setIsTabsAnimationEnabled(false)
    setTimeout(() => {
      setIsTabsAnimationEnabled(true)
    }, 250)
    setIsEditing(false)
  }

  const openAdditionalActions = () => {
    setAreAdditionalActionsOpen(true)
  }

  const closeAdditionalActions = () => {
    setAreAdditionalActionsOpen(false)
  }

  // ---------- Handlers (end) ----------

  return (
    <Detail>
      <BatchName>{batch.name}</BatchName>

      {/* When editing one of multiple sheets, BatchResultTallySheet renders its own tab bar with
        a sheet name form input replacing the selected tab, so we hide this main tab bar */}
      {(!isEditing || sheets.length === 1) && (
        // When editing is finished and we render this tab bar again, we don't want to re-animate
        // selection of the already selected tab. The Tabs `animate` prop doesn't respond well to
        // being toggled back and forth, so we disable and re-enable animation through our own
        // wrapper
        <TabsWrapper isAnimationEnabled={isTabsAnimationEnabled}>
          <Tabs
            id={batch.name}
            onChange={(newTabId: string) => {
              setSelectedTabId(newTabId)
            }}
            selectedTabId={selectedTabId}
          >
            {tabs.map(tab => (
              <Tab disabled={isRemovingSheet} id={tab.id} key={tab.id}>
                {tab.name}
              </Tab>
            ))}
            <Tabs.Expander />
            {sheets.length > 1 && (
              <Button
                disabled={areResultsFinalized || isRemovingSheet}
                icon="add"
                minimal
                onClick={addSheet}
              >
                Add Sheet
              </Button>
            )}
          </Tabs>
        </TabsWrapper>
      )}

      <BatchResultTallySheet
        addSheet={addSheet}
        areAdditionalActionsOpen={areAdditionalActionsOpen}
        areResultsFinalized={areResultsFinalized}
        batch={batch}
        closeAdditionalActions={closeAdditionalActions}
        contest={contest}
        disableEditing={disableEditing}
        discardNewAndUnsavedSheets={discardNewAndUnsavedSheets}
        enableEditing={enableEditing}
        isEditing={isEditing}
        isRemovingSheet={isRemovingSheet}
        key={selectedTabId}
        newAndUnsavedSheetId={newAndUnsavedSheetId}
        openAdditionalActions={openAdditionalActions}
        removeSheet={removeCurrentSheet}
        selectedTabId={selectedTabId}
        sheets={sheets}
        updateSheet={updateCurrentSheet}
      />
    </Detail>
  )
}

interface IBatchResultTallySheetProps {
  addSheet: () => Promise<void>
  areAdditionalActionsOpen: boolean
  areResultsFinalized: boolean
  batch: IBatch
  closeAdditionalActions: () => void
  contest: IContest
  disableEditing: () => void
  discardNewAndUnsavedSheets: () => void
  enableEditing: () => void
  isEditing: boolean
  isRemovingSheet: boolean
  newAndUnsavedSheetId: string | null
  openAdditionalActions: () => void
  removeSheet: () => Promise<void>
  selectedTabId: string
  sheets: IBatchResultTallySheetStateEntry[]
  updateSheet: (updatedSheet: IBatchResultTallySheet) => Promise<void>

  // Require a key to ensure that the state within this component resets when a different sheet is
  // selected
  key: string // eslint-disable-line react/no-unused-prop-types
}

const BatchResultTallySheet: React.FC<IBatchResultTallySheetProps> = ({
  addSheet,
  areAdditionalActionsOpen,
  areResultsFinalized,
  batch,
  closeAdditionalActions,
  contest,
  disableEditing,
  discardNewAndUnsavedSheets,
  enableEditing,
  isEditing,
  isRemovingSheet,
  newAndUnsavedSheetId,
  openAdditionalActions,
  removeSheet,
  selectedTabId,
  sheets,
  updateSheet,
}) => {
  const tabs = tabsFromSheets(sheets)
  const isTotalsSheet = selectedTabId === VOTE_TOTALS_TAB_ID
  const selectedSheet = isTotalsSheet
    ? null
    : sheets.find(sheet => sheet.id === selectedTabId)
  const isSelectedSheetNewAndUnsaved = selectedSheet
    ? selectedSheet.id === newAndUnsavedSheetId
    : false

  const formMethods = useForm<IBatchResultTallySheet>({
    defaultValues: selectedSheet
      ? sheetStateEntryToSheet(selectedSheet)
      : undefined,
    // Don't unregister inputs when they unmount (the default is switched from true to false in v7)
    shouldUnregister: false,
  })
  const {
    errors,
    formState,
    handleSubmit,
    register,
    reset: resetForm,
  } = formMethods
  // Important gotcha! You have to access properties on the formState to subscribe to it:
  // https://github.com/react-hook-form/react-hook-form/issues/9002
  const { isSubmitting } = formState

  const discardChanges = async () => {
    resetForm()
    disableEditing()
    discardNewAndUnsavedSheets()
  }

  const onValidSubmit: SubmitHandler<IBatchResultTallySheet> = async sheet => {
    try {
      await updateSheet(sheet)
    } catch {
      // Errors are automatically toasted by the queryClient
      return
    }
    disableEditing()
  }

  return (
    <>
      {isEditing && sheets.length > 1 && (
        // A special tab bar with a sheet name form input replacing the selected tab, rendered here
        // instead of in the parent component so that we can create a separate react-hook-form form
        // per sheet (sharing the form across sheets requires diligent resetting)
        <Tabs id={batch.name} selectedTabId={selectedTabId}>
          {tabs.map(tab =>
            selectedTabId === tab.id ? (
              <input
                aria-label="Sheet Name"
                // Should be fine accessibility-wise, having read and considered the accessibility
                // warning under
                // https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input#autofocus, since
                // we're auto-focusing after a relevant user action and the input is clearly
                // labeled
                // eslint-disable-next-line jsx-a11y/no-autofocus
                autoFocus={isSelectedSheetNewAndUnsaved}
                className={classnames(
                  Classes.INPUT,
                  errors.name && Classes.INTENT_DANGER
                )}
                key={tab.id}
                name="name"
                readOnly={isSubmitting}
                ref={register({
                  required: true,
                })}
              />
            ) : (
              <Tab disabled id={tab.id} key={tab.id}>
                {tab.name}
              </Tab>
            )
          )}
          <Tabs.Expander />
          <Button disabled icon="add" minimal>
            Add Sheet
          </Button>
        </Tabs>
      )}

      <div
        // Since we have to render two tab bars, we aren't able to use the tab bar's built-in
        // `panel` prop and have to manually apply attributes for tab panel accessibility
        aria-labelledby={`${Classes.TAB_PANEL}_${batch.name}_${selectedTabId}`}
        role="tabpanel"
      >
        <BatchResultTallySheetTable>
          <thead>
            <tr>
              <th>Choice</th>
              <th>Votes</th>
            </tr>
          </thead>
          <tbody>
            {contest.choices.map((choice, i) => (
              <tr key={choice.id}>
                <td>{choice.name}</td>
                <td>
                  {isTotalsSheet ? (
                    <span>
                      {sum(
                        sheets.map(sheet => sheet.results[choice.id] ?? 0)
                      ).toLocaleString()}
                    </span>
                  ) : isEditing ? (
                    <input
                      aria-label={`${choice.name} Votes`}
                      // Should be fine accessibility-wise, having read and considered the
                      // accessibility warning under
                      // https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input#autofocus,
                      // since we're auto-focusing after a relevant user action and the input is
                      // clearly labeled
                      // eslint-disable-next-line jsx-a11y/no-autofocus
                      autoFocus={!isSelectedSheetNewAndUnsaved && i === 0}
                      className={classnames(
                        Classes.INPUT,
                        errors.results?.[choice.id] && Classes.INTENT_DANGER
                      )}
                      name={`results[${choice.id}]`}
                      readOnly={isSubmitting}
                      ref={register({
                        min: 0,
                        required: true,
                        valueAsNumber: true,
                      })}
                      type="number"
                    />
                  ) : (
                    <span>
                      {(
                        selectedSheet?.results[choice.id] ?? ''
                      ).toLocaleString()}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </BatchResultTallySheetTable>

        <BatchResultTallySheetButtonRow>
          {batch.lastEditedBy && !isEditing && (
            <span className={Classes.TEXT_MUTED}>
              Last edited by: {batch.lastEditedBy}
            </span>
          )}
          <RowSpacer />
          {(() => {
            if (selectedTabId === VOTE_TOTALS_TAB_ID) {
              return areResultsFinalized ? (
                <span>Select a sheet to view tallies</span>
              ) : (
                <span>Select a sheet to edit tallies</span>
              )
            }
            if (isEditing) {
              return (
                <>
                  <Button
                    disabled={isSubmitting}
                    icon="delete"
                    minimal
                    onClick={discardChanges}
                  >
                    Discard Changes
                  </Button>
                  <Button
                    icon="tick"
                    intent="primary"
                    loading={isSubmitting}
                    onClick={handleSubmit(onValidSubmit)}
                  >
                    {sheets.length === 1 ? 'Save Tallies' : 'Save Sheet'}
                  </Button>
                </>
              )
            }
            return (
              <ButtonGroup>
                <Button
                  intent="primary"
                  disabled={areResultsFinalized || isRemovingSheet}
                  icon="edit"
                  onClick={enableEditing}
                >
                  {sheets.length === 1 ? 'Edit Tallies' : 'Edit Sheet'}
                </Button>
                <Popover
                  content={
                    <Menu>
                      {sheets.length === 1 ? (
                        <MenuItem
                          icon="applications"
                          onClick={addSheet}
                          text="Use Multiple Tally Sheets"
                        />
                      ) : (
                        <MenuItem
                          disabled={isRemovingSheet}
                          icon={isRemovingSheet ? undefined : 'remove'}
                          onClick={removeSheet}
                          shouldDismissPopover={false}
                          text={
                            isRemovingSheet ? (
                              <Spinner size={20} />
                            ) : (
                              'Remove Sheet'
                            )
                          }
                        />
                      )}
                    </Menu>
                  }
                  isOpen={areAdditionalActionsOpen || isRemovingSheet}
                  onClose={closeAdditionalActions}
                  position="bottom"
                >
                  <Button
                    intent="primary"
                    aria-label="Additional Actions"
                    disabled={areResultsFinalized || isRemovingSheet}
                    icon="caret-down"
                    onClick={openAdditionalActions}
                  />
                </Popover>
              </ButtonGroup>
            )
          })()}
        </BatchResultTallySheetButtonRow>
      </div>
    </>
  )
}

export default BatchDetail
