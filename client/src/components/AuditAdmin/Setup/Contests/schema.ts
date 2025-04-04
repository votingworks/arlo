import * as Yup from 'yup'
import number, { parse as parseNumber } from '../../../../utils/number-schema'
import { IChoice } from '../../../../types'
import { IAuditSettings } from '../../../useAuditSettings'

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
const contestsSchema = (auditType: IAuditSettings['auditType']) =>
  Yup.object().shape({
    contests: Yup.array()
      .required()
      .of(
        Yup.object().shape({
          name: Yup.string().required('Required'),
          numWinners: number()
            .typeError('Must be a number')
            .integer('Must be an integer')
            .min(0, 'Must be a positive number')
            .required('Required'),
          votesAllowed: number()
            .typeError('Must be a number')
            .integer('Must be an integer')
            .min(0, 'Must be a positive number')
            .required('Required'),
          ...(auditType === 'BALLOT_POLLING' && {
            totalBallotsCast: number()
              .typeError('Must be a number')
              .integer('Must be an integer')
              .min(0, 'Must be a positive number')
              .test(
                'is-sufficient',
                'Must be greater than or equal to the sum of votes for each candidate/choice',
                function testTotalBallotsCast(value?: unknown) {
                  const ballots = parseNumber(value)
                  const { choices } = this.parent
                  const totalVotes = choices.reduce(
                    (sum: number, choiceValue: IChoice) =>
                      sum + (parseNumber(choiceValue.numVotes) || 0),
                    0
                  )
                  const allowedVotesPerBallot: number = this.parent.votesAllowed
                  const totalAllowedVotes = allowedVotesPerBallot * ballots
                  return totalAllowedVotes >= totalVotes || this.createError()
                }
              )
              .required('Required'),
            jurisdictionIds: Yup.array()
              .required('Required')
              .of(Yup.string()),
          }),
          ...(auditType === 'BATCH_COMPARISON' && {
            pendingBallots: number()
              .typeError('Must be a number')
              .integer('Must be an integer')
              .min(0, 'Must be a positive number'),
          }),
          choices: Yup.array()
            .required()
            .of(
              Yup.object().shape({
                name: Yup.string().required('Required'),
                numVotes: number()
                  .typeError('Must be a number')
                  .integer('Must be an integer')
                  .min(0, 'Must be a positive number')
                  .required('Required'),
              })
            ),
        })
      ),
  })

export default contestsSchema
