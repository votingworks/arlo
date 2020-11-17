import React, { useState } from 'react'
import copy from 'copy-to-clipboard'
import { Button } from '@blueprintjs/core'

const CopyToClipboard = ({ getText }: { getText: () => string }) => {
  const [copied, setCopied] = useState(false)
  return (
    <Button
      icon={copied ? 'tick-circle' : 'clipboard'}
      onClick={() => {
        const success = copy(getText(), { format: 'text/html' })
        if (success) {
          setCopied(true)
          setTimeout(() => setCopied(false), 3000)
        }
      }}
      style={{ width: '160px' }}
    >
      {copied ? 'Copied' : 'Copy to clipboard'}
    </Button>
  )
}

export default CopyToClipboard
