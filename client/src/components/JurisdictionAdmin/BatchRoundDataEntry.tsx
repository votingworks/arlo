/* eslint-disable jsx-a11y/no-autofocus */
import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  HTMLTable,
  Colors,
  Button,
  Classes,
  Callout,
  Dialog,
  ButtonGroup,
  Popover,
  Menu,
  MenuItem,
} from '@blueprintjs/core'
import { useForm, useFieldArray } from 'react-hook-form'
import styled, { css } from 'styled-components'
import { toast } from 'react-toastify'
import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import {
  useBatches,
  IBatch,
  useRecordBatchResults,
  useFinalizeBatchResults,
  IBatchResults,
  IBatchResultTallySheet,
} from './useBatchResults'
import { sum } from '../../utils/number'
import { IContest } from '../../types'
import CopyToClipboard from '../Atoms/CopyToClipboard'
import { useConfirm, Confirm } from '../Atoms/Confirm'
import { IRound } from '../AuditAdmin/useRoundsAuditAdmin'

const ResultsTable = styled(HTMLTable).attrs({
  striped: true,
  bordered: true,
})`
  position: relative;
  border: 1px solid ${Colors.LIGHT_GRAY1};
  width: 100%;
  table-layout: fixed;
  border-collapse: separate;

  thead {
    position: sticky;
    top: 0;
    z-index: 1;
    box-shadow: 0 1px 0 ${Colors.GRAY4};
    background: ${Colors.WHITE};
  }

  thead tr th {
    overflow-x: hidden;
    vertical-align: bottom;
  }

  tr td {
    vertical-align: middle;
  }

  /* Exclude edit buttons from copy/paste */
  th:last-child,
  td:last-child {
    -moz-user-select: none; /* stylelint-disable-line property-no-vendor-prefix */
    -webkit-user-select: none; /* stylelint-disable-line property-no-vendor-prefix */
    user-select: none;
  }
`

const TallySheetsTable = styled(HTMLTable).attrs({
  striped: true,
  bordered: true,
})`
  border: 1px solid ${Colors.LIGHT_GRAY1};
  table-layout: fixed;
  border-collapse: separate;

  thead {
    box-shadow: 0 1px 0 ${Colors.GRAY4};
    background: ${Colors.WHITE};
  }
`

const ChoiceTD = styled.td`
  width: 100px;
  vertical-align: middle;
`

const totalsStyle = css`
  &&& {
    color: ${Colors.BLUE3};
    font-weight: 600;
  }
`

const TotalsTD = styled.td`
  ${totalsStyle} /* stylelint-disable-line value-keyword-case */
`
const TotalsTH = styled.th`
  ${totalsStyle} /* stylelint-disable-line value-keyword-case */
`

const BatchResultsForm = ({
  electionId,
  jurisdictionId,
  roundId,
  contest,
  batch,
  closeForm,
}: {
  electionId: string
  jurisdictionId: string
  roundId: string
  contest: IContest
  batch: IBatch
  closeForm: () => void
}) => {
  const recordBatchResults = useRecordBatchResults(
    electionId,
    jurisdictionId,
    roundId
  )
  const { register, handleSubmit, watch, formState, errors } = useForm<
    IBatchResults
  >({
    defaultValues:
      batch.resultTallySheets.length === 1
        ? batch.resultTallySheets[0].results
        : undefined,
  })

  const onSubmit = (results: IBatchResults) => {
    const tallySheet = {
      name: 'Tally Sheet #1',
      results,
    }
    recordBatchResults.mutate(
      { batchId: batch.id, resultTallySheets: [tallySheet] },
      { onSuccess: closeForm }
    )
  }

  return (
    <tr key={batch.id}>
      <td>{batch.name}</td>
      {contest.choices.map((choice, i) => (
        <ChoiceTD key={`${batch.name}-${choice.id}`}>
          <input
            className={Classes.INPUT}
            type="number"
            name={choice.id}
            ref={register({
              valueAsNumber: true,
              min: 0,
              required: true,
            })}
            style={{
              width: '100%',
              border: errors[choice.id] ? '1px solid red' : 'inherit',
            }}
            autoFocus={i === 0}
            aria-label={choice.name}
          />
        </ChoiceTD>
      ))}
      <TotalsTD>
        {sum(Object.values(watch()).filter(n => n)).toLocaleString()}
      </TotalsTD>
      <td style={{ paddingRight: 0 }}>
        <Button
          intent="primary"
          icon="tick"
          onClick={handleSubmit(onSubmit)}
          loading={formState.isSubmitting}
        >
          Save
        </Button>
        <Button
          small
          minimal
          style={{ marginLeft: '5px' }}
          icon="cross"
          onClick={closeForm}
          loading={formState.isSubmitting}
          aria-label="Cancel"
        />
      </td>
    </tr>
  )
}

const emptyTallySheet = (index: number) => ({
  name: `Tally Sheet #${index}`,
  results: {},
})

const BatchTallySheetsModal = ({
  electionId,
  jurisdictionId,
  roundId,
  contest,
  batch,
  closeModal,
}: {
  electionId: string
  jurisdictionId: string
  roundId: string
  contest: IContest
  batch: IBatch
  closeModal: () => void
}) => {
  const recordBatchResults = useRecordBatchResults(
    electionId,
    jurisdictionId,
    roundId
  )
  const initialTallySheets =
    batch.resultTallySheets.length > 1
      ? batch.resultTallySheets
      : batch.resultTallySheets.concat([
          emptyTallySheet(batch.resultTallySheets.length + 1),
        ])
  const { register, control, handleSubmit, formState, errors } = useForm<{
    resultTallySheets: IBatchResultTallySheet[]
  }>({
    defaultValues: { resultTallySheets: initialTallySheets },
  })
  const { fields, append, remove } = useFieldArray({
    control,
    name: 'resultTallySheets',
  })

  const onSubmit = async ({
    resultTallySheets,
  }: {
    resultTallySheets: IBatchResultTallySheet[]
  }) => {
    recordBatchResults.mutate(
      { batchId: batch.id, resultTallySheets },
      { onSuccess: closeModal }
    )
  }

  return (
    <Dialog
      icon="edit"
      title={`Edit Tally Sheets for Batch: ${batch.name}`}
      onClose={closeModal}
      isOpen
      style={{ width: 'unset', maxWidth: '960px' }}
    >
      <div className={Classes.DIALOG_BODY}>
        <TallySheetsTable>
          <thead>
            <tr>
              <th>Tally Sheet Label</th>
              {contest.choices.map(choice => (
                <th key={choice.id}>{choice.name}</th>
              ))}
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((tallySheet, index) => (
              <tr key={tallySheet.id}>
                <ChoiceTD key="tally-sheet-label">
                  <input
                    className={Classes.INPUT}
                    name={`resultTallySheets[${index}].name`}
                    type="text"
                    ref={register({ required: true })}
                    defaultValue={tallySheet.name}
                    style={{
                      border:
                        errors.resultTallySheets &&
                        errors.resultTallySheets[index] &&
                        errors.resultTallySheets[index]!.name
                          ? '1px solid red'
                          : 'inherit',
                    }}
                    aria-label="Tally Sheet Label"
                  />
                </ChoiceTD>
                {contest.choices.map(choice => (
                  <ChoiceTD key={choice.id}>
                    <input
                      className={Classes.INPUT}
                      type="number"
                      name={`resultTallySheets[${index}].results[${choice.id}]`}
                      ref={register({
                        valueAsNumber: true,
                        min: 0,
                        required: true,
                      })}
                      defaultValue={tallySheet.results[choice.id]}
                      style={{
                        border:
                          errors.resultTallySheets &&
                          errors.resultTallySheets[index] &&
                          errors.resultTallySheets[index]!.results &&
                          errors.resultTallySheets[index]!.results![choice.id]
                            ? '1px solid red'
                            : 'inherit',
                      }}
                      aria-label={choice.name}
                    />
                  </ChoiceTD>
                ))}
                <td>
                  <Button
                    onClick={() => remove(index)}
                    icon="trash"
                    disabled={fields.length === 1}
                  >
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </TallySheetsTable>
      </div>
      <div className={Classes.DIALOG_FOOTER}>
        <div
          className={Classes.DIALOG_FOOTER_ACTIONS}
          style={{ justifyContent: 'space-between' }}
        >
          <Button
            onClick={() => append(emptyTallySheet(fields.length + 1))}
            icon="plus"
            style={{ marginLeft: '0' }}
          >
            Add Tally Sheet
          </Button>
          <div>
            <Button onClick={closeModal}>Cancel</Button>
            <Button
              intent="primary"
              icon="tick"
              onClick={handleSubmit(onSubmit)}
              loading={formState.isSubmitting}
            >
              Save Tally Sheets
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  )
}

const BatchRoundDataEntry = ({ round }: { round: IRound }) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const contests = useContestsJurisdictionAdmin(electionId, jurisdictionId)
  const batchesResp = useBatches(electionId, jurisdictionId, round.id)
  const finalizeResults = useFinalizeBatchResults(
    electionId,
    jurisdictionId,
    round.id
  )
  const { confirm, confirmProps } = useConfirm()
  const [editing, setEditing] = useState<{
    batchId: IBatch['id']
    showTallySheetsModal: boolean
  } | null>(null)

  if (!contests || !batchesResp.isSuccess) return null

  // Batch comparison audits only support a single contest
  const [contest] = contests
  const { batches, resultsFinalizedAt } = batchesResp.data

  const batchChoiceVotes = (batch: IBatch, choiceId: string) =>
    batch.resultTallySheets.length > 0
      ? sum(
          batch.resultTallySheets.map(
            tallySheet => tallySheet.results[choiceId]
          )
        )
      : undefined

  const choiceTotal = (choiceId: string) =>
    sum(batches.map(batch => batchChoiceVotes(batch, choiceId) || 0))

  const onClickFinalize = () => {
    if (batches.some(batch => batch.resultTallySheets.length === 0)) {
      toast.error('Please enter results for all batches before finalizing.')
    } else {
      confirm({
        title: 'Are you sure you want to finalize your results?',
        description: (
          <>
            <p>
              You should only finalize your results once you have finished
              auditing every batch of ballots and have entered the results for
              each batch on this page.
            </p>
            <p>
              <strong>
                Before finalizing your results, check the results you have
                entered into Arlo page against the tally sheets.
              </strong>
            </p>
          </>
        ),
        yesButtonLabel: 'Confirm',
        onYesClick: async () => {
          await finalizeResults.mutateAsync()
        },
      })
    }
  }

  return (
    <div>
      <div>
        <p>
          When you have examined all of the ballots assigned to you, enter the
          number of votes recorded for each candidate/choice from the audited
          ballots in each batch.
        </p>
        {resultsFinalizedAt && (
          <Callout
            icon="tick-circle"
            intent="success"
            style={{ margin: '20px 0 20px 0' }}
          >
            Results finalized
          </Callout>
        )}
      </div>
      <ResultsTable id="results-table">
        <thead>
          <tr>
            <th
              style={{
                width: `${25 - Math.min(contest.choices.length, 10) * 1.5}%`,
              }}
            >
              Batch Name
            </th>
            {contest.choices.map(choice => (
              <th key={`th-${choice.id}`}>{choice.name}</th>
            ))}
            <TotalsTH>Batch Total Votes</TotalsTH>
            <th style={{ width: '125px' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {batches.map(batch =>
            editing &&
            batch.id === editing.batchId &&
            !editing.showTallySheetsModal ? (
              <BatchResultsForm
                electionId={electionId}
                jurisdictionId={jurisdictionId}
                roundId={round.id}
                contest={contest}
                batch={batch}
                key={batch.id}
                closeForm={() => setEditing(null)}
              />
            ) : (
              <tr key={batch.id}>
                <td>{batch.name}</td>
                {contest.choices.map(choice => {
                  const choiceVotes = batchChoiceVotes(batch, choice.id)
                  return (
                    <ChoiceTD key={`${batch.name}-${choice.id}`}>
                      {choiceVotes && choiceVotes.toLocaleString()}
                    </ChoiceTD>
                  )
                })}
                <TotalsTD>
                  {batch.resultTallySheets.length > 0 &&
                    sum(
                      contest.choices.map(
                        choice => batchChoiceVotes(batch, choice.id)!
                      )
                    ).toLocaleString()}
                </TotalsTD>
                <td>
                  {batch.resultTallySheets.length > 1 ? (
                    <Button
                      icon="edit"
                      disabled={editing !== null || !!resultsFinalizedAt}
                      onClick={() =>
                        setEditing({
                          batchId: batch.id,
                          showTallySheetsModal: true,
                        })
                      }
                    >
                      Edit Tally Sheets
                    </Button>
                  ) : (
                    <ButtonGroup>
                      <Button
                        icon="edit"
                        disabled={editing !== null || !!resultsFinalizedAt}
                        onClick={() =>
                          setEditing({
                            batchId: batch.id,
                            showTallySheetsModal: false,
                          })
                        }
                      >
                        Edit
                      </Button>
                      <Popover
                        position="bottom"
                        content={
                          <Menu>
                            <MenuItem
                              text="Use Multiple Tally Sheets"
                              onClick={() =>
                                setEditing({
                                  batchId: batch.id,
                                  showTallySheetsModal: true,
                                })
                              }
                            />
                          </Menu>
                        }
                      >
                        <Button
                          icon="chevron-down"
                          disabled={editing !== null || !!resultsFinalizedAt}
                          aria-label="More"
                        />
                      </Popover>
                    </ButtonGroup>
                  )}
                </td>
              </tr>
            )
          )}
          <tr>
            <TotalsTD>Choice Total Votes</TotalsTD>
            {contest.choices.map(choice => (
              <TotalsTD key={`total-${choice.id}`}>
                {choiceTotal(choice.id).toLocaleString()}
              </TotalsTD>
            ))}
            <TotalsTD>
              {sum(
                contest.choices.map(choice => choiceTotal(choice.id))
              ).toLocaleString()}
            </TotalsTD>
            <td />
          </tr>
        </tbody>
      </ResultsTable>
      {editing && editing.showTallySheetsModal && (
        <BatchTallySheetsModal
          batch={batches.find(batch => batch.id === editing.batchId)!}
          electionId={electionId}
          jurisdictionId={jurisdictionId}
          roundId={round.id}
          contest={contest}
          closeModal={() => setEditing(null)}
        />
      )}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: '20px',
        }}
      >
        <CopyToClipboard
          getText={() => document.getElementById('results-table')!.outerHTML}
        />
        <Button
          intent="primary"
          onClick={onClickFinalize}
          disabled={!!resultsFinalizedAt}
        >
          Finalize Results
        </Button>
        <Confirm {...confirmProps} />
      </div>
    </div>
  )
}

export default BatchRoundDataEntry
