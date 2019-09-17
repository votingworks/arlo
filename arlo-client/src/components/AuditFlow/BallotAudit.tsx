import React, { useState } from 'react'
import { Formik, FormikProps, getIn, Field } from 'formik'
import { H4, H3, Divider, Button } from '@blueprintjs/core'
import { BallotRow, FormBlock, RadioGroupFlex, ProgressActions } from './Atoms'
import BlockRadio from './BlockRadio'
import FormButton from '../Form/FormButton'
import { Ballot, Review } from '../../types'
import FormField from '../Form/FormField'

interface Props {
  goReview: () => void
  review: Review
  setReview: (arg0: {
    vote: Ballot['vote']
    comment: Ballot['comment']
  }) => void
}

interface Options {
  vote: Ballot['vote']
}

const BallotAudit: React.FC<Props> = ({
  review,
  goReview,
  setReview,
}: Props) => {
  const [commenting, setCommenting] = useState(!!review.comment)
  return (
    <BallotRow>
      <div className="ballot-side"></div>
      <div className="ballot-main">
        <H4>Are you looking at the right ballot?</H4>
        <p>
          Step 1: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed
          do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        </p>
        <p>
          Step 2: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed
          do eiusmod tempor incididunt ut labore et dolore magna aliqua.
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
          }: FormikProps<Options>) => {
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
                  <H3>[insert name of choice here]</H3>
                  <Divider />
                  <RadioGroupFlex
                    name="vote"
                    onChange={() => null} // required by blueprintjs but we're implementing on BlockRadio instead
                    selectedValue={getIn(values, 'vote')}
                  >
                    <BlockRadio
                      {...radioProps}
                      checked={getIn(values, 'vote') === 'YES'}
                      value="YES"
                    />
                    <BlockRadio
                      {...radioProps}
                      checked={getIn(values, 'vote') === 'NO'}
                      value="NO"
                    />
                    <BlockRadio
                      {...radioProps}
                      checked={getIn(values, 'vote') === 'NO_CONSENSUS'}
                      value="NO_CONSENSUS"
                    />
                    <BlockRadio
                      {...radioProps}
                      checked={getIn(values, 'vote') === 'NO_VOTE'}
                      value="NO_VOTE"
                    />
                  </RadioGroupFlex>
                  <Button minimal icon="edit" onClick={toggleCommenting}>
                    {commenting ? 'Remove comment' : 'Add comment'}
                  </Button>
                  {commenting && (
                    <Field
                      name="comment"
                      type="textarea"
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
                  >
                    Review
                  </FormButton>
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
