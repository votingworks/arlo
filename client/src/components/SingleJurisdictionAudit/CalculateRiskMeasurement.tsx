/* eslint-disable react/prop-types */
import React, { useEffect, useState, useCallback } from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import jsPDF from 'jspdf'
import QRCode from 'qrcode.react'
/* istanbul ignore next */
import { Formik, FormikProps, FieldArray, Field } from 'formik'
import { Spinner, ProgressBar } from '@blueprintjs/core'
import FormSection, {
  FormSectionLabel,
  FormSectionDescription,
} from '../Atoms/Form/FormSection'
import FormWrapper from '../Atoms/Form/FormWrapper'
import FormButton from '../Atoms/Form/FormButton'
import FormField from '../Atoms/Form/FormField'
import FormButtonBar from '../Atoms/Form/FormButtonBar'
import { api, testNumber, poll, apiDownload } from '../utilities'
import {
  IContest,
  IRound,
  ICandidate,
  IRoundContest,
  IAudit,
  IBallot,
  IErrorResponse,
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
            value={`${window.location.origin}/election/${electionId}/audit-board/${id}`}
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
  const jId = audit.jurisdictions[0].id // for react-hooks/exhaustive-deps rules
  const getBallots = useCallback(
    async (r: number): Promise<IBallot[]> => {
      const round = audit.rounds[r]
      const response = await api<{ ballots: IBallot[] }>(
        `/election/${electionId}/jurisdiction/${jId}/round/${round.id}/ballot-list`
      )
      if (!response) return []
      return response.ballots
    },
    [electionId, jId, audit.rounds]
  )

  const downloadBallotRetrievalList = (id: number, e: React.FormEvent) => {
    e.preventDefault()
    const jurisdictionID: string = audit.jurisdictions[0].id
    apiDownload(
      `/election/${electionId}/jurisdiction/${jurisdictionID}/${id}/retrieval-list`
    )
  }

  const downloadAuditReport = async (e: React.FormEvent) => {
    e.preventDefault()
    apiDownload(`/election/${electionId}/report`)
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
        labelCount += 1
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
        if (pageCount > 0) placeholders.addPage('letter')
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
        pageCount += 1
      })
      placeholders.autoPrint()
      placeholders.save(`Round ${r + 1} Placeholders.pdf`)
    }
  }

  const downloadDataEntry = (): void => {
    const auditBoards = new jsPDF({ format: 'letter' })
    audit.jurisdictions[0].auditBoards.forEach((board, i) => {
      const qr: HTMLCanvasElement | null = document.querySelector(
        `#qr-${board.id} > canvas`
      )
      /* istanbul ignore else */
      if (qr) {
        if (i > 0) auditBoards.addPage('letter')
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
    })
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
          (a, k) => ({
            ...a,
            [k]: Number(values.contests[i][k]),
          }),
          {} as IRoundPost['contests'][0]['results']
        ),
      })),
    }

    setIsLoading(true)
    const response = await api<IErrorResponse>(
      `/election/${electionId}/jurisdiction/${jurisdictionID}/${values.round}/results`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      }
    )
    if (!response) {
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
  }

  const [ballots, setBallots] = useState<IBallot[]>([])
  useEffect(() => {
    ;(async () => {
      if (audit.online) {
        const b = await getBallots(audit.rounds.length - 1)
        setBallots(b)
      }
    })()
  }, [audit.online, audit.rounds.length, getBallots])
  const completeBallots: number = ballots.filter(b => b.status).length

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
        contest.choices.reduce(
          (acc, choice) => ({
            ...acc,
            [choice.id]: contest.results[choice.id] || 0,
          }),
          {}
        )
      ),
      round: i + 1,
    }
    const isSubmitted =
      i + 1 < audit.rounds.length ||
      aggregateContests.every(
        (contest: AggregateContest) => !!contest.endMeasurements.isComplete
      )
    const completeContests = aggregateContests.reduce(
      (acc, c) => (c.endMeasurements.isComplete ? acc + 1 : acc),
      0
    )
    const aggregatedBallots = aggregateContests.reduce(
      (acc: number, contest: AggregateContest) =>
        /* istanbul ignore next */
        acc + (contest.sampleSize || 0),
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
          <form data-testid={`form-three-${i + 1}`}>
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
                  (contest: AggregateContest, contestIndex: number) => (
                    <p key={contest.id}>
                      Contest {contestIndex + 1}: {contest.sampleSize} ballots
                    </p>
                  )
                )}
              </FormSectionDescription>
              {i === 0 && audit.online && (
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
                              {audit.online ? (
                                <ProgressBar
                                  value={
                                    i + 1 < audit.rounds.length
                                      ? 1
                                      : completeBallots / ballots.length
                                  }
                                  animate={i + 1 === audit.rounds.length}
                                  intent="primary"
                                />
                              ) : (
                                <>
                                  {!isSubmitted && (
                                    <FormSectionDescription>
                                      Enter the number of votes recorded for
                                      each candidate/choice in the audited
                                      ballots for Round {i + 1}, Contest {j + 1}
                                    </FormSectionDescription>
                                  )}
                                  <InputSection>
                                    {Object.keys(contest).map(choiceId => {
                                      const { name } = aggregateContests[
                                        j
                                      ].choices.find(
                                        (candidate: ICandidate) =>
                                          candidate.id === choiceId
                                      )!
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
                              )}
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
                      disabled={
                        audit.online && completeBallots < ballots.length
                      }
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
          </form>
        )}
      />
    )
  })
  return <>{roundForms}</>
}

export default React.memo(CalculateRiskMeasurement)
