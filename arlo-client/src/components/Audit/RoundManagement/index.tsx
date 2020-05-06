import React, { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { useParams } from 'react-router-dom'
import { Wrapper } from '../../Atoms/Wrapper'
import H2Title from '../../Atoms/H2Title'
import { IRound } from '../useRoundsJurisdictionAdmin'
import { IErrorResponse, IBallot } from '../../../types'
import { api, checkAndToast } from '../../utilities'
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

  const [ballots, setBallots] = useState<IBallot[]>([])
  useEffect(() => {
    ;(async () => {
      try {
        const response: { ballots: IBallot[] } | IErrorResponse = await api(
          `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${round.id}/ballot-draws`
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
  }, [electionId, jurisdictionId, round])

  // const [{ online }] = useAuditSettings(electionId!)

  if (!round.isAuditComplete) {
    const { roundNum } = round
    return (
      <Wrapper className="single-page left">
        <H2Title>Round {roundNum} Audit Board Setup</H2Title>
        <CreateAuditBoards
          auditBoards={auditBoards}
          createAuditBoards={createAuditBoards}
        />
        {auditBoards.length > 0 && (
          <>
            <FormButton
              verticalSpaced
              onClick={() =>
                window.open(
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
            {/* make conditional on online */}
            <FormButton
              verticalSpaced
              onClick={() => downloadDataEntry(auditBoards)}
            >
              Download Audit Board Credentials for Data Entry
            </FormButton>
            <RoundProgress auditBoards={auditBoards} round={round} />
            {/* {online ? <RoundProgress /> : <RoundDataEntry />} */}
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
