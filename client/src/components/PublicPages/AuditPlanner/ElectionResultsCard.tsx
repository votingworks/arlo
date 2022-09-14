import React from 'react'
import styled from 'styled-components'
import { Button, Card, Classes, Colors, H2 } from '@blueprintjs/core'
import { useFieldArray, useForm } from 'react-hook-form'

import { Confirm, useConfirm } from '../../Atoms/Confirm'
import {
  constructInitialElectionResults,
  constructNewCandidate,
  ICandidate,
  IElectionResults,
} from './electionResults'
import { StyledTable } from '../../Atoms/Table'

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
  }
`

const CandidateContainer = styled.div`
  display: flex;

  .bp3-button {
    margin-right: 8px;
  }
  .bp3-input-group {
    flex-grow: 1;
  }
`

const VotesContainer = styled.div`
  display: flex;
`

const AdditionalInputsRow = styled.div`
  display: flex;
  margin-bottom: 16px;
  margin-left: 16px;
`

const AdditionalInputContainer = styled.div`
  align-items: start;
  display: flex;
  flex-direction: column;
  flex-grow: 1;

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

  const { control, handleSubmit, register, reset } = useForm<IElectionResults>({
    defaultValues: constructInitialElectionResults(),
  })
  const {
    append: addCandidate,
    fields: candidates,
    remove: removeCandidate,
  } = useFieldArray<ICandidate>({
    control,
    name: 'candidates',
  })

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
              {candidates.map((candidate, i) => (
                <tr key={candidate.id}>
                  <td>
                    <CandidateContainer>
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
                        defaultValue={candidate.name}
                        name={`candidates[${i}].name`}
                        placeholder="Candidate name"
                        readOnly={!editable}
                        ref={register()}
                      />
                    </CandidateContainer>
                  </td>
                  <td>
                    <VotesContainer>
                      <input
                        aria-label={`Candidate ${i} Votes`}
                        className={Classes.INPUT}
                        defaultValue={`${candidate.votes}`}
                        name={`candidates[${i}].votes`}
                        placeholder="0"
                        readOnly={!editable}
                        ref={register({ valueAsNumber: true })}
                        type="number"
                      />
                    </VotesContainer>
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
                  ref={register({ valueAsNumber: true })}
                  type="number"
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
                  ref={register({ valueAsNumber: true })}
                  type="number"
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
