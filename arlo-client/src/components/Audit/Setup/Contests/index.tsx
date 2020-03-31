/* eslint-disable jsx-a11y/label-has-associated-control */
import React from 'react'
import { Formik, FormikProps, Form, Field, FieldArray } from 'formik'
import { Spinner } from '@blueprintjs/core'
import { IAudit } from '../../../../types'
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
import { IContestValues, IValues, IChoiceValues } from './types'
import schema from './schema'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'

interface IProps {
  audit: IAudit
  isTargeted: boolean
  nextStage: ISidebarMenuItem
  prevStage: ISidebarMenuItem
}

const contestValues: { contests: IContestValues[] } = {
  contests: [
    {
      name: '',
      isTargeted: true,
      totalBallotsCast: '',
      numWinners: '1',
      votesAllowed: '1',
      choices: [
        {
          name: '',
          numVotes: '',
        },
        {
          name: '',
          numVotes: '',
        },
      ],
    },
  ],
}

const Contests: React.FC<IProps> = ({
  isTargeted,
  audit,
  nextStage,
  prevStage,
}) => {
  const initialValues: IValues = {
    contests: audit.contests.length ? audit.contests : contestValues.contests,
  }
  return (
    <Formik
      initialValues={initialValues}
      validationSchema={schema}
      onSubmit={v => {
        // eslint-disable-next-line no-console
        console.log(v)
        nextStage.activate()
      }}
    >
      {({ values, handleSubmit }: FormikProps<IValues>) => (
        <Form data-testid="form-one">
          <FormWrapper
            title={isTargeted ? 'Target Contests' : 'Opportunistic Contests'}
          >
            <FieldArray
              name="contests"
              render={() => (
                <>
                  {values.contests.map((contest: IContestValues, i: number) => (
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
                            disabled={audit.frozenAt}
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
                            disabled={audit.frozenAt}
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
                            disabled={audit.frozenAt}
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
                                (choice: IChoiceValues, j: number) => (
                                  /* eslint-disable react/no-array-index-key */
                                  <React.Fragment key={j}>
                                    <InputFieldRow>
                                      <InputLabel>
                                        Name of Candidate/Choice {j + 1}
                                        <Field
                                          name={`contests[${i}].choices[${j}].name`}
                                          disabled={audit.frozenAt}
                                          component={FlexField}
                                        />
                                      </InputLabel>
                                      <InputLabel>
                                        Votes for Candidate/Choice {j + 1}
                                        <Field
                                          name={`contests[${i}].choices[${j}].numVotes`}
                                          disabled={audit.frozenAt}
                                          component={FlexField}
                                        />
                                      </InputLabel>
                                      {contest.choices.length > 2 &&
                                        !audit.contests.length && (
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
                              {!audit.contests.length && (
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
                            disabled={audit.frozenAt}
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
