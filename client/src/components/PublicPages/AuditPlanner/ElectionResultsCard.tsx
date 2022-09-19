import classnames from 'classnames'
import React from 'react'
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
import { sum } from '../../../utils/number'

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

const numericValidationRule = {
  message: 'Can only contain numeric characters',
  value: /^[0-9]+$/,
}

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

  const {
    control,
    formState,
    getValues,
    handleSubmit,
    register,
    reset: resetForm,
    trigger,
  } = useForm<IElectionResultsFormState>({
    defaultValues: constructInitialElectionResults(),
  })
  const { errors, isSubmitted, isSubmitting } = formState
  const {
    append: addCandidate,
    fields: candidateFields,
    remove: removeCandidate,
  } = useFieldArray<ICandidateFormState>({
    control,
    name: 'candidates',
  })

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
                      aria-label={`Candidate ${i} Name`}
                      className={classnames(
                        Classes.INPUT,
                        errors.candidates?.[i]?.name && Classes.INTENT_DANGER
                      )}
                      name={`candidates[${i}].name`}
                      placeholder="Candidate name"
                      readOnly={!editable}
                      ref={register({
                        required: 'Required',
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
                      <input
                        aria-label={`Candidate ${i} Votes`}
                        className={classnames(
                          Classes.INPUT,
                          errors.candidates?.[i]?.votes && Classes.INTENT_DANGER
                        )}
                        name={`candidates[${i}].votes`}
                        onChange={validateAllCandidateVotesFields}
                        placeholder="0"
                        readOnly={!editable}
                        ref={register({
                          min: {
                            message: 'Cannot be less than 0',
                            value: 0,
                          },
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
                        type="number"
                      />
                      <Button
                        aria-label={`Remove Candidate ${i}`}
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
                  disabled={!editable}
                  icon="plus"
                  onClick={() => addCandidate(constructNewCandidate())}
                >
                  Add Candidate
                </Button>
              </td>
              <td />
            </tr>
            <tr>
              <td>
                <FormGroup
                  helperText={
                    <ErrorMessage
                      errors={errors}
                      name="numWinners"
                      render={({ message }) => message}
                    />
                  }
                  intent={errors.numWinners && 'danger'}
                  label="Number of Winners"
                  labelFor="numWinners"
                >
                  <input
                    className={classnames(
                      Classes.INPUT,
                      errors.numWinners && Classes.INTENT_DANGER
                    )}
                    id="numWinners"
                    name="numWinners"
                    placeholder="0"
                    readOnly={!editable}
                    ref={register({
                      min: {
                        message: 'Cannot be less than 1',
                        value: 1,
                      },
                      pattern: numericValidationRule,
                      required: 'Required',
                      validate: value => {
                        if (value > getValues().candidates.length) {
                          return 'Cannot be greater than number of candidates'
                        }
                        return true
                      },
                      valueAsNumber: true,
                    })}
                    type="number"
                  />
                </FormGroup>
              </td>
              <td>
                <FormGroup
                  helperText={
                    <ErrorMessage
                      errors={errors}
                      name="totalBallotsCast"
                      render={({ message }) => message}
                    />
                  }
                  intent={errors.totalBallotsCast && 'danger'}
                  label="Total Ballots Cast"
                  labelFor="totalBallotsCast"
                >
                  <input
                    className={classnames(
                      Classes.INPUT,
                      errors.totalBallotsCast && Classes.INTENT_DANGER
                    )}
                    id="totalBallotsCast"
                    name="totalBallotsCast"
                    placeholder="0"
                    readOnly={!editable}
                    ref={register({
                      pattern: numericValidationRule,
                      required: 'Required',
                      validate: value => {
                        if (
                          value <
                          sum(
                            getValues().candidates.map(
                              candidate => candidate.votes || 0
                            )
                          )
                        ) {
                          return 'Cannot be less than sum of candidate votes'
                        }
                        return true
                      },
                      valueAsNumber: true,
                    })}
                    type="number"
                  />
                </FormGroup>
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
                  enableElectionResultsEditing()
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
