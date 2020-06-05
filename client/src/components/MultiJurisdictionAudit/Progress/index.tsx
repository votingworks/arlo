import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Column, Cell } from 'react-table'
import { Button } from '@blueprintjs/core'
import H2Title from '../../Atoms/H2Title'
import {
  JurisdictionRoundStatus,
  IJurisdiction,
  prettifyStatus,
} from '../useJurisdictions'
import JurisdictionDetail from './JurisdictionDetail'
import Table, { sortByRank } from '../../Atoms/Table'

const Wrapper = styled.div`
  flex-grow: 1;
`

interface IProps {
  jurisdictions: IJurisdiction[]
}

const Progress: React.FC<IProps> = ({ jurisdictions }: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
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
      filter: 'text',
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
      accessor: ({ currentRoundStatus }) =>
        currentRoundStatus && currentRoundStatus.numBallotsAudited,
    },
    {
      Header: 'Remaining in Round',
      accessor: ({ currentRoundStatus }) =>
        currentRoundStatus &&
        currentRoundStatus.numBallotsSampled -
          currentRoundStatus.numBallotsAudited,
    },
  ]

  return (
    <Wrapper>
      <H2Title>Audit Progress by Jurisdiction</H2Title>
      <Table data={jurisdictions} columns={columns} />
      <JurisdictionDetail
        jurisdiction={jurisdictionDetail}
        electionId={electionId}
        handleClose={() => setJurisdictionDetail(null)}
      />
    </Wrapper>
  )
}

export default Progress
