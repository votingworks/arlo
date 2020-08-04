import React from 'react'
import { useParams } from 'react-router-dom'
import { H5 } from '@blueprintjs/core'
import { Field, Formik, Form, FormikProps } from 'formik'
import H2Title from '../../Atoms/H2Title'
import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import { IRound } from '../useRoundsJurisdictionAdmin'
import Card from '../../Atoms/SpacedCard'
import FormField from '../../Atoms/Form/FormField'
import FormButton from '../../Atoms/Form/FormButton'
import { testNumber } from '../../utilities'

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

  const submit = (values: IValues) => {
    console.log(values)
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
          <FormButton type="submit" intent="primary" onClick={handleSubmit}>
            Submit Data for Round {round.roundNum}
          </FormButton>
        </Form>
      )}
    </Formik>
  )
}

export default RoundDataEntry
