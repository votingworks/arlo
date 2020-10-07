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
// import useJurisdictions from '../../useJurisdictions'
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
  auditType,
}) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [contests, updateContests] = useStandardizedContests(electionId)
  const [filter, setFilter] = useState('')
  //   const jurisdictions = useJurisdictions(electionId)

  if (!contests) return null // Still loading

  const isBatch = auditType === 'BATCH_COMPARISON'
  // const isBallotComparison = auditType === 'BALLOT_COMPARISON'

  /* istanbul ignore next */
  if (isBatch && !isTargeted && nextStage.activate) nextStage.activate() // skip to next stage if on opportunistic contests screen and during a batch audit (until batch audits support multiple contests)

  const submit = async (values: { contests: IStandardizedContestField[] }) => {
    const selectedContests: IStandardizedContest[] = values.contests.reduce(
      (a: IStandardizedContest[], { checked, name, jurisdictionIds }) => {
        if (checked) return [...a, { name, jurisdictionIds }]
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
      accessor: row => row.jurisdictionIds.join(' - '),
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
              Choose which contests to target for audit by checking the
              checkboxes below. To filter the contest list, use the search box
              at the top.
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
