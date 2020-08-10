import React from 'react'
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
import { testNumber } from '../../utilities'
import useResults, { IResultValues } from './useResults'

const BottomButton = styled(FormButton)`
  margin: 30px 0;
`

const BlockLabel = styled.label`
  display: block;
  margin: 20px 0;
`

interface IProps {
  round: IRound
}

interface IValues {
  results: IResultValues
}

const RoundDataEntry = ({ round }: IProps) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const contests = useContestsJurisdictionAdmin(electionId, jurisdictionId)
  const [results, updateResults] = useResults(
    electionId,
    jurisdictionId,
    round.id
  )

  if (!results) return null
  const alreadySubmittedResults = Object.values(results.results).some(a =>
    Object.values(a).some(b => b)
  )

  const submit = async (values: IValues) => {
    updateResults(values.results)
  }

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
                  <BlockLabel
                    key={choice.id}
                    htmlFor={`results[${contest.id}][${choice.id}]`}
                  >
                    Votes for {choice.name}:
                    {alreadySubmittedResults ? (
                      results[contest.id][choice.id]
                    ) : (
                      <Field
                        id={`results[${contest.id}][${choice.id}]`}
                        name={`results[${contest.id}][${choice.id}]`}
                        disabled={alreadySubmittedResults}
                        validate={testNumber()}
                        component={FormField}
                      />
                    )}
                  </BlockLabel>
                ))}
              </Card>
            ))}
          <BottomButton
            type="submit"
            intent="primary"
            disabled={alreadySubmittedResults}
            onClick={handleSubmit}
          >
            {alreadySubmittedResults
              ? `Already Submitted Data for Round ${round.roundNum}`
              : `Submit Data for Round ${round.roundNum}`}
          </BottomButton>
        </Form>
      )}
    </Formik>
  )
}

export default RoundDataEntry
