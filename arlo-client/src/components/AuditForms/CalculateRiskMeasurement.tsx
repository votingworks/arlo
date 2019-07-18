import React, { useRef } from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import { Formik, FormikProps } from 'formik'
import * as Yup from 'yup'
import FormSection, {
  FormSectionLabel,
  FormSectionDescription,
} from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormButton from '../Form/FormButton'
import FormField from '../Form/FormField'
import FormButtonBar from '../Form/FormButtonBar'
import { api } from '../utilities'
import { Contest, Round, RoundContest } from '../../types'

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
  'candidate-1': number | ''
  'candidate-2': number | ''
}

const CalculateRiskMeasurmeent = (props: Props) => {
  const { audit, isLoading, setIsLoading, updateAudit } = props

  const sumOfAuditedVotes: { current: number } = useRef(0)

  const downloadBallotRetrievalList = (id: number, e: any) => {
    e.preventDefault()
    const jurisdictionID: string = audit.jurisdictions[0].id
    window.open(`/jurisdiction/${jurisdictionID}/${id}/retrieval-list`)
  }

  const downloadAuditReport = async (i: number, round: any, evt: any) => {
    evt.preventDefault()
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
        contests: [
          {
            id: 'contest-1',
            results: {
              'candidate-1': Number(values['candidate-1']),
              'candidate-2': Number(values['candidate-2']),
            },
          },
        ],
      }

      setIsLoading(true)
      await api(`/jurisdiction/${jurisdictionID}/${values.round}/results`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      })
      sumOfAuditedVotes.current +=
        Number(values['candidate-1']) + Number(values['candidate-2'])
      updateAudit()
    } catch (err) {
      toast.error(err.message)
    }
  }

  const auditedResults: CalculateRiskMeasurementValues[] = audit.rounds.map(
    (r: Round, i: number) => ({
      ...r.contests[0].results,
      round: i + 1,
    })
  )

  return audit.rounds.map((v: Round, i: number) => {
    const round: number = i + 1
    const contest: RoundContest = v.contests[0]
    const maxVotes: number = audit.contests.find(
      (c: Contest) => c.id === contest.id
    ).totalBallotsCast
    const showCalculateButton =
      i + 1 === audit.rounds.length &&
      contest &&
      contest.endMeasurements &&
      !contest.endMeasurements.isComplete
    const schema = Yup.object().shape({
      'candidate-1': Yup.number().test(
        'overCountOne',
        'Cannot exceed the number of total ballots cast',
        function(votes) {
          return (
            (this.parent['candidate-2'] || 0) +
              (votes || 0) +
              sumOfAuditedVotes.current <=
            maxVotes
          )
        }
      ),
      'candidate-2': Yup.number().test(
        'overCountTwo',
        'Cannot exceed the number of total ballots cast',
        function(votes) {
          return (
            (this.parent['candidate-1'] || 0) +
              (votes || 0) +
              sumOfAuditedVotes.current <=
            maxVotes
          )
        }
      ),
    })
    /* eslint-disable react/no-array-index-key */
    return (
      <Formik
        key={i}
        onSubmit={calculateRiskMeasurement}
        initialValues={auditedResults[i]}
        validationSchema={schema}
        enableReinitialize
        render={({
          values,
          errors,
          touched,
          handleChange,
          handleBlur,
          handleSubmit,
        }: FormikProps<CalculateRiskMeasurementValues>) => (
          <FormWrapper title={`Round ${i + 1}`}>
            <FormSection
              label={`Ballot Retrieval List \n
                ${contest ? `${contest.sampleSize} Ballots` : ''}`}
            >
              {/*<SectionLabel>
                Ballot Retrieval List \n
                {contest ? `${contest.sampleSize} Ballots` : ''}
              </SectionLabel>*/}
              <FormButton
                onClick={(e: React.MouseEvent) =>
                  downloadBallotRetrievalList(round, e)
                }
                inline
              >
                Download Ballot Retrieval List for Round {i + 1}
              </FormButton>
              <FormSectionLabel>
                Audited Results: Round {round}
              </FormSectionLabel>
              <FormSectionDescription>
                Enter the number of votes recorded for each candidate/choice in
                the audited ballots for Round {i + 1}
              </FormSectionDescription>
              <form>
                <input type="hidden" name="round" value={values.round} />{' '}
                {/**
                 * use setFieldValue('round', round) ?
                 * need to pass updated round index to calculateRiskMeasurement
                 **/}
                <InputSection>
                  <InlineInput>
                    <InputLabel>{audit.contests[0].choices[0].name}</InputLabel>
                    <FormField
                      name="'candidate-1'"
                      onChange={handleChange}
                      onBlur={handleBlur}
                      value={values['candidate-1']}
                      type="number"
                      error={errors['candidate-1']}
                      touched={touched['candidate-1']}
                    />
                  </InlineInput>
                  <InlineInput>
                    <InputLabel>{audit.contests[0].choices[1].name}</InputLabel>
                    <FormField
                      name="'candidate-2'"
                      onChange={handleChange}
                      onBlur={handleBlur}
                      value={values['candidate-2']}
                      type="number"
                      error={errors['candidate-2']}
                      touched={touched['candidate-2']}
                    />
                  </InlineInput>
                </InputSection>
              </form>
            </FormSection>
            {isLoading && <p>Loading...</p>}
            {showCalculateButton && !isLoading && (
              <FormButtonBar>
                <FormButton type="submit" onClick={handleSubmit}>
                  Calculate Risk Measurement
                </FormButton>
              </FormButtonBar>
            )}
            {contest &&
              contest.endMeasurements.pvalue &&
              contest.endMeasurements.isComplete && (
                <FormSection>
                  <FormSectionLabel>
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
                  </InputSection>
                  {/* {Form 3} */}
                  {contest.endMeasurements.isComplete && (
                    <FormButton
                      onClick={(e: React.MouseEvent) =>
                        downloadAuditReport(i, v, e)
                      }
                      size="sm"
                      inline
                    >
                      Download Audit Report
                    </FormButton>
                  )}
                </FormSection>
              )}
          </FormWrapper>
        )}
      />
    )
  })
}

export default React.memo(CalculateRiskMeasurmeent)
