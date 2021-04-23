import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Formik,
  FormikProps,
  Field,
  FieldProps,
  getIn,
  FormikHelpers,
} from 'formik'
import {
  Button,
  HTMLTable,
  Dialog,
  Classes,
  Callout,
  Colors,
  FormGroup,
  H4,
} from '@blueprintjs/core'
import styled from 'styled-components'
import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import { IRound } from '../useRoundsAuditAdmin'
import useOfflineBatchResults, {
  IOfflineBatchResult,
} from './useOfflineBatchResults'
import { testNumber } from '../../utilities'
import CopyToClipboard from '../../Atoms/CopyToClipboard'

const sum = (nums: number[]) => nums.reduce((a, b) => a + b, 0)

const OfflineBatchResultsForm = styled.form`
  table {
    position: relative;
    border: 1px solid ${Colors.LIGHT_GRAY1};
    width: 100%;
    table-layout: fixed;
    border-collapse: separate;

    th {
      position: sticky;
      top: 0;
      z-index: 1;
      border-bottom: 1px solid ${Colors.GRAY2};
      background: ${Colors.WHITE};
    }

    th,
    td {
      vertical-align: middle;
      word-wrap: break-word;
    }

    /* Exclude edit buttons from copy/paste */
    th:first-child,
    td:first-child {
      -moz-user-select: none; /* stylelint-disable-line property-no-vendor-prefix */
      -webkit-user-select: none; /* stylelint-disable-line property-no-vendor-prefix */
      user-select: none;
    }
  }
`

const Input = styled.input`
  /* Disable up/down toggle arrows on number inputs */
  ::-webkit-outer-spin-button,
  ::-webkit-inner-spin-button {
    margin: 0;
    -webkit-appearance: none; /* stylelint-disable-line property-no-vendor-prefix */
  }
  [type='number'] {
    -moz-appearance: textfield; /* stylelint-disable-line property-no-vendor-prefix */
  }
`

const totalStyle = { color: Colors.BLUE3, fontWeight: 600 }

const InputWithValidation = ({ field, form, ...props }: FieldProps) => {
  const error = getIn(form.errors, field.name)
  return (
    <div>
      <Input
        className={`bp3-input bp3-fill ${error ? 'bp3-intent-danger' : ''}`}
        {...field}
        {...props}
        value={field.value || ''}
      />
    </div>
  )
}

const SelectWithValidation = ({ field, form, ...props }: FieldProps) => {
  const error = getIn(form.errors, field.name)
  return (
    <div className="bp3-select bp3-fill">
      <select
        className={error ? 'bp3-input bp3-intent-danger' : ''}
        {...field}
        {...props}
      />
    </div>
  )
}

interface IProps {
  round: IRound
}

const OfflineBatchRoundDataEntry = ({ round }: IProps) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const contests = useContestsJurisdictionAdmin(electionId, jurisdictionId)
  const [
    batchResults,
    addResult,
    updateResult,
    removeResult,
    finalizeResults,
  ] = useOfflineBatchResults(electionId, jurisdictionId, round.id)
  const [isConfirmOpen, setIsConfirmOpen] = useState(false)

  if (!contests || !batchResults) return null

  // We only support one contest for now
  const contest = contests[0]

  const { results, finalizedAt } = batchResults

  const total = (choiceId: string) =>
    sum(results.map(batch => batch.choiceResults[choiceId]))

  const emptyBatch = (): IOfflineBatchResult => ({
    batchName: '',
    batchType: '',
    choiceResults: {},
  })

  interface FormValues {
    editingBatch: IOfflineBatchResult | null
    editingBatchIndex: number | null
  }

  const submit = async (
    { editingBatch, editingBatchIndex }: FormValues,
    actions: FormikHelpers<FormValues>
  ) => {
    let success = false
    if (editingBatchIndex === results.length) {
      success = await addResult(editingBatch!)
    } else if (editingBatch === null) {
      success = await removeResult(results[editingBatchIndex!].batchName)
    } else {
      success = await updateResult(
        results[editingBatchIndex!].batchName,
        editingBatch
      )
    }
    if (success) actions.resetForm()
    actions.setSubmitting(false)
  }

  return (
    <Formik
      initialValues={
        {
          editingBatch: null,
          editingBatchIndex: null,
        } as FormValues
      }
      enableReinitialize
      onSubmit={submit}
      validateOnChange={false}
      validateOnBlur={false}
    >
      {(props: FormikProps<FormValues>) => {
        const {
          handleSubmit,
          values,
          setValues,
          isSubmitting,
          errors,
          handleReset,
        } = props
        return (
          <OfflineBatchResultsForm>
            <div style={{ width: '510px', marginBottom: '20px' }}>
              <p>
                When you have examined all the ballots assigned to you, enter
                the number of votes recorded for each candidate/choice for each
                batch of audited ballots.
              </p>
              {finalizedAt && (
                <Callout
                  icon="tick-circle"
                  intent="success"
                  style={{ margin: '20px 0 20px 0' }}
                >
                  Results finalized at{' '}
                  {new Date(`${finalizedAt}`).toLocaleString()}
                </Callout>
              )}
            </div>
            <fieldset disabled={!!finalizedAt}>
              <HTMLTable striped bordered id="results-table">
                <thead>
                  <tr>
                    <th />
                    <th>Batch Name</th>
                    <th>Batch Type</th>
                    {contest.choices.map(choice => (
                      <th key={`th-${choice.id}`}>{choice.name}</th>
                    ))}
                    <th style={totalStyle}>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {results.length === 0 && (
                    <tr>
                      <td colSpan={contest.choices.length + 3}>
                        No batches added. Add your first batch below.
                      </td>
                    </tr>
                  )}
                  {results.map((batch, index) => (
                    <tr key={batch.batchName}>
                      <td style={{ textAlign: 'center' }}>
                        <Button
                          icon="edit"
                          onClick={() =>
                            setValues({
                              editingBatch: batch,
                              editingBatchIndex: index,
                            })
                          }
                        >
                          Edit
                        </Button>
                      </td>
                      <td>{batch.batchName}</td>
                      <td>{batch.batchType}</td>
                      {contest.choices.map(choice => (
                        <td key={`${batch.batchName}-${choice.id}`}>
                          {batch.choiceResults[choice.id].toLocaleString()}
                        </td>
                      ))}
                      <td style={totalStyle}>
                        {sum(
                          Object.values(batch.choiceResults)
                        ).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                  <tr>
                    <td style={totalStyle} />
                    <td style={totalStyle}>Total</td>
                    <td style={totalStyle} />
                    {contest.choices.map(choice => (
                      <td style={totalStyle} key={`total-${choice.id}`}>
                        {total(choice.id).toLocaleString()}
                      </td>
                    ))}
                    <td style={totalStyle}>
                      {sum(
                        contest.choices.map(choice => total(choice.id))
                      ).toLocaleString()}
                    </td>
                  </tr>
                </tbody>
              </HTMLTable>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginTop: '20px',
                }}
              >
                <Button
                  icon="plus"
                  onClick={() =>
                    setValues({
                      editingBatch: emptyBatch(),
                      editingBatchIndex: results.length,
                    })
                  }
                  intent="primary"
                  disabled={!!finalizedAt}
                >
                  Add batch
                </Button>
                <CopyToClipboard
                  getText={() =>
                    document.getElementById('results-table')!.outerHTML
                  }
                />
                <Button
                  onClick={() => setIsConfirmOpen(true)}
                  disabled={!!finalizedAt}
                >
                  Finalize Results
                </Button>
              </div>
            </fieldset>

            {(() => {
              const addingBatch = values.editingBatchIndex === results.length
              return (
                values.editingBatchIndex !== null && (
                  <Dialog
                    icon={addingBatch ? 'plus' : 'edit'}
                    onClose={handleReset}
                    title={
                      addingBatch
                        ? 'Add Batch'
                        : `Edit Batch: ${results[values.editingBatchIndex!].batchName}`
                    }
                    isOpen={values.editingBatchIndex !== null}
                    style={{ width: 'none' }}
                    transitionDuration={0}
                  >
                    <div
                      className={Classes.DIALOG_BODY}
                      style={{ display: 'flex' }}
                    >
                      <div style={{ flexGrow: 1 }}>
                        <H4>Batch Info</H4>
                        <FormGroup
                          label="Batch Name"
                          labelFor="editingBatch-batchName"
                        >
                          <Field
                            type="text"
                            name="editingBatch.batchName"
                            id="editingBatch-batchName"
                            component={InputWithValidation}
                            validate={(value: string) =>
                              !value ? 'Required' : null
                            }
                            autoFocus
                          />
                        </FormGroup>
                        <FormGroup
                          label="Batch Type"
                          labelFor="editingBatch-batchType"
                        >
                          <Field
                            name="editingBatch.batchType"
                            id="editingBatch-batchType"
                            component={SelectWithValidation}
                            validate={(value: string) =>
                              !value ? 'Required' : null
                            }
                          >
                            <option></option>
                            <option>Absentee By Mail</option>
                            {/* <option>Advance</option> */}
                            <option>Election Day</option>
                            <option>Provisional</option>
                            <option>Other</option>
                          </Field>
                        </FormGroup>
                      </div>
                      <div style={{ marginLeft: '20px', flexGrow: 1 }}>
                        <H4>Audited Votes</H4>
                        {contest.choices.map(choice => (
                          <div key={`editing-${choice.id}`}>
                            <FormGroup
                              label={choice.name}
                              labelFor={`editingBatch-choiceResults-${choice.id}`}
                            >
                              <Field
                                type="number"
                                name={`editingBatch.choiceResults.${choice.id}`}
                                id={`editingBatch-choiceResults-${choice.id}`}
                                component={InputWithValidation}
                                validate={testNumber()}
                              />
                            </FormGroup>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className={Classes.DIALOG_FOOTER}>
                      {errors && errors.editingBatch && (
                        <p style={{ color: Colors.RED2, textAlign: 'center' }}>
                          Please fill in the empty fields above before saving
                          this batch.
                        </p>
                      )}
                      <div className={Classes.DIALOG_FOOTER_ACTIONS}>
                        <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            flexGrow: 1,
                          }}
                        >
                          {!addingBatch ? (
                            <Button
                              onClick={() =>
                                // Use null to signify that we want to delete this batch
                                submit({ ...values, editingBatch: null }, props)
                              }
                              intent="danger"
                              style={{ marginLeft: 0 }}
                              tabIndex={-1}
                            >
                              Remove Batch
                            </Button>
                          ) : (
                            <div />
                          )}
                          <div>
                            <Button onClick={handleReset} tabIndex={-1}>
                              Cancel
                            </Button>
                            <Button
                              intent="primary"
                              loading={isSubmitting}
                              onClick={handleSubmit as React.FormEventHandler}
                            >
                              Save Batch
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </Dialog>
                )
              )
            })()}

            <Dialog
              icon="info-sign"
              onClose={() => setIsConfirmOpen(false)}
              title="Are you sure you want to finalize your results?"
              isOpen={isConfirmOpen}
            >
              <div className={Classes.DIALOG_BODY}>
                <p>
                  <strong>This action cannot be undone.</strong>
                </p>
                <p>
                  You should only finalize your results once you have finished
                  auditing every batch of ballots and have entered the results
                  for each batch on this page.
                </p>
                <p>
                  <strong>
                    Before finalizing your results, check the results you have
                    entered into Arlo page against the tally sheets.
                  </strong>
                </p>
              </div>
              <div className={Classes.DIALOG_FOOTER}>
                <div className={Classes.DIALOG_FOOTER_ACTIONS}>
                  <Button onClick={() => setIsConfirmOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    intent="primary"
                    onClick={async () => {
                      await finalizeResults()
                      setIsConfirmOpen(false)
                    }}
                    disabled={results.length === 0}
                  >
                    Finalize Results
                  </Button>
                </div>
              </div>
            </Dialog>
          </OfflineBatchResultsForm>
        )
      }}
    </Formik>
  )
}

export default OfflineBatchRoundDataEntry
