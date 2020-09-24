import React from 'react'
import { ProgressBar, H4 } from '@blueprintjs/core'
import styled from 'styled-components'
import { IAuditBoard } from '../useAuditBoards'

const MainBarWrapper = styled.div`
  margin-bottom: 20px;
  width: 500px;
  font-size: 16px;
`

const SmallBarWrapper = styled.div`
  margin-bottom: 10px;
  width: 400px;
`

const RoundProgress = ({ auditBoards }: { auditBoards: IAuditBoard[] }) => {
  if (!auditBoards.length) return null
  const sum = (ns: number[]) => ns.reduce((a, b) => a + b)
  const auditedBallots = sum(
    auditBoards.map(ab => ab.currentRoundStatus.numAuditedBallots)
  )
  const sampledBallots = sum(
    auditBoards.map(ab => ab.currentRoundStatus.numSampledBallots)
  )
  return (
    <>
      <MainBarWrapper>
        <H4>Audit Board Progress</H4>
        <span>
          {auditedBallots} of {sampledBallots} ballots audited{' '}
        </span>
        <ProgressBar
          value={auditedBallots / sampledBallots}
          animate={auditedBallots < sampledBallots}
          intent="primary"
        />
      </MainBarWrapper>
      {auditBoards.map(
        ({
          id,
          name,
          currentRoundStatus: { numAuditedBallots, numSampledBallots },
        }) => (
          <SmallBarWrapper key={id}>
            {numSampledBallots > 0 ? (
              <>
                <span>{`${name}: ${numAuditedBallots} of ${numSampledBallots} ballots audited `}</span>
                <ProgressBar
                  value={numAuditedBallots / numSampledBallots}
                  animate={numAuditedBallots < numSampledBallots}
                  intent="primary"
                />
              </>
            ) : (
              <span>{name}: no ballots to audit</span>
            )}
          </SmallBarWrapper>
        )
      )}
    </>
  )
}

export default RoundProgress
