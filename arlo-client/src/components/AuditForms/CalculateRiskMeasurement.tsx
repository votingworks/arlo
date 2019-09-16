import React from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
/* istanbul ignore next */
import { Formik, FormikProps, FieldArray, Form, Field } from 'formik'
import * as Yup from 'yup'
import { Spinner } from '@blueprintjs/core'
import FormSection, {
  FormSectionLabel,
  FormSectionDescription,
} from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormButton from '../Form/FormButton'
import FormField from '../Form/FormField'
import FormButtonBar from '../Form/FormButtonBar'
import { api } from '../utilities'
import { Contest, Round, Candidate, RoundContest, Audit } from '../../types'

const InputSection = styled.div`
  display: block;
  margin-top: 25px;
  width: 100%;
`

const InputLabel = styled.label`
  display: inline-block;
  margin-top: 5px;
`

const InlineWrapper = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  margin-bottom: 10px;
  width: 50%;
`

interface Props {
  audit: Audit
  isLoading: boolean
  setIsLoading: (isLoading: boolean) => void
  updateAudit: () => void
  electionId: string
}

interface CalculateRiskMeasurementValues {
  round: number
  contests: {
    [key: string]: number | ''
  }[]
}

interface RoundPost {
  contests: {
    id: string
    results: {
      [key: string]: number | ''
    }
  }[]
}

const numberSchema = Yup.number()
  .typeError('Must be a number')
  .integer('Must be an integer')
  .min(0, 'Must be a positive number')
  .required('Required')

const testNumber = (value: any) =>
  numberSchema
    .validate(value)
    .then(success => undefined, error => error.errors[0])

type AggregateContest = Contest & RoundContest

const CalculateRiskMeasurement: React.FC<Props> = ({
  audit,
  isLoading,
  setIsLoading,
  updateAudit,
  electionId,
}: Props) => {
  const downloadBallotRetrievalList = (id: number, e: React.FormEvent) => {
    e.preventDefault()
    const jurisdictionID: string = audit.jurisdictions[0].id
    window.open(
      `/election/${electionId}/jurisdiction/${jurisdictionID}/${id}/retrieval-list`
    )
  }

  const downloadAuditReport = async (e: React.FormEvent) => {
    e.preventDefault()
    window.open(`/election/${electionId}/audit/report`)
    updateAudit()
  }

  const calculateRiskMeasurement = async (
    values: CalculateRiskMeasurementValues
  ) => {
    const jurisdictionID: string = audit.jurisdictions[0].id
    const body: RoundPost = {
      contests: audit.contests.map((contest: Contest, i: number) => ({
        id: contest.id,
        results: {
          ...values.contests[i],
        },
      })),
    }

    try {
      setIsLoading(true)
      await api(`/jurisdiction/${jurisdictionID}/${values.round}/results`, {
        electionId,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      })
      updateAudit()
    } catch (err) {
      toast.error(err.message)
    }
  }

  const roundForms = audit.rounds.map((round: Round, i: number) => {
    const aggregateContests: AggregateContest[] = audit.contests.reduce(
      (acc: AggregateContest[], contest: Contest) => {
        const roundContest = round.contests.find(
          v => v.id === contest.id
        ) as RoundContest
        acc.push({ ...contest, ...roundContest })
        return acc
      },
      []
    )
    const roundValues = {
      contests: aggregateContests.map((contest: AggregateContest) =>
        contest.choices.reduce((acc, choice) => {
          return { ...acc, [choice.id]: contest.results[choice.id] || 0 }
        }, {})
      ),
      round: i + 1,
    }
    const isSubmitted =
      i + 1 < audit.rounds.length ||
      aggregateContests.every(
        (contest: AggregateContest) => !!contest.endMeasurements.isComplete
      )
    const completeContests = aggregateContests.reduce((acc, c) => {
      if (c.endMeasurements.isComplete) {
        acc += 1
      }
      return acc
    }, 0)
    const aggregatedBallots = aggregateContests.reduce(
      (acc: number, contest: AggregateContest) => {
        acc += contest.sampleSize
        return acc
      },
      0
    )
    /* eslint-disable react/no-array-index-key */
    return (
      <Formik
        key={i}
        onSubmit={calculateRiskMeasurement}
        initialValues={roundValues}
        enableReinitialize
        render={({
          values,
          handleSubmit,
        }: FormikProps<CalculateRiskMeasurementValues>) => (
          <Form data-testid={`form-three-${i + 1}`}>
            <hr />
            <FormWrapper title={`Round ${i + 1}`}>
              <FormSectionLabel>
                Ballot Retrieval List: {aggregatedBallots} Total Ballots
              </FormSectionLabel>
              <FormSectionDescription>
                {aggregateContests.map(
                  (contest: AggregateContest, i: number) => (
                    <p key={contest.id}>
                      Contest {i + 1}: {contest.sampleSize} ballots
                    </p>
                  )
                )}
              </FormSectionDescription>
              <FormButton
                onClick={(e: React.FormEvent) =>
                  downloadBallotRetrievalList(i + 1, e)
                }
                inline
              >
                Download Aggregated Ballot Retrieval List for Round {i + 1}
              </FormButton>
              <FieldArray
                name="contests"
                render={() => {
                  return (
                    <>
                      {values.contests.map((contest, j) => {
                        return (
                          <FormSection
                            key={aggregateContests[j].id}
                            label={`Contest ${j + 1}: ${
                              aggregateContests[j].name
                            }`}
                          >
                            <>
                              <FormSectionLabel>
                                Audited Results: Round {i + 1}, Contest {j + 1}{' '}
                                {aggregateContests[j].endMeasurements.isComplete
                                  ? 'COMPLETE'
                                  : 'INCOMPLETE'}
                              </FormSectionLabel>
                              {aggregateContests[j].endMeasurements
                                .isComplete && (
                                <InputSection>
                                  <InlineWrapper>
                                    <InputLabel>Risk Limit: </InputLabel>
                                    {audit.riskLimit}%
                                  </InlineWrapper>
                                  <InlineWrapper>
                                    <InputLabel>P-value: </InputLabel>{' '}
                                    {
                                      aggregateContests[j].endMeasurements
                                        .pvalue
                                    }
                                  </InlineWrapper>
                                </InputSection>
                              )}
                              {!isSubmitted && (
                                <FormSectionDescription>
                                  Enter the number of votes recorded for each
                                  candidate/choice in the audited ballots for
                                  Round {i + 1}, Contest {j + 1}
                                </FormSectionDescription>
                              )}
                              <InputSection>
                                {Object.keys(contest).map(choiceId => {
                                  const name = aggregateContests[
                                    j
                                  ].choices.find(
                                    (candidate: Candidate) =>
                                      candidate.id === choiceId
                                  )!.name
                                  return (
                                    <React.Fragment key={choiceId}>
                                      <InlineWrapper>
                                        <InputLabel
                                          htmlFor={`round-${i}-contest-${j}-choice-${choiceId}`}
                                        >
                                          {name}
                                        </InputLabel>
                                        <Field
                                          id={`round-${i}-contest-${j}-choice-${choiceId}`}
                                          name={`contests[${j}][${choiceId}]`}
                                          validate={testNumber}
                                          component={FormField}
                                          disabled={isSubmitted}
                                        />
                                      </InlineWrapper>
                                    </React.Fragment>
                                  )
                                })}
                              </InputSection>
                            </>
                          </FormSection>
                        )
                      })}
                    </>
                  )
                }}
              />
              {i + 1 === audit.rounds.length && isLoading && <Spinner />}
              <FormSection>
                <FormSectionLabel>
                  Audit Progress: {completeContests} of {audit.contests.length}{' '}
                  complete
                </FormSectionLabel>
              </FormSection>
              {i + 1 === audit.rounds.length &&
                aggregateContests.some(
                  (contest: AggregateContest) =>
                    !contest.endMeasurements.isComplete
                ) &&
                !isLoading && (
                  <FormButtonBar>
                    <FormButton
                      type="button"
                      intent="primary"
                      onClick={handleSubmit}
                    >
                      Calculate Risk Measurement
                    </FormButton>
                  </FormButtonBar>
                )}
              <FormSection>
                {completeContests === audit.contests.length && (
                  <FormButton
                    onClick={downloadAuditReport}
                    data-testid="submit-form-three"
                    intent="success"
                  >
                    Download Audit Report
                  </FormButton>
                )}
              </FormSection>
            </FormWrapper>
          </Form>
        )}
      />
    )
  })
  return <>{roundForms}</>
}

export default React.memo(CalculateRiskMeasurement)
