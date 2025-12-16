/* eslint-disable react/prop-types */
import React, { useState, useCallback, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Column, Cell, TableInstance, SortingRule } from 'react-table'
import { Button, Switch, Icon, Spinner } from '@blueprintjs/core'
import H2Title from '../../Atoms/H2Title'
import {
  JurisdictionRoundStatus,
  IJurisdiction,
  getJurisdictionStatus,
  JurisdictionProgressStatus,
  useDiscrepanciesByJurisdiction,
  DiscrepanciesByJurisdiction,
  useLastLoginByJurisdiction,
} from '../../useJurisdictions'
import JurisdictionDetail from './JurisdictionDetail'
import {
  Table,
  sortByRank,
  FilterInput,
  downloadTableAsCSV,
} from '../../Atoms/Table'
import {
  IRound,
  isGeneratingReport,
  useGenerateReport,
} from '../useRoundsAuditAdmin'
import StatusTag, { IStatusTagProps } from '../../Atoms/StatusTag'
import { IAuditSettings } from '../../useAuditSettings'
import { FileProcessingStatus, IFileInfo } from '../../useCSV'
import ProgressMap from './ProgressMap'
import { sum } from '../../../utils/number'
import { apiDownload, assert } from '../../utilities'
import AsyncButton from '../../Atoms/AsyncButton'
import useSearchParams from '../../useSearchParams'
import { JurisdictionDiscrepancies } from './JurisdictionDiscrepancies'

const Wrapper = styled.div`
  flex-grow: 1;
  > p {
    margin-bottom: 25px;
  }
`

const TableControls = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  gap: 20px;
`

const formatNumber = ({ value }: { value: number | null }) =>
  value && value.toLocaleString()

// eslint-disable-next-line @typescript-eslint/ban-types
const totalFooter = <T extends object>(headerName: string) => (
  info: TableInstance<T>
) => sum(info.rows.map(row => row.values[headerName])).toLocaleString()

// We count the number of batch-contest pairs with discrepancies, not the number
// of batches with discrepancies.
const countDiscrepanciesForJurisdiction = (
  discrepancies: DiscrepanciesByJurisdiction,
  jurisdictionId: string
) => {
  return sum(
    Object.values(discrepancies[jurisdictionId] ?? {}).map(
      contestDiscrepancies => Object.keys(contestDiscrepancies).length
    )
  )
}

export interface IProgressProps {
  jurisdictions: IJurisdiction[]
  auditSettings: IAuditSettings
  round: IRound | null
}

const Progress: React.FC<IProgressProps> = ({
  jurisdictions,
  auditSettings,
  round,
}: IProgressProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const { auditType } = auditSettings
  const showDiscrepancies =
    Boolean(round) &&
    (auditType === 'BALLOT_COMPARISON' || auditType === 'BATCH_COMPARISON') &&
    false
  const discrepancyQuery = useDiscrepanciesByJurisdiction(electionId, {
    enabled: showDiscrepancies,
  })
  const lastLoginQuery = useLastLoginByJurisdiction(electionId)
  const generateReportMutation = useGenerateReport(electionId)

  const prevGenerateReportTaskRef = useRef<IRound['generateReportTask']>()
  const currentGenerateReportTask = round?.generateReportTask
  useEffect(() => {
    if (
      prevGenerateReportTaskRef.current &&
      !prevGenerateReportTaskRef.current.completedAt &&
      currentGenerateReportTask?.completedAt
    ) {
      // Background report generation just completed, auto-download
      const a = document.createElement('a')
      a.href = `/api/election/${electionId}/report`
      a.download = '' // Use server-generated file name
      document.body.appendChild(a)
      a.click()
      a.remove()
    }
    prevGenerateReportTaskRef.current = currentGenerateReportTask
  }, [prevGenerateReportTaskRef, currentGenerateReportTask])

  // Store sort and filter state in URL search params to allow it to persist
  // across page refreshes
  const [sortAndFilterState, setSortAndFilterState] = useSearchParams<{
    sort?: string
    dir?: string // asc | desc
    filter?: string
  }>()
  const [isShowingUnique, setIsShowingUnique] = useState<boolean>(true)
  const [jurisdictionDetailId, setJurisdictionDetailId] = useState<
    string | null
  >(null)
  const [
    jurisdictionDiscrepanciesId,
    setJurisdictionDiscrepanciesId,
  ] = useState<string | null>(null)

  const ballotsOrBatches =
    auditType === 'BATCH_COMPARISON' ? 'Batches' : 'Ballots'

  const columns: Column<IJurisdiction>[] = [
    {
      Header: 'Jurisdiction',
      accessor: ({ name }) => name,
      // eslint-disable-next-line react/display-name
      Cell: ({ row: { original: jurisdiction } }: Cell<IJurisdiction>) => (
        <Button
          small
          intent="primary"
          minimal
          onClick={() => setJurisdictionDetailId(jurisdiction.id)}
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
        const { ballotManifest, batchTallies, cvrs } = jurisdiction

        const Status = (props: IStatusTagProps) => (
          <StatusTag
            {...props}
            interactive
            onClick={() => setJurisdictionDetailId(jurisdiction.id)}
          />
        )

        const files: IFileInfo['processing'][] = [ballotManifest.processing]
        if (batchTallies) files.push(batchTallies.processing)
        if (cvrs) files.push(cvrs.processing)

        const numComplete = files.filter(
          f => f && f.status === FileProcessingStatus.PROCESSED
        ).length
        const filesUploadedText = `${numComplete}/${files.length} files uploaded`

        const jurisdictionStatus = getJurisdictionStatus(
          jurisdiction,
          lastLoginQuery.data![jurisdiction.id]
        )

        switch (jurisdictionStatus) {
          case JurisdictionProgressStatus.UPLOADS_COMPLETE:
            return (
              <Status intent="success">
                {auditType === 'BALLOT_POLLING'
                  ? 'Manifest uploaded'
                  : filesUploadedText}
              </Status>
            )
          case JurisdictionProgressStatus.UPLOADS_FAILED:
            return (
              <Status intent="danger">
                {auditType === 'BALLOT_POLLING'
                  ? 'Manifest upload failed'
                  : 'Upload failed'}
              </Status>
            )
          case JurisdictionProgressStatus.UPLOADS_IN_PROGRESS:
            return <Status intent="in-progress">{filesUploadedText}</Status>
          case JurisdictionProgressStatus.UPLOADS_NOT_STARTED_LOGGED_IN:
            return <Status intent="warning">Logged in</Status>
          case JurisdictionProgressStatus.UPLOADS_NOT_STARTED_NO_LOGIN:
            return <Status>Not logged in</Status>
          case JurisdictionProgressStatus.AUDIT_IN_PROGRESS:
            return <Status intent="in-progress">In progress</Status>
          case JurisdictionProgressStatus.AUDIT_COMPLETE:
            return <Status intent="success">Complete</Status>
          case JurisdictionProgressStatus.AUDIT_NOT_STARTED_LOGGED_IN:
            return <Status intent="warning">Logged in</Status>
          case JurisdictionProgressStatus.AUDIT_NOT_STARTED_NO_LOGIN:
            return <Status>Not logged in</Status>
          /* istanbul ignore next - unreachable when exhaustive */
          default:
            return null
        }
      },
      sortType: sortByRank((jurisdiction: IJurisdiction) => {
        const {
          currentRoundStatus,
          ballotManifest,
          batchTallies,
          cvrs,
        } = jurisdiction
        const progressStatus = getJurisdictionStatus(
          jurisdiction,
          lastLoginQuery.data![jurisdiction.id]
        )
        const hasLoggedIn = ![
          JurisdictionProgressStatus.UPLOADS_NOT_STARTED_NO_LOGIN,
          JurisdictionProgressStatus.AUDIT_NOT_STARTED_NO_LOGIN,
        ].includes(progressStatus)

        /**
         * Ascending sort order ...
         *
         * When round has not started:
         * -2. Not logged in, no file uploads completed
         * -1. Logged in, no file uploads completed
         *  0. Logged in, uploads attempted but failed
         *  n. Order by successful processed files regardless of login status
         *
         * When round has been started
         * 0: Not logged in, audit actions not taken
         * 1. Logged in, audit actions not taken
         * 2. Audit in progress, regardless of login status
         * 3. Audit complete, regardless of login status
         */

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
          if (numComplete === 0) return hasLoggedIn ? -1 : -2
          return numComplete
        }
        return {
          [JurisdictionRoundStatus.NOT_STARTED]: hasLoggedIn ? 1 : 0,
          [JurisdictionRoundStatus.IN_PROGRESS]: 2,
          [JurisdictionRoundStatus.COMPLETE]: 3,
        }[currentRoundStatus.status]
      }),
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
    const hasExpectedNumBallots = jurisdictions.some(
      jurisdiction => jurisdiction.expectedBallotManifestNumBallots !== null
    )
    if (hasExpectedNumBallots) {
      columns.push({
        Header: 'Expected Ballots in Manifest',
        accessor: ({ expectedBallotManifestNumBallots }) =>
          expectedBallotManifestNumBallots,
        Cell: formatNumber,
        Footer: totalFooter('Expected Ballots in Manifest'),
      })
      columns.push({
        Header: 'Difference From Expected Ballots',
        accessor: ({
          ballotManifest: { numBallots },
          expectedBallotManifestNumBallots,
        }) =>
          numBallots !== null && expectedBallotManifestNumBallots !== null
            ? numBallots - expectedBallotManifestNumBallots
            : null,
        Cell: formatNumber,
      })
    }

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
    if (showDiscrepancies) {
      columns.push({
        Header: 'Discrepancies',
        accessor: ({ id }) =>
          discrepancyQuery.isSuccess &&
          countDiscrepanciesForJurisdiction(discrepancyQuery.data, id),
        Cell: ({
          value,
          row: { original: jurisdiction },
        }: Cell<IJurisdiction>) => {
          if (discrepancyQuery.isLoading) {
            return (
              <div style={{ display: 'flex', justifyContent: 'start' }}>
                <Spinner size={Spinner.SIZE_SMALL} />
              </div>
            )
          }
          if (!value) return null
          return (
            <Button
              onClick={() => setJurisdictionDiscrepanciesId(jurisdiction.id)}
              icon={<Icon icon="flag" intent="danger" />}
            >
              Review {value.toLocaleString()}
            </Button>
          )
        },
        Footer: discrepancyQuery.isLoading
          ? () => null
          : totalFooter('Discrepancies'),
      })
    }
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
    // Special column for full hand tally
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

  const filter = sortAndFilterState?.filter || ''
  const filteredJurisdictions = jurisdictions.filter(({ name }) =>
    name.toLowerCase().includes(filter.toLowerCase())
  )

  const initialSortBy = sortAndFilterState?.sort
    ? [
        {
          id: sortAndFilterState.sort,
          desc: sortAndFilterState.dir === 'desc',
        },
      ]
    : undefined
  const onSortByChange = useCallback(
    (newSortBy: SortingRule<unknown>[]) => {
      assert(newSortBy.length <= 1)
      const sortBy = newSortBy[0]
      setSortAndFilterState({
        ...sortAndFilterState,
        sort: sortBy?.id,
        dir: sortBy && (sortBy.desc ? 'desc' : 'asc'),
      })
    },
    [sortAndFilterState, setSortAndFilterState]
  )

  const downloadButtons = (
    <div style={{ display: 'flex', alignSelf: 'end', gap: '5px' }}>
      <Button
        icon="download"
        onClick={() => generateReportMutation.mutateAsync()}
        loading={round ? isGeneratingReport([round]) : false}
      >
        Download In-Flight Audit Report
      </Button>
      <Button
        icon="download"
        onClick={() => {
          downloadTableAsCSV({
            tableId: 'progress-table',
            fileName: `audit-progress-${
              auditSettings.auditName
            }-${new Date().toISOString()}.csv`,
          })
        }}
      >
        Download Table as CSV
      </Button>
      {showDiscrepancies && (
        <AsyncButton
          icon="flag"
          onClick={() =>
            apiDownload(`/election/${electionId}/discrepancy-report`)
          }
        >
          Download Discrepancy Report
        </AsyncButton>
      )}
    </div>
  )

  const splitTableControlsAcrossTwoRows = Boolean(showDiscrepancies)

  if (!lastLoginQuery.isSuccess) {
    return null
  }

  const lastLoginByJurisdiction = lastLoginQuery.data

  return (
    <Wrapper>
      <H2Title>Audit Progress</H2Title>
      {jurisdictions && auditSettings.state && (
        <ProgressMap
          stateAbbreviation={auditSettings.state}
          jurisdictions={jurisdictions}
          isRoundStarted={!!round}
          auditType={auditType}
        />
      )}
      <TableControls
        style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            width: '100%',
          }}
        >
          <div style={{ flexGrow: 1 }}>
            <FilterInput
              placeholder="Filter by jurisdiction name..."
              value={filter}
              onChange={value =>
                setSortAndFilterState({
                  ...sortAndFilterState,
                  filter: value || undefined,
                })
              }
            />
          </div>
          {round && (
            <Switch
              checked={isShowingUnique}
              label={`Count unique sampled ${ballotsOrBatches.toLowerCase()}`}
              onChange={() => setIsShowingUnique(!isShowingUnique)}
              style={{ marginBottom: 0 }}
            />
          )}
          {!splitTableControlsAcrossTwoRows && downloadButtons}
        </div>
        {splitTableControlsAcrossTwoRows && downloadButtons}
      </TableControls>
      <Table
        data={filteredJurisdictions}
        columns={columns}
        id="progress-table"
        initialSortBy={initialSortBy}
        onSortByChange={onSortByChange}
      />
      {jurisdictionDetailId && (
        <JurisdictionDetail
          jurisdiction={
            jurisdictions.find(
              jurisdiction => jurisdiction.id === jurisdictionDetailId
            )!
          }
          lastLoginActivity={lastLoginByJurisdiction[jurisdictionDetailId]}
          electionId={electionId}
          round={round}
          handleClose={() => setJurisdictionDetailId(null)}
          auditSettings={auditSettings}
        />
      )}
      {jurisdictionDiscrepanciesId && (
        <JurisdictionDiscrepancies
          discrepancies={discrepancyQuery.data!}
          jurisdiction={
            jurisdictions.find(
              jurisdiction => jurisdiction.id === jurisdictionDiscrepanciesId
            )!
          }
          electionId={electionId}
          handleClose={() => setJurisdictionDiscrepanciesId(null)}
        />
      )}
    </Wrapper>
  )
}

export default Progress
