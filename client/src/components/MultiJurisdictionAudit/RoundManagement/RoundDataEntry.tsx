import React from 'react'
import { useParams } from 'react-router-dom'
import H2Title from '../../Atoms/H2Title'
import useContests from '../useContests'
import { IRound } from '../useRoundsJurisdictionAdmin'

interface IParams {
  electionId: string
}

interface IProps {
  round: IRound
}

const RoundDataEntry = ({ round }: IProps) => {
  const { electionId } = useParams<IParams>()
  const [contests] = useContests(electionId)
  return (
    <>
      <H2Title>Round {round.roundNum} Data Entry</H2Title>
      {contests &&
        contests.map(contest => {
          return <p key={contest.id}>{contest.name}</p>
        })}
    </>
  )
}

export default RoundDataEntry
