import React from 'react'
import styled from 'styled-components'
import { Button, Card, Colors, H2, InputGroup } from '@blueprintjs/core'

import IntegerInput from './IntegerInput'
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
  electionResults: IElectionResults
  enableEditing: () => void
  planAudit: () => void
  setElectionResults: (electionResults: IElectionResults) => void
}

const ElectionResultsCard: React.FC<IProps> = ({
  editable,
  electionResults,
  enableEditing,
  planAudit,
  setElectionResults,
}) => {
  const { candidates, numWinners, totalBallotsCast } = electionResults
  const { confirm, confirmProps } = useConfirm()

  const setCandidate = (candidateIndex: number, candidate: ICandidate) => {
    setElectionResults({
      ...electionResults,
      candidates: [
        ...candidates.slice(0, candidateIndex),
        candidate,
        ...candidates.slice(candidateIndex + 1),
      ],
    })
  }

  const addCandidate = () => {
    setElectionResults({
      ...electionResults,
      candidates: [...candidates, constructNewCandidate(candidates.length)],
    })
  }

  const removeCandidate = (candidateIndex: number) => {
    setElectionResults({
      ...electionResults,
      candidates: [
        ...candidates.slice(0, candidateIndex),
        ...candidates.slice(candidateIndex + 1),
      ],
    })
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
              {electionResults.candidates.map((candidate, i) => (
                <tr key={candidate.id}>
                  <td>
                    {editable ? (
                      <CandidateContainer>
                        {i >= 2 && (
                          <Button
                            aria-label={`Remove Candidate ${i}`}
                            icon="minus"
                            onClick={() => removeCandidate(i)}
                          />
                        )}
                        <InputGroup
                          aria-label={`Candidate ${i} Name`}
                          name={`candidate[${i}].name`}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                            setCandidate(i, {
                              ...candidate,
                              name: e.target.value,
                            })
                          }
                          placeholder="Candidate name"
                          value={candidate.name}
                        />
                      </CandidateContainer>
                    ) : (
                      candidate.name
                    )}
                  </td>
                  <td>
                    {editable ? (
                      <VotesContainer>
                        <IntegerInput
                          ariaLabel={`Candidate ${i} Votes`}
                          name={`candidate[${i}].votes`}
                          onChange={newValue =>
                            setCandidate(i, {
                              ...candidate,
                              votes: newValue,
                            })
                          }
                          value={candidate.votes}
                        />
                      </VotesContainer>
                    ) : (
                      candidate.votes
                    )}
                  </td>
                </tr>
              ))}
              {editable && (
                <tr>
                  <td>
                    <Button icon="plus" onClick={addCandidate}>
                      Add Candidate
                    </Button>
                  </td>
                  <td />
                </tr>
              )}
            </tbody>
          </CandidatesTable>

          <AdditionalInputsRow>
            <AdditionalInputContainer>
              <label>
                <span>Number of Winners</span>
                {editable ? (
                  <IntegerInput
                    name="numberOfWinners"
                    onChange={newValue =>
                      setElectionResults({
                        ...electionResults,
                        numWinners: newValue,
                      })
                    }
                    value={numWinners}
                  />
                ) : (
                  numWinners
                )}
              </label>
            </AdditionalInputContainer>
            <AdditionalInputContainer>
              <label>
                <span>Total Ballots Cast</span>
                {editable ? (
                  <IntegerInput
                    name="totalBallotsCast"
                    onChange={newValue =>
                      setElectionResults({
                        ...electionResults,
                        totalBallotsCast: newValue,
                      })
                    }
                    value={totalBallotsCast}
                  />
                ) : (
                  totalBallotsCast
                )}
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
                  setElectionResults(constructInitialElectionResults())
                  enableEditing()
                },
              })
            }
          >
            Clear
          </CardAction>
          {editable ? (
            <CardAction onClick={planAudit}>Plan Audit</CardAction>
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
