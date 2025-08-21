import { useAuthDataContext } from './UserContext'
import { assert } from './utilities'

export interface BatchInventoryConfig {
  showBallotManifest: boolean
}

const BATCH_INVENTORY_CONFIGS: {
  [organizationId: string]: BatchInventoryConfig
} = {
  // Georgia
  'b216ad0d-1481-44e4-a2c1-95da40175084': {
    showBallotManifest: true,
  },
  // Nevada
  'b6f34a14-1cb2-4d44-8f29-b4fe04fd2932': {
    showBallotManifest: false,
  },
  // Rhode Island
  '0225f953-c201-46c8-8582-617eb72ce2b4': {
    showBallotManifest: false,
  },
  // Washington
  '541e7ab0-5d05-4635-b988-f66a254902c7': {
    showBallotManifest: false,
  },

  // Audit Specialist Sandbox
  'b7b99303-b1ac-4b52-8a02-22c10846cff3': {
    showBallotManifest: true,
  },
  // Ginny's Sandbox
  'b45800ff-a239-42b3-b285-414cb94d2b6b': {
    showBallotManifest: true,
  },
  // Verified Voting Sandbox
  'e348fcfd-bd23-4b96-a003-6c3a79abd240': {
    showBallotManifest: true,
  },
  // VotingWorks Internal Sandbox
  'a67791e3-90a0-4d4e-a5e7-929f82bf4ce6': {
    showBallotManifest: false,
  },
  // Maryland (Brian local development)
  'b6c82242-7737-49dd-b315-cc34f8ad8de0': {
    showBallotManifest: true,
  },
}

// eslint-disable-next-line import/prefer-default-export
export const useBatchInventoryFeatureFlag = (
  jurisdictionId: string
): BatchInventoryConfig | undefined => {
  const auth = useAuthDataContext()
  assert(auth?.user?.type === 'jurisdiction_admin')
  const jurisdiction = auth.user.jurisdictions.find(
    j => j.id === jurisdictionId
  )
  const { organizationId } = jurisdiction?.election || {}
  return organizationId === undefined
    ? undefined
    : BATCH_INVENTORY_CONFIGS[organizationId]
}
