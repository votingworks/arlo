import React from 'react'
import { Formik, FormikProps, Form, getIn } from 'formik'
import { H4, H3, Divider, RadioGroup } from '@blueprintjs/core'
import styled from 'styled-components'
import BallotRow from './BallotRow'
import BlockRadio from './BlockRadio'
import FormButton from '../Form/FormButton'
import { Ballot } from '../../types'

const FormBlock = styled(Form)`
  background-color: #ced9e0;
  padding: 20px;
`

const RadioGroupFlex = styled(RadioGroup)`
  display: flex;
  flex-wrap: wrap;
  justify-content: space-evenly;
  padding-top: 20px;
`

const ProgressActions = styled.div`
  display: flex;
  flex-direction: row-reverse;
  margin-top: 20px;
`

interface Props {
  review: () => void
  vote: Ballot['vote']
  setVote: (arg0: Ballot['vote']) => void
}

interface Options {
  vote: Ballot['vote']
}

const BallotAudit: React.FC<Props> = ({ review, vote, setVote }: Props) => {
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
          initialValues={{ vote }}
          onSubmit={({ vote }) => {
            setVote(vote)
            review()
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
                    <BlockRadio {...radioProps} value="YES">
                      Yes/For
                    </BlockRadio>
                    <BlockRadio {...radioProps} value="NO">
                      No/Against
                    </BlockRadio>
                    <BlockRadio {...radioProps} value="NO_CONSENSUS">
                      No audit board consensus
                    </BlockRadio>
                    <BlockRadio {...radioProps} value="NO_VOTE">
                      Blank vote/no mark
                    </BlockRadio>
                  </RadioGroupFlex>
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
