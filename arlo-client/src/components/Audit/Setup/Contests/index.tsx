/* eslint-disable jsx-a11y/label-has-associated-control */
import React from 'react'
import { useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import { Formik, FormikProps, Form, Field, FieldArray } from 'formik'
import { Spinner } from '@blueprintjs/core'
import FormWrapper from '../../../Form/FormWrapper'
import FormSection, { FormSectionDescription } from '../../../Form/FormSection'
import FormField from '../../../Form/FormField'
import {
  TwoColumnSection,
  InputFieldRow,
  InputLabel,
  FlexField,
  Action,
} from '../../EstimateSampleSize'
import FormButtonBar from '../../../Form/FormButtonBar'
import FormButton from '../../../Form/FormButton'
import { IContests } from './types'
import schema from './schema'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import useContestsApi from './useContestsApi'
import { IContest, ICandidate } from '../../../../types'

interface IProps {
  isTargeted: boolean
  nextStage: ISidebarMenuItem
  prevStage: ISidebarMenuItem
  locked: boolean
}

const Contests: React.FC<IProps> = ({
  isTargeted,
  nextStage,
  prevStage,
  locked,
}) => {
  const contestValues: IContests = {
    contests: [
      {
        id: '',
        name: '',
        isTargeted,
        totalBallotsCast: '',
        numWinners: '1',
        votesAllowed: '1',
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
    ],
  }
  const { electionId } = useParams()
  const [{ contests }, updateContests] = useContestsApi(electionId!, isTargeted)
  const filteredContests = {
    contests: contests.filter(c => c.isTargeted === isTargeted),
  }
  const submit = async (values: IContests) => {
    try {
      const responseOne = await updateContests(values.contests)
      if (!responseOne) return
      nextStage.activate()
    } catch (err) {
      toast.error(err.message)
    }
  }
  return (
    <Formik
      initialValues={
        filteredContests.contests.length ? filteredContests : contestValues
      }
      validationSchema={schema}
      onSubmit={submit}
    >
      {({ values, handleSubmit }: FormikProps<IContests>) => (
        <Form data-testid="form-one">
          <FormWrapper
            title={isTargeted ? 'Target Contests' : 'Opportunistic Contests'}
          >
            <FieldArray
              name="contests"
              render={() => (
                <>
                  {values.contests.map((contest: IContest, i: number) => (
                    /* eslint-disable react/no-array-index-key */
                    <React.Fragment key={i}>
                      {i > 0 && (
                        /* istanbul ignore next */
                        <FormSection>
                          <hr />
                        </FormSection>
                      )}
                      <FormSection
                        label={`Contest ${
                          /* istanbul ignore next */
                          values.contests.length > 1 ? i + 1 : ''
                        } Info`}
                        description="Enter the name of the contest that will drive the audit."
                      >
                        <label htmlFor={`contests[${i}].name`}>
                          Contest{' '}
                          {/* istanbul ignore next */
                          values.contests.length > 1 ? i + 1 : ''}{' '}
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
                          />
                        </label>
                        {/* values.contests.length > 1 &&
                            !audit.contests.length && (
                              <Action
                                onClick={() => contestsArrayHelpers.remove(i)}
                              >
                                Remove Contest {i + 1}
                              </Action>
                            ) */}
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
                            disabled={locked}
                            component={FormField}
                          />
                        </label>
                      </FormSection>
                    </React.Fragment>
                  ))}
                  {/* <FormButtonBar>
                    {!audit.contests.length && (
                      <FormButton
                        type="button"
                        onClick={() =>
                          contestsArrayHelpers.push({ ...contestValues[0] })
                        }
                      >
                        Add another isTargeted contest
                      </FormButton>
                    )}
                  </FormButtonBar> */}
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
        </Form>
      )}
    </Formik>
  )
}

export default Contests
