import React, { useState, useEffect } from 'react'
import { Formik, FormikProps, Field } from 'formik'
import { H4, H3, Button } from '@blueprintjs/core'
import { BallotRow, ContestCard, ProgressActions, FlushDivider } from './Atoms'
import FormButton from '../Atoms/Form/FormButton'
import { IBallotInterpretation, Interpretation, IContest } from '../../types'
import FormField from '../Atoms/Form/FormField'
import BlockCheckbox from './BlockCheckbox'

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
  goReview,
  previousBallot,
}: IProps) => {
  return (
    <BallotRow>
      <div className="ballot-side"></div>
      <div className="ballot-main">
        <H4>Instructions</H4>
        <p>
          Select <strong>all</strong> the candidates/choices below that you see
          marked on the paper ballot.
        </p>
        <p>
          If the voter did not vote in the contest, select &quot;Blank vote/Not
          on Ballot.&quot;
        </p>
        <p>
          If the audit board cannot agree, select &quot;Audit board can&apos;t
          agree.&quot; You may add a comment for additional information about
          the disagreement.
        </p>
        <Formik
          initialValues={{ interpretations }}
          enableReinitialize
          onSubmit={values => {
            setInterpretations(values.interpretations)
            goReview()
          }}
          render={({
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
                  <FormButton
                    type="submit"
                    onClick={handleSubmit}
                    intent="success"
                  >
                    Review
                  </FormButton>
                  <Button onClick={previousBallot} minimal>
                    Back
                  </Button>
                </ProgressActions>
              </form>
            )
          }}
        />
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
  const [commenting, setCommenting] = useState(false)
  useEffect(() => {
    setCommenting(!!interpretation.comment)
  }, [interpretation.comment])

  const toggleCommenting = () => {
    setCommenting(!commenting)
    setInterpretation({ ...interpretation, comment: null })
  }

  const onCheckboxClick = (value: string) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { checked } = e.currentTarget
    if (value === Interpretation.BLANK || value === Interpretation.CANT_AGREE) {
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
      <H3>{contest.name}</H3>
      <FlushDivider />
      {contest.choices.map(c => (
        <BlockCheckbox
          key={c.id}
          handleChange={onCheckboxClick(c.id)}
          checked={isVote && interpretation.choiceIds.includes(c.id)}
          label={c.name}
        />
      ))}
      <BlockCheckbox
        handleChange={onCheckboxClick(Interpretation.CANT_AGREE)}
        gray
        checked={interpretation.interpretation === Interpretation.CANT_AGREE}
        label="Audit board can't agree"
      />
      <BlockCheckbox
        handleChange={onCheckboxClick(Interpretation.BLANK)}
        gray
        checked={interpretation.interpretation === Interpretation.BLANK}
        label="Blank vote/Not on Ballot"
      />
      <Button minimal icon="edit" onClick={toggleCommenting}>
        {commenting ? 'Remove comment' : 'Add comment'}
      </Button>
      {commenting && (
        <Field
          name={`comment-${contest.name}`}
          type="textarea"
          component={FormField}
          value={interpretation.comment || ''}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setInterpretation({
              ...interpretation,
              comment: e.currentTarget.value,
            })
          }
        />
      )}
    </ContestCard>
  )
}

export default BallotAudit
