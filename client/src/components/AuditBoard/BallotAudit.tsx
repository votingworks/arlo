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
import { IBallotInterpretation, Interpretation, IContest } from '../../types'
import { IBallot } from '../JurisdictionAdmin/useBallots'
import BlockCheckbox from './BlockCheckbox'

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
): IBallotInterpretation {
  return {
    contestId: contest.id,
    interpretation: null,
    choiceIds: [],
    comment: null,
    hasInvalidWriteIn: false,
  }
}

interface IProps {
  ballot: IBallot
  contests: IContest[]
  confirmSelections: (interpretations: IBallotInterpretation[]) => void
  confirmBallotNotFound: () => void
  previousBallot: () => void
  // eslint-disable-next-line react/no-unused-prop-types
  key: string // Require a key (ballot ID) to force a state reset whenever a new ballot is toggled
}

const BallotAudit: React.FC<IProps> = ({
  ballot,
  contests,
  confirmSelections,
  confirmBallotNotFound,
  previousBallot,
}: IProps) => {
  const initialInterpretations = contests.map(
    contest =>
      ballot.interpretations.find(i => i.contestId === contest.id) ||
      constructEmptyInterpretation(contest)
  )
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
                disabled={
                  !(
                    interpretations.filter(
                      ({ interpretation }) => interpretation != null
                    ).length > 0
                  )
                }
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
  interpretation: IBallotInterpretation
  setInterpretation: (i: IBallotInterpretation) => void
}

export const INVALID_WRITE_IN = 'INVALID_WRITE_IN'

const BallotAuditContest = ({
  contest,
  interpretation,
  setInterpretation,
}: IBallotAuditContestProps) => {
  const onCheckboxClick = (value: string) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { checked } = e.currentTarget
    if (
      value === Interpretation.BLANK ||
      value === Interpretation.CANT_AGREE ||
      value === Interpretation.CONTEST_NOT_ON_BALLOT
    ) {
      setInterpretation({
        ...interpretation,
        interpretation: checked ? value : null,
        choiceIds: [],
        hasInvalidWriteIn: false,
      })
    } else if (value === INVALID_WRITE_IN) {
      let newInterpretation: Interpretation | null
      if (interpretation.choiceIds.length > 0) {
        newInterpretation = Interpretation.VOTE
      } else if (checked) {
        newInterpretation = Interpretation.BLANK
      } else {
        newInterpretation = null
      }
      setInterpretation({
        ...interpretation,
        interpretation: newInterpretation,
        hasInvalidWriteIn: checked,
      })
    } else {
      const choiceIds = checked
        ? [...interpretation.choiceIds, value]
        : interpretation.choiceIds.filter(v => v !== value)
      let newInterpretation: Interpretation | null
      if (choiceIds.length > 0) {
        newInterpretation = Interpretation.VOTE
      } else if (interpretation.hasInvalidWriteIn) {
        newInterpretation = Interpretation.BLANK
      } else {
        newInterpretation = null
      }
      setInterpretation({
        ...interpretation,
        interpretation: newInterpretation,
        choiceIds,
      })
    }
  }

  const isVote = interpretation.interpretation === Interpretation.VOTE

  return (
    <ContestCard>
      <BlockCheckboxes>
        <LeftCheckboxes>
          <ContestTitle>{contest.name}</ContestTitle>
          {contest.choices.map(c => (
            <BlockCheckbox
              key={c.id}
              handleChange={onCheckboxClick(c.id)}
              checked={isVote && interpretation.choiceIds.includes(c.id)}
              label={c.name}
            />
          ))}
        </LeftCheckboxes>
        <RightCheckboxes>
          <BlockCheckbox
            handleChange={onCheckboxClick(Interpretation.BLANK)}
            checked={
              interpretation.interpretation === Interpretation.BLANK &&
              !interpretation.hasInvalidWriteIn
            }
            label="Blank Vote"
            small
          />
          <BlockCheckbox
            handleChange={onCheckboxClick(Interpretation.CONTEST_NOT_ON_BALLOT)}
            checked={
              interpretation.interpretation ===
              Interpretation.CONTEST_NOT_ON_BALLOT
            }
            label="Not on Ballot"
            small
          />
          <BlockCheckbox
            handleChange={onCheckboxClick(INVALID_WRITE_IN)}
            checked={interpretation.hasInvalidWriteIn}
            label="Invalid Write-In"
            small
          />
          <NoteField
            name={`comment-${contest.name}`}
            value={interpretation.comment || ''}
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
