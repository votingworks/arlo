import classnames from 'classnames'
import React from 'react'
import styled from 'styled-components'
import {
  Button,
  Card,
  Classes,
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
  ICandidate,
  IElectionResults,
} from './electionResults'
import { sum } from '../../../utils/number'

const Container = styled(Card)`
  padding: 24px;
`

const Heading = styled(H2)`
  margin-bottom: 24px;
`

const CandidatesTable = styled(HTMLTable)`
  margin-bottom: 24px;
  table-layout: fixed;
  width: 100%;

  &.bp3-html-table th {
    font-size: 18px;
    padding: 8px;
  }

  &.bp3-html-table td {
    height: 68px; // Large enough to house candidate inputs plus inline error messages
    padding: 8px;
    vertical-align: top;
  }
  &.bp3-html-table tr:nth-child(1) td {
    height: 76px; // Extra height to accommodate extra top padding
    padding-top: 16px;
  }
  &.bp3-html-table tr:last-child td {
    height: 108px; // Extra height to accommodate input labels
  }

  &.bp3-html-table th:nth-child(3),
  &.bp3-html-table td:nth-child(3) {
    width: 62px; // Large enough to house candidate delete buttons
  }

  &.bp3-html-table .bp3-form-group {
    margin-bottom: 0;
  }

  &.bp3-html-table .bp3-input[readonly] {
    background: transparent;
    box-shadow: none;
  }

  &.bp3-html-table .bp3-label {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 8px;
  }
`

const InputFullWidth = styled.input`
  width: 100%;
`

const CardActionsRow = styled.div`
  display: flex;
  justify-content: end;

  .bp3-button:last-child {
    margin-left: 12px;
  }
`

interface IProps {
  editable: boolean
  enableEditing: () => void
  planAudit: (electionResults: IElectionResults) => void
}

const ElectionResultsCard: React.FC<IProps> = ({
  editable,
  enableEditing,
  planAudit,
}) => {
  const { confirm, confirmProps } = useConfirm()

  const {
    control,
    formState,
    getValues,
    handleSubmit,
    register,
    reset,
    trigger,
  } = useForm<IElectionResults>({
    defaultValues: constructInitialElectionResults(),
  })
  const { errors, isSubmitted } = formState
  const {
    append: addCandidate,
    fields: candidateFields,
    remove: removeCandidate,
  } = useFieldArray<ICandidate>({
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
      <Container data-testid="electionResultsCard">
        <Heading>Election Results</Heading>

        <CandidatesTable>
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Votes</th>
              <th></th>
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
                    <InputFullWidth
                      aria-label={`Candidate ${i} Name`}
                      className={classnames(
                        Classes.INPUT,
                        errors.candidates?.[i]?.name && Classes.INTENT_DANGER
                      )}
                      defaultValue={candidateField.name}
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
                    <input
                      aria-label={`Candidate ${i} Votes`}
                      className={classnames(
                        Classes.INPUT,
                        errors.candidates?.[i]?.votes && Classes.INTENT_DANGER
                      )}
                      defaultValue={`${candidateField.votes}`}
                      name={`candidates[${i}].votes`}
                      onChange={validateAllCandidateVotesFields}
                      placeholder="0"
                      readOnly={!editable}
                      ref={register({
                        min: {
                          value: 0,
                          message: 'Cannot be less than 0',
                        },
                        required: 'Required',
                        validate: () => {
                          if (
                            getValues().candidates.every(
                              candidate => candidate.votes <= 0
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
                  </FormGroup>
                </td>
                <td>
                  {i >= 2 && (
                    <Button
                      aria-label={`Remove Candidate ${i}`}
                      disabled={!editable}
                      icon="delete"
                      intent="danger"
                      minimal
                      onClick={() => removeCandidate(i)}
                    />
                  )}
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
                        value: 1,
                        message: 'Cannot be less than 1',
                      },
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
                    className={Classes.INPUT}
                    id="totalBallotsCast"
                    name="totalBallotsCast"
                    placeholder="0"
                    readOnly={!editable}
                    ref={register({
                      required: 'Required',
                      validate: value => {
                        if (
                          value <
                          sum(
                            getValues().candidates.map(
                              candidate => candidate.votes
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
              <td />
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
                  reset()
                  enableEditing()
                },
              })
            }
          >
            Clear
          </Button>
          {editable ? (
            <Button intent="primary" large onClick={handleSubmit(planAudit)}>
              Plan Audit
            </Button>
          ) : (
            <Button large onClick={enableEditing}>
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
