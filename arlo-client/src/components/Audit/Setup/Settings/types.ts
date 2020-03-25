import { IAuditSettings } from '../../../../types'

export type IValues = Pick<
  IAuditSettings,
  'electionName' | 'online' | 'randomSeed' | 'riskLimit'
>
