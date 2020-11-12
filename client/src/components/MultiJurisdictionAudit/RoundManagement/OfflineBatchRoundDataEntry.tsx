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
  Label,
} from '@blueprintjs/core'
import styled from 'styled-components'
import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import { IRound } from '../useRoundsAuditAdmin'
import useOfflineBatchResults, {
  IOfflineBatchResult,
} from './useOfflineBatchResults'
import { testNumber } from '../../utilities'
import { replaceAtIndex } from '../../../utils/array'

const OfflineBatchResultsForm = styled.form`
  /* Disable up/down toggle arrows on number inputs */
  input::-webkit-outer-spin-button,
  input::-webkit-inner-spin-button {
    margin: 0;
    -webkit-appearance: none; /* stylelint-disable-line property-no-vendor-prefix */
  }
  input[type='number'] {
    -moz-appearance: textfield; /* stylelint-disable-line property-no-vendor-prefix */
  }

  table {
    position: relative;
    border: 1px solid ${Colors.LIGHT_GRAY3};
    width: 100%;
    table-layout: fixed;
    border-collapse: separate;

    th {
      position: sticky;
      top: 0;
      z-index: 1;
      border-bottom: 1px solid ${Colors.GRAY3};
      background: #ffffff;
    }

    th,
    td {
      vertical-align: middle;
    }
  }
`

const InputWithValidation = ({ field, form, ...props }: FieldProps) => {
  const error = getIn(form.errors, field.name)
  return (
    <div>
      <input
        className={`bp3-input bp3-fill ${error ? 'bp3-intent-danger' : ''}`}
        {...field}
        {...props}
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

// In order to add/remove rows and let users edit the batch name, we need to generate our own unique keys for each row
interface IResultRow extends IOfflineBatchResult {
  rowKey: string
}

const OfflineBatchRoundDataEntry = ({ round }: IProps) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const contests = useContestsJurisdictionAdmin(electionId, jurisdictionId)
  const [batchResults, updateResults, finalizeResults] = useOfflineBatchResults(
    electionId,
    jurisdictionId,
    round.id
  )
  const [isConfirmOpen, setIsConfirmOpen] = useState(false)

  if (!contests || !batchResults) return null

  // We only support one contest for now
  const contest = contests[0]

  const { results, finalizedAt } = batchResults

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
    const newResults = replaceAtIndex(
      results,
      editingBatchIndex!,
      editingBatch!
    ).filter(b => b) // Filter out null (used to delete a batch)
    if (await updateResults(newResults)) actions.resetForm()
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
          dirty,
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
                  Results finalized at {new Date(finalizedAt).toLocaleString()}
                </Callout>
              )}
            </div>
            <fieldset disabled={!!finalizedAt}>
              <HTMLTable striped bordered>
                <thead>
                  <tr>
                    <th />
                    <th>Batch Name</th>
                    <th>Batch Type</th>
                    {contest.choices.map(choice => (
                      <th key={`th-${choice.id}`}>{choice.name}</th>
                    ))}
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
                      <td>
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
                          {/* <Field
                              type="number"
                              name={`results.${r}.choiceResults.${choice.id}`}
                              component={InputWithValidation}
                              validate={testNumber()}
                            /> */}
                        </td>
                      ))}
                    </tr>
                  ))}
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
                >
                  Add batch
                </Button>
                <Button onClick={() => setIsConfirmOpen(true)} disabled={dirty}>
                  Finalize Results
                </Button>
              </div>
            </fieldset>

            {(() => {
              const addingBatch = values.editingBatchIndex === results.length
              return (
                <Dialog
                  icon={addingBatch ? 'plus' : 'edit'}
                  onClose={handleReset}
                  title={addingBatch ? 'Add Batch' : 'Edit Batch'}
                  isOpen={values.editingBatchIndex !== null}
                >
                  <div className={Classes.DIALOG_BODY}>
                    <Label>Batch Name</Label>
                    <Field
                      type="text"
                      name="editingBatch.batchName"
                      component={InputWithValidation}
                      validate={(value: string) => (!value ? 'Required' : null)}
                    />
                    <Label>Batch Type</Label>
                    <Field
                      name="editingBatch.batchType"
                      component={SelectWithValidation}
                      validate={(value: string) => (!value ? 'Required' : null)}
                    >
                      <option></option>
                      <option>Absentee By Mail</option>
                      <option>Advance</option>
                      <option>Election Day</option>
                      <option>Provisional</option>
                      <option>Other</option>
                    </Field>
                    {contest.choices.map(choice => (
                      <div key={`editing-${choice.id}`}>
                        <Label>{choice.name}</Label>
                        <Field
                          type="number"
                          name={`editingBatch.choiceResults.${choice.id}`}
                          component={InputWithValidation}
                          validate={testNumber()}
                        />
                      </div>
                    ))}
                  </div>
                  <div className={Classes.DIALOG_FOOTER}>
                    <div className={Classes.DIALOG_FOOTER_ACTIONS}>
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                        }}
                      >
                        {!addingBatch && (
                          <Button
                            onClick={async () => {
                              await submit(
                                { ...values, editingBatch: null },
                                props
                              )
                            }}
                            intent="danger"
                            style={{ marginLeft: 0 }}
                          >
                            Remove Batch
                          </Button>
                        )}
                        <div>
                          <Button onClick={handleReset}>Cancel</Button>
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
            })()}

            <Dialog
              icon="info-sign"
              onClose={() => setIsConfirmOpen(false)}
              title="Are you sure you want to finalize your results?"
              isOpen={isConfirmOpen}
            >
              <div className={Classes.DIALOG_BODY}>
                <p>This action cannot be undone.</p>
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
