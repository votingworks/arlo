import React from 'react'
import { toast } from 'react-toastify'
import { useParams } from 'react-router-dom'
import { H5 } from '@blueprintjs/core'
import { Field, Formik, Form, FormikProps } from 'formik'
import styled from 'styled-components'
import H2Title from '../../Atoms/H2Title'
import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import { IRound } from '../useRoundsJurisdictionAdmin'
import Card from '../../Atoms/SpacedCard'
import FormField from '../../Atoms/Form/FormField'
import FormButton from '../../Atoms/Form/FormButton'
import { testNumber, api } from '../../utilities'

const BottomButton = styled(FormButton)`
  margin: 30px 0;
`

interface IValues {
  results: {
    [contestId: string]: {
      [choiceId: string]: string | number
    }
  }
}

interface IProps {
  round: IRound
}

const RoundDataEntry = ({ round }: IProps) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const contests = useContestsJurisdictionAdmin(electionId, jurisdictionId)

  const results = contests
    ? contests.reduce(
        (a, contest) => ({
          [contest.id]: contest.choices.reduce(
            (b, choice) => ({ [choice.id]: '' }),
            {}
          ),
        }),
        {}
      )
    : null

  const submit = async ({ results: r }: IValues) => {
    const body = JSON.stringify(
      Object.keys(r).reduce(
        (a, contestId) => ({
          ...a,
          [contestId]: Object.keys(r[contestId]).reduce(
            (b, choiceId) => ({
              ...b,
              [choiceId]: Number(r[contestId][choiceId]),
            }),
            {}
          ),
        }),
        {}
      )
    )
    try {
      await api(
        `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${round.id}/results`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body,
        }
      )
      return true
    } catch (err) {
      toast.error(err.message)
      return false
    }
  }

  if (!results) return null
  return (
    <Formik initialValues={{ results }} enableReinitialize onSubmit={submit}>
      {({ handleSubmit }: FormikProps<IValues>) => (
        <Form>
          <H2Title>Round {round.roundNum} Data Entry</H2Title>
          <p>
            When you have examined all the ballots assigned to you, enter the
            number of votes recorded for each candidate/choice from the audited
            ballots.
          </p>
          {contests &&
            contests.map(contest => (
              <Card key={contest.id}>
                <H5>{contest.name}</H5>
                {contest.choices.map(choice => (
                  <label
                    key={choice.id}
                    htmlFor={`results[${contest.id}][${choice.id}]`}
                  >
                    Votes for {choice.name}:
                    <Field
                      id={`results[${contest.id}][${choice.id}]`}
                      name={`results[${contest.id}][${choice.id}]`}
                      disabled={round.endedAt}
                      validate={testNumber()}
                      component={FormField}
                    />
                  </label>
                ))}
              </Card>
            ))}
          <BottomButton type="submit" intent="primary" onClick={handleSubmit}>
            Submit Data for Round {round.roundNum}
          </BottomButton>
        </Form>
      )}
    </Formik>
  )
}

export default RoundDataEntry
