/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Formik, FormikProps, Field } from 'formik'
import { Checkbox, Spinner } from '@blueprintjs/core'
import { Cell } from 'react-table'
import uuidv4 from 'uuidv4'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import useStandardizedContests from '../../useStandardizedContests'
import useJurisdictions from '../../useJurisdictions'
import { Table, FilterInput } from '../../../Atoms/Table'
import { IAuditSettings } from '../../useAuditSettings'
import useContestsBallotComparison, {
  INewContest,
} from '../../useContestsBallotComparison'
import FormField from '../../../Atoms/Form/FormField'

interface IProps {
  isTargeted: boolean
  nextStage: ISidebarMenuItem
  prevStage: ISidebarMenuItem
  locked: boolean
  auditType: IAuditSettings['auditType']
}

interface IFormValues {
  [contestName: string]: {
    id: string
    isTargeted: boolean
    numWinners: number
    jurisdictionIds: string[]
    checked: boolean
  }
}

const ContestSelect: React.FC<IProps> = ({
  isTargeted,
  nextStage,
  prevStage,
  //   locked,
}) => {
  const { electionId } = useParams<{ electionId: string }>()
  const standardizedContests = useStandardizedContests(electionId)
  const [contests, updateContests] = useContestsBallotComparison(electionId)
  const [filter, setFilter] = useState('')
  const jurisdictions = useJurisdictions(electionId)

  if (!standardizedContests || !jurisdictions || !contests) return null // Still loading

  const initialValues: IFormValues = Object.fromEntries(
    standardizedContests.map(({ name, jurisdictionIds }) => {
      const matchingContest = contests.find(contest => contest.name === name)
      return [
        name,
        {
          id: matchingContest ? matchingContest.id : uuidv4(),
          isTargeted: matchingContest ? matchingContest.isTargeted : isTargeted,
          numWinners: matchingContest ? matchingContest.numWinners : 1,
          jurisdictionIds,
          checked: !!matchingContest,
        },
      ]
    })
  )

  const submit = async (values: IFormValues) => {
    const newContests: INewContest[] = Object.entries(values)
      .filter(([_, { checked }]) => checked)
      // eslint-disable-next-line no-shadow
      .map(([name, { id, isTargeted, numWinners, jurisdictionIds }]) => ({
        name,
        id,
        isTargeted,
        numWinners,
        jurisdictionIds,
      }))
    const response = await updateContests(newContests)
    // TEST TODO
    /* istanbul ignore next */
    if (!response) return
    /* istanbul ignore else */
    if (nextStage.activate) nextStage.activate()
    else throw new Error('Wrong menuItems passed in: activate() is missing')
  }

  const filteredStandardizedContests = standardizedContests.filter(
    ({ name, jurisdictionIds }) => {
      const jurisdictionNames = jurisdictionIds.map(
        jurisdictionId =>
          jurisdictions.find(({ id }) => id === jurisdictionId)!.name
      )
      return [name, ...jurisdictionNames].some(str =>
        str.toLowerCase().includes(filter.toLowerCase())
      )
    }
  )

  return (
    <Formik initialValues={initialValues} onSubmit={submit}>
      {({ values, handleSubmit, setFieldValue }: FormikProps<IFormValues>) => (
        <form>
          <FormWrapper
            title={isTargeted ? 'Target Contests' : 'Opportunistic Contests'}
          >
            <p>
              Choose which contests to{' '}
              {isTargeted ? 'target for audit' : 'audit opportunistically'} by
              checking the checkboxes below. To filter the contest list, use the
              search box at the top.
            </p>
            <FilterInput
              placeholder="Filter by contest or jurisdiction name..."
              value={filter}
              onChange={value => setFilter(value)}
            />
            <Table
              data={filteredStandardizedContests}
              columns={[
                {
                  id: 'select',
                  Header: 'Select',
                  accessor: 'name',
                  // eslint-disable-next-line react/display-name
                  Cell: ({ value: contestName }: Cell) => (
                    <Checkbox
                      inline
                      checked={values[contestName].checked}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setFieldValue(
                          `${contestName}.checked`,
                          e.currentTarget.checked
                        )
                      }
                      disabled={values[contestName].isTargeted !== isTargeted}
                    />
                  ),
                },
                {
                  id: 'name',
                  Header: 'Contest Name',
                  accessor: 'name',
                },
                {
                  id: 'jurisdictions',
                  Header: 'Jurisdictions',
                  accessor: 'jurisdictionIds',
                  disableSortBy: true,
                  Cell: ({ value: jurisdictionIds }: Cell) =>
                    jurisdictionIds.length === jurisdictions.length
                      ? 'All'
                      : jurisdictionIds
                          .map(
                            (id: string) =>
                              jurisdictions.find(j => j.id === id)!.name
                          )
                          .join(' - '),
                },
                {
                  id: 'winners',
                  Header: 'Winners',
                  accessor: 'name',
                  disableSortBy: true,
                  // eslint-disable-next-line react/display-name
                  Cell: ({ value: contestName }: Cell) => (
                    <Field
                      type="number"
                      name={`${contestName}.numWinners`}
                      disabled={
                        !values[contestName].checked ||
                        values[contestName].isTargeted !== isTargeted
                      }
                      min={1}
                      component={FormField}
                    />
                  ),
                },
              ]}
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

export default ContestSelect
