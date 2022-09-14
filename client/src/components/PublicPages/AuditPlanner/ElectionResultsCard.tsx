import React from 'react'
import styled from 'styled-components'
import { Button, Card, Classes, Colors, H2 } from '@blueprintjs/core'
import { ErrorMessage } from '@hookform/error-message'
import { useFieldArray, useForm } from 'react-hook-form'

import { Confirm, useConfirm } from '../../Atoms/Confirm'
import {
  constructInitialElectionResults,
  constructNewCandidate,
  ICandidate,
  IElectionResults,
} from './electionResults'
import { StyledTable } from '../../Atoms/Table'
import { sum } from '../../../utils/number'

const Container = styled(Card)`
  padding: 0;
`

const InnerContainer = styled.div`
  padding: 24px;

  .bp3-input[readonly] {
    background: transparent;
    box-shadow: none;
  }
`

const Heading = styled(H2)`
  margin-bottom: 24px;
`

const CandidatesTable = styled(StyledTable)`
  margin-bottom: 24px;

  th {
    font-size: 20px;
    padding: 16px;
  }
  td {
    padding: 16px;
    vertical-align: top;
  }
`

const CandidateNameContainer = styled.td`
  .bp3-input {
    width: 100%;
  }
`

const AdditionalInputsRow = styled.div`
  display: flex;
  margin-bottom: 16px;
`

const AdditionalInputContainer = styled.div`
  margin-left: 16px;
  width: 50%;

  label > span {
    color: ${Colors.DARK_GRAY5};
    display: block;
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 12px;
  }
`

const CardActionsRow = styled.div`
  display: flex;
`

const CardAction = styled(Button)`
  &.bp3-button {
    border-radius: 0;
    border-top: 1px solid ${Colors.LIGHT_GRAY3};
    box-shadow: none;
    font-size: 20px;
    min-height: 60px;
    width: 50%;
  }
  &.bp3-button:focus {
    z-index: 1; // Ensures that focus outlines aren't covered
  }
  &.bp3-button:first-child {
    border-bottom-left-radius: 3px;
  }
  &.bp3-button:last-child {
    border-bottom-right-radius: 3px;
  }
  &.bp3-button:not(:last-child) {
    border-right: 1px solid ${Colors.LIGHT_GRAY3};
  }
`

const InputErrorText = styled.p`
  color: ${Colors.RED1};
  margin-bottom: 0;
  margin-left: 4px;
  margin-top: 8px;
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
  const { errors } = formState
  const {
    append: addCandidate,
    fields: candidateFields,
    remove: removeCandidate,
  } = useFieldArray<ICandidate>({
    control,
    name: 'candidates',
  })

  const validateAllCandidateVotesFields = () => {
    trigger(
      [...Array(candidateFields.length).keys()].map(
        i => `candidates[${i}].votes`
      )
    )
  }

  return (
    <>
      <Container data-testid="election-results-card">
        <InnerContainer>
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
                  <CandidateNameContainer>
                    {i >= 2 && (
                      <Button
                        aria-label={`Remove Candidate ${i}`}
                        disabled={!editable}
                        icon="minus"
                        onClick={() => removeCandidate(i)}
                      />
                    )}
                    <input
                      aria-label={`Candidate ${i} Name`}
                      className={Classes.INPUT}
                      defaultValue={candidateField.name}
                      name={`candidates[${i}].name`}
                      placeholder="Candidate name"
                      readOnly={!editable}
                      ref={register({
                        required: 'Name is required for all candidates.',
                      })}
                    />
                    <ErrorMessage
                      errors={errors}
                      name={`candidates[${i}].name`}
                      render={({ message }) => (
                        <InputErrorText>{message}</InputErrorText>
                      )}
                    />
                  </CandidateNameContainer>
                  <td>
                    <input
                      aria-label={`Candidate ${i} Votes`}
                      className={Classes.INPUT}
                      defaultValue={`${candidateField.votes}`}
                      name={`candidates[${i}].votes`}
                      onChange={validateAllCandidateVotesFields}
                      placeholder="0"
                      readOnly={!editable}
                      ref={register({
                        min: {
                          value: 0,
                          message:
                            'Candidate vote counts cannot be less than 0.',
                        },
                        required: 'Vote count is required for all candidates.',
                        validate: () => {
                          if (
                            getValues().candidates.every(
                              candidate => candidate.votes <= 0
                            )
                          ) {
                            return 'At least 1 candidate must have greater than 0 votes.'
                          }
                          return true
                        },
                        valueAsNumber: true,
                      })}
                      type="number"
                    />
                    <ErrorMessage
                      errors={errors}
                      name={`candidates[${i}].votes`}
                      render={({ message }) => (
                        <InputErrorText>{message}</InputErrorText>
                      )}
                    />
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
            </tbody>
          </CandidatesTable>

          <AdditionalInputsRow>
            <AdditionalInputContainer>
              <label>
                <span>Number of Winners</span>
                <input
                  className={Classes.INPUT}
                  name="numWinners"
                  placeholder="0"
                  readOnly={!editable}
                  ref={register({
                    min: {
                      value: 1,
                      message: 'Number of winners cannot be less than 1.',
                    },
                    required: 'Number of winners is required.',
                    validate: value => {
                      if (value > getValues().candidates.length) {
                        return 'Number of winners cannot be greater than the number of candidates.'
                      }
                      return true
                    },
                    valueAsNumber: true,
                  })}
                  type="number"
                />
                <ErrorMessage
                  errors={errors}
                  name="numWinners"
                  render={({ message }) => (
                    <InputErrorText>{message}</InputErrorText>
                  )}
                />
              </label>
            </AdditionalInputContainer>
            <AdditionalInputContainer>
              <label>
                <span>Total Ballots Cast</span>
                <input
                  className={Classes.INPUT}
                  name="totalBallotsCast"
                  placeholder="0"
                  readOnly={!editable}
                  ref={register({
                    required: 'Total ballots cast is required.',
                    validate: value => {
                      if (
                        value <
                        sum(
                          getValues().candidates.map(
                            candidate => candidate.votes
                          )
                        )
                      ) {
                        return 'Total ballots cast cannot be less than the sum of candidate votes.'
                      }
                      return true
                    },
                    valueAsNumber: true,
                  })}
                  type="number"
                />
                <ErrorMessage
                  errors={errors}
                  name="totalBallotsCast"
                  render={({ message }) => (
                    <InputErrorText>{message}</InputErrorText>
                  )}
                />
              </label>
            </AdditionalInputContainer>
          </AdditionalInputsRow>
        </InnerContainer>

        <CardActionsRow>
          <CardAction
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
          </CardAction>
          {editable ? (
            <CardAction onClick={handleSubmit(planAudit)}>
              Plan Audit
            </CardAction>
          ) : (
            <CardAction onClick={enableEditing}>Edit</CardAction>
          )}
        </CardActionsRow>
      </Container>
      <Confirm {...confirmProps} />
    </>
  )
}

export default ElectionResultsCard
