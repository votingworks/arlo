import React from 'react'
import { Ballot } from '../../types';
import { Formik, FormikProps, Form, Field } from 'formik';
import { BallotRow } from './Ballot'
import { H4, H3, Divider } from '@blueprintjs/core';
import styled from 'styled-components';

const FormBlock = styled(Form)`
  background-color: #CED9E0;
`

const Option = styled(Field)`

`

interface Props {
  review: () => void
  vote: Ballot["vote"]
  setVote: (arg0: Ballot["vote"]) => void
}

interface Options {
  vote: Ballot["vote"]
  yes: boolean
  no: boolean
  noConsensus: boolean
  noVote: boolean
}

const BallotAudit: React.FC<Props> = ({ review, vote, setVote }: Props) => {
  return (
    <BallotRow>
      <div className="ballot-side"></div>
      <div className="ballot-main">
        <H4>Are you looking at the right ballot?</H4>
        <p>Step 1:  Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
        <p>Step 2: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
        <Formik
          initialValues={{
            vote,
            yes: false,
            no: false,
            noConsensus: false,
            noVote: false
          }}
          onSubmit={({ vote }) => {
            setVote(vote)
            review()
          }}
          render={({
            handleChange,
            values,
            setFieldValue
          }: FormikProps<Options>) => {
            const handleOptionChange = (o: string) => (e: React.FormEvent) => {
              setFieldValue("vote", o);
              ['yes', 'no', 'noConsensus', 'noVote'].forEach(f => setFieldValue(f, false))
              setFieldValue(o, true)
            }
            return (
              <FormBlock>
                <H3>[insert name of choice here]</H3>
                <Divider />
                <Option name="yes" onChange={handleOptionChange("yes")} />
              </FormBlock>
            )
          }}
        />
      </div>
    </BallotRow>
  )
}

export default BallotAudit
