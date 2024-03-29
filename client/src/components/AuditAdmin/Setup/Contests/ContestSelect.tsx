/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState } from 'react'
import { Formik, FormikProps } from 'formik'
import { Checkbox, NumericInput } from '@blueprintjs/core'
import { Cell } from 'react-table'
import uuidv4 from 'uuidv4'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import useStandardizedContests from '../../../useStandardizedContests'
import { useJurisdictionsDeprecated } from '../../../useJurisdictions'
import { Table, FilterInput } from '../../../Atoms/Table'
import useContestsBallotComparison, {
  INewContest,
} from '../../../useContestsBallotComparison'

interface IProps {
  electionId: string
  isTargeted: boolean
  goToPrevStage: () => void
  goToNextStage: () => void
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
  electionId,
  isTargeted,
  goToPrevStage,
  goToNextStage,
}) => {
  const standardizedContests = useStandardizedContests(electionId)
  const [contests, updateContests] = useContestsBallotComparison(electionId)
  const [filter, setFilter] = useState('')
  const jurisdictions = useJurisdictionsDeprecated(electionId)

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
    goToNextStage()
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
      {({
        values,
        handleSubmit,
        setValues,
        isSubmitting,
      }: FormikProps<IFormValues>) => (
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
                        // We have to use setValues because the contest name
                        // might have a dot or apostrophe in it, so
                        // setFieldValue won't work.
                        setValues({
                          ...values,
                          [contestName]: {
                            ...values[contestName],
                            checked: e.currentTarget.checked,
                          },
                        })
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
                    <NumericInput
                      type="number"
                      value={values[contestName].numWinners}
                      onValueChange={(value: number) =>
                        // We have to use setValues because the contest name
                        // might have a dot or apostrophe in it, so
                        // setFieldValue won't work.
                        setValues({
                          ...values,
                          [contestName]: {
                            ...values[contestName],
                            numWinners: value,
                          },
                        })
                      }
                      disabled={
                        !values[contestName].checked ||
                        values[contestName].isTargeted !== isTargeted
                      }
                      min={1}
                      minorStepSize={null} // Only allow integers
                      style={{ width: '60px' }}
                    />
                  ),
                },
              ]}
            />
          </FormWrapper>
          <FormButtonBar>
            <FormButton onClick={goToPrevStage}>Back</FormButton>
            <FormButton
              type="submit"
              intent="primary"
              loading={isSubmitting}
              onClick={handleSubmit}
            >
              Save &amp; Next
            </FormButton>
          </FormButtonBar>
        </form>
      )}
    </Formik>
  )
}

export default ContestSelect
