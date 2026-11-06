import React, { useState } from 'react'
import {
  Classes,
  Colors,
  Dialog,
  Divider,
  H5,
  H6,
  HTMLTable,
  TextArea,
} from '@blueprintjs/core'
import styled from 'styled-components'
import {
  IJurisdiction,
  BatchContestDecision,
  BatchDiscrepancyStatus,
  DiscrepanciesByContest,
  IBallotContestDiscrepancies,
  IBatchContestDiscrepancies,
  IDiscrepancyNote,
  JurisdictionRoundStatus,
  isOutstanding,
  useAddJurisdictionDiscrepancyNote,
  useSetBatchContestStatus,
  useUnfinalizeBatchTallies,
} from '../../useJurisdictions'
import { IRound } from '../useRoundsAuditAdmin'
import AsyncButton from '../../Atoms/AsyncButton'
import useContestsJurisdictionAdmin from '../../JurisdictionAdmin/useContestsJurisdictionAdmin'
import { IContest } from '../../../types'
import { IAuditSettings } from '../../useAuditSettings'
import { assert } from '../../utilities'
import CopyToClipboard from '../../Atoms/CopyToClipboard'
import ContestSelect from './ContestSelect'
import StatusTag, { ExtendedIntent } from '../../Atoms/StatusTag'
import JurisdictionAdmins from './JurisdictionAdmins'

export const STATUS_TAGS: Record<
  BatchDiscrepancyStatus,
  { label: string; intent: ExtendedIntent }
> = {
  NEEDS_REVIEW: { label: 'Needs Review', intent: 'danger' },
  JURISDICTION_CONTACTED: { label: 'Contacted', intent: 'warning' },
  ACCEPTED: { label: 'Accepted', intent: 'success' },
  MATCHES: { label: 'Matches', intent: 'success' },
  RE_TALLYING: { label: 'Re-tallying', intent: 'in-progress' },
}

const ContestDiscrepanciesTable = styled(HTMLTable).attrs({
  bordered: true,
  striped: true,
})`
  background: #ffffff;
  border: 1px solid ${Colors.LIGHT_GRAY1};
  margin-bottom: 16px;
  table-layout: fixed;
  width: 100%;

  td {
    vertical-align: middle;
  }
`

const TableHeader = styled(H6)`
  margin-bottom: 4px;
`

const rowStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
}

function getChoiceName(
  contests: IContest[],
  contestId: string,
  choiceId: string
) {
  const contest = contests.find(c => c.id === contestId)
  assert(contest !== undefined)
  const choice = contest.choices.find(c => c.id === choiceId)
  assert(choice !== undefined)
  return choice.name
}

function formatChoiceVotes(
  contests: IContest[],
  contestId: string,
  votes: Record<string, number>
) {
  const contest = contests.find(c => c.id === contestId)
  assert(contest !== undefined)
  return (
    contest.choices
      .filter(choice => votes[choice.id] > 0)
      .map(choice => `${choice.name} ${votes[choice.id].toLocaleString()}`)
      .join(', ') || 'none'
  )
}

function formatVoteCount(val: string | number | undefined): string {
  switch (val) {
    case 'o':
      return 'Overvote'
    case 'u':
      return 'Undervote'
    case undefined: // Seen on 'reportedVotes' when a candidate did not have a vote originally
      return '0'
    default:
      if (typeof val === 'string') {
        return val
      }
      return val.toLocaleString()
  }
}

const BatchContestDiscrepancies: React.FC<{
  contests: IContest[]
  contestId: string
  contestDiscrepancies: IBatchContestDiscrepancies
}> = ({ contests, contestId, contestDiscrepancies }) => (
  <div
    style={{
      display: 'grid',
      gridTemplateColumns: 'max-content auto',
      columnGap: '12px',
      rowGap: '4px',
      marginBottom: '16px',
    }}
  >
    {(
      [
        [
          'Change in margin',
          contestDiscrepancies.changeInMargin.toLocaleString(),
        ],
        ['Ballots in batch', contestDiscrepancies.numBallots.toLocaleString()],
        [
          'Reported',
          formatChoiceVotes(
            contests,
            contestId,
            contestDiscrepancies.reportedVotes
          ),
        ],
        [
          'Audited',
          formatChoiceVotes(
            contests,
            contestId,
            contestDiscrepancies.auditedVotes
          ),
        ],
      ] as const
    ).map(([label, text]) => (
      <React.Fragment key={label}>
        <span className={Classes.TEXT_MUTED}>{label}</span>
        <span style={rowStyle}>
          {text}
          {label === 'Audited' && (
            <CopyToClipboard
              iconOnly
              label="Copy audited votes"
              getText={() => ({ text, format: 'text/plain' })}
            />
          )}
        </span>
      </React.Fragment>
    ))}
  </div>
)

const BallotContestDiscrepancies: React.FC<{
  contests: IContest[]
  contestId: string
  contestDiscrepancies: IBallotContestDiscrepancies
}> = ({ contests, contestId, contestDiscrepancies }) => (
  <ContestDiscrepanciesTable>
    <thead>
      <tr>
        <th>Choice</th>
        <th>Reported Votes</th>
        <th>Audited Votes</th>
        <th>Discrepancy</th>
      </tr>
    </thead>
    <tbody>
      {Object.keys(contestDiscrepancies.discrepancies)
        .filter(choiceID => contestDiscrepancies.discrepancies[choiceID] !== 0)
        .map(choiceId => (
          <tr key={choiceId}>
            <td>{getChoiceName(contests, contestId, choiceId)}</td>
            <td>
              {formatVoteCount(contestDiscrepancies.reportedVotes[choiceId])}
            </td>
            <td>
              {formatVoteCount(contestDiscrepancies.auditedVotes[choiceId])}
            </td>
            <td>
              {formatVoteCount(contestDiscrepancies.discrepancies[choiceId])}
            </td>
          </tr>
        ))}
    </tbody>
  </ContestDiscrepanciesTable>
)

export interface IBatchOrBallotDiscrepancies {
  id?: string // Batch comparison only
  name: string
  isExtra?: boolean // Batch comparison only
  discrepancies: DiscrepanciesByContest
}

export interface IJurisdictionReviewProps {
  discrepancies: IBatchOrBallotDiscrepancies[]
  notes?: IDiscrepancyNote[]
  isReTallying: boolean
  auditType: IAuditSettings['auditType']
  electionId: string
  handleClose: () => void
  jurisdiction: IJurisdiction
  round: IRound
  initialContestId?: string
}

const JurisdictionReview: React.FC<IJurisdictionReviewProps> = ({
  discrepancies,
  notes,
  isReTallying,
  auditType,
  handleClose,
  jurisdiction,
  electionId,
  round,
  initialContestId,
}) => {
  const contestsQuery = useContestsJurisdictionAdmin(
    electionId,
    jurisdiction.id
  )
  const unfinalize = useUnfinalizeBatchTallies(electionId)
  const setBatchContestStatus = useSetBatchContestStatus(electionId)
  const addNote = useAddJurisdictionDiscrepancyNote(electionId)
  const [selectedContestId, setSelectedContestId] = useState(
    initialContestId ?? ''
  )
  const [noteText, setNoteText] = useState('')
  const isFinalized =
    jurisdiction.currentRoundStatus!.status === JurisdictionRoundStatus.COMPLETE
  const canUnfinalize =
    auditType === 'BATCH_COMPARISON' && round.endedAt === null && isFinalized

  if (!contestsQuery.isSuccess) {
    return null
  }

  const contests = contestsQuery.data
  const canSelectContest =
    auditType === 'BATCH_COMPARISON' && contests.length > 1
  const shownBatches = selectedContestId
    ? discrepancies.filter(
        ({ discrepancies: byContest }) => selectedContestId in byContest
      )
    : discrepancies

  return (
    <Dialog
      isOpen
      onClose={handleClose}
      style={{ width: '600px' }}
      title={`${jurisdiction.name} Review`}
    >
      <div className={Classes.DIALOG_BODY} style={{ marginBottom: 0 }}>
        <JurisdictionAdmins jurisdiction={jurisdiction} />
        {notes && (
          <div style={{ marginBottom: '16px' }}>
            <div className={`${Classes.TEXT_MUTED} ${Classes.TEXT_SMALL}`}>
              Notes
            </div>
            {notes.map(note => (
              <div key={note.createdAt} style={{ marginTop: '8px' }}>
                <div style={{ whiteSpace: 'pre-wrap' }}>{note.text}</div>
                <div className={`${Classes.TEXT_MUTED} ${Classes.TEXT_SMALL}`}>
                  {new Date(note.createdAt).toLocaleString()}
                </div>
              </div>
            ))}
            <TextArea
              fill
              growVertically
              disabled={addNote.isLoading}
              placeholder="Add a note"
              value={noteText}
              onChange={e => setNoteText(e.currentTarget.value)}
              style={{ marginTop: '8px' }}
            />
            <AsyncButton
              disabled={noteText.trim() === ''}
              onClick={async () => {
                await addNote.mutateAsync({
                  jurisdictionId: jurisdiction.id,
                  text: noteText.trim(),
                })
                setNoteText('')
              }}
              style={{ marginTop: '8px' }}
            >
              Add Note
            </AsyncButton>
          </div>
        )}
        <Divider style={{ margin: '16px 0' }} />
        {(canSelectContest || canUnfinalize || isReTallying) && (
          <div style={{ ...rowStyle, marginBottom: '16px' }}>
            {canSelectContest && (
              <ContestSelect
                contests={contests}
                value={selectedContestId}
                onChange={setSelectedContestId}
              />
            )}
            <div style={{ flexGrow: 1 }} />
            {canUnfinalize && (
              <AsyncButton
                intent="danger"
                onClick={() =>
                  unfinalize.mutateAsync({
                    jurisdictionId: jurisdiction.id,
                    roundId: round.id,
                  })
                }
              >
                Unfinalize Tallies
              </AsyncButton>
            )}
            {isReTallying && (
              <StatusTag intent="in-progress">Re-tallying</StatusTag>
            )}
          </div>
        )}
        {selectedContestId && shownBatches.length === 0 && (
          <p className={Classes.TEXT_MUTED}>
            {jurisdiction.currentRoundStatusByContestId![selectedContestId]
              ? 'No discrepancies for this contest'
              : 'No batches sampled for this contest'}
          </p>
        )}
        {shownBatches.map(({ id, name, isExtra, discrepancies: byContest }) => {
          // In contest setup order
          const shownContests = contests.filter(
            contest =>
              contest.id in byContest &&
              (!selectedContestId || contest.id === selectedContestId)
          )
          return (
            <div key={name} style={{ marginBottom: '16px' }}>
              <H5 style={rowStyle}>
                <span>
                  {isExtra && '(Extra) '}
                  {name}
                </span>
                {auditType === 'BATCH_COMPARISON' && (
                  <CopyToClipboard
                    iconOnly
                    label="Copy batch name"
                    getText={() => ({ text: name, format: 'text/plain' })}
                  />
                )}
              </H5>
              {shownContests.map(contest => {
                const contestDiscrepancies = byContest[contest.id]
                const status =
                  auditType === 'BATCH_COMPARISON'
                    ? (contestDiscrepancies as IBatchContestDiscrepancies)
                        .status
                    : null
                const setStatus = (newStatus: BatchContestDecision) =>
                  setBatchContestStatus.mutateAsync({
                    jurisdictionId: jurisdiction.id,
                    roundId: round.id,
                    batchId: id!,
                    contestId: contest.id,
                    status: newStatus,
                  })
                return (
                  <div key={contest.id}>
                    <TableHeader style={rowStyle}>
                      <span>{contest.name}</span>
                      <CopyToClipboard
                        iconOnly
                        label="Copy contest name"
                        getText={() => ({
                          text: contest.name,
                          format: 'text/plain',
                        })}
                      />
                      {status && (
                        <StatusTag intent={STATUS_TAGS[status].intent}>
                          {STATUS_TAGS[status].label}
                        </StatusTag>
                      )}
                      {isOutstanding(status) && (
                        <>
                          <div style={{ flexGrow: 1 }} />
                          {status === 'NEEDS_REVIEW' && (
                            <AsyncButton
                              small
                              onClick={() =>
                                setStatus('JURISDICTION_CONTACTED')
                              }
                            >
                              Mark Contacted
                            </AsyncButton>
                          )}
                          <AsyncButton
                            small
                            onClick={() => setStatus('ACCEPTED')}
                          >
                            Accept
                          </AsyncButton>
                        </>
                      )}
                    </TableHeader>
                    {auditType === 'BATCH_COMPARISON' ? (
                      <BatchContestDiscrepancies
                        contests={contests}
                        contestId={contest.id}
                        contestDiscrepancies={
                          contestDiscrepancies as IBatchContestDiscrepancies
                        }
                      />
                    ) : (
                      <BallotContestDiscrepancies
                        contests={contests}
                        contestId={contest.id}
                        contestDiscrepancies={
                          contestDiscrepancies as IBallotContestDiscrepancies
                        }
                      />
                    )}
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>
    </Dialog>
  )
}

export { JurisdictionReview }
