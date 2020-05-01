import React, { useState, useEffect, useCallback } from 'react'
import { toast } from 'react-toastify'
import { useParams } from 'react-router-dom'
import Wrapper from '../../Atoms/Wrapper'
import H2Title from '../../Atoms/H2Title'
import { useAuthDataContext } from '../../UserContext'
import { IRound, IErrorResponse, IBallot, IAuditBoard } from '../../../types'
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

const RoundManagement = () => {
  const { electionId } = useParams()
  const { meta } = useAuthDataContext()
  const { jurisdictions } = meta!
  const jurisdictionId = jurisdictions[0].id

  const [rounds, setRounds] = useState<IRound[]>([])
  useEffect(() => {
    if (electionId && jurisdictionId) {
      ;(async () => {
        try {
          const response: { rounds: IRound[] } | IErrorResponse = await api(
            `/election/${electionId}/jurisdiction/${jurisdictionId}/round`
          )
          // checkAndToast left here for consistency and reference but not tested since it's vestigial
          /* istanbul ignore next */
          if (checkAndToast(response)) return
          setRounds(response.rounds)
        } catch (err) /* istanbul ignore next */ {
          // TEST TODO
          toast.error(err.message)
        }
      })()
    }
  }, [electionId, jurisdictionId, setRounds])

  const [ballots, setBallots] = useState<IBallot[]>([])
  useEffect(() => {
    if (electionId && jurisdictionId && rounds.length) {
      ;(async () => {
        try {
          const response: { ballots: IBallot[] } | IErrorResponse = await api(
            `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${rounds[rounds.length - 1].id}/ballot-draws`
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
    }
  }, [electionId, jurisdictionId, rounds, setBallots])

  // const [{ online }] = useAuditSettings(electionId!)

  const [auditBoards, setAuditBoards] = useState<IAuditBoard[]>([])
  const getAuditBoards = useCallback(async () => {
    try {
      const response:
        | { auditBoards: IAuditBoard[] }
        | IErrorResponse = await api(
        `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${rounds[rounds.length - 1].id}/audit-board`
      )
      // checkAndToast left here for consistency and reference but not tested since it's vestigial
      /* istanbul ignore next */
      if (checkAndToast(response)) return
      setAuditBoards(response.auditBoards)
    } catch (err) /* istanbul ignore next */ {
      // TEST TODO
      toast.error(err.message)
    }
  }, [electionId, jurisdictionId, rounds])
  useEffect(() => {
    if (electionId && jurisdictionId && rounds.length) {
      getAuditBoards()
    }
  }, [electionId, jurisdictionId, rounds, getAuditBoards])

  if (rounds.length > 0 && rounds[rounds.length - 1].isAuditComplete)
    return (
      <Wrapper className="single-page">
        <H2Title>
          Congratulations! Your Risk-Limiting Audit is now complete.
        </H2Title>
      </Wrapper>
    )
  return (
    <Wrapper className="single-page left">
      <H2Title>Round {rounds.length} Audit Board Setup</H2Title>
      {rounds.length > 0 && (
        <CreateAuditBoards
          auditBoards={auditBoards}
          electionId={electionId!}
          jurisdictionId={jurisdictionId}
          roundId={rounds[rounds.length - 1].id}
          getAuditBoards={getAuditBoards}
        />
      )}
      {auditBoards.length > 0 && (
        <>
          <FormButton
            verticalSpaced
            onClick={() =>
              window.open(
                `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${rounds[rounds.length - 1].id}/retrieval-list`
              )
            }
          >
            Download Aggregated Ballot Retrival List for Round {rounds.length}
          </FormButton>
          <FormButton
            verticalSpaced
            onClick={() => downloadPlaceholders(rounds.length, ballots)}
          >
            Download Placeholder Sheets for Round {rounds.length}
          </FormButton>
          <FormButton
            verticalSpaced
            onClick={() => downloadLabels(rounds.length, ballots)}
          >
            Download Ballot Labels for Round {rounds.length}
          </FormButton>
          {/* make conditional on online */}
          <FormButton
            verticalSpaced
            onClick={() => downloadDataEntry(auditBoards)}
          >
            Download Audit Board Credentials for Data Entry
          </FormButton>
          <RoundProgress />
          {/* {online ? <RoundProgress /> : <RoundDataEntry />} */}
        </>
      )}
    </Wrapper>
  )
}

export default RoundManagement
