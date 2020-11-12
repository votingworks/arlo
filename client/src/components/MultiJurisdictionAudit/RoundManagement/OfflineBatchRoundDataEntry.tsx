import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Formik,
  FormikProps,
  Field,
  FieldArray,
  FieldProps,
  FieldInputProps,
  ErrorMessage,
  getIn,
} from 'formik'
import {
  Button,
  HTMLTable,
  Dialog,
  Classes,
  Callout,
  NumericInput,
  Tag,
  Colors,
} from '@blueprintjs/core'
import styled from 'styled-components'
import uuidv4 from 'uuidv4'
import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import { IRound } from '../useRoundsAuditAdmin'
import useOfflineBatchResults, {
  IOfflineBatchResults,
  IOfflineBatchResult,
} from './useOfflineBatchResults'
import FormField from '../../Atoms/Form/FormField'
import { testNumber } from '../../utilities'

const OfflineBatchResultsForm = styled.form`
  input::-webkit-outer-spin-button,
  input::-webkit-inner-spin-button {
    margin: 0;
    -webkit-appearance: none; /* stylelint-disable-line property-no-vendor-prefix */
  }

  /* Firefox */
  input[type='number'] {
    -moz-appearance: textfield; /* stylelint-disable-line property-no-vendor-prefix */
  }
`

const InputWithValidation = (props: FieldProps) => {
  const error = getIn(props.form.errors, props.field.name)
  return (
    <div>
      <input
        className={`bp3-input bp3-fill ${error ? 'bp3-intent-danger' : ''}`}
        {...props.field}
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

  const emptyResultRow = () => ({
    rowKey: uuidv4(),
    batchName: '',
    batchType: null,
    choiceResults: {},
  })

  return (
    <Formik
      initialValues={{
        results:
          results.length > 0
            ? results.map(result => ({ ...result, rowKey: uuidv4() }))
            : [emptyResultRow()],
      }}
      enableReinitialize
      onSubmit={async (values, actions) => {
        // TODO validation to prevent partially empty rows
        // Omit empty rows
        const cleanResults = values.results
          .filter(
            result =>
              result.batchName !== '' &&
              Object.values(result.choiceResults).every(
                value => (value as string | number) !== ''
              )
          )
          // Drop rowKey field
          .map(({ batchName, choiceResults, batchType }) => ({
            batchName,
            choiceResults,
            batchType,
          }))
        await updateResults(cleanResults)
        actions.setSubmitting(false)
      }}
      validateOnChange={false}
      validateOnBlur={false}
    >
      {({
        handleSubmit,
        handleReset,
        values,
        isSubmitting,
        errors,
      }: FormikProps<{ results: IResultRow[] }>) => (
        <OfflineBatchResultsForm>
          <div style={{ width: '510px' }}>
            <p>
              When you have examined all the ballots assigned to you, enter the
              number of votes recorded for each candidate/choice for each batch
              of audited ballots.
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
          <FieldArray
            name="results"
            render={arrayHelpers => (
              <fieldset disabled={!!finalizedAt}>
                <HTMLTable striped bordered>
                  <thead>
                    <tr>
                      <th />
                      <th>Batch Name</th>
                      {contest.choices.map(choice => (
                        <th key={`th-${choice.id}`}>{choice.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {values.results.map(({ rowKey }, r) => (
                      // eslint-disable-next-line react/no-array-index-key
                      <tr key={rowKey}>
                        <td>
                          <Button
                            icon="cross"
                            intent="danger"
                            minimal
                            onClick={() => {
                              arrayHelpers.remove(r)
                              if (values.results.length === 1)
                                arrayHelpers.push(emptyResultRow())
                            }}
                          />
                        </td>
                        <td>
                          <Field
                            type="text"
                            name={`results.${r}.batchName`}
                            component={InputWithValidation}
                            validate={(value: string) =>
                              !value ? 'Required' : null
                            }
                          />
                        </td>
                        <td>
                          <Field
                            as="select"
                            name={`results.${r}.batchType`}
                            // component={InputWithValidation}
                            validate={(value: string) =>
                              !value ? 'Required' : null
                            }
                          >
                            <option>Absentee By Mail</option>
                            <option>Advance</option>
                            <option>Election Day</option>
                            <option>Provisional</option>
                            <option>Other</option>
                          </Field>
                        </td>
                        {contest.choices.map(choice => (
                          // eslint-disable-next-line react/no-array-index-key
                          <td key={`${r}-${choice.id}`}>
                            <Field
                              type="number"
                              name={`results.${r}.choiceResults.${choice.id}`}
                              className="bp3-input bp3-fill"
                              component={InputWithValidation}
                              validate={testNumber()}
                            />
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
                    onClick={() => arrayHelpers.push(emptyResultRow())}
                    intent="primary"
                  >
                    Add batch
                  </Button>
                  <div>
                    {errors && errors.results && (
                      <span style={{ color: Colors.RED2 }}>
                        Please fill in any empty fields above before saving your
                        results.
                      </span>
                    )}
                    <Button
                      loading={isSubmitting}
                      onClick={handleSubmit as (e: React.FormEvent) => void}
                      intent="primary"
                      style={{ margin: '0 10px 0 10px' }}
                    >
                      Save Results
                    </Button>
                    <Button onClick={() => setIsConfirmOpen(true)}>
                      Finalize Results
                    </Button>
                  </div>
                </div>
              </fieldset>
            )}
          />

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
                <Button onClick={() => setIsConfirmOpen(false)}>Cancel</Button>
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
      )}
    </Formik>
  )
}

export default OfflineBatchRoundDataEntry
