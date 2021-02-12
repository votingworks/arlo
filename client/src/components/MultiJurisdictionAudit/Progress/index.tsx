import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Column, Cell } from 'react-table'
import { Button, Switch, ITagProps } from '@blueprintjs/core'
import H2Title from '../../Atoms/H2Title'
import { JurisdictionRoundStatus, IJurisdiction } from '../useJurisdictions'
import JurisdictionDetail from './JurisdictionDetail'
import { Table, sortByRank, FilterInput } from '../../Atoms/Table'
import { IRound } from '../useRoundsAuditAdmin'
import StatusTag from '../../Atoms/StatusTag'
import { IAuditSettings } from '../useAuditSettings'
import { FileProcessingStatus, IFileInfo } from '../useCSV'

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

const formatNumber = (n: number | null) => n && n.toLocaleString()

interface IProps {
  jurisdictions: IJurisdiction[]
  auditSettings: IAuditSettings
  round: IRound | null
}

const Progress: React.FC<IProps> = ({
  jurisdictions,
  auditSettings,
  round,
}: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [filter, setFilter] = useState<string>('')
  const [isShowingUnique, setIsShowingUnique] = useState<boolean>(true)
  const [
    jurisdictionDetail,
    setJurisdictionDetail,
  ] = useState<IJurisdiction | null>(null)

  const ballotsOrBatches =
    auditSettings.auditType === 'BATCH_COMPARISON' ? 'Batches' : 'Ballots'

  const columns: Column<IJurisdiction>[] = [
    {
      Header: 'Jurisdiction',
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
      accessor: jurisdiction => {
        const {
          currentRoundStatus,
          ballotManifest,
          batchTallies,
          cvrs,
        } = jurisdiction

        const Status = (props: Omit<ITagProps, 'minimal'>) => (
          <StatusTag
            {...props}
            interactive
            onClick={() => setJurisdictionDetail(jurisdiction)}
          />
        )

        if (!currentRoundStatus) {
          const files: IFileInfo['processing'][] = [ballotManifest.processing]
          if (batchTallies) files.push(batchTallies.processing)
          if (cvrs) files.push(cvrs.processing)

          const numComplete = files.filter(
            f => f && f.status === FileProcessingStatus.PROCESSED
          ).length
          const anyFailed = files.some(
            f => f && f.status === FileProcessingStatus.ERRORED
          )

          // Special case when we just have a ballotManifest
          if (files.length === 1) {
            if (anyFailed) {
              return <Status intent="danger">Manifest upload failed</Status>
            }
            if (numComplete === 1) {
              return <Status intent="success">Manifest uploaded</Status>
            }
            return <Status>No manifest uploaded</Status>
          }

          // When we have multiple files
          if (anyFailed) {
            return <Status intent="danger">Upload failed</Status>
          }
          return (
            <Status
              intent={numComplete === files.length ? 'success' : undefined}
            >
              {numComplete}/{files.length} files uploaded
            </Status>
          )
        }
        return {
          [JurisdictionRoundStatus.NOT_STARTED]: <Status>Not started</Status>,
          [JurisdictionRoundStatus.IN_PROGRESS]: (
            <Status intent="warning">In progress</Status>
          ),
          [JurisdictionRoundStatus.COMPLETE]: (
            <Status intent="success">Complete</Status>
          ),
        }[currentRoundStatus.status]
      },
      sortType: sortByRank(
        ({ currentRoundStatus, ballotManifest, batchTallies, cvrs }) => {
          if (!currentRoundStatus) {
            const files: IFileInfo['processing'][] = [ballotManifest.processing]
            if (batchTallies) files.push(batchTallies.processing)
            if (cvrs) files.push(cvrs.processing)

            const numComplete = files.filter(
              f => f && f.status === FileProcessingStatus.PROCESSED
            ).length
            const anyFailed = files.some(
              f => f && f.status === FileProcessingStatus.ERRORED
            )
            if (anyFailed) return 0
            if (numComplete === 0) return -1
            return numComplete
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
      Header: `${ballotsOrBatches} in Manifest`,
      accessor: ({ ballotManifest: { numBallots, numBatches } }) =>
        formatNumber(
          auditSettings.auditType === 'BATCH_COMPARISON'
            ? numBatches
            : numBallots
        ),
    },
  ]
  if (round) {
    columns.push(
      {
        Header: `${ballotsOrBatches} Audited`,
        accessor: ({ currentRoundStatus: s }) =>
          s &&
          formatNumber(
            isShowingUnique ? s.numUniqueAudited : s.numSamplesAudited
          ),
      },
      {
        Header: `${ballotsOrBatches} Remaining`,
        accessor: ({ currentRoundStatus: s }) =>
          s &&
          formatNumber(
            isShowingUnique
              ? s.numUnique - s.numUniqueAudited
              : s.numSamples - s.numSamplesAudited
          ),
      }
    )
    if (
      jurisdictions[0].currentRoundStatus &&
      jurisdictions[0].currentRoundStatus.numBatchesAudited !== undefined
    ) {
      columns.push({
        Header: 'Batches Audited',
        accessor: ({ currentRoundStatus: s }) =>
          s && formatNumber(s.numBatchesAudited!),
      })
    }
  }

  const filteredJurisdictions = jurisdictions.filter(({ name }) =>
    name.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <Wrapper>
      <H2Title>Audit Progress</H2Title>
      <p>
        Click on a column name to sort by that column&apos;s data. To reverse
        sort, click on the column name again.
        <br /> To view a single jurisdiction&apos;s data, click the name of the
        jurisdiction.
      </p>
      <TableControls>
        <Switch
          checked={isShowingUnique}
          label={`Count unique sampled ${ballotsOrBatches.toLowerCase()}`}
          onChange={() => setIsShowingUnique(!isShowingUnique)}
        />
        <FilterInput
          placeholder="Filter by jurisdiction name..."
          value={filter}
          onChange={value => setFilter(value)}
        />
      </TableControls>
      <Table data={filteredJurisdictions} columns={columns} />
      {jurisdictionDetail && (
        <JurisdictionDetail
          jurisdiction={jurisdictionDetail}
          electionId={electionId}
          round={round}
          handleClose={() => setJurisdictionDetail(null)}
          auditSettings={auditSettings}
        />
      )}
    </Wrapper>
  )
}

export default Progress
