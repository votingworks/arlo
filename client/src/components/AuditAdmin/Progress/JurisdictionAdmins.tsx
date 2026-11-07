import React from 'react'
import { Classes } from '@blueprintjs/core'
import { IJurisdiction } from '../../useJurisdictions'
import CopyToClipboard from '../../Atoms/CopyToClipboard'

const JurisdictionAdmins: React.FC<{ jurisdiction: IJurisdiction }> = ({
  jurisdiction,
}) => (
  <div style={{ marginBottom: '16px' }}>
    <div className={`${Classes.TEXT_MUTED} ${Classes.TEXT_SMALL}`}>
      {jurisdiction.adminEmails.length > 1
        ? 'Jurisdiction Admins'
        : 'Jurisdiction Admin'}
    </div>
    {jurisdiction.adminEmails.map(email => (
      <div
        key={email}
        style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
      >
        {email}
        <CopyToClipboard
          iconOnly
          label="Copy email"
          getText={() => ({ text: email, format: 'text/plain' })}
        />
      </div>
    ))}
  </div>
)

export default JurisdictionAdmins
