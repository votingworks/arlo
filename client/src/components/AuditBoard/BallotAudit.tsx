import React, { useState } from 'react'
import styled from 'styled-components'
import { Button, Colors, H3, H4, TextArea } from '@blueprintjs/core'
import {
  BallotRow,
  ContestCard,
  ProgressActions,
  BlockCheckboxes,
  LeftCheckboxes,
  RightCheckboxes,
  SubTitle,
  FlushDivider,
} from './Atoms'
import FormButton from '../Atoms/Form/FormButton'
import { Interpretation, IContest } from '../../types'
import { IBallot } from '../JurisdictionAdmin/useBallots'
import BlockCheckbox from './BlockCheckbox'
import {
  ballotInterpretationToFormState,
  IBallotInterpretationFormState,
  INVALID_WRITE_IN,
} from './ballotInterpretation'

const BallotMainRow = styled.div`
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
`

const BallotRowValue = styled(H4)`
  margin-bottom: 0;
  color: ${Colors.BLACK};
`

const NotFoundButton = styled(Button)`
  border-radius: 5px;
  width: 13.5em;
  font-weight: 600;
  &.bp3-button.bp3-large {
    height: 2em;
    min-height: auto;
    font-size: 14px;
  }
  @media only screen and (max-width: 767px) {
    width: auto;
  }
`

const NoteField = styled(TextArea)`
  &.bp3-input {
    height: 100px;
  }
`

const ContestTitle = styled(H3)`
  margin-bottom: 20px;
  font-weight: 500;
`

const SubmitButton = styled(FormButton)`
  border-radius: 5px;
  width: 12em;
  font-weight: 600;

  @media only screen and (max-width: 767px) {
    width: auto;
  }
`

function constructEmptyInterpretation(
  contest: IContest
): IBallotInterpretationFormState {
  return {
    choiceIds: [],
    comment: null,
    contestId: contest.id,
    isBlankVoteChecked: false,
    isContestNotOnBallotChecked: false,
    isInvalidWriteInChecked: false,
  }
}

function hasInterpretationBeenSpecified({
  choiceIds,
  isBlankVoteChecked,
  isContestNotOnBallotChecked,
  isInvalidWriteInChecked,
}: IBallotInterpretationFormState): boolean {
  return (
    choiceIds.length > 0 ||
    isBlankVoteChecked ||
    isContestNotOnBallotChecked ||
    isInvalidWriteInChecked
  )
}

interface IProps {
  ballot: IBallot
  contests: IContest[]
  confirmSelections: (interpretations: IBallotInterpretationFormState[]) => void
  confirmBallotNotFound: () => void
  previousBallot: () => void
  // eslint-disable-next-line react/no-unused-prop-types
  key: string // Require a key (ballot ID) to force a state reset whenever a new ballot is toggled
}

const BallotAudit = ({
  ballot,
  contests,
  confirmSelections,
  confirmBallotNotFound,
  previousBallot,
}: IProps): React.ReactElement => {
  const initialInterpretations = contests.map(contest => {
    const ballotInterpretation = ballot.interpretations.find(
      i => i.contestId === contest.id
    )
    return ballotInterpretation
      ? ballotInterpretationToFormState(ballotInterpretation)
      : constructEmptyInterpretation(contest)
  })
  const [interpretations, setInterpretations] = useState(initialInterpretations)
  const onSubmit = () => confirmSelections(interpretations)
  const resetForm = () => setInterpretations(initialInterpretations)

  return (
    <>
      <BallotMainRow>
        {ballot.batch.container && (
          <div>
            <SubTitle>Container</SubTitle>
            <BallotRowValue>{ballot.batch.container}</BallotRowValue>
          </div>
        )}
        {ballot.batch.tabulator && (
          <div>
            <SubTitle>Tabulator</SubTitle>
            <BallotRowValue>{ballot.batch.tabulator}</BallotRowValue>
          </div>
        )}
        <div>
          <SubTitle>Batch</SubTitle>
          <BallotRowValue>{ballot.batch.name}</BallotRowValue>
        </div>
        <div>
          <SubTitle>Ballot Number</SubTitle>
          <BallotRowValue>{ballot.position}</BallotRowValue>
        </div>
        {ballot.imprintedId !== undefined && (
          <div>
            <SubTitle>Imprinted ID</SubTitle>
            <BallotRowValue>{ballot.imprintedId}</BallotRowValue>
          </div>
        )}
        <div>
          <NotFoundButton
            onClick={() => {
              resetForm()
              confirmBallotNotFound()
            }}
            intent="danger"
            large
          >
            Ballot Not Found
          </NotFoundButton>
        </div>
      </BallotMainRow>
      <FlushDivider />
      <BallotRow>
        <div className="ballot-main">
          <SubTitle>Ballot Contests</SubTitle>
          <form>
            {contests.map((contest, i) => (
              <BallotAuditContest
                key={contest.id}
                contest={contest}
                interpretation={interpretations[i]}
                setInterpretation={newInterpretation => {
                  const newInterpretations = [...interpretations]
                  newInterpretations[i] = newInterpretation
                  setInterpretations(newInterpretations)
                }}
              />
            ))}
            <ProgressActions>
              <SubmitButton
                type="submit"
                onClick={e => {
                  e.preventDefault()
                  onSubmit()
                }}
                intent="success"
                large
                disabled={!interpretations.some(hasInterpretationBeenSpecified)}
              >
                Submit Selections
              </SubmitButton>
              <Button onClick={previousBallot} intent="none">
                Back
              </Button>
            </ProgressActions>
          </form>
        </div>
      </BallotRow>
    </>
  )
}

interface IBallotAuditContestProps {
  contest: IContest
  interpretation: IBallotInterpretationFormState
  setInterpretation: (i: IBallotInterpretationFormState) => void
}

const BallotAuditContest = ({
  contest,
  interpretation,
  setInterpretation,
}: IBallotAuditContestProps): React.ReactElement => {
  const {
    choiceIds,
    comment,
    isBlankVoteChecked,
    isContestNotOnBallotChecked,
    isInvalidWriteInChecked,
  } = interpretation

  const onCheckboxClick = (value: string) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { checked } = e.currentTarget
    if (value === Interpretation.BLANK) {
      setInterpretation({
        ...interpretation,
        choiceIds: [],
        isBlankVoteChecked: checked,
        isContestNotOnBallotChecked: false,
        isInvalidWriteInChecked: false,
      })
    } else if (value === Interpretation.CONTEST_NOT_ON_BALLOT) {
      setInterpretation({
        ...interpretation,
        choiceIds: [],
        isBlankVoteChecked: false,
        isContestNotOnBallotChecked: checked,
        isInvalidWriteInChecked: false,
      })
    } else if (value === INVALID_WRITE_IN) {
      setInterpretation({
        ...interpretation,
        isBlankVoteChecked: false,
        isContestNotOnBallotChecked: false,
        isInvalidWriteInChecked: checked,
      })
    } else {
      const newChoiceIds = checked
        ? [...choiceIds, value]
        : choiceIds.filter(v => v !== value)
      setInterpretation({
        ...interpretation,
        choiceIds: newChoiceIds,
        isBlankVoteChecked: false,
        isContestNotOnBallotChecked: false,
      })
    }
  }

  return (
    <ContestCard>
      <BlockCheckboxes>
        <LeftCheckboxes>
          <ContestTitle>{contest.name}</ContestTitle>
          {contest.choices.map(c => (
            <BlockCheckbox
              key={c.id}
              handleChange={onCheckboxClick(c.id)}
              checked={choiceIds.includes(c.id)}
              label={c.name}
            />
          ))}
        </LeftCheckboxes>
        <RightCheckboxes>
          <BlockCheckbox
            handleChange={onCheckboxClick(Interpretation.BLANK)}
            checked={isBlankVoteChecked}
            label="Blank Vote"
            small
          />
          <BlockCheckbox
            handleChange={onCheckboxClick(Interpretation.CONTEST_NOT_ON_BALLOT)}
            checked={isContestNotOnBallotChecked}
            label="Not on Ballot"
            small
          />
          <BlockCheckbox
            handleChange={onCheckboxClick(INVALID_WRITE_IN)}
            checked={isInvalidWriteInChecked}
            label="Invalid Write-In"
            small
          />
          <NoteField
            name={`comment-${contest.name}`}
            value={comment || ''}
            placeholder="Add Note"
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
              setInterpretation({
                ...interpretation,
                comment: e.currentTarget.value,
              })
            }
          />
        </RightCheckboxes>
      </BlockCheckboxes>
    </ContestCard>
  )
}

export default BallotAudit
