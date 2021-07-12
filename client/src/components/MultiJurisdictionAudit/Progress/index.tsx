import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Column, Cell, TableInstance } from 'react-table'
import { Button, Switch, ITagProps } from '@blueprintjs/core'
import H2Title from '../../Atoms/H2Title'
import {
  JurisdictionRoundStatus,
  IJurisdiction,
  getJurisdictionStatus,
  JurisdictionProgressStatus,
} from '../useJurisdictions'
import JurisdictionDetail from './JurisdictionDetail'
import {
  Table,
  sortByRank,
  FilterInput,
  DownloadCSVButton,
} from '../../Atoms/Table'
import { IRound } from '../useRoundsAuditAdmin'
import StatusTag from '../../Atoms/StatusTag'
import { IAuditSettings } from '../useAuditSettings'
import { FileProcessingStatus, IFileInfo } from '../useCSV'
import Map from './ProgressMap'

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
`

const formatNumber = ({ value }: { value: number | null }) =>
  value && value.toLocaleString()

const sum = (nums: number[]) => nums.reduce((a, b) => a + b, 0)

const totalFooter = <T extends object>(headerName: string) => (
  info: TableInstance<T>
) => sum(info.rows.map(row => row.values[headerName])).toLocaleString()

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

  // gives prop validation error if used as auditSettings.auditType
  const { auditType } = auditSettings

  const ballotsOrBatches =
    auditType === 'BATCH_COMPARISON' ? 'Batches' : 'Ballots'

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
      Footer: 'Total',
    },
    {
      Header: 'Status',
      // eslint-disable-next-line react/display-name
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

        const files: IFileInfo['processing'][] = [ballotManifest.processing]
        if (batchTallies) files.push(batchTallies.processing)
        if (cvrs) files.push(cvrs.processing)

        const numComplete = files.filter(
          f => f && f.status === FileProcessingStatus.PROCESSED
        ).length

        const jurisdictionStatus = getJurisdictionStatus(jurisdiction)
        switch (jurisdictionStatus) {
          case JurisdictionProgressStatus.UPLOADS_COMPLETE:
            return (
              <Status intent="success">
                {(auditType === 'BALLOT_POLLING' && 'Manifest uploaded') ||
                  `${numComplete}/${files.length} files uploaded`}
              </Status>
            )
          case JurisdictionProgressStatus.UPLOADS_FAILED:
            return (
              <Status intent="danger">
                {(auditType === 'BALLOT_POLLING' && 'Manifest upload failed') ||
                  'Upload failed'}
              </Status>
            )
          case JurisdictionProgressStatus.AUDIT_IN_PROGRESS:
            return <Status intent="warning">In progress</Status>
          case JurisdictionProgressStatus.UPLOADS_NOT_STARTED:
            return (
              <Status>
                {(!currentRoundStatus &&
                  auditType === 'BALLOT_POLLING' &&
                  'No manifest uploaded') ||
                  (!currentRoundStatus &&
                    files.length > 0 &&
                    `${numComplete}/${files.length} files uploaded`) ||
                  (currentRoundStatus && 'Not started')}
              </Status>
            )
          case JurisdictionProgressStatus.AUDIT_COMPLETE:
            return <Status intent="success">Complete</Status>
          case JurisdictionProgressStatus.AUDIT_NOT_STARTED:
            return <Status intent="success">Not started</Status>
          default:
            return null
        }
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
      Footer: info => {
        const numJurisdictionsComplete = sum(
          info.rows.map(row => {
            const {
              currentRoundStatus,
              ballotManifest,
              batchTallies,
              cvrs,
            } = row.original

            if (!currentRoundStatus) {
              const files: IFileInfo['processing'][] = [
                ballotManifest.processing,
              ]
              if (batchTallies) files.push(batchTallies.processing)
              if (cvrs) files.push(cvrs.processing)

              const numComplete = files.filter(
                f => f && f.status === FileProcessingStatus.PROCESSED
              ).length

              return numComplete === files.length ? 1 : 0
            }
            return currentRoundStatus.status ===
              JurisdictionRoundStatus.COMPLETE
              ? 1
              : 0
          })
        )
        return `${numJurisdictionsComplete.toLocaleString()}/${info.rows.length.toLocaleString()} complete`
      },
    },
    {
      Header: 'Ballots in Manifest',
      accessor: ({ ballotManifest: { numBallots } }) => numBallots,
      Cell: formatNumber,
      Footer: totalFooter('Ballots in Manifest'),
    },
  ]

  if (!round) {
    if (auditType === 'BATCH_COMPARISON') {
      columns.push({
        Header: 'Batches in Manifest',
        accessor: ({ ballotManifest: { numBatches } }) => numBatches,
        Cell: formatNumber,
        Footer: totalFooter('Batches in Manifest'),
      })
      columns.push({
        Header: 'Valid Voted Ballots in Batches',
        accessor: ({ batchTallies }) => batchTallies!.numBallots,
        Cell: formatNumber,
        Footer: totalFooter('Valid Voted Ballots in Batches'),
      })
    }

    if (auditType === 'HYBRID') {
      columns.push({
        Header: 'Non-CVR Ballots in Manifest',
        accessor: ({ ballotManifest: { numBallotsNonCvr } }) =>
          numBallotsNonCvr !== undefined ? numBallotsNonCvr : null,
        Cell: formatNumber,
        Footer: totalFooter('Non-CVR Ballots in Manifest'),
      })
      columns.push({
        Header: 'CVR Ballots in Manifest',
        accessor: ({ ballotManifest: { numBallotsCvr } }) =>
          numBallotsCvr !== undefined ? numBallotsCvr : null,
        Cell: formatNumber,
        Footer: totalFooter('CVR Ballots in Manifest'),
      })
    }

    if (auditType === 'BALLOT_COMPARISON' || auditType === 'HYBRID') {
      columns.push({
        Header: 'Ballots in CVR',
        accessor: ({ cvrs }) => cvrs!.numBallots,
        Cell: formatNumber,
        Footer: totalFooter('Ballots in CVR'),
      })
    }
  }

  if (round) {
    columns.push(
      {
        Header: `${ballotsOrBatches} Audited`,
        accessor: ({ currentRoundStatus: s }) =>
          s && (isShowingUnique ? s.numUniqueAudited : s.numSamplesAudited),
        Cell: formatNumber,
        Footer: totalFooter(`${ballotsOrBatches} Audited`),
      },
      {
        Header: `${ballotsOrBatches} Remaining`,
        accessor: ({ currentRoundStatus: s }) =>
          s &&
          (isShowingUnique
            ? s.numUnique - s.numUniqueAudited
            : s.numSamples - s.numSamplesAudited),
        Cell: formatNumber,
        Footer: totalFooter(`${ballotsOrBatches} Remaining`),
      }
    )
    // Special column for offline batch results (full hand tally)
    if (
      jurisdictions[0].currentRoundStatus &&
      jurisdictions[0].currentRoundStatus.numBatchesAudited !== undefined
    ) {
      columns.push({
        Header: 'Batches Audited',
        accessor: ({ currentRoundStatus: s }) => s && s.numBatchesAudited!,
        Cell: formatNumber,
        Footer: totalFooter('Batches Audited'),
      })
    }
  }

  const filteredJurisdictions = jurisdictions.filter(({ name }) =>
    name.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <Wrapper>
      <H2Title>Audit Progress</H2Title>
      {jurisdictions && auditSettings.state && (
        <Map
          stateName={auditSettings.state}
          jurisdictions={jurisdictions}
          isRoundStarted={!!round}
          auditType={auditType}
        />
      )}
      <p>
        Click on a column name to sort by that column&apos;s data. To reverse
        sort, click on the column name again.
        <br /> To view a single jurisdiction&apos;s data, click the name of the
        jurisdiction.
      </p>
      <TableControls>
        <div style={{ flexGrow: 1, marginRight: '20px' }}>
          <FilterInput
            placeholder="Filter by jurisdiction name..."
            value={filter}
            onChange={value => setFilter(value)}
          />
        </div>
        <Switch
          checked={isShowingUnique}
          label={`Count unique sampled ${ballotsOrBatches.toLowerCase()}`}
          onChange={() => setIsShowingUnique(!isShowingUnique)}
          style={{ marginRight: '20px' }}
        />
        <DownloadCSVButton
          tableId="progress-table"
          fileName={`audit-progress-${
            auditSettings.auditName
          }-${new Date().toISOString()}.csv`}
        />
      </TableControls>
      <Table
        data={filteredJurisdictions}
        columns={columns}
        id="progress-table"
      />
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
