import React from 'react'
import { ProgressBar, H4, Tag, Intent } from '@blueprintjs/core'
import styled from 'styled-components'
import { IAuditBoard } from '../useAuditBoards'

const MainBarWrapper = styled.div`
  margin-bottom: 30px;
  width: 500px;
  font-size: 16px;
`

const SmallBarWrapper = styled.div`
  margin-bottom: 30px;
  width: 400px;
  > div:first-child {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
  }
  .bp3-tag {
    margin-left: 5px;
  }
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
  const progressIntent = ((): Intent => {
    if (auditedBallots === 0) return Intent.NONE
    if (auditedBallots < sampledBallots) return Intent.PRIMARY
    return Intent.SUCCESS
  })()
  return (
    <>
      <MainBarWrapper>
        <H4>Audit Board Progress</H4>
        <p>
          {auditedBallots} of {sampledBallots} ballots audited{' '}
        </p>
        <ProgressBar
          value={auditedBallots / sampledBallots}
          animate={false}
          intent={progressIntent}
        />
      </MainBarWrapper>
      {auditBoards.map(
        ({
          id,
          name,
          currentRoundStatus: { numAuditedBallots, numSampledBallots },
          signedOffAt,
        }) => {
          const [status, intent] = ((): [string, Intent] => {
            if (numAuditedBallots === 0) return ['Not started', Intent.NONE]
            if (numAuditedBallots < numSampledBallots)
              return ['In progress', Intent.PRIMARY]
            if (!signedOffAt) return ['Not signed off', Intent.WARNING]
            return ['Signed off', Intent.SUCCESS]
          })()
          return (
            <SmallBarWrapper key={id}>
              {numSampledBallots > 0 ? (
                <>
                  <div>
                    <span>{`${name}: ${numAuditedBallots} of ${numSampledBallots} ballots audited `}</span>
                    <Tag intent={intent}>{status}</Tag>
                  </div>
                  <ProgressBar
                    value={numAuditedBallots / numSampledBallots}
                    animate={false}
                    intent={intent}
                  />
                </>
              ) : (
                <>{name}: no ballots to audit</>
              )}
            </SmallBarWrapper>
          )
        }
      )}
    </>
  )
}

export default RoundProgress
