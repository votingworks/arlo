import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Column, Cell } from 'react-table'
import { Button, Switch } from '@blueprintjs/core'
import H2Title from '../../Atoms/H2Title'
import {
  JurisdictionRoundStatus,
  IJurisdiction,
  prettifyStatus,
} from '../useJurisdictions'
import JurisdictionDetail from './JurisdictionDetail'
import { Table, sortByRank, FilterInput } from '../../Atoms/Table'

const Wrapper = styled.div`
  flex-grow: 1;
  > p {
    margin-bottom: 25px;
  }
`

const TableControls = styled.div`
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 0.5rem;

  > div {
    width: 50%;
  }
`

interface IProps {
  jurisdictions: IJurisdiction[]
}

const Progress: React.FC<IProps> = ({ jurisdictions }: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [filter, setFilter] = useState<string>('')
  const [isShowingBallots, setIsShowingBallots] = useState<boolean>(true)
  const [
    jurisdictionDetail,
    setJurisdictionDetail,
  ] = useState<IJurisdiction | null>(null)

  const columns: Column<IJurisdiction>[] = [
    {
      Header: 'Jurisdiction Name',
      accessor: 'name',
      // eslint-disable-next-line react/display-name
      Cell: ({ row: { original: jurisdiction } }: Cell<IJurisdiction>) => (
        <Button
          small
          intent="primary"
          minimal
          onClick={() => setJurisdictionDetail(jurisdiction)}
        >
          {jurisdiction.name}
        </Button>
      ),
    },
    {
      Header: 'Status',
      accessor: ({ currentRoundStatus, ballotManifest: { processing } }) => {
        if (!currentRoundStatus) return prettifyStatus(processing)
        return {
          [JurisdictionRoundStatus.NOT_STARTED]: 'Not started',
          [JurisdictionRoundStatus.IN_PROGRESS]: 'In progress',
          [JurisdictionRoundStatus.COMPLETE]: 'Complete',
        }[currentRoundStatus.status]
      },
      sortType: sortByRank(
        ({ currentRoundStatus, ballotManifest: { processing } }) => {
          if (!currentRoundStatus)
            switch (processing && processing.status) {
              case 'ERRORED':
                return 1
              case 'PROCESSED':
                return 2
              default:
                return 0
            }
          return {
            [JurisdictionRoundStatus.NOT_STARTED]: 0,
            [JurisdictionRoundStatus.IN_PROGRESS]: 1,
            [JurisdictionRoundStatus.COMPLETE]: 2,
          }[currentRoundStatus.status]
        }
      ),
    },
    {
      Header: 'Total Audited',
      accessor: ({ currentRoundStatus: s }) =>
        s && (isShowingBallots ? s.numBallotsAudited : s.numSamplesAudited),
    },
    {
      Header: 'Remaining in Round',
      accessor: ({ currentRoundStatus: s }) =>
        s &&
        (isShowingBallots
          ? s.numBallots - s.numBallotsAudited
          : s.numSamples - s.numSamplesAudited),
    },
  ]

  const filteredJurisdictions = jurisdictions.filter(({ name }) =>
    name.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <Wrapper>
      <H2Title>Audit Progress by Jurisdiction</H2Title>
      <p>
        Click on a column name to sort by that column&apos;s data. To reverse
        sort, click on the column name again.
        <br /> To view a single jurisdiction&apos;s data, click the name of the
        jurisdiction.
      </p>
      <TableControls>
        <Switch
          checked={isShowingBallots}
          label="Count unique sampled ballots"
          onChange={() => setIsShowingBallots(!isShowingBallots)}
        />
        <FilterInput
          placeholder="Filter by jurisdiction name..."
          value={filter}
          onChange={value => setFilter(value)}
        />
      </TableControls>
      <Table data={filteredJurisdictions} columns={columns} />
      <JurisdictionDetail
        jurisdiction={jurisdictionDetail}
        electionId={electionId}
        handleClose={() => setJurisdictionDetail(null)}
      />
    </Wrapper>
  )
}

export default Progress
