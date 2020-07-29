import React, { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { useParams } from 'react-router-dom'
import { Wrapper } from '../../Atoms/Wrapper'
import H2Title from '../../Atoms/H2Title'
import { IRound } from '../useRoundsJurisdictionAdmin'
import { IBallot } from '../../../types'
import { api, checkAndToast, apiDownload } from '../../utilities'
// import useAuditSettings from '../Setup/useAuditSettings'
import CreateAuditBoards from './CreateAuditBoards'
import RoundProgress from './RoundProgress'
// import RoundDataEntry from './RoundDataEntry'
import FormButton from '../../Atoms/Form/FormButton'
import {
  downloadPlaceholders,
  downloadLabels,
  downloadDataEntry,
} from './generateSheets'
import { IAuditBoard } from '../useAuditBoards'
import QRs from './QRs'
import useAuditSettings from '../useAuditSettings'
import RoundDataEntry from './RoundDataEntry'

interface IProps {
  round: IRound
  auditBoards: IAuditBoard[]
  createAuditBoards: (auditBoards: { name: string }[]) => Promise<boolean>
}

const RoundManagement = ({ round, auditBoards, createAuditBoards }: IProps) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()

  const [ballots, setBallots] = useState<IBallot[] | null>(null)
  useEffect(() => {
    ;(async () => {
      try {
        const response: { ballots: IBallot[] } = await api(
          `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${round.id}/ballots`
        )
        // checkAndToast left here for consistency and reference but not tested since it's vestigial
        /* istanbul ignore next */
        if (checkAndToast(response)) return
        setBallots(response.ballots)
      } catch (err) /* istanbul ignore next */ {
        // TEST TODO
        toast.error(err.message)
      }
    })()
  }, [
    electionId,
    jurisdictionId,
    round,
    // We need to reload the ballots after we create the audit boards in order
    // to populate ballot.auditBoard
    auditBoards,
  ])

  const [{ online }] = useAuditSettings(electionId)

  if (!ballots) return null // Still loading

  if (!round.isAuditComplete) {
    const { roundNum } = round
    return (
      <Wrapper className="single-page left">
        <H2Title>Round {roundNum} Audit Board Setup</H2Title>
        <CreateAuditBoards
          auditBoards={auditBoards}
          createAuditBoards={createAuditBoards}
          numBallots={ballots.length}
          roundNum={roundNum}
        />
        {auditBoards.length > 0 && (
          <>
            <FormButton
              verticalSpaced
              onClick={() =>
                apiDownload(
                  `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${round.id}/retrieval-list`
                )
              }
            >
              Download Aggregated Ballot Retrival List for Round {roundNum}
            </FormButton>
            <FormButton
              verticalSpaced
              onClick={() => downloadPlaceholders(roundNum, ballots)}
            >
              Download Placeholder Sheets for Round {roundNum}
            </FormButton>
            <FormButton
              verticalSpaced
              onClick={() => downloadLabels(roundNum, ballots)}
            >
              Download Ballot Labels for Round {roundNum}
            </FormButton>
            {online && (
              <>
                <FormButton
                  verticalSpaced
                  onClick={() => downloadDataEntry(auditBoards)}
                >
                  Download Audit Board Credentials for Data Entry
                </FormButton>
                <QRs passphrases={auditBoards.map(b => b.passphrase)} />
              </>
            )}
            {online ? (
              <RoundProgress auditBoards={auditBoards} round={round} />
            ) : (
              <RoundDataEntry round={round} />
            )}
          </>
        )}
      </Wrapper>
    )
  }
  return (
    <Wrapper className="single-page">
      <H2Title>
        Congratulations! Your Risk-Limiting Audit is now complete.
      </H2Title>
    </Wrapper>
  )
}

export default RoundManagement
