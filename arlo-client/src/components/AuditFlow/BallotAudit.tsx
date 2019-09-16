import React from 'react'
import { Formik, FormikProps, Form, getIn } from 'formik'
import { H4, H3, Divider, RadioGroup, Radio } from '@blueprintjs/core'
import styled from 'styled-components'
import BallotRow from './BallotRow'
import { Ballot } from '../../types'

const FormBlock = styled(Form)`
  background-color: #ced9e0;
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
            handleChange,
            values,
            setFieldValue,
          }: FormikProps<Options>) => {
            return (
              <FormBlock>
                <H3>[insert name of choice here]</H3>
                <Divider />
                <RadioGroup
                  name="vote"
                  onChange={e => setFieldValue('vote', e.currentTarget.value)}
                  selectedValue={getIn(values, 'vote')}
                >
                  <Radio value="YES">Yes/For</Radio>
                  <Radio value="NO">No/Against</Radio>
                  <Radio value="NO_CONSENSUS">No audit board consensus</Radio>
                  <Radio value="NO_VOTE">Blank vote/no mark</Radio>
                </RadioGroup>
              </FormBlock>
            )
          }}
        />
      </div>
    </BallotRow>
  )
}

export default BallotAudit
