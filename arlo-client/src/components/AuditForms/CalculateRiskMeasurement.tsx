import React from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import { Formik, FormikProps, FieldArray, Form, Field } from 'formik'
// import * as Yup from 'yup'
import FormSection, {
  FormSectionLabel,
  FormSectionDescription,
} from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormButton from '../Form/FormButton'
import FormField from '../Form/FormField'
import FormButtonBar from '../Form/FormButtonBar'
import { api } from '../utilities'
import { Contest, Round, Candidate, RoundContest } from '../../types'

const InputSection = styled.div`
  display: block;
  margin-top: 25px;
  width: 100%;
  font-size: 0.4em;
`

const InputLabel = styled.label`
  display: inline-block;
`

const InlineInput = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  margin-bottom: 10px;
  width: 50%;
`

interface Props {
  audit: any
  isLoading: boolean
  setIsLoading: (isLoading: boolean) => void
  updateAudit: () => void
}

interface CalculateRiskMeasurementValues {
  round: number
  contests: {
    [key: string]: number | ''
  }[]
}

type AggregateContest = Contest & RoundContest

const CalculateRiskMeasurmeent = (props: Props) => {
  const { audit, isLoading, setIsLoading, updateAudit } = props

  //const sumOfAuditedVotes: { current: number } = useRef(0)

  const downloadBallotRetrievalList = (id: number, e: any) => {
    e.preventDefault()
    const jurisdictionID: string = audit.jurisdictions[0].id
    window.open(`/jurisdiction/${jurisdictionID}/${id}/retrieval-list`)
  }

  const downloadAuditReport = async (e: React.MouseEvent) => {
    e.preventDefault()
    try {
      window.open(`/audit/report`)
      updateAudit()
    } catch (err) {
      toast.error(err.message)
    }
  }

  const calculateRiskMeasurement = async (
    values: CalculateRiskMeasurementValues
  ) => {
    try {
      const jurisdictionID: string = audit.jurisdictions[0].id
      const body: any = {
        contests: audit.contests.map((contest: Contest, i: number) => ({
          // map values.contests
          id: contest.id,
          results: {
            ...values.contests[i],
          },
        })),
      }

      setIsLoading(true)
      await api(`/jurisdiction/${jurisdictionID}/${values.round}/results`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      })
      //sumOfAuditedVotes.current +=
      //  Number(values['candidate-1']) + Number(values['candidate-2'])
      updateAudit()
    } catch (err) {
      toast.error(err.message)
    }
  }

  const rounds: CalculateRiskMeasurementValues[] = audit.rounds.map(
    (r: Round, i: number) => ({
      contests: audit.contests.map((contest: Contest, j: number) => ({
        ...contest.choices.reduce((acc, choice: Candidate) => {
          return { ...acc, [choice.id]: r.contests[j].results[choice.id] || '' }
        }, {}),
      })),
      round: i + 1,
    })
  )

  return audit.rounds.map((round: Round, i: number) => {
    const aggregateContests: AggregateContest[] = audit.contests.reduce(
      (acc: any[], contest: Contest) => {
        const roundContest = round.contests.find(v => v.id === contest.id)
        acc.push({ ...contest, ...roundContest })
        return acc
      },
      []
    )
    const completeContests = aggregateContests.reduce((acc, c) => {
      if (c.endMeasurements.isComplete) {
        acc += 1
      }
      return acc
    }, 0)
    /*
      const overCount = function(this: {
      parent: { [key: string]: number }
    }): boolean {
      const count = Object.values(this.parent).reduce(
        (c: number, v: number) => {
          c += v || 0
          return c
        },
        0
      )
      const maxVotes = this.parent.parent.id
      return count + sumOfAuditedVotes.current <= max
    }
    const schema = Yup.object().shape({
      contests: Yup.lazy(() => {
        return Object.keys(v.contests).reduce((acc: any, result: string) => {
          acc[result] = Yup.number().test(
            'overCount',
            'Cannot exceed the number of total ballots cast',
            overCount
          )
          return acc
        }, {})
      })
    }) */
    /* eslint-disable react/no-array-index-key */
    const aggregatedBallots = aggregateContests.reduce(
      (acc: number, contest: AggregateContest) => {
        acc += contest.sampleSize
        return acc
      },
      0
    )
    return (
      <Formik
        key={i}
        onSubmit={calculateRiskMeasurement}
        initialValues={rounds[i]}
        //validationSchema={schema}
        enableReinitialize
        render={({
          values,
          handleSubmit,
        }: FormikProps<CalculateRiskMeasurementValues>) => (
          <Form>
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
              {/*<SectionLabel>
                Ballot Retrieval List \n
                {contest ? `${contest.sampleSize} Ballots` : ''}
              </SectionLabel>*/}
              <FormButton
                onClick={(e: React.MouseEvent) =>
                  downloadBallotRetrievalList(i + 1, e)
                }
                inline
              >
                Download Aggregated Ballot Retrieval List for Round {i + 1}
              </FormButton>
              {/** contest iteration */}
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
                            {aggregateContests[j].endMeasurements.isComplete ? (
                              <>
                                <FormSectionLabel>
                                  Contest Status: COMPLETE
                                </FormSectionLabel>
                                <InputSection>
                                  <InlineInput>
                                    <InputLabel>Risk Limit: </InputLabel>
                                    {audit.riskLimit}%
                                  </InlineInput>
                                  <InlineInput>
                                    <InputLabel>P-value: </InputLabel>{' '}
                                    {
                                      aggregateContests[j].endMeasurements
                                        .pvalue
                                    }
                                  </InlineInput>
                                </InputSection>
                              </>
                            ) : (
                              <>
                                <FormSectionLabel>
                                  Audited Results: Round {i + 1}, Contest{' '}
                                  {j + 1} INCOMPLETE
                                </FormSectionLabel>
                                <FormSectionDescription>
                                  Enter the number of votes recorded for each
                                  candidate/choice in the audited ballots for
                                  Round {i + 1}, Contest {j + 1}
                                </FormSectionDescription>
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
                                        <InlineInput>
                                          <InputLabel>{name}</InputLabel>
                                          <Field
                                            name={`contests[${j}][${choiceId}]`}
                                            type="number"
                                            component={FormField}
                                          />
                                        </InlineInput>
                                      </React.Fragment>
                                    )
                                  })}
                                </InputSection>
                              </>
                            )}
                          </FormSection>
                        )
                      })}
                    </>
                  )
                }}
              />
              {isLoading && <p>Loading...</p>}
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
                    <FormButton type="button" onClick={handleSubmit}>
                      Calculate Risk Measurement
                    </FormButton>
                  </FormButtonBar>
                )}
              <FormSection>
                {/*<FormSectionLabel>
                  Audit Status:{' '}
                  {contest.endMeasurements.isComplete
                    ? 'COMPLETE'
                    : 'INCOMPLETE'}
                </FormSectionLabel>
                <InputSection>
                  <InlineInput>
                    <InputLabel>Risk Limit: </InputLabel>
                    {audit.riskLimit}%
                  </InlineInput>
                  <InlineInput>
                    <InputLabel>P-value: </InputLabel>{' '}
                    {contest.endMeasurements.pvalue}
                  </InlineInput>
                </InputSection>*/}
                {/* {Form 3} */}
                {completeContests === audit.contests.length && (
                  <FormButton
                    onClick={(e: React.MouseEvent) => downloadAuditReport(e)}
                    size="sm"
                    inline
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
}

export default React.memo(CalculateRiskMeasurmeent)
