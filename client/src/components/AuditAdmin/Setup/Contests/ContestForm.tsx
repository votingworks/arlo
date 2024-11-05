/* eslint-disable jsx-a11y/label-has-associated-control */
import React from 'react'
import equal from 'fast-deep-equal'
import styled from 'styled-components'
import {
  Formik,
  FormikProps,
  Field,
  FieldArray,
  ErrorMessage,
  getIn,
} from 'formik'
import {
  HTMLSelect,
  Menu,
  Checkbox,
  Popover,
  Position,
  Button,
  Colors,
  HTMLTable,
} from '@blueprintjs/core'
import uuidv4 from 'uuidv4'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormSection from '../../../Atoms/Form/FormSection'
import FormField from '../../../Atoms/Form/FormField'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import schema from './schema'
import { useContests, useUpdateContests } from '../../../useContests'
import { useJurisdictionsDeprecated } from '../../../useJurisdictions'
import { IContest } from '../../../../types'
import Card from '../../../Atoms/SpacedCard'
import { testNumber } from '../../../utilities'
import { isObjectEmpty } from '../../../../utils/objects'
import useStandardizedContests from '../../../useStandardizedContests'
import { ErrorLabel } from '../../../Atoms/Form/_helpers'
import { partition } from '../../../../utils/array'
import { AuditType } from '../../../useAuditSettings'
import { parse as parseNumber } from '../../../../utils/number-schema'

export const WideField = styled(FormField)`
  width: 100%;
`

const CustomMenuItem = styled.li`
  .bp3-menu-item {
    display: inline-block;
    width: 100%;
  }
  .bp3-checkbox {
    float: right;
    margin: 0;
  }
`

type ICheckboxList = {
  title: string
  value: string
  checked: boolean
}[]

interface IDropdownCheckboxListProps {
  formikBag: {
    values: FormikProps<{ contests: IContestValues[] }>['values']
    setFieldValue: FormikProps<{ contests: IContestValues[] }>['setFieldValue']
  }
  text: string
  optionList: ICheckboxList
  contestIndex: number
}

const DropdownCheckboxList: React.FC<IDropdownCheckboxListProps> = ({
  formikBag: { values, setFieldValue },
  text,
  optionList,
  contestIndex,
}) => {
  const jurisdictionList = values.contests[contestIndex].jurisdictionIds
  const updateList = (value: string, checked: boolean) => {
    const itemIndex = jurisdictionList.indexOf(value)
    /* istanbul ignore else */
    if (checked && itemIndex === -1) {
      jurisdictionList.push(value)
    } else if (!checked && itemIndex > -1) {
      jurisdictionList.splice(itemIndex, 1)
    }
    setFieldValue(`contests[${contestIndex}].jurisdictionIds`, jurisdictionList)
  }
  const selectAll = (checked: boolean) => {
    if (checked) {
      setFieldValue(
        `contests[${contestIndex}].jurisdictionIds`,
        optionList.map(v => v.value)
      )
    } else {
      setFieldValue(`contests[${contestIndex}].jurisdictionIds`, [])
    }
  }
  const menu = (
    <Menu>
      <CustomMenuItem key="select-all">
        {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
        <label className="bp3-menu-item">
          Select all
          <Checkbox
            inline
            checked={
              getIn(values, `contests[${contestIndex}].jurisdictionIds`)
                .length === optionList.length
            }
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              selectAll(e.currentTarget.checked)
            }
          />
        </label>
      </CustomMenuItem>
      {optionList.map(v => (
        <CustomMenuItem key={v.value}>
          {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
          <label className="bp3-menu-item">
            {v.title}
            <Checkbox
              inline
              checked={jurisdictionList.indexOf(v.value) > -1}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateList(v.value, e.currentTarget.checked)
              }
            />
          </label>
        </CustomMenuItem>
      ))}
    </Menu>
  )
  return (
    <Popover position={Position.BOTTOM} content={menu}>
      <FormButton>{text}</FormButton>
    </Popover>
  )
}

const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

interface IProps {
  electionId: string
  isTargeted: boolean
  auditType: AuditType
  goToPrevStage: () => void
  goToNextStage: () => void
}

interface IChoiceValues {
  id: string
  name: string
  numVotes: string
  numVotesCvr?: number
  numVotesNonCvr?: number
}

export interface IContestValues {
  id: string
  name: string
  isTargeted: boolean
  numWinners: string
  votesAllowed: string
  choices: IChoiceValues[]
  totalBallotsCast?: string
  jurisdictionIds: string[]
}

const contestToValues = (contest: IContest): IContestValues => ({
  ...contest,
  numWinners: contest.numWinners.toString(),
  votesAllowed: contest.votesAllowed.toString(),
  choices: contest.choices.map(choice => ({
    ...choice,
    numVotes: choice.numVotes.toString(),
  })),
  totalBallotsCast: contest.totalBallotsCast?.toString(),
})

const contestFromValues = (contest: IContestValues): IContest => ({
  ...contest,
  id: contest.id || uuidv4(), // preserve given id if present, generate new one if empty string
  totalBallotsCast: parseNumber(contest.totalBallotsCast),
  numWinners: parseNumber(contest.numWinners),
  votesAllowed: parseNumber(contest.votesAllowed),
  choices: contest.choices.map(choice => ({
    ...choice,
    id: choice.id || uuidv4(),
    numVotes: parseNumber(choice.numVotes),
  })),
})

const ContestForm: React.FC<IProps> = ({
  electionId,
  isTargeted,
  goToPrevStage,
  goToNextStage,
  auditType,
}) => {
  const contestValues: IContestValues[] = [
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

  const isHybrid = auditType === 'HYBRID'
  const isBallotPolling = auditType === 'BALLOT_POLLING'

  const contestsQuery = useContests(electionId)
  const updateContestsMutation = useUpdateContests(electionId, auditType)
  const jurisdictions = useJurisdictionsDeprecated(electionId)
  const standardizedContests = useStandardizedContests(electionId)

  if (
    (isHybrid && !standardizedContests) ||
    !jurisdictions ||
    !contestsQuery.isSuccess
  )
    return null // Still loading

  const contests = contestsQuery.data
  const [formContests, restContests] = partition(
    contests,
    c => c.isTargeted === isTargeted
  )

  const initialValues = {
    contests: formContests.length
      ? formContests.map(contestToValues)
      : contestValues,
  }

  const isOpportunisticFormClean = (
    touched: Record<string, unknown>,
    values: { contests: IContestValues[] }
  ) => {
    return (
      !isTargeted && (isObjectEmpty(touched) || equal(initialValues, values))
    )
  }

  const submit = async (values: { contests: IContestValues[] }) => {
    const contestsToUpdate = isHybrid
      ? values.contests.map(contest => ({
          ...contest,
          jurisdictionIds: standardizedContests!.find(
            c => c.name === contest.name
          )!.jurisdictionIds,
        }))
      : values.contests
    await updateContestsMutation.mutateAsync(
      contestsToUpdate.map(contestFromValues).concat(restContests)
    )
    goToNextStage()
  }
  return (
    <Formik
      initialValues={initialValues}
      validationSchema={schema(auditType)}
      enableReinitialize
      onSubmit={submit}
    >
      {({
        values,
        touched,
        handleSubmit,
        setFieldValue,
        isSubmitting,
      }: FormikProps<{ contests: IContestValues[] }>) => (
        <form
          data-testid="form-one"
          style={{ width: '100%' }}
          onSubmit={e => {
            e.preventDefault()
            if (isOpportunisticFormClean(touched, values)) goToNextStage()
            else handleSubmit()
          }}
        >
          <FormWrapper
            title={isTargeted ? 'Target Contests' : 'Opportunistic Contests'}
          >
            <FieldArray
              name="contests"
              render={contestsArrayHelpers => (
                <>
                  {values.contests.map((contest: IContestValues, i: number) => {
                    const jurisdictionOptions = jurisdictions.map(j => ({
                      title: j.name,
                      value: j.id,
                      checked: contest.jurisdictionIds.indexOf(j.id) > -1,
                    }))
                    return (
                      /* eslint-disable react/no-array-index-key */
                      <Card
                        key={i}
                        elevation={0}
                        style={{ background: Colors.LIGHT_GRAY5 }}
                      >
                        <FormSection
                          label={`Contest ${
                            values.contests.length > 1 ? i + 1 : ''
                          } Info`}
                          style={{
                            marginTop: 0,
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '10px',
                          }}
                        >
                          {isHybrid && standardizedContests ? (
                            <label htmlFor={`contests[${i}].name`}>
                              <b>Contest Name</b>
                              <br />
                              <Field
                                component={Select}
                                id={`contests[${i}].name`}
                                name={`contests[${i}].name`}
                                onChange={(
                                  e: React.FormEvent<HTMLSelectElement>
                                ) =>
                                  setFieldValue(
                                    `contests[${i}].name`,
                                    e.currentTarget.value
                                  )
                                }
                                value={values.contests[i].name}
                                options={[
                                  { value: '' },
                                  ...standardizedContests.map(({ name }) => ({
                                    label: name,
                                    value: name,
                                  })),
                                ]}
                              />
                              <ErrorMessage
                                name={`contests[${i}].name`}
                                component={ErrorLabel}
                              />
                            </label>
                          ) : (
                            <label htmlFor={`contests[${i}].name`}>
                              <b>Name</b>
                              <Field
                                id={`contests[${i}].name`}
                                name={`contests[${i}].name`}
                                component={FormField}
                              />
                            </label>
                          )}
                          <label htmlFor={`contests[${i}].numWinners`}>
                            <b>Number of Winners</b>
                            <Field
                              id={`contests[${i}].numWinners`}
                              name={`contests[${i}].numWinners`}
                              component={FormField}
                              validate={testNumber()}
                            />
                          </label>
                          <label htmlFor={`contests[${i}].votesAllowed`}>
                            <b>Votes Allowed</b>
                            <Field
                              id={`contests[${i}].votesAllowed`}
                              name={`contests[${i}].votesAllowed`}
                              component={FormField}
                              validate={testNumber()}
                            />
                          </label>
                        </FormSection>
                        <FieldArray
                          name={`contests[${i}].choices`}
                          render={choicesArrayHelpers => (
                            <FormSection
                              label="Vote Totals"
                              description="Enter the name and vote total for each contest choice on the ballot."
                            >
                              <HTMLTable
                                striped
                                bordered
                                style={{
                                  width: '100%',
                                  border: `1px solid ${Colors.LIGHT_GRAY1}`,
                                }}
                              >
                                <thead>
                                  <th>Choice Name</th>
                                  <th>Votes</th>
                                  <th />
                                </thead>
                                <tbody>
                                  {contest.choices.map(
                                    (choice: IChoiceValues, j: number) => (
                                      <tr key={j}>
                                        <td>
                                          <Field
                                            name={`contests[${i}].choices[${j}].name`}
                                            component={WideField}
                                          />
                                        </td>
                                        <td>
                                          <Field
                                            name={`contests[${i}].choices[${j}].numVotes`}
                                            component={WideField}
                                          />
                                        </td>
                                        <td>
                                          <Button
                                            onClick={() =>
                                              choicesArrayHelpers.remove(j)
                                            }
                                            intent="danger"
                                            icon="remove"
                                            disabled={
                                              contest.choices.length < 2
                                            }
                                            minimal
                                          >
                                            Remove
                                          </Button>
                                        </td>
                                      </tr>
                                    )
                                  )}
                                </tbody>
                              </HTMLTable>
                              <Button
                                style={{ marginTop: '10px' }}
                                onClick={() =>
                                  choicesArrayHelpers.push({
                                    name: '',
                                    numVotes: '',
                                  })
                                }
                                icon="add"
                              >
                                Add Choice
                              </Button>
                            </FormSection>
                          )}
                        />
                        {isBallotPolling && (
                          <FormSection
                            label="Total Ballot Cards Cast"
                            description="Enter the overall number of ballot cards cast in jurisdictions containing this contest."
                          >
                            <label htmlFor={`contests[${i}].totalBallotsCast`}>
                              Total Ballot Cards Cast for Contest{' '}
                              {/* istanbul ignore next */
                              values.contests.length > 1 ? i + 1 : ''}
                              <Field
                                id={`contests[${i}].totalBallotsCast`}
                                name={`contests[${i}].totalBallotsCast`}
                                validate={testNumber()}
                                component={FormField}
                              />
                            </label>
                          </FormSection>
                        )}
                        {!isHybrid && (
                          <FormSection
                            label="Contest Universe"
                            description="Select the jurisdictions where this contest appeared on the ballot."
                            style={{ marginBottom: 0 }}
                          >
                            <DropdownCheckboxList
                              text="Select Jurisdictions"
                              optionList={jurisdictionOptions}
                              formikBag={{ values, setFieldValue }}
                              contestIndex={i}
                            />
                            <span style={{ marginLeft: '10px' }}>
                              {values.contests[i].jurisdictionIds.length === 0
                                ? 'No jurisdictions selected'
                                : `${values.contests[i].jurisdictionIds.length} jurisdictions selected`}
                            </span>
                            <ErrorMessage
                              name={`contests[${i}].jurisdictionIds`}
                              component={ErrorLabel}
                            />
                          </FormSection>
                        )}
                        {values.contests.length > 1 && (
                          <div
                            style={{
                              display: 'flex',
                              justifyContent: 'flex-end',
                            }}
                          >
                            <Button
                              icon="remove"
                              intent="danger"
                              minimal
                              onClick={() => contestsArrayHelpers.remove(i)}
                            >
                              Remove Contest
                            </Button>
                          </div>
                        )}
                      </Card>
                    )
                  })}
                  <div style={{ paddingTop: '15px' }}>
                    <Button
                      icon="add"
                      type="button"
                      onClick={() =>
                        contestsArrayHelpers.push({ ...contestValues[0] })
                      }
                    >
                      Add Contest
                    </Button>
                  </div>
                </>
              )}
            />
          </FormWrapper>
          <FormButtonBar style={{ marginTop: '15px' }}>
            <Button onClick={goToPrevStage} icon="arrow-left">
              Back
            </Button>
            <Button
              type="submit"
              intent="primary"
              rightIcon="arrow-right"
              loading={isSubmitting}
            >
              Save &amp; Next
            </Button>
          </FormButtonBar>
        </form>
      )}
    </Formik>
  )
}

export default ContestForm
