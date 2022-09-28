import { useAuthDataContext } from './UserContext'
import { assert } from './utilities'

const ENABLE_BATCH_INVENTORY_ORGANIZATION_IDS = [
  'b216ad0d-1481-44e4-a2c1-95da40175084', // Georgia
  'a67791e3-90a0-4d4e-a5e7-929f82bf4ce6', // VotingWorks Internal Sandbox
  'b45800ff-a239-42b3-b285-414cb94d2b6b', // Ginny's Sandbox
  'b7b99303-b1ac-4b52-8a02-22c10846cff3', // Audit Specialist Sandbox
  'e348fcfd-bd23-4b96-a003-6c3a79abd240', // Verified Voting Sandbox
]

// eslint-disable-next-line import/prefer-default-export
export const useBatchInventoryFeatureFlag = (
  jurisdictionId: string
): boolean => {
  const auth = useAuthDataContext()
  assert(auth?.user?.type === 'jurisdiction_admin')
  const jurisdiction = auth.user.jurisdictions.find(
    j => j.id === jurisdictionId
  )
  const { organizationId } = jurisdiction?.election || {}
  return (
    organizationId !== undefined &&
    ENABLE_BATCH_INVENTORY_ORGANIZATION_IDS.includes(organizationId)
  )
}
