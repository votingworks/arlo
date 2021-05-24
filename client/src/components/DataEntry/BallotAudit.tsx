import React from 'react'
import { Formik, FormikProps, Field } from 'formik'
import styled from 'styled-components'
import { H3 } from '@blueprintjs/core'
import {
  BallotRow,
  ContestCard,
  ProgressActions,
  BlockCheckboxes,
  LeftCheckboxes,
  RightCheckboxes,
  SubTitle,
} from './Atoms'
import FormButton from '../Atoms/Form/FormButton'
import { IBallotInterpretation, Interpretation, IContest } from '../../types'
import FormField from '../Atoms/Form/FormField'
import BlockCheckbox from './BlockCheckbox'

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

interface IProps {
  contests: IContest[]
  goReview: () => void
  interpretations: IBallotInterpretation[]
  setInterpretations: (interpretations: IBallotInterpretation[]) => void
  previousBallot: () => void
}

const BallotAudit: React.FC<IProps> = ({
  contests,
  interpretations,
  setInterpretations,
}: IProps) => {
  return (
    <BallotRow>
      <div className="ballot-main">
        <SubTitle>Ballot Contests</SubTitle>
        <Formik
          initialValues={{ interpretations }}
          enableReinitialize
          onSubmit={async values => {
            await setInterpretations(values.interpretations)
          }}
        >
          {({
            handleSubmit,
            values,
            setFieldValue,
          }: FormikProps<{ interpretations: IBallotInterpretation[] }>) => {
            return (
              <form>
                {contests.map((contest, i) => (
                  <BallotAuditContest
                    key={contest.id}
                    contest={contest}
                    interpretation={values.interpretations[i]}
                    setInterpretation={newInterpretation =>
                      setFieldValue(`interpretations[${i}]`, newInterpretation)
                    }
                  />
                ))}
                <ProgressActions>
                  <SubmitButton
                    type="submit"
                    onClick={handleSubmit}
                    intent="success"
                    large
                  >
                    Submit Selections
                  </SubmitButton>
                  {/* <Button onClick={previousBallot} minimal>
                    Back
                  </Button> */}
                </ProgressActions>
              </form>
            )
          }}
        </Formik>
      </div>
    </BallotRow>
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
            label="Blank vote"
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
