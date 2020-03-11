import React, { useState, useEffect } from 'react'
import { Formik, FormikProps, getIn, Field } from 'formik'
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
import { IReview, IContest } from '../../types'
import FormField from '../Form/FormField'

interface IProps {
  contest: IContest
  goReview: () => void
  review: IReview
  setReview: (arg0: { vote: string; comment: string }) => void
  previousBallot: () => void
}

interface IOptions {
  vote: string
  comment: string
}

const BallotAudit: React.FC<IProps> = ({
  contest,
  review,
  goReview,
  setReview,
  previousBallot,
}: IProps) => {
  const [commenting, setCommenting] = useState(false)
  useEffect(() => {
    setCommenting(!!review.comment)
  }, [review.comment])
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
          If the audit board cannot agree, select &quot;No audit board
          consensus.&quot; You may add a comment for additional information
          about the disagreement.
        </p>
        <Formik
          initialValues={review}
          enableReinitialize
          onSubmit={values => {
            setReview(values)
            goReview()
          }}
          render={({
            handleSubmit,
            values,
            setFieldValue,
          }: FormikProps<IOptions>) => {
            const radioProps = {
              name: 'vote',
              handleChange: (e: React.ChangeEvent<HTMLInputElement>) =>
                setFieldValue('vote', e.currentTarget.value),
            }
            const toggleCommenting = () => {
              setCommenting(!commenting)
              setFieldValue('comment', '')
            }
            return (
              <>
                <FormBlock>
                  <H3>{contest.name}</H3>
                  <FlushDivider />
                  <RadioGroupFlex
                    name="vote"
                    onChange={
                      /* istanbul ignore next */
                      () => undefined
                    } // required by blueprintjs but we're implementing on BlockRadio instead
                    selectedValue={getIn(values, 'vote')}
                  >
                    {contest.choices.map(c => (
                      <BlockRadio
                        key={c.id}
                        {...radioProps}
                        checked={getIn(values, 'vote') === c.name}
                        value={c.name}
                      />
                    ))}
                    <BlockRadio
                      {...radioProps}
                      gray
                      checked={
                        getIn(values, 'vote') === "Audit board can't agree"
                      }
                      value="Audit board can't agree"
                    />
                    <BlockRadio
                      {...radioProps}
                      gray
                      checked={getIn(values, 'vote') === 'Blank vote/no mark'}
                      value="Blank vote/no mark"
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
                    disabled={!values.vote}
                    intent="success"
                    data-testid={
                      !values.vote ? 'disabled-review' : 'enabled-review'
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
