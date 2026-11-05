import React, { useState } from 'react'
import {
  Classes,
  Colors,
  Dialog,
  Divider,
  H5,
  H6,
  HTMLTable,
} from '@blueprintjs/core'
import styled from 'styled-components'
import {
  IJurisdiction,
  DiscrepanciesByContest,
  JurisdictionRoundStatus,
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

function getContestName(contests: IContest[], contestId: string) {
  const contest = contests.find(c => c.id === contestId)
  assert(contest !== undefined)
  return contest.name
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

export interface IBatchOrBallotDiscrepancies {
  name: string
  isExtra?: boolean // Batch comparison only
  discrepancies: DiscrepanciesByContest
}

export interface IJurisdictionDiscrepanciesProps {
  discrepancies: IBatchOrBallotDiscrepancies[]
  auditType: IAuditSettings['auditType']
  electionId: string
  handleClose: () => void
  jurisdiction: IJurisdiction
  round: IRound
  initialContestId?: string
}

const JurisdictionDiscrepancies: React.FC<IJurisdictionDiscrepanciesProps> = ({
  discrepancies,
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
  const [selectedContestId, setSelectedContestId] = useState(
    initialContestId ?? ''
  )
  const canUnfinalize =
    auditType === 'BATCH_COMPARISON' &&
    round.endedAt === null &&
    jurisdiction.currentRoundStatus!.status === JurisdictionRoundStatus.COMPLETE

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
      title={`${jurisdiction.name} Discrepancies`}
    >
      <div className={Classes.DIALOG_BODY} style={{ marginBottom: 0 }}>
        <div style={{ marginBottom: '16px' }}>
          <div className={`${Classes.TEXT_MUTED} ${Classes.TEXT_SMALL}`}>
            {jurisdiction.adminEmails.length > 1
              ? 'Jurisdiction admins'
              : 'Jurisdiction admin'}
          </div>
          {jurisdiction.adminEmails.map(email => (
            <div key={email} style={rowStyle}>
              {email}
              <CopyToClipboard
                iconOnly
                label="Copy email"
                getText={() => ({ text: email, format: 'text/plain' })}
              />
            </div>
          ))}
        </div>
        {(canSelectContest || canUnfinalize) && (
          <div style={rowStyle}>
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
          </div>
        )}
        <Divider style={{ margin: '16px 0' }} />
        {selectedContestId && shownBatches.length === 0 && (
          <p className={Classes.TEXT_MUTED}>
            {jurisdiction.currentRoundStatusByContestId![selectedContestId]
              ? 'No discrepancies for this contest'
              : 'No batches sampled for this contest'}
          </p>
        )}
        {shownBatches.map(({ name, isExtra, discrepancies: byContest }) => {
          const shownContests = Object.entries(byContest).filter(
            ([contestId]) =>
              !selectedContestId || contestId === selectedContestId
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
              {shownContests.map(([contestId, contestDiscrepancies]) => (
                <div key={contestId}>
                  <TableHeader style={rowStyle}>
                    <span>{getContestName(contests, contestId)}</span>
                    <CopyToClipboard
                      iconOnly
                      label="Copy contest name"
                      getText={() => ({
                        text: getContestName(contests, contestId),
                        format: 'text/plain',
                      })}
                    />
                  </TableHeader>
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
                        .filter(
                          choiceID =>
                            contestDiscrepancies.discrepancies[choiceID] !== 0
                        )
                        .map(choiceId => (
                          <tr key={choiceId}>
                            <td>
                              {getChoiceName(contests, contestId, choiceId)}
                            </td>
                            <td>
                              {formatVoteCount(
                                contestDiscrepancies.reportedVotes[choiceId]
                              )}
                            </td>
                            <td>
                              {formatVoteCount(
                                contestDiscrepancies.auditedVotes[choiceId]
                              )}
                            </td>
                            <td>
                              {formatVoteCount(
                                contestDiscrepancies.discrepancies[choiceId]
                              )}
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </ContestDiscrepanciesTable>
                </div>
              ))}
            </div>
          )
        })}
      </div>
    </Dialog>
  )
}

export { JurisdictionDiscrepancies }
