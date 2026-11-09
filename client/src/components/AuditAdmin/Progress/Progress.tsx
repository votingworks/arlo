import React, { useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Column, Cell, TableInstance, SortingRule, SortByFn } from 'react-table'
import {
  Button,
  Switch,
  Icon,
  InputGroup,
  Spinner,
  Tooltip,
} from '@blueprintjs/core'
import H2Title from '../../Atoms/H2Title'
import {
  JurisdictionRoundStatus,
  IJurisdiction,
  getJurisdictionStatus,
  JurisdictionProgressStatus,
  useDiscrepanciesByJurisdiction,
  BallotDiscrepanciesByJurisdiction,
  BatchDiscrepanciesByJurisdiction,
  IBatchDiscrepancies,
  useLastLoginByJurisdiction,
  IRoundStatusCounts,
  IBatchRoundStatusCounts,
} from '../../useJurisdictions'
import JurisdictionDetail from './JurisdictionDetail'
import { Table, sortByRank, downloadTableAsCSV } from '../../Atoms/Table'
import { IRound } from '../useRoundsAuditAdmin'
import { IContest } from '../../../types'
import StatusTag, { IStatusTagProps } from '../../Atoms/StatusTag'
import { IAuditSettings } from '../../useAuditSettings'
import { FileProcessingStatus, IFileInfo } from '../../useCSV'
import ProgressMap from './ProgressMap'
import { sum } from '../../../utils/number'
import { assert } from '../../utilities'
import useSearchParams from '../../useSearchParams'
import {
  IBatchOrBallotDiscrepancies,
  JurisdictionReview,
} from './JurisdictionReview'
import ContestSelect from './ContestSelect'

const Wrapper = styled.div`
  flex-grow: 1;
  > p {
    margin-bottom: 25px;
  }
`

const TableControls = styled.div`
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 0.5rem;
`

const formatNumber = ({ value }: { value: number | null }) =>
  value && value.toLocaleString()

const totalFooter =
  <T extends object>(headerName: string) =>
  (info: TableInstance<T>) =>
    sum(info.rows.map(row => row.values[headerName])).toLocaleString()

// Sorts rows with a discrepancy first, then zeros, then empty rows, so
// discrepancies aren't buried below the zeros/empty on either sort direction.
// Jurisdictions that haven't saved tallies yet stay at the bottom either way
const sortLastTalliedAt: SortByFn<IJurisdiction> = (
  rowA,
  rowB,
  columnId,
  desc
) => {
  const a: string | null = rowA.values[columnId]
  const b: string | null = rowB.values[columnId]
  const aBelowB = desc ? -1 : 1
  if (a === b) return 0
  if (a === null) return aBelowB
  if (b === null) return -aBelowB
  return Date.parse(a) - Date.parse(b)
}

const sortDiscrepanciesFirst: SortByFn<IJurisdiction> = (
  rowA,
  rowB,
  columnId,
  desc
) => {
  const a: number | null = rowA.values[columnId]
  const b: number | null = rowB.values[columnId]

  // react-table negates the comparator's result when sorting descending, so
  // this is the value to return to keep row A below row B in both directions
  const aBelowB = desc ? -1 : 1

  if (a === b) return 0

  // Empty rows stay at the very bottom
  if (a === null) return aBelowB
  if (b === null) return -aBelowB

  // Zeros stay below all discrepancies
  if (a === 0) return aBelowB
  if (b === 0) return -aBelowB

  return a - b
}

const NO_DRAWS: IBatchRoundStatusCounts = {
  numSamples: 0,
  numSamplesAudited: 0,
  numUnique: 0,
  numUniqueAudited: 0,
  extras: {
    numSamples: 0,
    numSamplesAudited: 0,
    numUnique: 0,
    numUniqueAudited: 0,
  },
}

const withoutExtras = (
  counts: IRoundStatusCounts,
  extras: IRoundStatusCounts
): IRoundStatusCounts => ({
  numSamples: counts.numSamples - extras.numSamples,
  numSamplesAudited: counts.numSamplesAudited - extras.numSamplesAudited,
  numUnique: counts.numUnique - extras.numUnique,
  numUniqueAudited: counts.numUniqueAudited - extras.numUniqueAudited,
})

// We count the number of batch-contest pairs with discrepancies, not the number
// of batches with discrepancies.
const countDiscrepancies = (
  batchesOrBallots: IBatchOrBallotDiscrepancies[],
  contestId?: string
) =>
  sum(
    batchesOrBallots.map(
      ({ discrepancies }) =>
        Object.keys(discrepancies).filter(id => !contestId || id === contestId)
          .length
    )
  )

// Batch comparison sizes discrepancies by the votes they move the margin
const totalChangeInMargin = (
  batches: IBatchDiscrepancies[],
  contestId?: string
) =>
  sum(
    batches.flatMap(({ discrepancies }) =>
      Object.entries(discrepancies)
        .filter(([id]) => !contestId || id === contestId)
        .map(([, { changeInMargin }]) => Math.abs(changeInMargin))
    )
  )

const sortBatches = (batches: IBatchDiscrepancies[]) =>
  [...batches].sort(
    (a, b) =>
      Number(a.isExtra) - Number(b.isExtra) ||
      a.name.localeCompare(b.name, undefined, { numeric: true })
  )

export interface IProgressProps {
  jurisdictions: IJurisdiction[]
  auditSettings: IAuditSettings
  contests: IContest[]
  round: IRound | null
}

const Progress: React.FC<IProgressProps> = ({
  jurisdictions,
  auditSettings,
  contests,
  round,
}: IProgressProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const { auditType } = auditSettings
  const showDiscrepancies =
    Boolean(round) &&
    (auditType === 'BALLOT_COMPARISON' || auditType === 'BATCH_COMPARISON')
  const discrepancyQuery = useDiscrepanciesByJurisdiction(electionId, {
    enabled: showDiscrepancies,
  })
  const lastLoginQuery = useLastLoginByJurisdiction(electionId)

  // Store sort and filter state in URL search params to allow it to persist
  // across page refreshes
  const [sortAndFilterState, setSortAndFilterState] = useSearchParams<{
    sort?: string
    dir?: string // asc | desc
    filter?: string
    contest?: string // Scope the table to one contest
    excludeExtraBatches?: string
  }>()
  const excludeExtraBatches = sortAndFilterState?.excludeExtraBatches === 'true'
  // Only some organizations' audits sample extra batches
  const hasExtraBatches = jurisdictions.some(
    jurisdiction =>
      (jurisdiction.currentRoundStatus?.extras?.numSamples ?? 0) > 0
  )
  const jurisdictionDiscrepancies = (
    jurisdictionId: string
  ): IBatchOrBallotDiscrepancies[] | null => {
    if (!discrepancyQuery.data) return null
    if (auditType === 'BATCH_COMPARISON') {
      const batches = discrepancyQuery.data as BatchDiscrepanciesByJurisdiction
      return sortBatches(
        Object.values(batches[jurisdictionId]?.batches ?? {}).filter(
          batch => !(excludeExtraBatches && batch.isExtra)
        )
      )
    }
    const ballots = discrepancyQuery.data as BallotDiscrepanciesByJurisdiction
    return Object.entries(ballots[jurisdictionId] ?? {}).map(
      ([name, discrepancies]) => ({ name, discrepancies })
    )
  }
  const jurisdictionNotes = (jurisdictionId: string) =>
    auditType === 'BATCH_COMPARISON'
      ? (discrepancyQuery.data as BatchDiscrepanciesByJurisdiction)[
          jurisdictionId
        ]?.notes
      : undefined
  const canSelectContest =
    auditType === 'BATCH_COMPARISON' && contests.length > 1
  const selectedContest = canSelectContest
    ? contests.find(contest => contest.id === sortAndFilterState?.contest)
    : undefined
  // With a contest selected, the sample counts are that contest's. A
  // jurisdiction with no draws for the contest has no entry for it. With
  // extra batches excluded, only the batches the audit math drew count.
  const roundStatusCounts = (
    jurisdiction: IJurisdiction
  ): IRoundStatusCounts | null => {
    const counts = selectedContest
      ? (jurisdiction.currentRoundStatusByContestId?.[selectedContest.id] ??
        NO_DRAWS)
      : jurisdiction.currentRoundStatus
    return counts && excludeExtraBatches && counts.extras
      ? withoutExtras(counts, counts.extras)
      : counts
  }
  const [isShowingUnique, setIsShowingUnique] = useState<boolean>(true)
  const [jurisdictionDetailId, setJurisdictionDetailId] = useState<
    string | null
  >(null)
  const [jurisdictionReviewId, setJurisdictionReviewId] = useState<
    string | null
  >(null)

  const filter = sortAndFilterState?.filter || ''
  const ballotsOrBatches =
    auditType === 'BATCH_COMPARISON' ? 'Batches' : 'Ballots'

  const columns: Column<IJurisdiction>[] = [
    {
      Header: 'Jurisdiction',
      subHeader: (
        <InputGroup
          placeholder="Filter by name..."
          value={filter}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            setSortAndFilterState({
              ...sortAndFilterState,
              filter: event.target.value || undefined,
            })
          }
        />
      ),
      accessor: ({ name }) => name,
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
      minWidth: 210, // Room for the longest status on one line in the default fonts
      accessor: jurisdiction => {
        const { ballotManifest, batchTallies, cvrs } = jurisdiction

        const Status = (props: IStatusTagProps) => (
          <StatusTag
            {...props}
            interactive
            multiline
            onClick={() => setJurisdictionDetailId(jurisdiction.id)}
          />
        )

        const uploads: [string, IFileInfo['processing']][] = [
          ['Manifest', ballotManifest.processing],
        ]
        if (batchTallies) uploads.push(['Tallies', batchTallies.processing])
        if (cvrs) uploads.push(['CVR', cvrs.processing])

        const numComplete = uploads.filter(
          ([, f]) => f && f.status === FileProcessingStatus.PROCESSED
        ).length
        const filesUploadedText = `${numComplete}/${uploads.length} files uploaded`

        const lastLogin = lastLoginQuery.data![jurisdiction.id]
        const jurisdictionStatus = getJurisdictionStatus(
          jurisdiction,
          lastLogin
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
          case JurisdictionProgressStatus.UPLOADS_FAILED: {
            const [failedUpload, failedProcessing] = uploads.find(
              ([, f]) => f && f.status === FileProcessingStatus.ERRORED
            )!
            return (
              <Tooltip
                content={
                  <div style={{ maxWidth: '400px' }}>
                    {failedProcessing!.error}
                  </div>
                }
              >
                <Status intent="danger">{failedUpload} upload failed</Status>
              </Tooltip>
            )
          }
          case JurisdictionProgressStatus.UPLOADS_IN_PROGRESS:
            return <Status intent="in-progress">{filesUploadedText}</Status>
          case JurisdictionProgressStatus.UPLOADS_NOT_STARTED_LOGGED_IN:
          case JurisdictionProgressStatus.AUDIT_NOT_STARTED_LOGGED_IN:
            return (
              <Tooltip
                content={`${lastLogin.user!.key} at ${new Date(
                  lastLogin.timestamp
                ).toLocaleString()}`}
              >
                <Status intent="warning">Logged in</Status>
              </Tooltip>
            )
          case JurisdictionProgressStatus.UPLOADS_NOT_STARTED_NO_LOGIN:
            return <Status>Not logged in</Status>
          case JurisdictionProgressStatus.AUDIT_IN_PROGRESS:
            return <Status intent="in-progress">In progress</Status>
          case JurisdictionProgressStatus.AUDIT_COMPLETE:
            return <Status intent="success">Complete</Status>
          case JurisdictionProgressStatus.AUDIT_NOT_STARTED_NO_LOGIN:
            return <Status>Not logged in</Status>
          /* istanbul ignore next - unreachable when exhaustive */
          default:
            return null
        }
      },
      sortType: sortByRank((jurisdiction: IJurisdiction) => {
        const { currentRoundStatus, ballotManifest, batchTallies, cvrs } =
          jurisdiction
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
            const { currentRoundStatus, ballotManifest, batchTallies, cvrs } =
              row.original

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
      accessor: ({ ballotManifest }) =>
        selectedContest
          ? (ballotManifest.numBallotsByContestId?.[selectedContest.id] ?? null)
          : ballotManifest.numBallots,
      Cell: formatNumber,
      Footer: totalFooter('Ballots in Manifest'),
    },
  ]

  if (!round) {
    const hasExpectedNumBallots = jurisdictions.some(
      jurisdiction => jurisdiction.expectedBallotManifestNumBallots !== null
    )
    // The expected count is for all of a jurisdiction's ballots
    if (hasExpectedNumBallots && !selectedContest) {
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
        sortType: sortDiscrepanciesFirst,
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
        accessor: ({ batchTallies }) =>
          selectedContest
            ? (batchTallies!.numBallotsByContestId?.[selectedContest.id] ??
              null)
            : batchTallies!.numBallots,
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
      const discrepanciesHeader =
        auditType === 'BATCH_COMPARISON' ? 'Change in Margin' : 'Discrepancies'
      columns.push({
        Header: discrepanciesHeader,
        minWidth: 140, // Room for the Review button and its count on one line
        accessor: ({ id }) => {
          const discrepancies = jurisdictionDiscrepancies(id)
          return (
            discrepancies &&
            (auditType === 'BATCH_COMPARISON'
              ? totalChangeInMargin(
                  discrepancies as IBatchDiscrepancies[],
                  selectedContest?.id
                )
              : countDiscrepancies(discrepancies, selectedContest?.id))
          )
        },
        Cell: ({
          value: numDiscrepancies,
          row: { original: jurisdiction },
        }: Cell<IJurisdiction>) => {
          if (discrepancyQuery.isLoading) {
            return (
              <div style={{ display: 'flex', justifyContent: 'start' }}>
                <Spinner size={Spinner.SIZE_SMALL} />
              </div>
            )
          }
          const isUnderReview =
            discrepancyQuery.data?.[jurisdiction.id] !== undefined
          if (!numDiscrepancies && !isUnderReview) return null
          const isFinalized =
            jurisdiction.currentRoundStatus?.status ===
            JurisdictionRoundStatus.COMPLETE
          const icon = numDiscrepancies ? (
            <Icon icon="flag" intent="danger" />
          ) : (
            isFinalized && <Icon icon="tick-circle" intent="success" />
          )
          return (
            <Button
              onClick={() => setJurisdictionReviewId(jurisdiction.id)}
              icon={icon}
            >
              {numDiscrepancies
                ? `Review ${numDiscrepancies.toLocaleString()}`
                : 'Review'}
            </Button>
          )
        },
        Footer: discrepancyQuery.isLoading
          ? () => null
          : totalFooter(discrepanciesHeader),
      })
    }
    columns.push(
      {
        Header: `${ballotsOrBatches} Audited`,
        accessor: jurisdiction => {
          const s = roundStatusCounts(jurisdiction)
          return (
            s && (isShowingUnique ? s.numUniqueAudited : s.numSamplesAudited)
          )
        },
        Cell: formatNumber,
        Footer: totalFooter(`${ballotsOrBatches} Audited`),
      },
      {
        Header: `${ballotsOrBatches} Remaining`,
        accessor: jurisdiction => {
          const s = roundStatusCounts(jurisdiction)
          return (
            s &&
            (isShowingUnique
              ? s.numUnique - s.numUniqueAudited
              : s.numSamples - s.numSamplesAudited)
          )
        },
        Cell: formatNumber,
        Footer: totalFooter(`${ballotsOrBatches} Remaining`),
      }
    )
    // How recently each jurisdiction has saved tallies, which stops mattering
    // once the round closes
    if (auditType === 'BATCH_COMPARISON' && round.endedAt === null) {
      columns.push({
        Header: 'Last Tally Update',
        minWidth: 150, // Room for a date and time on one line
        accessor: ({ currentRoundStatus }) =>
          currentRoundStatus?.lastTalliedAt ?? null,
        Cell: ({ value }: { value: string | null }) =>
          value && (
            <span title={new Date(value).toLocaleString()}>
              {new Date(value).toLocaleString(undefined, {
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
              })}
            </span>
          ),
        sortType: sortLastTalliedAt,
      })
    }
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

  const filteredJurisdictions = jurisdictions.filter(
    ({ id, name }) =>
      name.toLowerCase().includes(filter.toLowerCase()) &&
      (!selectedContest || selectedContest.jurisdictionIds.includes(id))
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
      <TableControls>
        {canSelectContest && (
          <ContestSelect
            contests={contests}
            value={selectedContest?.id ?? ''}
            onChange={contestId =>
              setSortAndFilterState({
                ...sortAndFilterState,
                contest: contestId || undefined,
              })
            }
          />
        )}
        <div style={{ flexGrow: 1 }} />
        {round && (
          <Switch
            checked={isShowingUnique}
            label={`Count unique sampled ${ballotsOrBatches.toLowerCase()}`}
            onChange={() => setIsShowingUnique(!isShowingUnique)}
            style={{ marginBottom: 0 }}
          />
        )}
        {auditType === 'BATCH_COMPARISON' && hasExtraBatches && (
          <Switch
            checked={excludeExtraBatches}
            label="Exclude extra batches"
            onChange={() =>
              setSortAndFilterState({
                ...sortAndFilterState,
                excludeExtraBatches: excludeExtraBatches ? undefined : 'true',
              })
            }
            style={{ marginBottom: 0 }}
          />
        )}
      </TableControls>
      <Table
        data={filteredJurisdictions}
        columns={columns}
        id="progress-table"
        initialSortBy={initialSortBy}
        onSortByChange={onSortByChange}
      />
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          marginTop: '8px',
        }}
      >
        <Button
          minimal
          small
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
      </div>
      {jurisdictionDetailId && (
        <JurisdictionDetail
          jurisdiction={jurisdictions.find(
            jurisdiction => jurisdiction.id === jurisdictionDetailId
          )!}
          lastLoginActivity={lastLoginByJurisdiction[jurisdictionDetailId]}
          electionId={electionId}
          round={round}
          handleClose={() => setJurisdictionDetailId(null)}
          auditSettings={auditSettings}
        />
      )}
      {jurisdictionReviewId && (
        <JurisdictionReview
          discrepancies={jurisdictionDiscrepancies(jurisdictionReviewId)!}
          notes={jurisdictionNotes(jurisdictionReviewId)}
          isSingleJurisdictionAudit={jurisdictions.length === 1}
          auditType={auditType}
          jurisdiction={jurisdictions.find(
            jurisdiction => jurisdiction.id === jurisdictionReviewId
          )!}
          electionId={electionId}
          round={round!}
          initialContestId={selectedContest?.id}
          handleClose={() => setJurisdictionReviewId(null)}
        />
      )}
    </Wrapper>
  )
}

export default Progress
