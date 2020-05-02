import React from 'react'
import { ProgressBar } from '@blueprintjs/core'
import styled from 'styled-components'
import H2Title from '../../Atoms/H2Title'
import { IBallot, IAuditBoard, BallotStatus } from '../../../types'
import { IRound } from '../useRoundsJurisdictionAdmin'

const MainBarWrapper = styled.div`
  margin-bottom: 20px;
  width: 500px;
  font-size: 16px;
`

const SmallBarWrapper = styled.div`
  margin-bottom: 10px;
  width: 400px;
`

const RoundProgress = ({
  rounds,
  ballots,
  auditBoards,
}: {
  rounds: IRound[]
  ballots: IBallot[]
  auditBoards: IAuditBoard[]
}) => {
  const completeBallots = ballots.filter(
    b => b.status !== BallotStatus.NOT_AUDITED
  ).length
  const ballotsPerAB = auditBoards.map(a => {
    const all = ballots.filter(b => b.auditBoard!.id === a.id)
    return [all.filter(b => b.status).length, all.length]
  })
  return (
    <>
      <H2Title>Round {rounds.length} Progress</H2Title>
      <MainBarWrapper>
        <span>
          {completeBallots} of {ballots.length} ballots audited{' '}
        </span>
        <ProgressBar
          value={completeBallots / ballots.length}
          animate={completeBallots < ballots.length}
          intent="primary"
        />
      </MainBarWrapper>
      {ballotsPerAB.map((v, i) => (
        <SmallBarWrapper key={auditBoards[i].id}>
          <span>{`${auditBoards[i].name}: ${v[0]} of ${v[1]} ballots audited `}</span>
          <ProgressBar
            value={v[0] / v[1]}
            animate={v[0] < v[1]}
            intent="primary"
          />
        </SmallBarWrapper>
      ))}
    </>
  )
}

export default RoundProgress
