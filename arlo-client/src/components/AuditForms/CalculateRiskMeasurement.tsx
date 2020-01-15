/* eslint-disable react/prop-types */
import React from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import jsPDF from 'jspdf'
import QRCode from 'qrcode.react'
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
import { api, testNumber, poll, checkAndToast } from '../utilities'
import {
  IContest,
  IRound,
  ICandidate,
  IRoundContest,
  IAudit,
  IBallot,
  IErrorResponse,
  IAuditBoard,
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

const QRroot = styled.div`
  display: none;
`

const QRs: React.FC<{ electionId: string; boardIds: string[] }> = ({
  electionId,
  boardIds,
}) => {
  return (
    <QRroot id="qr-root">
      {boardIds.map(id => (
        <span key={id} id={`qr-${id}`}>
          <QRCode
            value={`${window.location.origin}/election/${electionId}/board/${id}`}
            size={200}
          />
        </span>
      ))}
    </QRroot>
  )
}

interface IProps {
  audit: IAudit
  isLoading: boolean
  setIsLoading: (isLoading: boolean) => void
  updateAudit: () => void
  getStatus: () => Promise<IAudit>
  electionId: string
}

interface ICalculateRiskMeasurementValues {
  round: number
  contests: {
    [key: string]: number | ''
  }[]
}

interface IRoundPost {
  contests: {
    id: string
    results: {
      [key: string]: number | ''
    }
  }[]
}

type AggregateContest = IContest & IRoundContest

const CalculateRiskMeasurement: React.FC<IProps> = ({
  audit,
  isLoading,
  setIsLoading,
  updateAudit,
  getStatus,
  electionId,
}: IProps) => {
  const getBallots = async (r: number): Promise<IBallot[]> => {
    const round = audit.rounds[r]
    const response = await api<
      | {
          ballots: IBallot[]
        }
      | IErrorResponse
    >(
      `/election/${electionId}/jurisdiction/${audit.jurisdictions[0].id}/round/${round.id}/ballot-list`
    )
    if (checkAndToast(response)) {
      return []
    } else {
      return response.ballots
    }
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

  const downloadDataEntry = async (): Promise<void> => {
    const auditBoards = new jsPDF({ format: 'letter' })
    audit.jurisdictions[0].auditBoards.forEach(
      (board: IAuditBoard, i: number) => {
        const qr: HTMLCanvasElement | null = document.querySelector(
          `#qr-${board.id} > canvas`
        )
        /* istanbul ignore else */
        if (qr) {
          i > 0 && auditBoards.addPage('letter')
          const url = qr.toDataURL()
          auditBoards.setFontSize(22)
          auditBoards.setFontStyle('bold')
          auditBoards.text(board.name, 20, 20)
          auditBoards.setFontSize(14)
          auditBoards.setFontStyle('normal')
          auditBoards.text(
            'Scan this QR code to enter the votes you see on your assigned ballots.',
            20,
            40
          )
          auditBoards.addImage(url, 'JPEG', 20, 50, 50, 50)
          auditBoards.text(
            auditBoards.splitTextToSize(
              'If you are not able to scan the QR code, you may also type the following URL into a web browser to access the data entry portal.',
              180
            ),
            20,
            120
          )
          auditBoards.text(
            `${window.location.origin}/auditboard/${board.passphrase}`,
            20,
            140
          )
        }
      }
    )
    auditBoards.autoPrint()
    auditBoards.save(`Audit Boards Credentials for Data Entry.pdf`)
  }

  const calculateRiskMeasurement = async (
    values: ICalculateRiskMeasurementValues
  ) => {
    const jurisdictionID: string = audit.jurisdictions[0].id
    const body: IRoundPost = {
      contests: audit.contests.map((contest: IContest, i: number) => ({
        id: contest.id,
        results: Object.keys(values.contests[i]).reduce(
          (a, k) => {
            a[k] = Number(values.contests[i][k])
            return a
          },
          {} as IRoundPost['contests'][0]['results']
        ),
      })),
    }

    try {
      setIsLoading(true)
      const response: IErrorResponse = await api(
        `/election/${electionId}/jurisdiction/${jurisdictionID}/${values.round}/results`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(body),
        }
      )
      if (checkAndToast(response)) {
        setIsLoading(false)
        return
      }
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

  const roundForms = audit.rounds.map((round: IRound, i: number) => {
    const aggregateContests: AggregateContest[] = audit.contests.reduce(
      (acc: AggregateContest[], contest: IContest) => {
        const roundContest = round.contests.find(
          v => v.id === contest.id
        ) as IRoundContest
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
        }: FormikProps<ICalculateRiskMeasurementValues>) => (
          <Form data-testid={`form-three-${i + 1}`}>
            {i === 0 && (
              <QRs
                electionId={electionId}
                boardIds={audit.jurisdictions[0].auditBoards.map(b => b.id)}
              />
            )}
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
              {i === 0 && (
                <FormButton onClick={() => downloadDataEntry()} inline>
                  Download Audit Boards Credentials for Data Entry
                </FormButton>
              )}
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
                                    (candidate: ICandidate) =>
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
