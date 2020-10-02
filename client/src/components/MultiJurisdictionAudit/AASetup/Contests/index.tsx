/* eslint-disable jsx-a11y/label-has-associated-control */
import React from 'react'
import { useParams } from 'react-router-dom'
import { Formik, FormikProps, Field, FieldArray } from 'formik'
import { Spinner } from '@blueprintjs/core'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormSection, {
  FormSectionDescription,
} from '../../../Atoms/Form/FormSection'
import FormField from '../../../Atoms/Form/FormField'
import {
  TwoColumnSection,
  InputFieldRow,
  InputLabel,
  FlexField,
  Action,
} from '../../../SingleJurisdictionAudit/EstimateSampleSize'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import schema from './schema'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import useContests from '../../useContests'
import useJurisdictions from '../../useJurisdictions'
import { IContest, ICandidate, IAuditSettings } from '../../../../types'
import DropdownCheckboxList from './DropdownCheckboxList'
import Card from '../../../Atoms/SpacedCard'
import { testNumber } from '../../../utilities'

interface IProps {
  isTargeted: boolean
  nextStage: ISidebarMenuItem
  prevStage: ISidebarMenuItem
  locked: boolean
  auditType: IAuditSettings['auditType']
}

const Contests: React.FC<IProps> = ({
  isTargeted,
  nextStage,
  prevStage,
  locked,
  auditType,
}) => {
  const contestValues: IContest[] = [
    {
      id: '',
      name: '',
      isTargeted,
      totalBallotsCast: '',
      numWinners: '1',
      votesAllowed: '1',
      jurisdictionIds: [],
      choices: [
        {
          id: '',
          name: '',
          numVotes: '',
        },
        {
          id: '',
          name: '',
          numVotes: '',
        },
      ],
    },
  ]
  const { electionId } = useParams<{ electionId: string }>()
  const [contests, updateContests] = useContests(electionId)
  const jurisdictions = useJurisdictions(electionId)

  if (!contests) return null // Still loading
  const filteredContests = contests.filter(c => c.isTargeted === isTargeted)

  const isBatch = auditType === 'BATCH_COMPARISON'
  // const isBallotComparison = auditType === 'BALLOT_COMPARISON'

  /* istanbul ignore next */
  if (isBatch && !isTargeted && nextStage.activate) nextStage.activate() // skip to next stage if on opportunistic contests screen and during a batch audit (until batch audits support multiple contests)

  const submit = async (values: { contests: IContest[] }) => {
    const response = await updateContests(values.contests)
    // TEST TODO
    /* istanbul ignore next */
    if (!response) return
    /* istanbul ignore else */
    if (nextStage.activate) nextStage.activate()
    else throw new Error('Wrong menuItems passed in: activate() is missing')
  }
  return (
    <Formik
      initialValues={{
        contests: filteredContests.length ? filteredContests : contestValues,
      }}
      validationSchema={schema}
      enableReinitialize
      onSubmit={submit}
    >
      {({
        values,
        handleSubmit,
        setFieldValue,
      }: FormikProps<{ contests: IContest[] }>) => (
        <form data-testid="form-one">
          <FormWrapper
            title={isTargeted ? 'Target Contests' : 'Opportunistic Contests'}
          >
            <FieldArray
              name="contests"
              render={contestsArrayHelpers => (
                <>
                  {values.contests.map((contest: IContest, i: number) => {
                    const jurisdictionOptions = jurisdictions.map(j => ({
                      title: j.name,
                      value: j.id,
                      checked: contest.jurisdictionIds.indexOf(j.id) > -1,
                    }))
                    return (
                      /* eslint-disable react/no-array-index-key */
                      <Card key={i}>
                        <FormSection
                          label={`Contest ${
                            values.contests.length > 1 ? i + 1 : ''
                          } Info`}
                          description="Enter the name of the contest that will drive the audit."
                        >
                          <br />
                          <label htmlFor={`contests[${i}].name`}>
                            Contest {values.contests.length > 1 ? i + 1 : ''}{' '}
                            Name
                            <Field
                              id={`contests[${i}].name`}
                              name={`contests[${i}].name`}
                              disabled={locked}
                              component={FormField}
                            />
                          </label>
                          <FormSectionDescription>
                            Enter the number of winners for the contest.
                          </FormSectionDescription>
                          <label htmlFor={`contests[${i}].numWinners`}>
                            Winners
                            <Field
                              id={`contests[${i}].numWinners`}
                              name={`contests[${i}].numWinners`}
                              disabled={locked}
                              component={FormField}
                              validate={testNumber()}
                            />
                          </label>
                          <FormSectionDescription>
                            Number of selections the voter can make in the
                            contest.
                          </FormSectionDescription>
                          <label htmlFor={`contests[${i}].votesAllowed`}>
                            Votes Allowed
                            <Field
                              id={`contests[${i}].votesAllowed`}
                              name={`contests[${i}].votesAllowed`}
                              disabled={locked}
                              component={FormField}
                              validate={testNumber()}
                            />
                          </label>
                        </FormSection>
                        <FieldArray
                          name={`contests[${i}].choices`}
                          render={choicesArrayHelpers => (
                            <FormSection
                              label="Candidates/Choices & Vote Totals"
                              description="Enter the name of each candidate choice that appears on the ballot for this contest."
                            >
                              <TwoColumnSection>
                                {contest.choices.map(
                                  (choice: ICandidate, j: number) => (
                                    /* eslint-disable react/no-array-index-key */
                                    <React.Fragment key={j}>
                                      <InputFieldRow>
                                        <InputLabel>
                                          Name of Candidate/Choice {j + 1}
                                          <Field
                                            name={`contests[${i}].choices[${j}].name`}
                                            disabled={locked}
                                            component={FlexField}
                                          />
                                        </InputLabel>
                                        <InputLabel>
                                          Votes for Candidate/Choice {j + 1}
                                          <Field
                                            name={`contests[${i}].choices[${j}].numVotes`}
                                            disabled={locked}
                                            component={FlexField}
                                            validate={testNumber()}
                                          />
                                        </InputLabel>
                                        {contest.choices.length > 2 &&
                                          !locked && (
                                            <Action
                                              onClick={() =>
                                                choicesArrayHelpers.remove(j)
                                              }
                                            >
                                              Remove choice {j + 1}
                                            </Action>
                                          )}
                                      </InputFieldRow>
                                    </React.Fragment>
                                  )
                                )}
                                {!locked && (
                                  <Action
                                    onClick={() =>
                                      choicesArrayHelpers.push({
                                        name: '',
                                        numVotes: '',
                                      })
                                    }
                                  >
                                    Add a new candidate/choice
                                  </Action>
                                )}
                              </TwoColumnSection>
                            </FormSection>
                          )}
                        />
                        <FormSection
                          label="Total Ballots Cast"
                          description="Enter the overall number of ballot cards cast in jurisdictions containing this contest."
                        >
                          <label htmlFor={`contests[${i}].totalBallotsCast`}>
                            Total Ballots for Contest{' '}
                            {/* istanbul ignore next */
                            values.contests.length > 1 ? i + 1 : ''}
                            <Field
                              id={`contests[${i}].totalBallotsCast`}
                              name={`contests[${i}].totalBallotsCast`}
                              validate={testNumber()}
                              disabled={locked}
                              component={FormField}
                            />
                          </label>
                        </FormSection>
                        <FormSection
                          label="Contest Universe"
                          description="Select the jurisdictions where this contest appeared on the ballot."
                        >
                          <DropdownCheckboxList
                            text="Select Jurisdictions"
                            optionList={jurisdictionOptions}
                            formikBag={{ values, setFieldValue }}
                            contestIndex={i}
                          />
                        </FormSection>
                        {values.contests.length > 1 && (
                          <FormButtonBar right>
                            <FormButton
                              intent="danger"
                              onClick={() => contestsArrayHelpers.remove(i)}
                            >
                              Remove Contest {i + 1}
                            </FormButton>
                          </FormButtonBar>
                        )}
                      </Card>
                    )
                  })}
                  {!isBatch && ( // TODO support multiple contests in batch comparison audits
                    <FormButtonBar>
                      <FormButton
                        type="button"
                        onClick={() =>
                          contestsArrayHelpers.push({ ...contestValues[0] })
                        }
                      >
                        Add another {isTargeted ? 'targeted' : 'opportunistic'}{' '}
                        contest
                      </FormButton>
                    </FormButtonBar>
                  )}
                </>
              )}
            />
          </FormWrapper>
          {nextStage.state === 'processing' ? (
            <Spinner />
          ) : (
            <FormButtonBar>
              <FormButton onClick={prevStage.activate}>Back</FormButton>
              <FormButton
                type="submit"
                intent="primary"
                disabled={nextStage.state === 'locked'}
                onClick={handleSubmit}
              >
                Save &amp; Next
              </FormButton>
            </FormButtonBar>
          )}
        </form>
      )}
    </Formik>
  )
}

export default Contests
