import classnames from 'classnames'
import React, { useEffect, useState } from 'react'
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
  Tab,
  Tabs,
} from '@blueprintjs/core'
import { SubmitHandler, useForm } from 'react-hook-form'

import { ButtonRow } from '../../Atoms/Layout'
import { Detail } from '../../Atoms/ListAndDetail'
import { IBatch, IBatchResultTallySheet } from '../useBatchResults'
import { IContest } from '../../../types'
import { sum } from '../../../utils/number'

interface ITabsWrapperProps {
  isAnimationEnabled?: boolean
}

// More on why this is needed can be found below, where it's used
const TabsWrapper = styled.div<ITabsWrapperProps>`
  .${Classes.TAB_INDICATOR_WRAPPER} {
    ${({ isAnimationEnabled = true }) =>
      !isAnimationEnabled && 'transition-duration: 0ms;'}
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
`

const BatchResultTallySheetButtonRow = styled(ButtonRow).attrs({
  alignItems: 'center',
  justifyContent: 'end',
})`
  min-height: 30px;
`

const VOTE_TOTALS_TAB_ID = 'vote-totals'

interface IBatchResultTallySheetWithId extends IBatchResultTallySheet {
  id: string
}

interface ITab {
  id: string
  name: string
}

function sheetWithId(
  sheet: IBatchResultTallySheet
): IBatchResultTallySheetWithId {
  return { ...sheet, id: uuidv4() }
}

function sheetWithoutId(
  sheet: IBatchResultTallySheetWithId
): IBatchResultTallySheet {
  return { name: sheet.name, results: sheet.results }
}

function defaultSheetName(sheetNumber: number) {
  return `Sheet ${sheetNumber}`
}

function constructEmptySheet(
  sheetName: string,
  contest: IContest
): IBatchResultTallySheet {
  const results: { [choiceId: string]: number } = {}
  contest.choices.forEach(choice => {
    results[choice.id] = 0
  })
  return { name: sheetName, results }
}

function tabsFromSheets(sheets: IBatchResultTallySheetWithId[]): ITab[] {
  if (sheets.length === 1) {
    return [{ id: sheets[0].id, name: 'Vote Totals' }]
  }
  return [
    { id: VOTE_TOTALS_TAB_ID, name: 'Vote Totals' },
    ...sheets.map(sheet => ({ id: sheet.id, name: sheet.name })),
  ]
}

interface IBatchDetailsProps {
  areResultsFinalized: boolean
  batch: IBatch
  contest: IContest
  saveBatchResults: (
    resultTallySheets: IBatchResultTallySheet[]
  ) => Promise<void>
  setAreChangesUnsaved: (areChangesUnsaved: boolean) => void

  // Require a key to ensure that the state within this component resets when a different batch is
  // selected
  key: string // eslint-disable-line react/no-unused-prop-types
}

const BatchDetails: React.FC<IBatchDetailsProps> = ({
  areResultsFinalized,
  batch,
  contest,
  saveBatchResults,
  setAreChangesUnsaved,
}) => {
  const [sheets, setSheets] = useState<IBatchResultTallySheetWithId[]>(
    (batch.resultTallySheets.length === 0
      ? [constructEmptySheet(defaultSheetName(1), contest)]
      : batch.resultTallySheets
    ).map(sheetWithId)
  )
  const tabs = tabsFromSheets(sheets)
  const [selectedTabId, setSelectedTabId] = useState(tabs[0].id)
  const [isEditing, setIsEditing] = useState(false)
  const [isTabsAnimationEnabled, setIsTabsAnimationEnabled] = useState(true)

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
    const newSheet = sheetWithId(constructEmptySheet(newSheetName, contest))
    const updatedSheets = [...sheets, newSheet]

    // Update client-side state first for immediate UI feedback
    setSheets(updatedSheets)
    setSelectedTabId(newSheet.id)
    await saveBatchResults(updatedSheets.map(sheetWithoutId))
  }

  const updateCurrentSheet = async (updatedSheet: IBatchResultTallySheet) => {
    const updatedSheets = sheets.map((sheet, i) =>
      i === currentSheetIndex ? { ...updatedSheet, id: sheet.id } : sheet
    )

    // Update client-side state first for immediate UI feedback
    setSheets(updatedSheets)
    await saveBatchResults(updatedSheets.map(sheetWithoutId))
  }

  const deleteCurrentSheet = async () => {
    let updatedSheets = sheets.filter((_, i) => i !== currentSheetIndex)
    if (updatedSheets.length === 1) {
      // If we're dropping back to 1 sheet, reset the name of that sheet back to the default
      updatedSheets = [{ ...updatedSheets[0], name: defaultSheetName(1) }]
    }

    // Update client-side state first for immediate UI feedback
    setSheets(updatedSheets)
    setSelectedTabId(
      // Auto-select the next sheet (or last sheet if none)
      updatedSheets[Math.min(currentSheetIndex, updatedSheets.length - 1)].id
    )
    await saveBatchResults(updatedSheets.map(sheetWithoutId))
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

  // ---------- Handlers (end) ----------

  return (
    <Detail>
      <H4>{batch.name}</H4>

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
              <Tab id={tab.id} key={tab.id}>
                {tab.name}
              </Tab>
            ))}
            <Tabs.Expander />
            {sheets.length > 1 && (
              <Button
                disabled={areResultsFinalized}
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
        areResultsFinalized={areResultsFinalized}
        batch={batch}
        contest={contest}
        deleteSheet={deleteCurrentSheet}
        disableEditing={disableEditing}
        enableEditing={enableEditing}
        isEditing={isEditing}
        key={selectedTabId}
        selectedTabId={selectedTabId}
        setAreChangesUnsaved={setAreChangesUnsaved}
        sheets={sheets}
        updateSheet={updateCurrentSheet}
      />
    </Detail>
  )
}

interface IBatchResultTallySheetProps {
  addSheet: () => Promise<void>
  areResultsFinalized: boolean
  batch: IBatch
  contest: IContest
  deleteSheet: () => Promise<void>
  disableEditing: () => void
  enableEditing: () => void
  isEditing: boolean
  selectedTabId: string
  setAreChangesUnsaved: (areChangesUnsaved: boolean) => void
  sheets: IBatchResultTallySheetWithId[]
  updateSheet: (updatedSheet: IBatchResultTallySheet) => Promise<void>

  // Require a key to ensure that the state within this component resets when a different sheet is
  // selected
  key: string // eslint-disable-line react/no-unused-prop-types
}

const BatchResultTallySheet: React.FC<IBatchResultTallySheetProps> = ({
  addSheet,
  areResultsFinalized,
  batch,
  contest,
  deleteSheet,
  disableEditing,
  enableEditing,
  isEditing,
  selectedTabId,
  setAreChangesUnsaved,
  sheets,
  updateSheet,
}) => {
  const tabs = tabsFromSheets(sheets)
  const isTotalsSheet = selectedTabId === VOTE_TOTALS_TAB_ID
  const selectedSheet = isTotalsSheet
    ? undefined
    : sheets.find(sheet => sheet.id === selectedTabId)

  const formMethods = useForm<IBatchResultTallySheet>({
    defaultValues: selectedSheet,
    shouldUnregister: false,
  })
  const { errors, formState, handleSubmit, register, reset } = formMethods
  // Important gotcha! You have to access properties on the formState to subscribe to it:
  // https://github.com/react-hook-form/react-hook-form/issues/9002
  const { isSubmitting, isDirty } = formState

  // Communicate up to the parent whether or not there are unsaved changes
  useEffect(() => {
    setAreChangesUnsaved(isDirty)
  }, [isDirty, setAreChangesUnsaved])

  const discardChanges = () => {
    reset(selectedSheet)
    disableEditing()
  }

  const onValidSubmit: SubmitHandler<IBatchResultTallySheet> = async sheet => {
    try {
      await updateSheet(sheet)
    } catch {
      // Errors are automatically toasted by the queryClient
      return
    }
    // Reset the form's isDirty value back to false
    reset(sheet)
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
            {contest.choices.map(choice => (
              <tr key={choice.id}>
                <td>{choice.name}</td>
                <td>
                  {isTotalsSheet ? (
                    <span>
                      {sum(
                        sheets.map(sheet => sheet.results[choice.id] || 0)
                      ).toLocaleString()}
                    </span>
                  ) : isEditing ? (
                    <input
                      aria-label={`${choice.name} Votes`}
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
                        selectedSheet?.results[choice.id] || 0
                      ).toLocaleString()}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </BatchResultTallySheetTable>

        <BatchResultTallySheetButtonRow>
          {(() => {
            if (selectedTabId === VOTE_TOTALS_TAB_ID) {
              return <span>Select a sheet to edit tallies.</span>
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
                  disabled={areResultsFinalized}
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
                          icon="remove"
                          onClick={deleteSheet}
                          text="Remove Sheet"
                        />
                      )}
                    </Menu>
                  }
                  position="bottom"
                >
                  <Button
                    aria-label="Additional Actions"
                    disabled={areResultsFinalized}
                    icon="caret-down"
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

export default BatchDetails
