import React from 'react'
import { useParams } from 'react-router-dom'
import { H5, H3 } from '@blueprintjs/core'
import { Field, Formik, FormikProps } from 'formik'
import styled from 'styled-components'
import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import useResults, { IResultValues } from './useResults'
import FormButton from '../Atoms/Form/FormButton'
import { IRound } from '../AuditAdmin/useRoundsAuditAdmin'
import { testNumber } from '../utilities'
import FormField from '../Atoms/Form/FormField'

const Contest = styled.div`
  padding: 10px 0;
`

const BottomButton = styled(FormButton)`
  margin: 30px 0;
`

const BlockLabel = styled.label`
  display: block;
  margin: 10px 0;
`

interface IProps {
  round: IRound
}

interface IValues {
  results: IResultValues
}

const RoundDataEntry: React.FC<IProps> = ({ round }) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const contestsQuery = useContestsJurisdictionAdmin(electionId, jurisdictionId)
  const [results, updateResults] = useResults(
    electionId,
    jurisdictionId,
    round.id
  )

  if (!results || !contestsQuery.isSuccess) return null
  const contests = contestsQuery.data

  const alreadySubmittedResults = Object.values(results).some(a =>
    Object.values(a).some(b => b)
  )

  const submit = async (values: IValues) => {
    updateResults(values.results)
  }

  return (
    <Formik initialValues={{ results }} enableReinitialize onSubmit={submit}>
      {({ handleSubmit, isSubmitting }: FormikProps<IValues>) => (
        <form>
          <H3>Enter Tallies</H3>
          <p>
            When you have examined all the ballots assigned to you, enter the
            number of votes recorded for each candidate/choice from the audited
            ballots.
          </p>
          {contests.map(contest => (
            <Contest key={contest.id}>
              <H5>{contest.name}</H5>
              {contest.choices.map(choice => (
                <BlockLabel
                  key={choice.id}
                  htmlFor={`results[${contest.id}][${choice.id}]`}
                >
                  Votes for {choice.name}:
                  <Field
                    id={`results[${contest.id}][${choice.id}]`}
                    name={`results[${contest.id}][${choice.id}]`}
                    disabled={alreadySubmittedResults}
                    validate={testNumber()}
                    component={FormField}
                  />
                </BlockLabel>
              ))}
            </Contest>
          ))}
          <BottomButton
            type="submit"
            intent="primary"
            loading={isSubmitting}
            disabled={alreadySubmittedResults}
            onClick={handleSubmit}
          >
            {alreadySubmittedResults ? `Tallies Submitted` : `Submit Tallies`}
          </BottomButton>
        </form>
      )}
    </Formik>
  )
}

export default RoundDataEntry
