/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Formik, FormikProps, getIn } from 'formik'
import { Checkbox, Spinner } from '@blueprintjs/core'
import { Column, Cell } from 'react-table'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import useStandardizedContests, {
  IStandardizedContest,
} from '../../useStandardizedContests'
import useJurisdictions from '../../useJurisdictions'
import { IAuditSettings } from '../../../../types'
import { Table, FilterInput } from '../../../Atoms/Table'

interface IProps {
  isTargeted: boolean
  nextStage: ISidebarMenuItem
  prevStage: ISidebarMenuItem
  locked: boolean
  auditType: IAuditSettings['auditType']
}

interface IStandardizedContestField extends IStandardizedContest {
  checked: boolean
}

const ContestSelect: React.FC<IProps> = ({
  isTargeted,
  nextStage,
  prevStage,
  //   locked,
}) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [contests, updateContests] = useStandardizedContests(electionId)
  const [filter, setFilter] = useState('')
  const jurisdictions = useJurisdictions(electionId)

  if (!contests || !jurisdictions.length) return null // Still loading

  const submit = async (values: { contests: IStandardizedContestField[] }) => {
    const selectedContests: IStandardizedContest[] = values.contests.reduce(
      (a: IStandardizedContest[], { id, checked, name, jurisdictionIds }) => {
        if (checked) return [...a, { id, name, jurisdictionIds }]
        return a
      },
      []
    )
    const response = await updateContests(selectedContests)
    // TEST TODO
    /* istanbul ignore next */
    if (!response) return
    /* istanbul ignore else */
    if (nextStage.activate) nextStage.activate()
    else throw new Error('Wrong menuItems passed in: activate() is missing')
  }

  const formContests: IStandardizedContestField[] = contests.map(c => ({
    ...c,
    checked: false,
  }))

  // TODO filter by jurisdiction names as well
  const filteredContests = formContests.filter(({ name }) =>
    name.toLowerCase().includes(filter.toLowerCase())
  )

  const columns = (
    values: { contests: IStandardizedContestField[] },
    setFieldValue: FormikProps<{
      contests: IStandardizedContestField[]
    }>['setFieldValue']
  ): Column<IStandardizedContest>[] => [
    {
      id: 'select',
      Header: 'Select',
      accessor: row => row,
      // eslint-disable-next-line react/display-name
      Cell: ({
        row: { original: contest, index },
      }: Cell<IStandardizedContest>) => (
        <Checkbox
          inline
          checked={getIn(values, `contests[${index}].checked`)}
          onChange={({
            currentTarget: { checked },
          }: React.ChangeEvent<HTMLInputElement>) =>
            setFieldValue(`contests[${index}]`, { ...contest, checked })
          }
        />
      ),
    },
    {
      Header: 'Contest Name',
      accessor: 'name',
    },
    {
      Header: 'Jurisdiction(s)',
      accessor: row =>
        row.jurisdictionIds.length === jurisdictions.length
          ? 'All'
          : row.jurisdictionIds
              .map(id => jurisdictions.find(j => j.id === id)!.name)
              .join(' - '),
    },
  ]

  return (
    <Formik
      initialValues={{
        contests: formContests,
      }}
      enableReinitialize
      onSubmit={submit}
    >
      {({
        values,
        handleSubmit,
        setFieldValue,
      }: FormikProps<{ contests: IStandardizedContestField[] }>) => (
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
              data={filteredContests}
              columns={columns(values, setFieldValue)}
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
