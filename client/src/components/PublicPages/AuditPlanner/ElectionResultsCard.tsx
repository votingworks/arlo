import classnames from 'classnames'
import React, { forwardRef, ReactNode } from 'react'
import styled from 'styled-components'
import {
  Button,
  Card,
  Classes,
  Colors,
  FormGroup,
  H2,
  HTMLTable,
} from '@blueprintjs/core'
import { ErrorMessage } from '@hookform/error-message'
import { useFieldArray, useForm } from 'react-hook-form'

import { Confirm, useConfirm } from '../../Atoms/Confirm'
import {
  constructInitialElectionResults,
  constructNewCandidate,
  ICandidateFormState,
  IElectionResultsFormState,
} from './electionResults'
import { useCssBreakpoints } from '../../../utils/responsiveness'

const HIDDEN_INPUT_CLASS_NAME = 'hidden-input'

const Container = styled(Card)`
  &.bp3-card {
    margin: auto;
    padding: 32px 24px;
  }
`

const Heading = styled(H2)`
  &.bp3-heading {
    margin-left: 8px;
    margin-bottom: 24px;
  }
`

const CandidatesTable = styled(HTMLTable)`
  &.bp3-html-table {
    margin-bottom: 24px;
    table-layout: fixed;
  }

  &.bp3-html-table th {
    padding: 8px;
  }

  &.bp3-html-table td {
    height: 70px; // Large enough to house inputs plus inline error messages
    padding: 8px;
    padding-bottom: 0;
    vertical-align: top;
    width: 296px; // Large enough to accommodate longest error string
  }
  &.bp3-html-table tr:first-child td {
    height: 78px; // Extra height to accommodate extra top padding
    padding-top: 16px;
  }
  &.bp3-html-table tr:not(:last-child) td:last-child {
    padding-right: 0; // To properly align remove candidate button
  }
  &.bp3-html-table tr:last-child td {
    height: 102px; // Extra height to accommodate input labels
  }

  &.bp3-html-table .bp3-form-group {
    margin-bottom: 0;
  }

  &.bp3-html-table .bp3-input {
    height: 40px;
    width: 100%;
  }
  &.bp3-html-table .bp3-input[readonly] {
    background: ${Colors.LIGHT_GRAY5};
    box-shadow: none;
  }
  &.bp3-html-table .bp3-input.${HIDDEN_INPUT_CLASS_NAME} {
    display: none;
  }

  &.bp3-html-table .bp3-label {
    font-weight: bold;
    margin-bottom: 8px;
  }
`

const CandidateVotesInputAndRemoveButtonContainer = styled.div`
  align-items: center;
  display: flex;

  .bp3-button {
    margin-left: 8px;
  }
`

const CardActionsRow = styled.div`
  display: flex;
  justify-content: end;
  margin-right: 8px;

  .bp3-button:last-child {
    margin-left: 12px;
  }
`

const minValueRule = (minValue: number) => ({
  message: `Cannot be less than ${minValue}`,
  value: minValue,
})

/**
 * Leave enough buffer to support an election of galactic scale while making it hard for users to
 * crash the sample size math by holding down the 0 key :D
 * Keep this in sync with the server-side limit in server/api/public.py
 */
const MAX_NUMERICAL_VALUE = 1e15

const maxValueRule = {
  message: 'Too large',
  value: MAX_NUMERICAL_VALUE,
}

const numericValidationRule = {
  message: 'Can only contain numeric characters',
  value: /^[0-9]+$/,
}

interface INumericInputProps {
  'aria-label'?: string
  hasError?: boolean
  id?: string
  idReadOnly?: string
  name: string
  onChange?: () => void
  placeholder?: string
  readOnly?: boolean
  value: number
}

const NumericInput = forwardRef<HTMLInputElement, INumericInputProps>(
  function NumericInput(props, ref) {
    const {
      hasError,
      id,
      idReadOnly,
      name,
      onChange,
      placeholder,
      readOnly,
      value,
    } = props

    // Render two inputs under the hood, one managed by react-hook-form via the passed in ref and
    // the other for read-only display
    return (
      <>
        <input
          aria-hidden={readOnly}
          aria-label={props['aria-label']}
          className={classnames(
            Classes.INPUT,
            hasError && Classes.INTENT_DANGER,
            readOnly && HIDDEN_INPUT_CLASS_NAME
          )}
          id={id}
          name={name}
          onChange={onChange}
          placeholder={placeholder}
          ref={ref}
          type="number"
        />
        {readOnly && (
          <input
            aria-label={props['aria-label']}
            className={Classes.INPUT}
            id={idReadOnly}
            readOnly
            value={value.toLocaleString()}
          />
        )}
      </>
    )
  }
)

interface INumericInputFormGroupProps
  extends Omit<INumericInputProps, 'idReadOnly'> {
  helperText?: ReactNode
  label?: string
}

const NumericInputFormGroup = forwardRef<
  HTMLInputElement,
  INumericInputFormGroupProps
>(function NumericInputFormGroup(props, ref) {
  const { hasError, helperText, id, label, readOnly } = props
  const idReadOnly = `${id}-readOnly`
  return (
    <FormGroup
      helperText={helperText}
      intent={hasError ? 'danger' : undefined}
      label={label}
      labelFor={readOnly ? idReadOnly : id}
    >
      <NumericInput {...props} id={id} idReadOnly={idReadOnly} ref={ref} />
    </FormGroup>
  )
})

interface IProps {
  clearElectionResults: () => void
  editable: boolean
  enableElectionResultsEditing: () => void
  planAudit: (electionResultsFormState: IElectionResultsFormState) => void
}

const ElectionResultsCard: React.FC<IProps> = ({
  clearElectionResults,
  editable,
  enableElectionResultsEditing,
  planAudit,
}) => {
  const { confirm, confirmProps } = useConfirm()
  const { isMobileWidth, isTabletWidth, isDesktopWidth } = useCssBreakpoints()
  const {
    control,
    formState,
    getValues,
    handleSubmit,
    register,
    reset: resetForm,
    trigger,
    watch,
  } = useForm<IElectionResultsFormState>({
    defaultValues: constructInitialElectionResults(),
  })
  const { errors, isSubmitted, isSubmitting, touched } = formState
  const {
    append: addCandidate,
    fields: candidateFields,
    remove: removeCandidate,
  } = useFieldArray<ICandidateFormState>({
    control,
    name: 'candidates',
  })

  const validateAllCandidateNameFields = () => {
    if (isSubmitted) {
      trigger(
        [...Array(candidateFields.length).keys()].map(
          i => `candidates[${i}].name`
        )
      )
    }
  }

  const validateAllCandidateVotesFields = () => {
    if (isSubmitted) {
      trigger(
        [...Array(candidateFields.length).keys()].map(
          i => `candidates[${i}].votes`
        )
      )
    }
  }

  return (
    <>
      <Container data-testid="electionResultsCard" elevation={1}>
        <Heading>Election Results</Heading>

        <CandidatesTable>
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Votes</th>
            </tr>
          </thead>
          <tbody>
            {candidateFields.map((candidateField, i) => (
              <tr key={candidateField.id}>
                <td>
                  <FormGroup
                    helperText={
                      <ErrorMessage
                        errors={errors}
                        name={`candidates[${i}].name`}
                        render={({ message }) => message}
                      />
                    }
                    intent={errors.candidates?.[i]?.name && 'danger'}
                  >
                    <input
                      aria-label={`Candidate ${i + 1} Name`}
                      className={classnames(
                        Classes.INPUT,
                        errors.candidates?.[i]?.name && Classes.INTENT_DANGER
                      )}
                      defaultValue={`Candidate ${i + 1}`}
                      name={`candidates[${i}].name`}
                      onChange={validateAllCandidateNameFields}
                      onFocus={() => {
                        const self = document.querySelector<HTMLInputElement>(
                          `input[name="candidates[${i}].name"]`
                        )
                        // Auto-select the default candidate name for easy replacement on first
                        // focus
                        if (self && !touched.candidates?.[i]?.name) {
                          self.select()
                        }
                      }}
                      placeholder="Candidate name"
                      readOnly={!editable}
                      ref={register({
                        required: 'Required',
                        validate: () => {
                          const { candidates } = getValues()
                          const allCandidatesHaveNames = candidates.every(
                            candidate => candidate.name
                          )
                          const candidateNames = candidates.map(
                            candidate => candidate.name
                          )
                          if (
                            // No need to display this message for all candidate name inputs
                            i === 0 &&
                            allCandidatesHaveNames &&
                            new Set(candidateNames).size < candidates.length
                          ) {
                            return 'Candidates must have unique names'
                          }
                          return true
                        },
                      })}
                    />
                  </FormGroup>
                </td>
                <td>
                  <FormGroup
                    helperText={
                      <ErrorMessage
                        errors={errors}
                        name={`candidates[${i}].votes`}
                        render={({ message }) => message}
                      />
                    }
                    intent={errors.candidates?.[i]?.votes && 'danger'}
                  >
                    <CandidateVotesInputAndRemoveButtonContainer>
                      <NumericInput
                        aria-label={`Candidate ${i + 1} Votes`}
                        hasError={Boolean(errors.candidates?.[i]?.votes)}
                        name={`candidates[${i}].votes`}
                        onChange={validateAllCandidateVotesFields}
                        placeholder="0"
                        readOnly={!editable}
                        ref={register({
                          min: minValueRule(0),
                          max: maxValueRule,
                          pattern: numericValidationRule,
                          required: 'Required',
                          validate: () => {
                            if (
                              // No need to display this message for all candidate votes inputs
                              i === 0 &&
                              getValues().candidates.every(
                                candidate => (candidate.votes || 0) <= 0
                              )
                            ) {
                              return 'At least 1 candidate must have greater than 0 votes'
                            }
                            return true
                          },
                          valueAsNumber: true,
                        })}
                        value={
                          watch<string, number | null>(
                            `candidates[${i}].votes`
                          ) || 0
                        }
                      />
                      <Button
                        aria-label={`Remove Candidate ${i + 1}`}
                        disabled={!editable || candidateFields.length === 2}
                        icon="delete"
                        intent={editable ? 'danger' : undefined}
                        minimal
                        onClick={() => removeCandidate(i)}
                      />
                    </CandidateVotesInputAndRemoveButtonContainer>
                  </FormGroup>
                </td>
              </tr>
            ))}
            <tr>
              <td>
                <Button
                  aria-label={isMobileWidth ? 'Add Candidate' : undefined}
                  disabled={!editable}
                  icon="plus"
                  onClick={() => addCandidate(constructNewCandidate())}
                >
                  {(isTabletWidth || isDesktopWidth) && 'Add Candidate'}
                </Button>
              </td>
              <td />
            </tr>
            <tr>
              <td>
                <NumericInputFormGroup
                  hasError={Boolean(errors.numWinners)}
                  helperText={
                    <ErrorMessage
                      errors={errors}
                      name="numWinners"
                      render={({ message }) => message}
                    />
                  }
                  id="numWinners"
                  label="Number of Winners"
                  name="numWinners"
                  placeholder="0"
                  readOnly={!editable}
                  ref={register({
                    min: minValueRule(1),
                    max: maxValueRule,
                    pattern: numericValidationRule,
                    required: 'Required',
                    validate: value => {
                      if (value >= getValues().candidates.length) {
                        return 'Must be less than number of candidates'
                      }
                      return true
                    },
                    valueAsNumber: true,
                  })}
                  value={watch('numWinners') || 0}
                />
              </td>
              <td>
                <NumericInputFormGroup
                  hasError={Boolean(errors.totalBallotsCast)}
                  helperText={
                    <ErrorMessage
                      errors={errors}
                      name="totalBallotsCast"
                      render={({ message }) => message}
                    />
                  }
                  id="totalBallotsCast"
                  label="Total Ballots Cast"
                  name="totalBallotsCast"
                  placeholder="0"
                  readOnly={!editable}
                  ref={register({
                    min: minValueRule(1),
                    max: maxValueRule,
                    pattern: numericValidationRule,
                    required: 'Required',
                    valueAsNumber: true,
                  })}
                  value={watch('totalBallotsCast') || 0}
                />
              </td>
            </tr>
          </tbody>
        </CandidatesTable>

        <CardActionsRow>
          <Button
            large
            onClick={() =>
              confirm({
                title: 'Confirm',
                description: 'Are you sure you want to clear and start over?',
                yesButtonLabel: 'Clear',
                onYesClick: () => {
                  resetForm()
                  clearElectionResults()
                },
              })
            }
          >
            Clear
          </Button>
          {editable ? (
            <Button
              intent="primary"
              large
              loading={isSubmitting}
              onClick={handleSubmit(planAudit)}
            >
              Plan Audit
            </Button>
          ) : (
            <Button large onClick={enableElectionResultsEditing}>
              Edit
            </Button>
          )}
        </CardActionsRow>
      </Container>
      <Confirm {...confirmProps} />
    </>
  )
}

export default ElectionResultsCard
