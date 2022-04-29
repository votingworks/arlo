import React from 'react'
import { Formik, FormikProps, Field } from 'formik'
import styled from 'styled-components'
import { Button, Colors, H3, H4 } from '@blueprintjs/core'
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
import FormField from '../Atoms/Form/FormField'
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

const NoteField = styled(Field)`
  textarea {
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
  }
}

interface IProps {
  ballot: IBallot
  contests: IContest[]
  confirmSelections: (interpretations: IBallotInterpretation[]) => void
  confirmBallotNotFound: () => void
  previousBallot: () => void
}

const BallotAudit: React.FC<IProps> = ({
  ballot,
  contests,
  confirmSelections,
  confirmBallotNotFound,
  previousBallot,
}: IProps) => {
  const interpretations = contests.map(
    contest =>
      ballot.interpretations.find(i => i.contestId === contest.id) ||
      constructEmptyInterpretation(contest)
  )

  return (
    <Formik
      initialValues={{ interpretations }}
      enableReinitialize
      onSubmit={values => {
        confirmSelections(values.interpretations)
      }}
    >
      {({
        handleSubmit,
        values,
        setFieldValue,
        resetForm,
      }: FormikProps<{ interpretations: IBallotInterpretation[] }>) => {
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
                      interpretation={values.interpretations[i]}
                      setInterpretation={newInterpretation =>
                        setFieldValue(
                          `interpretations[${i}]`,
                          newInterpretation
                        )
                      }
                    />
                  ))}
                  <ProgressActions>
                    <SubmitButton
                      type="submit"
                      onClick={handleSubmit}
                      intent="success"
                      large
                      disabled={
                        !(
                          values.interpretations.filter(
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
      }}
    </Formik>
  )
}

interface IBallotAuditContestProps {
  contest: IContest
  interpretation: IBallotInterpretation
  setInterpretation: (i: IBallotInterpretation) => void
}

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
      })
    } else {
      const choiceIds = checked
        ? [...interpretation.choiceIds, value]
        : interpretation.choiceIds.filter(v => v !== value)
      setInterpretation({
        ...interpretation,
        interpretation: choiceIds.length > 0 ? Interpretation.VOTE : null,
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
            checked={interpretation.interpretation === Interpretation.BLANK}
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
          <NoteField
            name={`comment-${contest.name}`}
            type="textarea"
            component={FormField}
            value={interpretation.comment || ''}
            placeholder="Add Note"
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
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
