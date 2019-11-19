import React from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import jsPDF from 'jspdf'
/* istanbul ignore next */
import { Formik, FormikProps, FieldArray, Form, Field } from 'formik'
import { Spinner } from '@blueprintjs/core'
import FormSection, {
  FormSectionLabel,
  FormSectionDescription,
} from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormButton from '../Form/FormButton'
import FormField from '../Form/FormField'
import FormButtonBar from '../Form/FormButtonBar'
import { api, testNumber, poll } from '../utilities'
import {
  Contest,
  Round,
  Candidate,
  RoundContest,
  Audit,
  Ballot,
} from '../../types'

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
  getStatus: () => Promise<Audit>
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

type AggregateContest = Contest & RoundContest

const CalculateRiskMeasurement: React.FC<Props> = ({
  audit,
  isLoading,
  setIsLoading,
  updateAudit,
  getStatus,
  electionId,
}: Props) => {
  const getBallots = async (r: number): Promise<Ballot[]> => {
    const round = audit.rounds[r]
    const { ballots } = await api<{ ballots: Ballot[] }>(
      `/election/${electionId}/jurisdiction/${audit.jurisdictions[0].id}/round/${round.id}/ballot-list`
    )
    return ballots
  }

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

  const downloadLabels = async (r: number): Promise<void> => {
    const ballots = await getBallots(r)
    /* istanbul ignore else */
    if (ballots.length) {
      const getX = (l: number): number => (l % 3) * 60 + 9 * ((l % 3) + 1)
      const getY = (l: number): number[] => [
        Math.floor(l / 3) * 25.5 + 20,
        Math.floor(l / 3) * 25.5 + 25,
        Math.floor(l / 3) * 25.5 + 34,
      ]
      const labels = new jsPDF({ format: 'letter' })
      labels.setFontSize(9)
      let labelCount = 0
      ballots.forEach(ballot => {
        labelCount++
        if (labelCount > 30) {
          labels.addPage('letter')
          labelCount = 1
        }
        const x = getX(labelCount - 1)
        const y = getY(labelCount - 1)
        labels.text(
          labels.splitTextToSize(ballot.auditBoard!.name, 60)[0],
          x,
          y[0]
        )
        labels.text(
          labels.splitTextToSize(`Batch Name: ${ballot.batch!.name}`, 60),
          x,
          y[1]
        )
        labels.text(`Ballot Number: ${ballot.position}`, x, y[2])
      })
      labels.autoPrint()
      labels.save(`Round ${r + 1} Labels.pdf`)
    }
  }

  const downloadPlaceholders = async (r: number): Promise<void> => {
    const ballots = await getBallots(r)
    /* istanbul ignore else */
    if (ballots.length) {
      const placeholders = new jsPDF({ format: 'letter' })
      placeholders.setFontSize(20)
      let pageCount = 0
      ballots.forEach(ballot => {
        pageCount > 0 && placeholders.addPage('letter')
        placeholders.text(
          placeholders.splitTextToSize(ballot.auditBoard!.name, 180),
          20,
          20
        )
        placeholders.text(
          placeholders.splitTextToSize(
            `Batch Name: ${ballot.batch!.name}`,
            180
          ),
          20,
          40
        )
        placeholders.text(`Ballot Number: ${ballot.position}`, 20, 100)
        pageCount++
      })
      placeholders.autoPrint()
      placeholders.save(`Round ${r + 1} Placeholders.pdf`)
    }
  }

  const calculateRiskMeasurement = async (
    values: CalculateRiskMeasurementValues
  ) => {
    const jurisdictionID: string = audit.jurisdictions[0].id
    const body: RoundPost = {
      contests: audit.contests.map((contest: Contest, i: number) => ({
        id: contest.id,
        results: Object.keys(values.contests[i]).reduce(
          (a, k) => {
            a[k] = Number(values.contests[i][k])
            return a
          },
          {} as RoundPost['contests'][0]['results']
        ),
      })),
    }

    try {
      setIsLoading(true)
      await api(
        `/election/${electionId}/jurisdiction/${jurisdictionID}/${values.round}/results`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(body),
        }
      )
      const condition = async () => {
        const { rounds } = await getStatus()
        const { contests } = rounds[rounds.length - 1]
        return !!contests.length && contests.every(c => !!c.sampleSize)
      }
      const complete = () => {
        updateAudit()
        setIsLoading(false)
      }
      poll(condition, complete, (err: Error) => toast.error(err.message))
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
        /* istanbul ignore next */
        acc += contest.sampleSize || 0
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
        validateOnChange={false}
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
              <FormButton onClick={() => downloadPlaceholders(i)} inline>
                Download Placeholders for Round {i + 1}
              </FormButton>
              <FormButton onClick={() => downloadLabels(i)} inline>
                Download Label Sheets for Round {i + 1}
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
                                          validate={testNumber()}
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
              <FormSection>
                <FormSectionLabel>
                  Audit Progress: {completeContests} of {audit.contests.length}{' '}
                  complete
                </FormSectionLabel>
              </FormSection>
              {i + 1 === audit.rounds.length && isLoading && <Spinner />}
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
