import React from 'react'
import { Button } from '@blueprintjs/core'
import { toast } from 'react-toastify'

import { Confirm, useConfirm } from '../Atoms/Confirm'
import { IRound, useReopenCurrentRound, useUndoRoundStart } from './support-api'
import { StyledTable } from '../Atoms/Table'
import StatusTag from '../Atoms/StatusTag'

interface IProps {
  electionId: string
  rounds: IRound[]
}

const RoundsTable = ({ electionId, rounds }: IProps): React.ReactElement => {
  if (rounds.length === 0) {
    return (
      <StyledTable style={{ tableLayout: 'auto' }}>
        <thead>
          <tr>
            <th>Round</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Round 1</td>
            <td>
              <StatusTag>Not started</StatusTag>
            </td>
          </tr>
        </tbody>
      </StyledTable>
    )
  }

  return (
    <StyledTable style={{ tableLayout: 'auto' }}>
      <thead>
        <tr>
          <th>Round</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {rounds.map((round, i) => (
          <tr key={round.id}>
            <td>Round {round.roundNum}</td>
            <td>
              {round.endedAt ? (
                <StatusTag intent="success">Completed</StatusTag>
              ) : (
                <StatusTag intent="warning">In progress</StatusTag>
              )}
            </td>
            <td>
              {i === rounds.length - 1 && (
                <LastRoundAction electionId={electionId} round={round} />
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </StyledTable>
  )
}

interface ILastRoundActionProps {
  electionId: string
  round: IRound
}

const LastRoundAction = ({
  electionId,
  round,
}: ILastRoundActionProps): React.ReactElement => {
  const { confirm, confirmProps } = useConfirm()
  const reopenCurrentRound = useReopenCurrentRound()
  const undoRoundStart = useUndoRoundStart(electionId)

  if (round.endedAt) {
    return (
      <>
        <Button
          onClick={() =>
            confirm({
              title: 'Confirm',
              description: `Are you sure you want to reopen round ${round.roundNum}?`,
              yesButtonLabel: 'Reopen',
              onYesClick: async () => {
                await reopenCurrentRound.mutateAsync({ electionId })
                toast.success(`Reopened round ${round.roundNum}`)
              },
            })
          }
        >
          Reopen
        </Button>
        <Confirm {...confirmProps} />
      </>
    )
  }
  return (
    <>
      <Button
        onClick={() =>
          confirm({
            title: 'Confirm',
            description: `Are you sure you want to undo the start of round ${round.roundNum}?`,
            yesButtonLabel: 'Undo Start',
            onYesClick: async () => {
              await undoRoundStart.mutateAsync({ roundId: round.id })
              toast.success(`Undid the start of round ${round.roundNum}`)
            },
          })
        }
      >
        Undo Start
      </Button>
      <Confirm {...confirmProps} />
    </>
  )
}

export default RoundsTable
