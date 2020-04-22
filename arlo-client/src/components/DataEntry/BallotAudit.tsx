import React, { useState, useEffect } from 'react'
import { Formik, FormikProps, Field } from 'formik'
import { H4, H3, Button } from '@blueprintjs/core'
import {
  BallotRow,
  FormBlock,
  RadioGroupFlex,
  ProgressActions,
  FlushDivider,
} from './Atoms'
import BlockRadio from './BlockRadio'
import FormButton from '../Form/FormButton'
import { IBallotInterpretation, Interpretation, IContest } from '../../types'
import FormField from '../Form/FormField'

interface IProps {
  contest: IContest
  goReview: () => void
  interpretation: IBallotInterpretation
  setInterpretation: (i: IBallotInterpretation) => void
  previousBallot: () => void
}

const BallotAudit: React.FC<IProps> = ({
  contest,
  interpretation,
  setInterpretation,
  goReview,
  previousBallot,
}: IProps) => {
  const [commenting, setCommenting] = useState(false)
  useEffect(() => {
    setCommenting(!!interpretation.comment)
  }, [interpretation.comment])
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
          If the voter did not vote in the contest, select &quot;Blank vote/no
          mark.&quot;
        </p>
        <p>
          If the audit board cannot agree, select &quot;Audit board can&apos;t
          agree.&quot; You may add a comment for additional information about
          the disagreement.
        </p>
        <Formik
          initialValues={interpretation}
          enableReinitialize
          onSubmit={values => {
            setInterpretation(values)
            goReview()
          }}
          render={({
            handleSubmit,
            values,
            setFieldValue,
          }: FormikProps<IBallotInterpretation>) => {
            // Since the radio button values must be strings, not full objects,
            // we condense our data model for interpretations to strings:
            // - For buttons representing interpretation VOTE (one for each
            // contest choice), the value is interpretation.choiceId
            // - For buttons representing other interpretations (BLANK,
            // CANT_AGREE), the value is interpretation.interpretation

            const radioProps = {
              name: 'interpretation',
              handleChange: (e: React.ChangeEvent<HTMLInputElement>) => {
                const { value } = e.currentTarget
                if (
                  value === Interpretation.BLANK ||
                  value === Interpretation.CANT_AGREE
                ) {
                  setFieldValue('interpretation', value)
                  setFieldValue('choiceId', null)
                } else {
                  setFieldValue('interpretation', Interpretation.VOTE)
                  setFieldValue('choiceId', value)
                }
              },
            }
            const toggleCommenting = () => {
              setCommenting(!commenting)
              setFieldValue('comment', null)
            }

            const isVote = values.interpretation === Interpretation.VOTE

            return (
              <>
                <FormBlock>
                  <H3>{contest.name}</H3>
                  <FlushDivider />
                  <RadioGroupFlex
                    name="interpretation"
                    onChange={
                      /* istanbul ignore next */
                      () => undefined
                    } // required by blueprintjs but we're implementing on BlockRadio instead
                    selectedValue={
                      (isVote ? values.choiceId : values.interpretation) ||
                      undefined
                    }
                  >
                    {contest.choices.map(c => (
                      <BlockRadio
                        key={c.id}
                        {...radioProps}
                        checked={isVote && values.choiceId === c.id}
                        value={c.id}
                        label={c.name}
                      />
                    ))}
                    <BlockRadio
                      {...radioProps}
                      gray
                      checked={
                        values.interpretation === Interpretation.CANT_AGREE
                      }
                      value={Interpretation.CANT_AGREE}
                      label="Audit board can't agree"
                    />
                    <BlockRadio
                      {...radioProps}
                      gray
                      checked={values.interpretation === Interpretation.BLANK}
                      value={Interpretation.BLANK}
                      label="Blank vote/no mark"
                    />
                  </RadioGroupFlex>
                  <Button minimal icon="edit" onClick={toggleCommenting}>
                    {commenting ? 'Remove comment' : 'Add comment'}
                  </Button>
                  {commenting && (
                    <Field
                      name="comment"
                      type="textarea"
                      data-testid="comment-textarea"
                      component={FormField}
                    />
                  )}
                </FormBlock>
                <ProgressActions>
                  <FormButton
                    type="submit"
                    onClick={handleSubmit}
                    disabled={!values.interpretation}
                    intent="success"
                    data-testid={
                      !values.interpretation
                        ? 'disabled-review'
                        : 'enabled-review'
                    }
                  >
                    Review
                  </FormButton>
                  <Button onClick={previousBallot} minimal>
                    Back
                  </Button>
                </ProgressActions>
              </>
            )
          }}
        />
      </div>
    </BallotRow>
  )
}

export default BallotAudit
